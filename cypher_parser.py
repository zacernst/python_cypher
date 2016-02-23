# -*- coding: utf-8 -*-

from cypher_tokenizer import *
from ply import yacc

atomic_facts = []
next_anonymous_variable = 0

start = 'full_query'


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
    def __init__(self, edge_label=None, direction=None):
        self.edge_label = edge_label


class EdgeExists(AtomicFact):
    """The constraint that an edge exists between two nodes, possibly
       having a specific label."""
    def __init__(self, node_1, node_2, edge_label=None):
        self.node_1 = node_1
        self.node_2 = node_2
        self.edge_label = edge_label


class AttributeHasValue(AtomicFact):
    """The constraint that a node must have an attribute with a specific
       value."""
    def __init__(self, designation, attribute, value):
        self.designation = designation
        self.attribute = attribute.split('.')
        self.value = value


class Node(object):
    """A node specification -- a set of conditions and a designation."""
    def __init__(self, node_class=None, designation=None,
                 attribute_conditions=None):
        self.node_class = node_class
        self.designation = designation
        self.attribute_conditions = attribute_conditions or {}


class AttributeConditionList(object):
    """A bunch of AttributeHasValue objects in a list"""
    def __init__(self, attribute_list=None):
        global atomic_facts
        self.attribute_list = attribute_list or {}


class MatchReturnQuery(object):
    """A near top-level class representing any Cypher query of the form
       MATCH... RETURN"""
    def __init__(self, literals=None, return_variables=None):
        self.literals = literals
        self.return_variables = return_variables


class Literals(object):
    """Class representing a sequence of nodes (which we're calling
       literals)."""
    def __init__(self, literal_list=None):
        self.literal_list = literal_list


class ReturnVariables(object):
    """Class representing a sequence (possibly length one) of variables
       to be returned in a MATCH... RETURN query. This includes variables
       with keypaths for attributes as well."""
    def __init__(self, variable):
        self.variable_list = [variable]


class CreateQuery(object):
    """Class representing a CREATE... RETURN query, including cases
       where the RETURN isn't present."""
    def __init__(self, literals, return_variables=None):
        self.literals = literals
        self.return_variables = return_variables


def p_node_clause(p):
    '''node_clause : LPAREN COLON NAME RPAREN
                   | LPAREN KEY COLON NAME RPAREN
                   | LPAREN KEY COLON NAME condition_list RPAREN'''
    global next_anonymous_variable
    global atomic_facts
    if len(p) == 5:
        # Just a class name
        p[0] = Node(node_class=p[3],
                    designation='_v' + str(next_anonymous_variable),
                    attribute_conditions={})
        next_anonymous_variable += 1
    elif len(p) == 6:
        # Node class name and variable
        p[0] = Node(node_class=p[4], designation=p[2], attribute_conditions={})
    elif len(p) == 7:
        p[0] = Node(node_class=p[4], designation=p[2],
                    attribute_conditions=p[5])
    # Record the atomic facts
    atomic_facts.append(ClassIs(p[0].designation, p[0].node_class))
    for attribute, value in p[0].attribute_conditions.iteritems():
        atomic_facts.append(
            AttributeHasValue(p[0].designation, attribute, value))


def p_condition(p):
    '''condition_list : KEY COLON STRING
                      | condition_list COMMA condition_list
                      | LCURLEY condition_list RCURLEY'''
    global atomic_facts
    if len(p) == 4 and p[2] == ':':
        p[0] = {p[1]: p[3].replace('"', '')}
    elif len(p) == 4 and p[2] == ',':
        p[0] = p[1]
        p[1].update(p[3])
    elif len(p) == 4 and isinstance(p[2], dict):
        p[0] = p[2]


def p_keypath(p):
    '''keypath : KEY DOT KEY
               | keypath DOT KEY'''
    if len(p) == 4 and isinstance(p[1], str):
        p[1] = [p[1]]
        p[1].append(p[3])
    elif len(p) == 4 and isinstance(p[1], list):
        p[1].append(p[3])
    else:
        print 'unhandled case in keypath...'
    p[0] = p[1]


def p_edge_condition(p):
    '''edge_condition : LBRACKET COLON NAME RBRACKET'''
    p[0] = EdgeCondition(edge_label=p[3])


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
        raise Exception("Unhandled case in edge_condition.")


def p_literals(p):
    '''literals : node_clause
                | literals COMMA literals
                | literals RIGHT_ARROW literals
                | literals labeled_edge literals'''
    if len(p) == 2:
        p[0] = Literals(literal_list=[p[1]])
    elif len(p) == 4 and p[2] == t_COMMA:
        p[0] = Literals(p[1].literal_list + p[3].literal_list)
    elif len(p) == 4 and p[2] == t_RIGHT_ARROW:
        p[0] = p[1]
        edge_fact = EdgeExists(p[1].literal_list[-1].designation,
                               p[3].literal_list[0].designation)
        p[0].literal_list += p[3].literal_list
        atomic_facts.append(edge_fact)
    elif len(p) == 4 and p[2] == t_LEFT_ARROW:
        p[0] = p[1]
        edge_fact = EdgeExists(p[3].literal_list[0].designation,
                               p[1].literal_list[-1].designation)
        p[0].literal_list += p[3].literal_list
        atomic_facts.append(edge_fact)
    elif isinstance(p[2], EdgeCondition) and p[2].direction == 'left_right':
        p[0] = p[1]
        edge_fact = EdgeExists(p[1].literal_list[-1].designation,
                               p[3].literal_list[0].designation,
                               edge_label=p[2].edge_label)
        p[0].literal_list += p[3].literal_list
        atomic_facts.append(edge_fact)
    elif isinstance(p[2], EdgeCondition) and p[2].direction == 'right_left':
        p[0] = p[1]
        edge_fact = EdgeExists(p[3].literal_list[0].designation,
                               p[1].literal_list[-1].designation,
                               edge_label=p[2].edge_label)
        p[0].literal_list += p[3].literal_list
        atomic_facts.append(edge_fact)
    else:
        print 'unhandled case in literals...'


def p_match_return(p):
    '''match_return : MATCH literals return_variables'''
    p[0] = MatchReturnQuery(literals=p[2], return_variables=p[3])


def p_create(p):
    '''create : CREATE literals return_variables'''
    p[0] = CreateQuery(p[2], return_variables=p[3])


def p_full_query(p):
    '''full_query : match_return
                  | create'''
    p[0] = p[1]


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
    raise ParsingException("Generic error while parsing.")


cypher_parser = yacc.yacc()
