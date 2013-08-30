#!/usr/bin/python

import db
import relation
import parser

import random
import sys

class ExpressionProcessor:
    '''Convert syntactic expressions into an operation (query plan)

    Also, perform any required type checking.
    '''
    def __init__(self, symbols):
        self.symbols = symbols

    def evaluate(self, expr):
        method = getattr(self, expr[0].lower())
        return method(*expr[1:])

    def alias(self, _id):
        return self.symbols[_id]

    def load(self, path, schema):
        return db.Operation('LOAD', schema, path=path)

    def table(self, tuple_list, schema):
        for tp in tuple_list:
            schema.validate_tuple(tp)
        return db.Operation('TABLE', schema, tuple_list=tuple_list)

    def distinct(self, expr):
        c_op = self.evaluate(expr)
        return db.Operation('DISTINCT', c_op.schema, children=[c_op])

    def __process_bitop(self, _type, id1, id2):
        c_op1 = self.symbols[id1]
        c_op2 = self.symbols[id2]

        c_op1.schema.check_compatible(c_op2.schema)
        return db.Operation(_type, c_op1.schema, children=[c_op1, c_op2])

    def union(self, id1, id2):
        return self.__process_bitop('UNION', id1, id2)

    def intersect(self, id1, id2):
        return self.__process_bitop('INTERSECT', id1, id2)

    def diff(self, id1, id2):
        return self.__process_bitop('DIFF', id1, id2)

    def limit(self, _id, count):
        c_op1 = self.symbols[_id]
        return db.Operation('LIMIT', c_op1.schema, children=[c_op1])

    def foreach(self, _id, column_names, rename_schema):
        c_op = self.symbols[_id]
        schema_in = c_op.schema
        schema_out = c_op.schema.project(column_names)

        # Rename the columns, if requested
        if rename_schema:
            schema_out.check_compatible(rename_schema)
            schema_out = rename_schema

        column_indexes = [schema_in.column_index(c) for c in column_names]
        return db.Operation('FOREACH', schema_out, children=[c_op],
                            column_indexes=column_indexes)
class StatementProcessor:
    '''Evaluate a list of statements'''

    def __init__(self, out=sys.stdout, eager_evaluation=False):
        # Map from identifiers to db operation
        self.symbols = {}

        self.db = db.LocalDatabase()
        self.out = out
        self.eager_evaluation = eager_evaluation
        self.ep = ExpressionProcessor(self.symbols)
        self.program_name = 'PROGRAM-' + str(random.randint(0,0x1000000000))

    def evaluate(self, statements):
        for statement in statements:
            method = getattr(self, statement[0].lower())
            method(*statement[1:])

    def assign(self, _id, expr):
        op = self.ep.evaluate(expr)
        self.symbols[_id] = op

    def describe(self, _id):
        op = self.symbols[_id]
        self.out.write('%s : %s\n' % (_id, str(op.schema)))

    def explain(self, _id):
        op = self.symbols[_id]
        self.out.write('%s : %s\n' % (_id, str(op)))

    def dump(self, _id):
        pass
    def dowhile(self, statement_list, termination_ex):
        pass

def evaluate(s, out=sys.stdout, eager_evaluation=False):
    _parser = parser.Parser()
    processor = StatementProcessor(out, eager_evaluation)

    statement_list = _parser.parse(s)
    processor.evaluate(statement_list)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'No input file provided'
        sys.exit(1)

    with open(sys.argv[1]) as fh:
        evaluate(fh.read())
