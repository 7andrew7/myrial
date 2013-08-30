#!/usr/bin/python

import db
import relation
import parser

import collections
import random
import sys
import types

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

    def join(self, arg1, arg2):
        c_op1 = self.symbols[arg1.id]
        c_op2 = self.symbols[arg2.id]
        schema1 = c_op1.schema
        schema2 = c_op2.schema

        # The parser validates that we're given equal column counts
        assert len(arg1.column_names) == len(arg2.column_names)

        # Compute pairs of join attributes that must match in the merged schema.
        # Also, enforce type safety.
        join_attributes = []
        offset = c_op1.schema.num_columns()
        for c1, c2 in zip(arg1.column_names, arg2.column_names):
            index1 = schema1.column_index(c1)
            index2 = schema2.column_index(c2)

            relation.Schema.check_columns_compatible(
                schema1, index1, schema2, index2)
            join_attributes.append((index1, index2 + offset))

        # compute the schema of the merged relation
        schema_out = relation.Schema.join([c_op1.schema, c_op2.schema],
                                          [arg1.id, arg2.id])

        return db.Operation('JOIN', schema_out, children=[c_op1, c_op2],
                            join_attributes=join_attributes)

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

        if self.eager_evaluation:
            # Transform the query into a database insertion
            key = db.RelationKey(
                user='system', program=self.program_name, relation=_id)
            insert = db.Operation('INSERT', schema=None, children=[op],
                                  relation_key=key)
            self.db.evaluate(insert)

            # Re-write the expression to be a scan of the materialized table
            self.symbols[_id] = db.Operation('SCAN', schema=op.schema,
                                             children=[], relation_key=key)

        else:
            self.symbols[_id] = op

    def describe(self, _id):
        op = self.symbols[_id]

        if type(self.out) == types.ListType:
            self.out.append(op.schema)
        else:
            s = '%s : %s\n' % (_id, str(op.schema))
            self.out.write(s)

    def explain(self, _id):
        op = self.symbols[_id]

        if type(self.out) == types.ListType:
            self.out.append(op)
        else:
            s = '%s : %s\n' % (_id, str(op))
            self.out.write(s)

    def dump(self, expr):
        op = self.ep.evaluate(expr)
        result = self.db.evaluate(op)

        if type(self.out) == types.ListType:
            self.out.append(collections.Counter(result))
        else:
            strs = (str(x) for x in result)
            self.out.write('[%s]\n' % ','.join(strs))

    def dowhile(self, statement_list, termination_ex):
        pass

def evaluate(s, out=sys.stdout, eager_evaluation=True):
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
