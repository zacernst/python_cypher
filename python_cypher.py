tokens = (
    'LBRACKET',
    'RBRACKET',
    'LPAREN',
    'RPAREN',
    'COLON',
    'RIGHT_ARROW',
    'NAME',
    'WHITESPACE',
    'LCURLEY',
    'RCURLEY',
    'COMMA',
    'QUOTE',
    'INTEGER',
    'STRING',
    'KEY',
    'MATCH',
    'RETURN',)

t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COLON = r':'
t_WHITESPACE = r'[ ]+'
t_RIGHT_ARROW = r'-->'
t_QUOTE = r'"'
t_LCURLEY = r'{'
t_RCURLEY = r'}'
t_COMMA = r','
t_STRING = r'"[A-Za-z0-9]+"'
t_MATCH = r'MATCH'
t_RETURN = r'RETURN'

t_ignore = r' '


def t_error(t):
    print 'error'


def t_NAME(t):
    r'[A-Z]+[a-z0-9]*'
    return t


def t_KEY(t):
    r'[A-Za-z]+[0-9]*'
    return t


def t_INTEGER(t):
    r'[0-9]+'
    return int(t)

import ply.lex as lex
lexer = lex.lex()

import ply.yacc as yacc


class Node(object):
    '''A node specification -- a set of conditions and a designation.'''
    def __init__(self, node_class=None, designation=None,
                 attribute_conditions=None):
        self.node_class = node_class
        self.designation = designation
        self.attribute_conditions = attribute_conditions


class AttributeConditionList(object):
    '''A bunch of AttributeCondition objects in a list'''
    def __init__(self, attribute_list=None):
        self.attribute_list = attribute_list or []

start = 'literals'

parameters = {}


def p_node_clause(p):
    '''node_clause : LPAREN NAME COLON RPAREN
                   | LPAREN NAME COLON KEY RPAREN
                   | LPAREN NAME COLON KEY condition_list RPAREN'''
    if len(p) == 4:
        p[0] = Node(node_condition=AttributeConditionList(), designation=p[2])
    elif len(p) == 5:
        # Just a class name
        p[0] = Node(node_class=p[2])
    elif len(p) == 6:
        # Node class name and variable
        p[0] = Node(node_class=p[2], designation=p[4])
    elif len(p) == 7:
        p[0] = Node(node_class=p[2], designation=p[4],
                    attribute_conditions=p[5])


class Relationship(object):
    def __init__(self, node_1, node_2, relationship_type=None,
                 min_depth=None, max_depth=None, arrow_direction=None):
        self.left_node = node_1
        self.right_node = node_2
        self.relationship_type = relationship_type
        self.min_depth = min_depth

        self.arrow_direction = arrow_direction


def p_relationship(p):
    '''relationship : node_clause RIGHT_ARROW node_clause'''
    if p[2] == t_RIGHT_ARROW:
        p[0] = Relationship(p[1], p[3], arrow_direction='left_right')
    else:
        print 'unhandled case?'


class VariableList(object):
    '''A list of variables, as in RETURN statements, e.g.'''
    def __init__(self, obj1, obj2):
        part1 = [obj1] if isinstance(obj1, str) else obj1.variables
        part2 = [obj2] if isinstance(obj2, str) else obj2.variables
        self.variables = part1 + part2


def p_condition(p):
    '''condition_list : KEY COLON STRING
                      | condition_list COMMA condition_list
                      | LCURLEY condition_list RCURLEY'''
    if len(p) == 4 and p[2] == ':':
        p[0] = AttributeConditionList(attribute_list=[{p[1]: p[3]}])
    elif len(p) == 4 and p[2] == ',':
        p[0] = p[1]
        p[1].attribute_list += p[3].attribute_list
    elif len(p) == 4 and isinstance(p[2], AttributeConditionList):
        p[0] = p[2]


class Literals(object):
    def __init__(self, literal_list=None):
        self.literal_list = literal_list


def p_literals(p):
    '''literals : node_clause
                | literals COMMA literals
                | literals RIGHT_ARROW literals'''
    if len(p) == 2:
        p[0] = Literals(literal_list=[p[1]])
    elif len(p) == 4 and p[2] == t_COMMA:
        p[0] = Literals(p[1].literal_list + p[3].literal_list)
    elif len(p) == 4 and p[2] == t_RIGHT_ARROW:
        import pdb; pdb.set_trace()
        p[0] = p[1]
        p[0].literal_list += p[3].literal_list
        print p[1].literal_list[-1], '-->', p[3].literal_list[0]
    else:
        print 'unhandled case in literals...'


def p_error(p):
    import pdb; pdb.set_trace()
    print 'error.'

sample = '(IMACLASS:x {bar : "baz", foo:"goo"})-->(IMALSOACLASS:), (LAST:y)'
# sample = '(IMACLASS:x {bar:"baz"})'
# sample = '(IMACLASS:x)'
lexer.input(sample)
tok = lexer.token()
while tok:
    print tok
    tok = lexer.token()

parser = yacc.yacc()
result = parser.parse(sample)
