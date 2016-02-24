# Cypher for Python

This is very much a work in progress.

Neo4J's graph query language, "Cypher", seems to be emerging as the _de facto_ standard. This is a
project to provide an implementation of Cypher for Python. The plan is for it to consist of two parts.
The first will be a parser that matches Neo4J's Cypher implementation, which produces a syntax tree
from arbitrary Cypher queries. The second will be a bridge allowing graphs (such as might be
generated from NetworkX) to be queried in Cypher.

## TL;DR

Use this to query graphs using the Cypher language. The project is very young, but under active
development. Up-to-date information will be kept on the [project wiki](https://github.com/zacernst/python_cypher/wiki).

## Why does this exist?

In the beginning, we had tables. Tables are perfect for a very wide range of data. But increasingly,
we're getting more interested in representing data that is not table-like. The canonical example
of this is a social network, which consists of people who have various relationships to each other.
For this sort of data, it's much cleaner and more intuitive to use graphs with vertices (nodes) and
edges (arrows), representing the various objects and their relationships.

Several excellent graph databases have emerged. In my opinion, the dominant player in the graph
database space is Neo4J. A large part of its success is due to its excellent query language, which
is called "Cypher". Cypher allows you to build queries that actually look like the structures you're
trying to find. For example, if you want to find all the people who like the move "Star Wars", you
might end up with a query that looks like this:

```
MATCH (p:Person)-[:LIKES]->(m:Movie {title:"Star Wars"}) RETURN p
```

This syntax is very nice and clear, and the learning curve is not steep, especially for Cypher's
more basic types of queries. So far, so good.

The trouble is that it would be awfully nice to be able to use Cypher to query other graph 
implementations. For example, I frequently end up loading a graph-like structure in memory using
a library like NetworkX. Searching the graph requires me to write specialized little functions
that are customized for my application. When I want to do a different kind of search, I have to write
a new function.

A much better solution would be to have a generic set of functions that translates Cypher queries
into searches for NetworkX or other graph systems. Then I could stop writing one-off ad-hoc code
and concentrate on the real work. That's what "Cypher for Python" is meant to do. You simply provide
your Cypher query as a string, and pass it to your graph. You get back the results of that Cypher
query with no extra futzing around.

## Roadmap and current status

The roadmap is to get a basic parser written that supports a small subset of Cypher. It will be used
to generate a list of atomic facts that would have to be satisfied by any results returned from that
query (e.g. there is a node with label "Foo", related to another node with label "Bar"). These atomic
facts will be recorded in Python classes which will have methods for testing whether they hold for
a particular choice of nodes. Finally, we'll add a set of methods for querying NetworkX (and other
systems') graphs. I think that a module like this will be frightfully useful.

Check the [github wiki](https://github.com/zacernst/python_cypher/wiki) for the project's current
status, roadmap, bugs, etc. Sphinx documentation will be available
[right here on Github](http://zacernst.github.io/python_cypher/index.html) as the project develops.
