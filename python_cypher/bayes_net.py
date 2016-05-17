import collections
import itertools
import hashlib
import random
import math
import networkx as nx


class BayesNetworkException(Exception):
    pass


def loglimit(x, base=2.):
    return 0. if x == 0. else math.log(x, base)


def information(x):
    return max(x * loglimit(x), 0.)


def mutual_information(pxy, pxpy):
    return max(pxy * loglimit(pxy / pxpy), 0.)


class BayesNode(object):
    """
    Class for nodes in the Bayes network
    """
    def __init__(self, label=None, note=None, prior_probability=None,
                 clamped=False, labels_to_nodes_dict=None):
        self.children = []
        self.parents = []
        self.hash_value = hashlib.md5(str(id(self))).hexdigest()
        self.label = label or self.hash_value[:5]
        self.note = note or ''
        self.prior_probability = prior_probability
        self.assignment = None
        self.activation_state = None
        self.clamped = clamped
        self.labels_to_nodes_dict = labels_to_nodes_dict or {}

    @property
    def node_dict(self):
        return self.all_connected_nodes_dict()

    def clamp(self, activation_state, label=None):
        label = label or self.label
        self.clamped = True
        self.activation_state = activation_state

    def set_prior_probability(self, prior_probability):
        self.prior_probability = prior_probability

    def connect(self, target):
        self.children.append(target)
        target.parents.append(self)
        for node in self.all_connected_nodes():
            setattr(node, self.label, self)
            setattr(node, target.label, target)

    def disconnect(self, target):
        self.children = [i for i in self.children if i is not target]
        target.parents = [i for i in target.parents if i is not self]

    def is_root(self):
        return len(self.parents) == 0

    def all_connected_nodes(self):
        seen_node_hashes = set()
        seen_nodes = [self]

        def _inner_function(node):
            seen_node_hashes.add(node.hash_value)
            for connected_node in node.children + node.parents:
                if connected_node.hash_value not in seen_node_hashes:
                    seen_nodes.append(connected_node)
                    seen_node_hashes.add(connected_node)
                    _inner_function(connected_node)

        _inner_function(self)
        seen_nodes.sort(key=lambda x: x.hash_value)
        return seen_nodes

    def all_connected_node_labels(self):
        return set(node.label for node in self.all_connected_nodes())

    def all_connected_nodes_dict(self):
        return {node.label: node for node in self.all_connected_nodes()}

    def root_nodes(self):
        root_nodes = [i for i in self.all_connected_nodes()
                      if len(i.parents) == 0]
        return root_nodes

    def validate(self, raise_exception=True):
        """
        Check for stuff
        """
        # Check that all root nodes have a prior probability
        root_nodes_without_prior = [
            node.label for node in self.root_nodes()
            if not isinstance(node.prior_probability, float)]
        root_nodes_have_prior = not root_nodes_without_prior

        if not root_nodes_have_prior and raise_exception:
            raise BayesNetworkException('Root node without prior')

    def set_dependencies(self):
        parent_assignment_dict = {
            assignment_tuple: collections.defaultdict(int) for assignment_tuple
            in itertools.product(*([[True, False]] * len(self.parents)))}
        self.parent_assignment_dict = parent_assignment_dict

    def set_all_dependencies(self):
        for node in self.all_connected_nodes():
            node.set_dependencies()

    def seed_probabilities(self, data):
        all_nodes = self.all_connected_nodes()
        for row in data:
            for node in all_nodes:
                node_assignment = row[node.label]
                parent_assignment = tuple(
                    [bool(row[parent.label]) for parent in node.parents])
                node.parent_assignment_dict[
                    parent_assignment][node_assignment] += 1
        for node in all_nodes:
            node.activation_probability_dict = collections.defaultdict(float)
            for parent_assignment, outcome_dict in (
                    node.parent_assignment_dict.iteritems()):
                try:
                    activation_probability = (
                    float(outcome_dict[True]) /
                    (outcome_dict[True] + outcome_dict[False]))
                except:
                    import pdb; pdb.set_trace()
                node.activation_probability_dict[parent_assignment] = (
                    activation_probability)
        for node in all_nodes:
            if node.is_root():
                prior_probability = float(
                    len([i for i in data if i[node.label]])) / len(data)
                node.prior_probability = prior_probability

    def monte_carlo(self, iterations=1000,
                    assumptions=None, end_conditions=None):
        all_nodes = self.all_connected_nodes()
        results = [] 
        def _iteration():
            sentinal = True
            while sentinal:
                sentinal = False
                for node in all_nodes:
                    if node.activation_state is not None:
                        continue
                    # Case: It's a root node
                    if len(node.parents) == 0:
                        node.activation_state = (
                            random.random() < node.prior_probability)
                        sentinal = True
                    # Case: It's not a root node
                    else:
                        if not all(
                            parent.activation_state is not None
                                for parent in node.parents):
                            continue
                        parent_activations = tuple(
                            [parent.activation_state for parent
                             in node.parents])
                        node.activation_state = (
                            random.random() <
                            node.activation_probability_dict[
                                parent_activations])
                        sentinal = True
            results.append(
                {node.label: node.activation_state for node in all_nodes})
            for node in all_nodes:
                node.activation_state = None
        iteration = 0
        while iteration < iterations:
            _iteration()
            iteration += 1
        if assumptions is None:
            return results

        trials_meeting_assumptions = 0
        trials_meeting_end_conditions = 0
        for result in results:
            if all(assumptions[node_label] == result[node_label]
                   for node_label in assumptions.iterkeys()):
                trials_meeting_assumptions += 1
                if all(end_conditions[node_label] == result[node_label]
                       for node_label in end_conditions.iterkeys()):
                    trials_meeting_end_conditions += 1
        try:
            out = (trials_meeting_assumptions,
               trials_meeting_end_conditions,
               (float(trials_meeting_end_conditions) /
               trials_meeting_assumptions))
        except ZeroDivisionError:
            import pdb; pdb.set_trace()
        return out


def event_and_pairwise_tallies(event_data):
    pairwise_tally = collections.defaultdict(float)
    event_tally = collections.defaultdict(float)
    pairwise_events = list(itertools.combinations(event_data[0].keys(), 2))
    for row in event_data:
        for event_pair in pairwise_events:
            event_1, event_2 = event_pair
            if row[event_1] and row[event_2]:
                pairwise_tally[event_pair] += 1
        for event, outcome in row.iteritems():
            if outcome:
                event_tally[event] += 1
    number_of_events = float(len(event_data))
    event_tally = {event: tally / number_of_events for event, tally in
                   event_tally.iteritems()}
    pairwise_tally = {event_pair: tally / number_of_events for
                      event_pair, tally in pairwise_tally.iteritems()}
    return event_tally, pairwise_tally


def mwst_skeleton(event_data):
    event_tally, pairwise_tally = event_and_pairwise_tallies(event_data)
    mutual_information_dict = {}
    for event_pair, pxy in pairwise_tally.iteritems():
        event_1, event_2 = event_pair
        px = event_tally[event_1]
        py = event_tally[event_2]
        pxpy = px * py
        mutual_information_dict[event_pair] = mutual_information(pxy, pxpy)
    ordered_mutual_information = sorted(
        ((event_pair, mutual_information) for event_pair, mutual_information
         in mutual_information_dict.iteritems()),
        key=lambda x: x[1], reverse=True)
    tmp_graph = nx.Graph()
    for event_pair, _ in ordered_mutual_information:
        event_1, event_2 = event_pair
        tmp_graph.add_edge(event_1, event_2)
        # We want it to error out, because we don't want cycles
        # If it doesn't throw an exception, then there's a cycle, which
        # we need to remove
        try:
            nx.find_cycle(tmp_graph)
            tmp_graph.remove_edge(event_1, event_2)
        except nx.exception.NetworkXNoCycle as err:
            # No cycles -- which is what we want
            pass
    return tmp_graph



if __name__ == '__main__':
    test_data = [
    {'verdict': 0, 'order': 0, 'guard_1': 0, 'guard_2': 0, 'dead': 0},
    {'verdict': 0, 'order': 0, 'guard_1': 0, 'guard_2': 0, 'dead': 0},
    {'verdict': 1, 'order': 1, 'guard_1': 1, 'guard_2': 1, 'dead': 1},
    {'verdict': 1, 'order': 0, 'guard_1': 0, 'guard_2': 0, 'dead': 0},
    {'verdict': 1, 'order': 1, 'guard_1': 1, 'guard_2': 0, 'dead': 1},
    {'verdict': 1, 'order': 1, 'guard_1': 1, 'guard_2': 1, 'dead': 1},
    {'verdict': 1, 'order': 1, 'guard_1': 0, 'guard_2': 1, 'dead': 1},
    {'verdict': 1, 'order': 1, 'guard_1': 0, 'guard_2': 0, 'dead': 0},
    {'verdict': 0, 'order': 1, 'guard_1': 1, 'guard_2': 1, 'dead': 1},
    {'verdict': 1, 'order': 1, 'guard_1': 1, 'guard_2': 1, 'dead': 1}]

    # event_tally, pairwise_tally = event_and_pairwise_tallies(test_data)
    tmp_graph = mwst_skeleton(test_data)

    # Now we have the skeleton of a tree. Need to choose a root node,
    # which can be arbitrary, and start building the `BayesNode` structure.
    all_nodes = tmp_graph.nodes()
    all_edges = tmp_graph.edges()
    all_nodes_dict = {node: BayesNode(label=node) for node in all_nodes}
    root = random.choice(all_nodes_dict.values())

    def _connect_nodes(some_node):
        # This list comprehension got a little out of hand
        for child_node in [
            node_label for node_label, node in all_nodes_dict.iteritems() if
            (node_label, some_node.label,) in all_edges or (
            some_node.label, node_label,) in all_edges and
            node_label != some_node.label and node_label not in
            some_node.all_connected_node_labels() and
            some_node not in node.parents and
                some_node not in node.children]:
            if (all_nodes_dict[child_node] in some_node.children or
                    all_nodes_dict[child_node] in some_node.parents):
                continue
            print 'connecting', some_node.label, child_node
            some_node.connect(all_nodes_dict[child_node])
            _connect_nodes(all_nodes_dict[child_node])

    _connect_nodes(root)
    node_1 = BayesNode(label='verdict')
    node_2 = BayesNode(label='order')
    node_3 = BayesNode(label='guard_1')
    node_4 = BayesNode(label='guard_2')
    node_5 = BayesNode(label='dead')
    node_1.connect(node_2)
    node_2.connect(node_3)
    node_2.connect(node_4)
    node_3.connect(node_5)
    node_4.connect(node_5)
    node_5.set_all_dependencies()
    node_1.prior_probability = .9
    node_1.seed_probabilities(test_data)
    root.set_all_dependencies()
    # root.prior_probability = .5
    root.seed_probabilities(test_data)

    
    print root.monte_carlo(
        iterations=10000,
        assumptions={'guard_1': False},
        end_conditions={'dead': True})


