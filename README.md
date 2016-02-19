# Cypher for Python

This is very much a work in progress.

Neo4J's graph query language, "Cypher", seems to be emerging as the _de facto_ standard. This is a
project to provide an implementation of Cypher for Python. The plan is for it to consist of two parts.
The first will be a parser that matches Neo4J's Cypher implementation, which produces a syntax tree
from arbitrary Cypher queries. The second will be a bridge allowing graphs (such as might be
generated from networkx) to be queried in Cypher.

The roadmap is to get a basic parser written that supports a small subset of Cypher. It will be used
to generate a list of atomic facts that would have to be satisfied by any results returned from that
query (e.g. there is a node with label "Foo", related to another node with label "Bar"). These atomic
facts will be recorded in Python classes which will have methods for testing whether they hold for
a particular choice of nodes. Finally, we'll add a set of methods for querying networkx (and other
systems') graphs.
