# -*- coding: utf-8 -*-

import itertools
import networkx as nx
import copy
import hashlib
import random
import time
from cypher_tokenizer import *
from cypher_parser import *

PRINT_TOKENS = False
PRINT_MATCHING_ASSIGNMENTS = False


class CypherParserBaseClass(object):
    """Base class that specific parsers will inherit from. Certain methods
       must be defined in the child class. See the docs."""
    def __init__(self):
        self.tokenizer = cypher_tokenizer
        self.parser = cypher_parser

    def parse(self, query):
        """Calls yacc to parse the query string into an AST."""
        self.tokenizer.input(query)
        tok = self.tokenizer.token()
        while tok:
            if PRINT_TOKENS:
                print tok
            tok = self.tokenizer.token()
        return self.parser.parse(query)

    def query(self, graph_object, query_string):
        """Top-level function that's called by the parser when a query has
           been transformed to its AST. This function routes the parsed
           query to a smaller number of high-level functions for handing
           specific types of queries (e.g. MATCH, CREATE, ...)"""
        parsed_query = self.parse(query_string)
        if isinstance(parsed_query, MatchReturnQuery):
            for match in self.matching_nodes(graph_object, parsed_query):
                yield match
        elif isinstance(parsed_query, CreateQuery):
            self.create_query(graph_object, parsed_query)
        else:
            raise Exception("Unhandled case in query function.")

    def create_query(self, graph_object, parsed_query):
        """For executing queries of the form CREATE... RETURN."""
        designation_to_node = {}
        for literal in parsed_query.literals.literal_list:
            designation_to_node[literal.designation] = self._create_node(
                graph_object, literal.node_class,
                **literal.attribute_conditions)
            for edge_fact in [
                fact for fact in atomic_facts if
                    isinstance(fact, EdgeExists)]:
                source_node = designation_to_node[edge_fact.node_1]
                target_node = designation_to_node[edge_fact.node_2]
                edge_label = edge_fact.edge_label
                self._create_edge(source_node, target_node,
                                  edge_label=edge_label)
        import pdb; pdb.set_trace()

    def matching_nodes(self, graph_object, parsed_query):
        """For executing queries of the form MATCH... RETURN."""
        all_designations = set()
        for fact in atomic_facts:
            if hasattr(fact, 'designation') and fact.designation is not None:
                all_designations.add(fact.designation)
        all_designations = sorted(list(all_designations))

        domain = self._get_domain(graph_object)
        for domain_assignment in itertools.product(
                *[domain] * len(all_designations)):
            var_to_element = {all_designations[index]: element for index,
                              element in enumerate(domain_assignment)}
            # Not sure if element_to_var will be useful
            # element_to_var = {
            #     v: k for k, v in var_to_element.iteritems()}
            sentinal = True
            for atomic_fact in atomic_facts:
                if isinstance(atomic_fact, ClassIs):
                    var_class = self._node_class(
                        self._get_node(graph_object,
                                       var_to_element[
                                           atomic_fact.designation]))
                    # var = atomic_fact.designation
                    desired_class = atomic_fact.class_name
                    if var_class != desired_class:
                        sentinal = False
                        break
                if isinstance(atomic_fact, AttributeHasValue):
                    attribute = atomic_fact.attribute
                    desired_value = atomic_fact.value
                    value = self._node_attribute_value(
                        self._get_node(
                            graph_object,
                            var_to_element[atomic_fact.designation]),
                        attribute)
                    if value != desired_value:
                        sentinal = False
                        break
                if isinstance(atomic_fact, EdgeExists):
                    if not any((self._edge_class(connecting_edge) ==
                                atomic_fact.edge_label)
                               for _, connecting_edge in
                               self._edges_connecting_nodes(
                                   graph_object,
                                   var_to_element[atomic_fact.node_1],
                                   var_to_element[atomic_fact.node_2])):
                        sentinal = False
                        break
            if sentinal:
                if PRINT_MATCHING_ASSIGNMENTS:
                    print var_to_element  # For debugging purposes only
                variables_to_return = (
                    parsed_query.return_variables.variable_list)
                return_list = []
                for return_path in variables_to_return:
                    if isinstance(return_path, str):
                        return_list.append(var_to_element[return_path])
                        break
                    node = self._get_node(
                        graph_object, var_to_element[return_path.pop(0)])
                    return_list.append(
                        self._node_attribute_value(node, return_path))
                yield return_list

    def _get_domain(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _get_domain needs to be defined in child class.")

    def _get_node(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _get_domain needs to be defined in child class.")

    def _node_attribute_value(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _get_domain needs to be defined in child class.")

    def _edge_exists(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _edge_exists needs to be defined in child class.")

    def _edges_connecting_nodes(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _edges_connecting_nodes needs to be defined "
            "in child class.")

    def _node_class(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _node_class needs to be defined in child class.")

    def _edge_class(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _edge_class needs to be defined in child class.")

    def _create_node(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _create_node needs to be defined in child class.")

    def _create_edge(self, *args, **kwargs):
        raise NotImplementedError(
            "Method _create_edge needs to be defined in child class.")


class CypherToNetworkx(CypherParserBaseClass):
    """Child class inheriting from ``CypherParserBaseClass`` to hook up
       Cypher functionality to NetworkX.
    """
    def _get_domain(self, obj):
        return obj.nodes()

    def _get_node(self, graph_object, node_name):
        return graph_object.node[node_name]

    def _node_attribute_value(self, node, attribute_list):
        out = copy.deepcopy(node)
        for attribute in attribute_list:
            try:
                out = out.get(attribute)
            except:
                raise Exception(
                    "Asked for non-existent attribute {} in node {}.".format(
                        attribute, node))
        return out

    def _edge_exists(self, graph_obj, source, target,
                     edge_class=None, directed=True):
        sentinal = True
        if source not in g.edge or target not in g.edge[source]:
            sentinal = False
        return sentinal

    def _edges_connecting_nodes(self, graph_object, source, target):
        try:
            for index, data in graph_object.edge[source][target].iteritems():
                yield index, data
        except:
            pass

    def _node_class(self, node, class_key='class'):
        return node.get(class_key, None)

    def _edge_class(self, edge, class_key='class'):
        try:
            out = edge.get(class_key, None)
        except AttributeError:
            out = None
        return out

    def _create_node(self, graph_object, node_class, **attribute_conditions):
        """Create a node and return it so it can be referred to later."""
        new_id = unique_id()
        attribute_conditions['class'] = node_class
        graph_object.add_node(new_id, **attribute_conditions)
        return new_id

    def _create_edge(self, graph_object, source_node,
                     target_node, edge_label=None):
        new_edge_id = unique_id()
        edges_dict = graph_object.edge[source_node].get(target_node, {})
        number_of_existing_edges = len(edges_dict)
        if number_of_existing_edges == 0:



def random_hash():
    """Return a random hash for naming new nods and edges."""
    random_hash = hashlib.md5(str(random.random() + time.time())).hexdigest()
    return random_hash


def unique_id():
    """Call ``random_hash`` and prepend ``_id_`` to it."""
    return '_id_' + random_hash()


def main():
    sample = ','.join(['MATCH (x:SOMECLASS {bar : "baz"',
                       'foo:"goo"})<-[:WHATEVER]-(:ANOTHERCLASS)',
                       '(y:LASTCLASS) RETURN x.foo, y'])

    sample = 'CREATE (n:SOMECLASS)-->(m:ANOTHERCLASS) RETURN n'

    # Now we make a little graph for testing
    g = nx.MultiDiGraph()
    g.add_node('node_1', {'class': 'SOMECLASS', 'foo': 'goo', 'bar': 'baz'})
    g.add_node('node_2', {'class': 'ANOTHERCLASS', 'foo': 'goo'})
    g.add_node('node_3', {'class': 'LASTCLASS', 'foo': 'goo', 'bar': 'notbaz'})
    g.add_node('node_4', {'class': 'SOMECLASS', 'foo': 'boo', 'bar': 'baz'})

    g.add_edge('node_2', 'node_1')
    g.add_edge('node_2', 'node_3')
    g.add_edge('node_4', 'node_2')

    g['node_2']['node_1'][0]['class'] = 'WHATEVER'

    # Let's enumerate the possible assignments
    my_parser = CypherToNetworkx()
    for matching_assignment in my_parser.query(g, sample):
        print matching_assignment

if __name__ == '__main__':
    # This main method is just for testing
    main()
