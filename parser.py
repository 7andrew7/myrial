#!/usr/bin/python

import ply.yacc as yacc

import relation
import scanner
from scanner import tokens

import sys

# symbol table
relations = {}

class UnknownSymbolException(Exception):
    pass

def lookup(sym):
    if not sym in relations:
        raise UnknownSymbolException(sym)
    return relations[sym]

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    pass

def p_statement_assign(p):
    'statement : ID EQUALS expression SEMI'
    global relations
    relations[p[1]] = p[3]

def p_statement_dump(p):
    'statement : DUMP expression SEMI'
    print p[2]

def p_expression_id(p):
    'expression : ID'
    p[0] = lookup(p[1])

def p_expression_load(p):
    'expression : LOAD STRING_LITERAL AS schema'
    p[0] = ('LOAD', p[2], p[4])

def p_expression_union(p):
    'expression : UNION ID COMMA ID'
    p[0] = ('UNION', lookup(p[2]), lookup(p[4]))

def p_expression_intersect(p):
    'expression : INTERSECT ID COMMA ID'
    p[0] = ('INTERSECT', lookup(p[2]), lookup(p[4]))

def p_expression_diff(p):
    'expression : DIFF ID COMMA ID'
    p[0] = ('DIFF', lookup(p[2]), lookup(p[4]))

def p_expression_table(p):
    'expression : TABLE LBRACKET tuple_list RBRACKET AS schema'
    p[0] = ('TABLE', p[3], p[6])

def p_tuple_list(p):
    '''tuple_list : tuple_list COMMA tuple
                  | tuple'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_tuple(p):
    'tuple : LPAREN literal_list RPAREN'
    p[0] = p[2]

def p_literal_list(p):
    '''literal_list : literal_list COMMA literal
                    | literal'''
    if len(p) == 4:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_literal(p):
    '''literal : INTEGER_LITERAL
               | STRING_LITERAL'''
    p[0] = p[1]

def p_schema(p):
    'schema : LPAREN column_list RPAREN'
    p[0] = p[2]

def p_column_list(p):
    '''column_list : column_list COMMA column
                   | column'''
    if len(p) == 4:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_column(p):
    'column : ID COLON type_name'
    p[0] = relation.Column(p[1], p[3])

def p_type_name(p):
    '''type_name : STRING
                 | INT'''
    p[0] = p[1]

def p_error(p):
    print "Syntax error in input: " + str(p)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'No input file provided'
        sys.exit(1)
    parser = yacc.yacc(debug=True)

    with open(sys.argv[1]) as fh:
        parser.parse(fh.read(), tracking=True)
