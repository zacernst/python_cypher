import itertools
import networkx as nx
from cypher_tokenizer import *
from cypher_parser import *


# sample = '(IMACLASS:x {bar:"baz"})'
# sample = '(IMACLASS:x)'
# cypher_tokenizer.input(sample)
# tok = cypher_tokenizer.token()
# while tok:
#     print tok
#     tok = cypher_tokenizer.token()

# result = cypher_parser.parse(sample)

class CypherParserBaseClass(object):
    def __init__(self):
        self.tokenizer = cypher_tokenizer
        self.parser = cypher_parser

    def parse(self, text):
        self.tokenizer.input(text)
        tok = self.tokenizer.token()
        while tok:
            tok = self.tokenizer.token()
        result = self.parser.parse(text)
        return result


class CypherToNetworkx(CypherParserBaseClass):
    def _get_domain(self, obj):
        pass


sample = ','.join(['MATCH (x:SOMECLASS {bar : "baz"',
                   'foo:"goo"})-->(:ANOTHERCLASS)',
                   '(y:LASTCLASS) RETURN x, y'])
my_parser = CypherParserBaseClass()
result = my_parser.parse(sample)
exit()


# Now we make a little graph for testing
g = nx.Graph()
g.add_node('node_1', {'class': 'SOMECLASS', 'foo': 'goo', 'bar': 'baz'})
g.add_node('node_2', {'class': 'ANOTHERCLASS', 'foo': 'not_bar'})
g.add_node('node_3', {'class': 'LASTCLASS', 'foo': 'goo', 'bar': 'notbaz'})
g.add_node('node_4', {'class': 'SOMECLASS', 'foo': 'not goo', 'bar': 'baz'})

g.add_edge('node_1', 'node_2')
g.add_edge('node_2', 'node_3')
g.add_edge('node_4', 'node_2')

# Let's enumerate the possible assignments
all_designations = set()
for fact in atomic_facts:
    if hasattr(fact, 'designation') and fact.designation is not None:
        all_designations.add(fact.designation)
all_designations = sorted(list(all_designations))

domain = g.nodes()
for domain_assignment in itertools.product(*[domain] * len(all_designations)):
    var_to_element = {all_designations[index]: element for index, element
                      in enumerate(domain_assignment)}
    element_to_var = {v: k for k, v in var_to_element.iteritems()}
    sentinal = True
    for atomic_fact in atomic_facts:
        if isinstance(atomic_fact, ClassIs):
            var_class = g.node[
                var_to_element[atomic_fact.designation]].get('class', None)
            var = atomic_fact.designation
            desired_class = atomic_fact.class_name
            if var_class != desired_class:
                sentinal = False
        if isinstance(atomic_fact, AttributeHasValue):
            attribute = atomic_fact.attribute
            desired_value = atomic_fact.value
            value = g.node[
                var_to_element[atomic_fact.designation]].get(attribute, None)
            if value != desired_value:
                sentinal = False
    if sentinal:
        print var_to_element
