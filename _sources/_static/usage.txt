Usage
*****

This is all subject to change.

Let's say you have a NetworkX graph and you want to find all the nodes that
satisfy the following Cypher query: ::

    MATCH (n:Person)-[:LIVES_IN]->(m:City) RETURN n.name, m

The following steps will accomplish this:

#. Instantiate the parser class for NetworkX.
#. Parse the Cypher query from a string into an AST.
#. Call that query on the NetworkX graph, yielding back the results.

The following code snippet will perform these steps, and print all the matches
from your graph:

::
  networkx_parser = CypherToNetworkx()
  query_string = "MATCH (n:Person)-[:LIVES_IN]->(m:City) RETURN n.name, m"
  for result in networkx_parser.query(my_graph, query_string):
      print result
