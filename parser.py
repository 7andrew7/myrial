#!/usr/bin/python

import ply.yacc as yacc

import collections
import relation
import scanner

import sys

JoinTarget = collections.namedtuple('JoinTarget',['id', 'column_names'])

class Parser:
    def __init__(self, log=yacc.PlyLogger(sys.stderr)):
        self.log = log
        self.tokens = scanner.tokens

    def p_statement_list(self, p):
        '''statement_list : statement_list statement
                          | statement'''
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_statement_assign(self, p):
        'statement : ID EQUALS expression SEMI'
        p[0] = ('ASSIGN', p[1], p[3])

    def p_statement_dump(self, p):
        'statement : DUMP ID SEMI'
        p[0] = ('DUMP', p[2])

    def p_statement_describe(self, p):
        'statement : DESCRIBE ID SEMI'
        p[0] = ('DESCRIBE', p[2])

    def p_statement_explain(self, p):
        'statement : EXPLAIN ID SEMI'
        p[0] = ('EXPLAIN', p[2])

    def p_statement_dowhile(self, p):
        'statement : DO statement_list WHILE expression SEMI'
        p[0] = ('DOWHILE', p[2], p[4])

    def p_expression_id(self, p):
        'expression : ID'
        p[0] = ('ALIAS', p[1])

    def p_expression_load(self, p):
        'expression : LOAD STRING_LITERAL AS schema'
        p[0] = ('LOAD', p[2], p[4])

    def p_expression_table(self, p):
        'expression : TABLE LBRACKET tuple_list RBRACKET AS schema'
        schema = p[6]
        tuple_list = p[3]

        # TODO Move this to type checker?
        for tup in tuple_list:
            schema.validate_tuple(tup)
        p[0] = ('TABLE', tuple_list, schema)

    def p_expression_limit(self, p):
        'expression : LIMIT ID COMMA INTEGER_LITERAL'
        p[0] = ('LIMIT', p[2], p[4])

    def p_expression_distinct(self, p):
        'expression : DISTINCT expression'
        p[0] = ('DISTINCT', p[2])

    def p_expression_binary_set_operation(self, p):
        'expression : setop ID COMMA ID'
        p[0] = (p[1], p[2], p[4])

    def p_setop(self, p):
        '''setop : INTERSECT
                 | DIFF
                 | UNION'''
        p[0] = p[1]

    def p_expression_foreach(self, p):
        'expression : FOREACH ID EMIT LPAREN column_name_list RPAREN \
        optional_as'
        p[0] = ('FOREACH', p[2], p[5], p[7])

    def p_expression_join(self, p):
        'expression : JOIN join_argument COMMA join_argument'
        p[0] = ('JOIN', p[2], p[4])

    def p_join_argument_list(self, p):
        'join_argument : ID BY LPAREN column_name_list RPAREN'
        p[0] = JoinTarget(p[1], p[4])

    def p_join_argument_single(self, p):
        'join_argument : ID BY column_name'
        p[0] = JoinTarget(p[1], (p[3],))

    def p_optional_as(self, p):
        '''optional_as : AS schema
                       | empty'''
        if len(p) == 3:
            p[0] = p[2]
        else:
            p[0] = None

    def p_schema(self, p):
        'schema : LPAREN column_def_list RPAREN'
        p[0] = relation.Schema(p[2])

    def p_column_def_list(self, p):
        '''column_def_list : column_def_list COMMA column_def
                           | column_def'''
        if len(p) == 4:
            cols = p[1] + [p[3]]
        else:
            cols = [p[1]]
        p[0] = cols

    def p_column_def(self, p):
        'column_def : column_name COLON type_name'
        p[0] = relation.Column(p[1], p[3])

    def p_column_name_list(self, p):
        '''column_name_list : column_name_list COMMA column_name
                            | column_name'''
        if len(p) == 4:
            p[0] = p[1] + (p[3],)
        else:
            p[0] = (p[1],)

    def p_column_name_dotted(self, p):
        'column_name : column_name DOT ID'
        p[0] = p[1] + '.' + p[3]

    def p_column_name_simple(self, p):
        'column_name : ID'
        p[0] = p[1]

    def p_empty(self, p):
        'empty :'
        pass

    def p_tuple_list(self, p):
        '''tuple_list : tuple_list COMMA tuple
                      | tuple'''
        if len(p) == 4:
            p[0] = p[1] + [p[3]]
        else:
            p[0] = [p[1]]

    def p_tuple(self, p):
        'tuple : LPAREN literal_list RPAREN'
        p[0] = p[2]

    def p_literal_list(self, p):
        '''literal_list : literal_list COMMA literal
                        | literal'''
        if len(p) == 4:
            p[0] = p[1] + (p[3],)
        else:
            p[0] = (p[1],)

    def p_literal(self, p):
        '''literal : INTEGER_LITERAL
                   | STRING_LITERAL'''
        p[0] = p[1]

    def p_type_name(self, p):
        '''type_name : STRING
                     | INT'''
        p[0] = p[1]

    def parse(self, s):
        parser = yacc.yacc(module=self, debug=True)
        return parser.parse(s, lexer=scanner.lexer, tracking=True)

    def p_error(self, p):
        self.log.error("Syntax error: %s" %  str(p))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'No input file provided'
        sys.exit(1)

    parser = Parser()

    with open(sys.argv[1]) as fh:
        print parser.parse(fh.read())
