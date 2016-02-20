from cypher_tokenizer import *
from ply import yacc

atomic_facts = []
next_anonymous_variable = 0

start = 'match_return'

class AtomicFact(object):
    """ maybe useful, maybe not. """
    pass


class ClassIs(AtomicFact):
    def __init__(self, designation, class_name):
        self.designation = designation
        self.class_name = class_name


class EdgeExists(AtomicFact):
    def __init__(self, node_1, node_2, direction=None, edge_label=None):
        self.node_1 = node_1
        self.node_2 = node_2
        self.direction = direction


class AttributeHasValue(AtomicFact):
    def __init__(self, designation, attribute, value):
        self.designation = designation
        self.attribute = attribute
        self.value = value


class Node(object):
    '''A node specification -- a set of conditions and a designation.'''
    def __init__(self, node_class=None, designation=None,
                 attribute_conditions=None):
        self.node_class = node_class
        self.designation = designation
        self.attribute_conditions = attribute_conditions or {}


class AttributeConditionList(object):
    '''A bunch of AttributeHasValue objects in a list'''
    def __init__(self, attribute_list=None):
        global atomic_facts
        self.attribute_list = attribute_list or {}


class Relationship(object):
    def __init__(self, node_1, node_2, relationship_type=None,
                 min_depth=None, max_depth=None, arrow_direction=None):
        self.left_node = node_1
        self.right_node = node_2
        self.relationship_type = relationship_type
        self.min_depth = min_depth
        self.arrow_direction = arrow_direction


class VariableList(object):
    '''A list of variables, as in RETURN statements, e.g.'''
    def __init__(self, obj1, obj2):
        part1 = [obj1] if isinstance(obj1, str) else obj1.variables
        part2 = [obj2] if isinstance(obj2, str) else obj2.variables
        self.variables = part1 + part2


class MatchReturnQuery(object):
    def __init__(self, literals=None, return_variables=None):
        self.literals = literals
        self.return_variables = return_variables


class Literals(object):
    def __init__(self, literal_list=None):
        self.literal_list = literal_list


class ReturnVariables(object):
    def __init__(self, variable):
        self.variable_list = [variable]


class Keypath(object):
    def __init__(self, variable):
        self.path = [variable]


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


#def p_relationship(p):
#    '''relationship : literals RIGHT_ARROW literals'''
#    import pdb; pdb.set_trace()
#    global atomic_facts
#    if p[2] == t_RIGHT_ARROW:
#        p[0] = Relationship(p[1], p[3], arrow_direction='left_right')
#        atomic_facts.append(EdgeExists(p[0].designation,
#                            p[2].designation,
#                            direction='left_right'))
#    else:
#        print 'unhandled case?'


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
        p[1] = Keypath(p[1])
        p[1].path.append(p[3])
    elif len(p) == 4 and isinstance(p[1], Keypath):
        p[1].path.append(p[3])
    else:
        print 'unhandled case in keypath...'
    p[0] = p[1]


def p_literals(p):
    '''literals : node_clause
                | literals COMMA literals
                | literals RIGHT_ARROW literals'''
    if len(p) == 2:
        p[0] = Literals(literal_list=[p[1]])
    elif len(p) == 4 and p[2] == t_COMMA:
        p[0] = Literals(p[1].literal_list + p[3].literal_list)
    elif len(p) == 4 and p[2] == t_RIGHT_ARROW:
        p[0] = p[1]
        p[0].literal_list += p[3].literal_list
        print p[1].literal_list[-1], '-->', p[3].literal_list[0]
        edge_fact = EdgeExists(p[1].literal_list[-1].designation,
                               p[3].literal_list[0].designation)
        atomic_facts.append(edge_fact)
    elif len(p) == 4 and p[2] == t_LEFT_ARROW:
        p[0] = p[1]
        p[0].literal_list += p[3].literal_list
        print p[1].literal_list[-1], '-->', p[3].literal_list[0]
        edge_fact = EdgeExists(p[3].literal_list[0].designation,
                               p[1].literal_list[-1].designation)
        atomic_facts.append(edge_fact)
    else:
        print 'unhandled case in literals...'


def p_match_return(p):
    '''match_return : MATCH literals return_variables'''
    print 'in match_return'
    p[0] = MatchReturnQuery(literals=p[2], return_variables=p[3])


def p_return_variables(p):
    '''return_variables : RETURN KEY
                        | RETURN keypath
                        | return_variables COMMA KEY
                        | return_variables COMMA keypath'''
    if len(p) == 3 and isinstance(p[2], (str, Keypath)):
        p[0] = ReturnVariables(p[2])
    elif len(p) == 4:
        p[1].variable_list.append(p[3])
        p[0] = p[1]


def p_error(p):
    print 'error.'


cypher_parser = yacc.yacc()
