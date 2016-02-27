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


if __name__ == '__main__':
    unittest.main()
