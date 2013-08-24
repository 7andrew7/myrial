#!/usr/bin/python

import ply.yacc as yacc

import relation
import scanner
from scanner import tokens

# dictionary mapping variable names to relations/views
relations = {}

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    pass

def p_statement_assign(p):
    'statement : ID EQUALS expression SEMI'
    relations[p[1]] = p[3]

def p_statement_dump(p):
    'statement : DUMP ID SEMI'
    if not p[2] in relations:
        print 'Unknown variable: ' + p[2]
    else:
        print relations[p[2]]

def p_expression_table(p):
    'expression : TABLE LBRACKET tuple_list RBRACKET AS schema'
    p[0] = relation.Relation(p[6], p[3])

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

import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'No input file provided'
        sys.exit(1)
    parser = yacc.yacc(debug=True)

    with open(sys.argv[1]) as fh:
        parser.parse(fh.read())
