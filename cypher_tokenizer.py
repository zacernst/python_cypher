# -*- coding: utf-8 -*-

import ply.lex as lex
# Test

tokens = (
    'LBRACKET',
    'RBRACKET',
    'DASH',
    'GREATERTHAN',
    'LESSTHAN',
    'LPAREN',
    'RPAREN',
    'COLON',
    'RIGHT_ARROW',
    'LEFT_ARROW',
    'MATCH',
    'CREATE',
    'RETURN',
    'DOT',
    'NAME',
    'WHITESPACE',
    'LCURLEY',
    'RCURLEY',
    'COMMA',
    'QUOTE',
    'INTEGER',
    'STRING',
    'KEY',)


t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_DASH = r'-'
t_GREATERTHAN = r'>'
t_LESSTHAN = r'<'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COLON = r':'
t_WHITESPACE = r'[ ]+'
t_RIGHT_ARROW = r'-->'
t_LEFT_ARROW = r'<--'
t_QUOTE = r'"'
t_LCURLEY = r'{'
t_RCURLEY = r'}'
t_COMMA = r','
t_STRING = r'"[A-Za-z0-9]+"'

t_ignore = r' '


def t_error(t):
    print 'tokenizer error'


def t_MATCH(t):
    r'MATCH'
    return t


def t_CREATE(t):
    r'CREATE'
    return t


def t_RETURN(t):
    r'RETURN'
    return t


def t_DOT(t):
    r'\.'
    return t


def t_NAME(t):
    r'[A-Z]+[a-z0-9]*'
    return t


def t_KEY(t):
    r'[A-Za-z]+[0-9]*'
    return t


def t_INTEGER(t):
    r'[0-9]+'
    return int(t)

cypher_tokenizer = lex.lex()
