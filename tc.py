#!/usr/bin/python

"""
Perform type-analysis over the AST.

1) Associate a schema type with each expression
2) Report type mismatches
"""

import parser

import sys

def process_expression(symbols, expression):
    expression['schema'] = 'foo'

##########################################################
# statement handlers
##########################################################

def assignment_handler(symbols, type=None, id=None, exp=None):
    process_expression(symbols, exp)
    symbols[id] = exp['schema']

def describe_handler(symbols, type=None, exp=None):
    process_expression(symbols, exp)
    print str(exp)

def dump_handler(symbols, type=None, exp=None):
    pass

def dowhile_handler(symbols, type=None, statements=None, term_expression=None):
    for statement in statements:
        process_statement(symbols, statement)

statement_handlers = {'ASSIGN': assignment_handler, 'DESCRIBE':
                      describe_handler, 'DUMP': dump_handler, 'DOWHILE':
                      dowhile_handler }

def process_statement(symbols, statement):
    handler = statement_handlers[statement['type']]
    handler(symbols, **statement)

def check_types(statements):
    symbols = {}

    for statement in statements:
        process_statement(symbols, statement)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'No input file provided'
        sys.exit(1)

    with open(sys.argv[1]) as fh:
        statements = parser.parse(fh.read())
        check_types(statements)
