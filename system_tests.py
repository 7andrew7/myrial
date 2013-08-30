
import myrial

import collections
import unittest

"""
Tests of parsing + evaluation
"""

class SystemTests(unittest.TestCase):

  def test_employees(self):
    query = '''Emp = LOAD "employees.txt" AS (id:int, dept_id:int,
    name:string, salary:int);
    Dept = LOAD "departments.txt" AS (id:int, name:string, manager_id:int);
    A = JOIN Emp BY dept_id, Dept BY id;
    DUMP A;'''

    output = []
    myrial.evaluate(query, out=output)

    expected = collections.Counter(
      [(1, 2, 'Bill Howe', 25000, 2, 'human resources', 2),
       (2, 1, 'Dan Halperin', 90000, 1, 'accounting', 5),
       (3, 1, 'Andrew Whitaker', 5000, 1, 'accounting', 5),
       (4, 2, 'Shumo Chu', 150000, 2, 'human resources', 2),
       (5, 1, 'Victor Almeida', 50102, 1, 'accounting', 5),
       (6, 3, 'Dan Suciu', 51211, 3, 'engineering', 2),
       (7, 1, 'Magdalena Balazinska', 98121, 1, 'accounting', 5)])

    self.assertEqual(output[0], expected)

  def test_fof(self):
    query = '''E1 = LOAD "edge.txt" AS (source:int, dest:int);
    E2 = E1;

    A = JOIN E1 BY dest, E2 BY source;
    FoF = FOREACH A EMIT (E1.source, E2.dest) AS (source:int, dest:int);
    DUMP FoF;'''

    output = []
    myrial.evaluate(query, out=output)

    expected = collections.Counter(
      [(1, 3),(3, 5),(8, 1),(2, 4),(2, 4),(3, 5),(4, 6),(5, 7),(5, 8),(6, 9),
       (9, 2)])
    self.assertEqual(output[0], expected)

  def do_eager_test(self, query):
    '''Ensure that lazy evaluation and eager give the same result'''

    self.parser.parse(query)
    lazy_result = self.output.getvalue()

    eager_output = StringIO.StringIO()
    eager_parser = parser.Parser(out=eager_output, eager_evaluation=True)
    eager_parser.parse(query)
    eager_result = eager_output.getvalue()

    self.assertEqual(lazy_result, eager_result)

  def ___test_fof_eager(self):
    # oops, this doesn't work because tuples come back in different order.
    # Need to normalize the result
    with open('fof.myl') as fh:
      self.do_eager_test(fh.read())

