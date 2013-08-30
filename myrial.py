#!/usr/bin/python

import db
import parser

from db import Operation

import sys

class Evaluator:
    '''Evaluate a list of statements'''
    def __init__(self, out=sys.stdout, eager_evaluation=False):
        # Map from identifiers to db operations required to stream the result
        self.symbols = {}
        self.db = db.LocalDatabase()

        self.out = out
        self.eager_evaluation = eager_evaluation

    def evaluate(self, statements):
        for statement in statements:
            method = getattr(self, statement[0].lower())
            method(*statement[1:])

    def assign(self, _id, expression):
        pass

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'No input file provided'
        sys.exit(1)

    parser = parser.Parser()
    evaluator = Evaluator()

    with open(sys.argv[1]) as fh:
        statement_list = parser.parse(fh.read())
        evaluator.evaluate(statement_list)
