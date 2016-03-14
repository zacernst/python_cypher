import unittest
import networkx as nx
from python_cypher import python_cypher


class TestPythonCypher(unittest.TestCase):

    def test_upper(self):
        """Test we can parse a CREATE... RETURN query."""
        g = nx.MultiDiGraph()
        query = 'CREATE (n:SOMECLASS) RETURN n'
        test_parser = python_cypher.CypherToNetworkx()
        test_parser.query(g, query)

    def test_create_node(self):
        """Test we can build a query and create a node"""
        g = nx.MultiDiGraph()
        query = 'CREATE (n) RETURN n'
        test_parser = python_cypher.CypherToNetworkx()
        for i in test_parser.query(g, query):
            pass
        self.assertEqual(len(g.node), 1)

    def test_create_node_and_edge(self):
        """Test we can build a query and create two nodes and an edge"""
        g = nx.MultiDiGraph()
        query = 'CREATE (n)-->(m) RETURN n, m'
        test_parser = python_cypher.CypherToNetworkx()
        for i in test_parser.query(g, query):
            pass
        self.assertEqual(len(g.node), 2)
        self.assertEqual(len(g.edge), 2)

    def test_return_attribute(self):
        """Test we can return attribute from matching node"""
        g = nx.MultiDiGraph()
        create_query = 'CREATE (n:SOMECLASS {foo: "bar"}) RETURN n'
        match_query = 'MATCH (n) RETURN n.foo'
        test_parser = python_cypher.CypherToNetworkx()
        list(test_parser.query(g, create_query))
        out = list(test_parser.query(g, match_query))
        self.assertEqual(out[0], ['bar'])


if __name__ == '__main__':
    unittest.main()
