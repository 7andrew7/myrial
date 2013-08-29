#!/usr/bin/python

import ply.yacc as yacc

import collections
import evaluate
import relation
import scanner

from evaluate import Expression

import sys

JoinTarget = collections.namedtuple('JoinTarget',['id', 'column_names'])

class Parser:
    def __init__(self):
        # Map from identifier to expression objects/trees
        self.symbols = {}
        self.evaluator = evaluate.LocalEvaluator()
        self.tokens = scanner.tokens

    def p_statement_list(self, p):
        '''statement_list : statement_list statement
                          | statement'''
        pass

    def p_statement_assign(self, p):
        'statement : ID EQUALS expression SEMI'
        self.symbols[p[1]] = p[3]

    def p_statement_dump(self, p):
        'statement : DUMP expression SEMI'
        result = self.evaluator.evaluate(p[2])
        strs = (str(x) for x in result)
        print '[%s]' % ','.join(strs)

    def p_statement_describe(self, p):
        'statement : DESCRIBE ID SEMI'
        ex = self.symbols[p[2]]
        print '%s : %s' % (p[2], str(ex.schema))

    def p_statement_explain(self, p):
        'statement : EXPLAIN ID SEMI'
        ex = self.symbols[p[2]]
        print '%s : %s' % (p[2], str(ex))

    def p_statement_dowhile(self, p):
        'statement : DO statement_list WHILE expression SEMI'
        pass

    def p_expression_id(self, p):
        'expression : ID'
        p[0] = self.symbols[p[1]]

    def p_expression_load(self, p):
        'expression : LOAD STRING_LITERAL AS schema'
        p[0] = Expression('LOAD', p[4], path=p[2])

    def p_expression_table(self, p):
        'expression : TABLE LBRACKET tuple_list RBRACKET AS schema'
        schema = p[6]
        tuple_list = p[3]
        for tup in tuple_list:
            schema.validate_tuple(tup)
        p[0] = Expression('TABLE', p[6], tuple_list=tuple_list)

    def p_expression_limit(self, p):
        'expression : LIMIT ID COMMA INTEGER_LITERAL'
        ex = self.symbols[p[2]]
        p[0] = Expression('LIMIT', ex.schema, children=[ex], count=p[4])

    def p_expression_binary_set_operation(self, p):
        'expression : setop ID COMMA ID'
        ex1 = self.symbols[p[2]]
        ex2 = self.symbols[p[4]]
        assert ex1.schema.compatible(ex2.schema)

        p[0] = Expression(p[1], ex1.schema, children=[ex1, ex2])

    def p_setop(self, p):
        '''setop : INTERSECT
                 | DIFF
                 | UNION'''
        p[0] = p[1]

    def p_expression_foreach(self, p):
        'expression : FOREACH ID EMIT LPAREN column_name_list RPAREN \
        optional_as'

        # TODO: we should allow duplicate columns to be selected, as long as
        # the user provides a rename schema

        ex = self.symbols[p[2]]
        schema_in = ex.schema
        schema_out = ex.schema.project(p[5])

        # Rename the columns, if requested
        if p[7]:
            assert schema_out.compatible(p[7])
            schema_out = p[7]

        column_indexes = [schema_in.column_index(c) for c in p[5]]
        p[0] = Expression('FOREACH', schema_out, children=[ex],
                          column_indexes=column_indexes)

    def p_expression_join(self, p):
        'expression : JOIN join_argument COMMA join_argument'
        target1 = p[2]
        target2 = p[4]

        # Look up the expression and schema for the given identifiers
        exp1 = self.symbols[target1.id]
        exp2 = self.symbols[target2.id]
        schema1 = exp1.schema
        schema2 = exp2.schema

        # Each target must refer to the same number of join attributes
        assert len(target1.column_names) == len(target2.column_names)

        # Compute pairs of join attributes that must match in the merged schema.
        # Also, enforce type safety.
        join_attributes = []
        offset = exp1.schema.num_columns()
        for c1, c2 in zip(target1.column_names, target2.column_names):
            index1 = schema1.column_index(c1)
            index2 = schema2.column_index(c2)
            assert schema1.column_type(index1) == schema2.column_type(index2)

            join_attributes.append((index1, index2 + offset))

        # compute the schema of the merged relation
        schema_out = relation.Schema.join([exp1.schema, exp2.schema],
                                          [target1.id, target2.id])

        p[0] = Expression('JOIN', schema_out, children=[exp1, exp2],
                          join_attributes=join_attributes)

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

    def p_column_namea_dotted(self, p):
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
        parser.parse(s, lexer=scanner.lexer, tracking=True)

    def p_error(self, p):
        print "Syntax error: %s" %  str(p)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'No input file provided'
        sys.exit(1)

    parser = Parser()
    with open(sys.argv[1]) as fh:
        parser.parse(fh.read())
