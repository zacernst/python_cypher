# -*- coding: utf-8 -*-

from cypher_tokenizer import *
from ply import yacc

next_anonymous_variable = 0

start = 'full_query'


def constraint_function(function_string):
    """Translates a string in a WHERE clause into the appropriate
       function. The function is stored as an attribute in the
       ``Constraint`` object that's generated as the Cypher query
       is parsed.
    """
    def _equals(arg1, arg2):
        return arg1 == arg2

    def _greater_than(arg1, arg2):
        return arg1 > arg2

    def _less_than(arg1, arg2):
        return arg1 < arg2

    def _greater_or_equal(arg1, arg2):
        return arg1 >= arg2

    def _less_or_equal(arg1, arg2):
        return arg1 <= arg2

    if function_string == '=':
        return _equals
    elif function_string == '>':
        return _greater_than
    elif function_string == '<':
        return _less_than
    elif function_string == '>=':
        return _greater_or_equal


class ParsingException(Exception):
    """A generic Exception class for the parser."""
    def __init__(self, msg):
        print msg


class AtomicFact(object):
    """All facts will inherit this class. Not really used yet."""
    pass


class ClassIs(AtomicFact):
    """Represents a constraint that a vertex must be of a specific class."""
    def __init__(self, designation, class_name):
        self.designation = designation
        self.class_name = class_name


class EdgeCondition(AtomicFact):
    """Represents the constraint that an edge must have a specific
       label, or that it must be run in a specific direction."""
    def __init__(self, edge_label=None, direction=None, designation=None):
        self.edge_label = edge_label
        self.designation = designation


class EdgeExists(AtomicFact):
    """The constraint that an edge exists between two nodes, possibly
       having a specific label."""
    def __init__(self, node_1, node_2, designation=None, edge_label=None):
        self.node_1 = node_1
        self.node_2 = node_2
        self.edge_label = edge_label


class Node(object):
    """A node specification -- a set of conditions and a designation."""
    def __init__(self, node_class=None, designation=None,
                 attribute_conditions=None, connecting_edges=None):
        self.node_class = node_class
        self.designation = designation
        self.attribute_conditions = attribute_conditions or {}
        self.connecting_edges = connecting_edges or []


class NodeHasDocument(object):
    """Condition saying that the node has the (entire) dictionary document."""
    def __init__(self, designation=None, document=None):
        self.designation = designation
        self.document = document


class MatchQuery(object):
    """A near top-level class representing any Cypher query of the form
       MATCH... [WHERE...]"""
    def __init__(self, literals=None, return_variables=None,
                 where_clause=None):
        self.literals = literals
        self.return_variables = return_variables
        self.where_clause = where_clause


class Literals(object):
    """Class representing a sequence of nodes (which we're calling
       literals)."""
    def __init__(self, literal_list=None):
        self.literal_list = literal_list or []


class ReturnVariables(object):
    """Class representing a sequence (possibly length one) of variables
       to be returned in a MATCH... RETURN query. This includes variables
       with keypaths for attributes as well."""
    def __init__(self, variable):
        self.variable_list = [variable]


class CreateClause(object):
    """Class representing a CREATE... RETURN query, including cases
       where the RETURN isn't present."""
    def __init__(self, literals, return_variables=None):
        self.literals = literals
        self.return_variables = return_variables


class MatchWhereReturnQuery(object):
    def __init__(self, match_clause=None,
                 where_clause=None, return_variables=None):
        self.match_clause = match_clause
        self.where_clause = where_clause
        self.return_variables = return_variables


class Constraint(object):
    '''Class representing a constraint for use in a MATCH query. For
       example, WHERE x.foo = "bar"'''
    def __init__(self, keypath, value, function_string):
        self.keypath = keypath
        self.value = value
        self.function = constraint_function(function_string)


class Or(object):
    '''A disjunction'''
    def __init__(self, left_disjunct, right_disjunct):
        self.left_disjunct = left_disjunct
        self.right_disjunct = right_disjunct


class Not(object):
    '''Negation'''
    def __init__(self, argument):
        self.argument = argument


class WhereClause(object):
    '''WHERE clause'''
    def __init__(self, constraint):
        self.constraint = constraint


def p_node_clause(p):
    '''node_clause : LPAREN KEY RPAREN
                   | LPAREN COLON NAME RPAREN
                   | LPAREN KEY COLON NAME RPAREN
                   | LPAREN KEY COLON NAME condition_list RPAREN'''
    global next_anonymous_variable
    if len(p) == 4:
        p[0] = Node(designation=p[2])
    elif len(p) == 5:
        # Just a class name
        p[0] = Node(node_class=p[3],
                    designation='_v' + str(next_anonymous_variable))
        next_anonymous_variable += 1
    elif len(p) == 6:
        # Node class name and variable
        p[0] = Node(node_class=p[4], designation=p[2])
    elif len(p) == 7:
        p[0] = Node(node_class=p[4], designation=p[2],
                    attribute_conditions=p[5])


def p_condition(p):
    '''condition_list : KEY COLON STRING
                      | condition_list COMMA condition_list
                      | LCURLEY condition_list RCURLEY
                      | KEY COLON condition_list'''
    if len(p) == 4 and p[2] == ':' and isinstance(p[3], str):
        p[0] = {p[1]: p[3].replace('"', '')}
    elif len(p) == 4 and p[2] == ':' and isinstance(p[3], dict):
        p[0] = {p[1]: p[3]}
    elif len(p) == 4 and p[2] == ',':
        p[0] = p[1]
        p[1].update(p[3])
    elif len(p) == 4 and isinstance(p[2], dict):
        p[0] = p[2]


def p_constraint(p):
    '''constraint : keypath EQUALS STRING
                  | constraint OR constraint
                  | constraint AND constraint
                  | NOT constraint
                  | LPAREN constraint RPAREN'''
    if p[2] == '=':
        p[0] = Constraint(p[1], p[3], '=')
    elif p[2] == '>':
        p[0] = Constraint(p[1], p[3], '>')
    elif p[2] == 'OR':
        p[0] = Or(p[1], p[3])
    elif p[2] == 'AND':
        p[0] = Not(Or(Not(p[1]), Not(p[3])))
    elif p[1] == 'NOT':
        p[0] = Not(p[2])
    elif p[1] == '(':
        p[0] = p[2]
    else:
        raise Exception("Unhandled case in p_constraint.")


def p_where_clause(p):
    '''where_clause : WHERE constraint'''
    if isinstance(p[2], (Constraint, Or, Not,)):
        p[0] = WhereClause(p[2])
    else:
        raise Exception("Unhandled case in p_where_clause.")


def p_keypath(p):
    '''keypath : KEY DOT KEY
               | keypath DOT KEY'''
    if len(p) == 4 and isinstance(p[1], str):
        p[1] = [p[1]]
        p[1].append(p[3])
    elif len(p) == 4 and isinstance(p[1], list):
        p[1].append(p[3])
    else:
        raise Exception('unhandled case in keypath.')
    p[0] = p[1]


def p_edge_condition(p):
    '''edge_condition : LBRACKET COLON NAME RBRACKET
                      | LBRACKET KEY COLON NAME RBRACKET'''
    if p[2] == t_COLON:
        p[0] = EdgeCondition(edge_label=p[3])
    elif p[3] == t_COLON and len(p) == 6:
        p[0] = EdgeCondition(edge_label=p[4], designation=p[2])
        pass
    else:
        raise Exception("Unhandled case in p_edge_condition")


def p_labeled_edge(p):
    '''labeled_edge : DASH edge_condition DASH GREATERTHAN
                    | LESSTHAN DASH edge_condition DASH'''
    if p[1] == t_DASH:
        p[0] = p[2]
        p[0].direction = 'left_right'
    elif p[1] == t_LESSTHAN:
        p[0] = p[3]
        p[0].direction = 'right_left'
    else:
        raise Exception("Unhandled case in p_labeled_edge.")


def p_literals(p):
    '''literals : node_clause
                | literals COMMA literals
                | literals RIGHT_ARROW literals
                | literals LEFT_ARROW literals
                | literals labeled_edge literals'''
    if len(p) == 2:
        p[0] = Literals(literal_list=[p[1]])
    elif len(p) == 4 and p[2] == t_COMMA:
        p[0] = Literals(p[1].literal_list + p[3].literal_list)

    elif len(p) == 4 and p[2] == t_RIGHT_ARROW:
        p[0] = p[1]
        edge_fact = EdgeExists(p[1].literal_list[-1].designation,
                               p[3].literal_list[0].designation)
        p[0].literal_list[-1].connecting_edges.append(edge_fact)
        p[0].literal_list += p[3].literal_list
    elif len(p) == 4 and p[2] == t_LEFT_ARROW:
        p[0] = p[1]
        edge_fact = EdgeExists(p[3].literal_list[0].designation,
                               p[1].literal_list[-1].designation)
        p[0].literal_list[-1].connecting_edges.append(edge_fact)
        p[0].literal_list += p[3].literal_list
    elif isinstance(p[2], EdgeCondition) and p[2].direction == 'left_right':
        p[0] = p[1]
        edge_fact = EdgeExists(p[1].literal_list[-1].designation,
                               p[3].literal_list[0].designation,
                               edge_label=p[2].edge_label)
        p[0].literal_list[-1].connecting_edges.append(edge_fact)
        p[0].literal_list += p[3].literal_list
    elif isinstance(p[2], EdgeCondition) and p[2].direction == 'right_left':
        p[0] = p[1]
        edge_fact = EdgeExists(p[3].literal_list[0].designation,
                               p[1].literal_list[-1].designation,
                               edge_label=p[2].edge_label)
        p[0].literal_list[-1].connecting_edges.append(edge_fact)
        p[0].literal_list += p[3].literal_list
    else:
        raise Exception('unhandled case in p_literals')


def p_match_clause(p):
    '''match_clause : MATCH literals'''
    if len(p) == 3:
        p[0] = MatchQuery(literals=p[2], return_variables=None)
    else:
        raise Exception("Unhandled case in p_match_clause.")


def p_create_clause(p):
    '''create_clause : CREATE literals'''
    p[0] = CreateClause(p[2])


class CreateReturnQuery(object):
    def __init__(self, create_clause=None, return_variables=None):
        self.create_clause = create_clause
        self.return_variables = return_variables


def p_full_query(p):
    '''full_query : match_clause where_clause return_variables
                  | match_clause return_variables
                  | create_clause return_variables'''
    if isinstance(p[1], MatchQuery) and isinstance(p[2], WhereClause):
        p[0] = MatchWhereReturnQuery(match_clause=p[1],
                                     where_clause=p[2],
                                     return_variables=p[3])
    elif isinstance(p[1], MatchQuery) and isinstance(p[2], ReturnVariables):
        p[0] = MatchWhereReturnQuery(match_clause=p[1],
                                     where_clause=None,
                                     return_variables=p[2])
    elif isinstance(p[1], CreateClause):
        p[0] = CreateReturnQuery(create_clause=p[1], return_variables=p[2])
    else:
        raise Exception("Unhandled case in p_full_query.")


def p_return_variables(p):
    '''return_variables : RETURN KEY
                        | RETURN keypath
                        | return_variables COMMA KEY
                        | return_variables COMMA keypath'''
    if len(p) == 3 and isinstance(p[2], (str, list)):
        p[0] = ReturnVariables(p[2])
    elif len(p) == 4:
        p[1].variable_list.append(p[3])
        p[0] = p[1]


def p_error(p):
    import pdb; pdb.set_trace()
    raise ParsingException("Generic error while parsing.")


cypher_parser = yacc.yacc()
