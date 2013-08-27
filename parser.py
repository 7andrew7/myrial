#!/usr/bin/python

import ply.yacc as yacc

import relation
import scanner
from scanner import tokens

import sys

# Map from identifier to expression objects
symbols = {}

class Expression:
    '''Representation of a myrial expression '''
    def  __init__(self, _type, schema, children=[], **kwargs):
        self.type = _type
        self.schema = schema
        self.children = children
        self.kwargs = kwargs

    def __str__(self):
        col_strs = [str(c) for c in self.schema]
        child_strs = [str(c) for c in self.children]
        return "{%s %s (%s) ==> [%s]}" % (self.type,
                                          str(self.kwargs),
                                          ','.join(col_strs),
                                          ','.join(child_strs))

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    pass

def p_statement_assign(p):
    'statement : ID EQUALS expression SEMI'
    global symbols
    symbols[p[1]] = p[3]

def p_statement_dump(p):
    'statement : DUMP expression SEMI'
    pass

def p_statement_describe(p):
    'statement : DESCRIBE ID SEMI'
    ex = symbols[p[2]]
    col_strs = [str(c) for c in ex.schema]
    print '%s : (%s)' % (p[2], ','.join(col_strs))

def p_statement_explain(p):
    'statement : EXPLAIN ID SEMI'
    ex = symbols[p[2]]
    print '%s : %s' % (p[2], str(ex))

def p_statement_dowhile(p):
    'statement : DO statement_list WHILE expression SEMI'
    pass

def p_expression_id(p):
    'expression : ID'
    p[0] = symbols[p[1]]

def p_expression_load(p):
    'expression : LOAD STRING_LITERAL AS schema'
    p[0] = Expression('LOAD', p[4], path=p[2])

def p_expression_union(p):
    'expression : UNION ID COMMA ID'
    p[0] = ('UNION', p[2], p[4])

def p_expression_intersect(p):
    'expression : INTERSECT ID COMMA ID'
    p[0] = ('INTERSECT', p[2], p[4])

def p_expression_diff(p):
    'expression : DIFF ID COMMA ID'
    p[0] = ('DIFF', p[2], p[4])

def p_expression_table(p):
    'expression : TABLE LBRACKET tuple_list RBRACKET AS schema'
    p[0] = ('TABLE', p[3], p[6])

def p_expression_foreach(p):
    'expression : FOREACH ID EMIT LPAREN column_name_list RPAREN optional_as'
    p[0] = ('FOREACH', p[2], p[5])
    if len(p) == 8:
        p[0] += (p[7],)

def p_expression_join(p):
    'expression : JOIN join_argument COMMA join_argument'
    p[0] = ('JOIN', p[2], p[4])

def p_join_argument_list(p):
    'join_argument : ID BY LPAREN column_name_list RPAREN'
    p[0] = (p[1], p[4])

def p_join_argument_single(p):
    'join_argument : ID BY column_name'
    p[0] = (p[1], (p[3],))

def p_schema(p):
    'schema : LPAREN column_def_list RPAREN'
    p[0] = p[2]

def p_column_def_list(p):
    '''column_def_list : column_def_list COMMA column_def
                       | column_def'''
    if len(p) == 4:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_column_def(p):
    'column_def : column_name COLON type_name'
    p[0] = relation.Column(p[1], p[3])

def p_column_name_list(p):
    '''column_name_list : column_name_list COMMA column_name
                        | column_name'''
    if len(p) == 4:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_column_name_dotted(p):
    'column_name : column_name DOT ID'
    p[0] = p[1] + '.' + p[3]

def p_column_name_simple(p):
    'column_name : ID'
    p[0] = p[1]

def p_optional_as(p):
    '''optional_as : AS schema
                   | empty'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None

def p_empty(p):
    'empty :'
    pass

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

def p_type_name(p):
    '''type_name : STRING
                 | INT'''
    p[0] = p[1]

def parse(s):
    parser = yacc.yacc(debug=True)
    parser.parse(s, tracking=True)

def p_error(p):
    print "Syntax error: %s" %  str(p)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'No input file provided'
        sys.exit(1)

    with open(sys.argv[1]) as fh:
        parse(fh.read())
