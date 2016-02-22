# -*- coding: utf-8 -*-

import itertools
import networkx as nx
import copy
from cypher_tokenizer import *
from cypher_parser import *

PRINT_TOKENS = False
PRINT_MATCHING_ASSIGNMENTS = False


class CypherParserBaseClass(object):
    def __init__(self):
        self.tokenizer = cypher_tokenizer
        self.parser = cypher_parser

    def parse(self, query):
        self.tokenizer.input(query)
        tok = self.tokenizer.token()
        while tok:
            if PRINT_TOKENS:
                print tok
            tok = self.tokenizer.token()
        return self.parser.parse(query)

    def query(self, graph_object, query_string):
        parsed_query = self.parse(query_string)
        if isinstance(parsed_query, MatchReturnQuery):
            for match in self.matching_nodes(graph_object, parsed_query):
                yield match
        elif isinstance(parsed_query, CreateQuery):
            self.create_query(graph_object, parsed_query)
        else:
            raise Exception("Unhandled case in query function.")

    def matching_nodes(self, graph_object, parsed_query):
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
            element_to_var = {
                v: k for k, v in var_to_element.iteritems()}
            sentinal = True
            for atomic_fact in atomic_facts:
                if isinstance(atomic_fact, ClassIs):
                    var_class = self._node_class(
                        self._get_node(graph_object,
                                       var_to_element[
                                           atomic_fact.designation]))
                    var = atomic_fact.designation
                    desired_class = atomic_fact.class_name
                    if var_class != desired_class:
                        sentinal = False
                        break
                if isinstance(atomic_fact, AttributeHasValue):
                    attribute = atomic_fact.attribute
                    desired_value = atomic_fact.value
                    value = self._node_attribute_value(
                        self._get_node(graph_object,
                                       var_to_element[atomic_fact.designation]),
                        attribute)
                    if value != desired_value:
                        sentinal = False
                        break
                if isinstance(atomic_fact, EdgeExists):
                    if not any(
                        self._edge_class(connecting_edge) == atomic_fact.edge_label
                        for _, connecting_edge in self._edges_connecting_nodes(
                            graph_object, var_to_element[atomic_fact.node_1],
                                var_to_element[atomic_fact.node_2])):
                            sentinal = False
                            break
            if sentinal:
                if PRINT_MATCHING_ASSIGNMENTS:
                    print var_to_element  # For debugging purposes only
                variables_to_return = parsed_query.return_variables.variable_list
                return_list = []
                for return_path in variables_to_return:
                    if isinstance(return_path, str):
                        return_list.append(var_to_element[return_path])
                        break
                    node = self._get_node(graph_object, var_to_element[return_path.pop(0)])
                    return_list.append(self._node_attribute_value(node, return_path))
                yield return_list


class CypherToNetworkx(CypherParserBaseClass):
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
                    "Tried to get non-existent attribute {} in node {}.".format(
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

if __name__ == '__main__':
    # This main method is just for testing
    sample = ','.join(['MATCH (x:SOMECLASS {bar : "baz"',
                       'foo:"goo"})<-[:WHATEVER]-(:ANOTHERCLASS)',
                       '(y:LASTCLASS) RETURN x.foo, y'])

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
