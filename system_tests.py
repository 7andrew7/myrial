
import myrial

import collections
import unittest

"""
Tests of parsing + evaluation
"""

emp_query = '''Emp = LOAD "employees.txt" AS (id:int, dept_id:int,
name:string, salary:int);
Dept = LOAD "departments.txt" AS (id:int, name:string, manager_id:int);
A = JOIN Emp BY dept_id, Dept BY id;
DUMP A;'''

fof_query = '''E1 = LOAD "edge.txt" AS (source:int, dest:int);
E2 = E1;

A = JOIN E1 BY dest, E2 BY source;
FoF = FOREACH A EMIT (E1.source, E2.dest) AS (source:int, dest:int);
DUMP FoF;'''

tc_query = '''
Edge = TABLE[(1,2),(2,3),(3,4),(3,5),(6,5),(7,2)]
  AS (source:int, dest:int);

Reachable = Edge;
DO
  _A = JOIN Reachable BY dest, Edge BY source;
  NewlyReachable = DISTINCT FOREACH _A EMIT (Reachable.source, Edge.dest) AS
      (source:int, dest:int);
  Delta = DIFF NewlyReachable, Reachable;
  Reachable = UNION Delta, Reachable;
WHILE Delta;
DUMP Reachable;
'''

class SystemTests(unittest.TestCase):

  def test_employees(self):

    output = []
    myrial.evaluate(emp_query, out=output)

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
    output = []
    myrial.evaluate(fof_query, out=output)

    expected = collections.Counter(
      [(1, 3),(3, 5),(8, 1),(2, 4),(2, 4),(3, 5),(4, 6),(5, 7),(5, 8),(6, 9),
       (9, 2)])
    self.assertEqual(output[0], expected)

  def __do_eager_test(self, query):
    '''Validate that lazy and eager evaluation yield the same result'''
    out1 = []
    myrial.evaluate(query, out=out1, eager_evaluation=False)

    out2 = []
    myrial.evaluate(query, out=out2, eager_evaluation=True)

    self.assertEqual(out1, out2)

  def test_employees_eager(self):
    self.__do_eager_test(emp_query)

  def test_fof_eager(self):
    self.__do_eager_test(fof_query)

  def test_transitive_closure(self):
    output = []
    myrial.evaluate(tc_query, out=output)

    expected = collections.Counter(
      [(1, 2),(7, 3),(1, 3),(1, 4),(7, 4),(1, 5), (7, 5),(2, 3),(7, 2),(2, 5),
       (3, 4),(2, 4),(6, 5),(3, 5)])

    self.assertEqual(output[0], expected)
