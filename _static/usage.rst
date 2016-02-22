Usage
*****

This is all subject to change.

Let's say you have a NetworkX graph and you want to find all the nodes that
satisfy the following Cypher query:

.. code-block::

    MATCH (n:Person)-[:LIVES_IN]->(m:City) RETURN n.name, m

The first step is to parse the Cypher query; the second is to call that query
on the NetworkX graph, and yield back all the results.
