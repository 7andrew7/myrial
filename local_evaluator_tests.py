import evaluate
import random
import relation
from evaluate import Expression

import collections
import unittest

"""
Unit tests of various expression evaluators
"""

class LocalEvaluatorTests(unittest.TestCase):
  def setUp(self):
    self.evaluator = evaluate.LocalEvaluator()
    self.employee_schema = relation.Schema.from_strings(
      ['id:int','dept_id:int', 'name:string','salary:int'])
    self.department_schema = relation.Schema.from_strings(
      ['dept_id:int', 'name:string', 'manager_id:int'])

    self.employee_tuples = collections.Counter([
      (1,2,'Bill Howe',25000),
      (2,1,'Dan Halperin',90000),
      (3,1,'Andrew Whitaker',5000),
      (4,2,'Shumo Chu',150000),
      (5,1,'Victor Almeida',50102),
      (6,3,'Dan Suciu',51211),
      (7,1,'Magdalena Balazinska',98121),
    ])

    self.department_tuples = collections.Counter([
      (1,'accounting',5),
      (2,'human resources',2),
      (3,'engineering',2),
      (4,'sales',7),
    ])

  def test_load(self):
    ex = Expression('LOAD', self.employee_schema, path='employees.txt')
    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(actual,self.employee_tuples)

    ex = Expression('LOAD', self.department_schema, path='departments.txt')
    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(actual,self.department_tuples)

  def test_table(self):
    tuples = [(random.randint(0, 100), random.randint(0, 100))
              for k in range(10)]
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])

    ex = Expression('TABLE', schema, tuple_list=tuples)
    actual = self.evaluator.evaluate_to_bag(ex)
    expected = collections.Counter(tuples)
    self.assertEqual(actual,expected)

  def test_join(self):
    l1 = Expression('LOAD', self.employee_schema, path='employees.txt')
    l2 = Expression('LOAD', self.department_schema, path='departments.txt')
    schema_out = relation.Schema.join(
      [self.employee_schema, self.department_schema],
      ['Employee', 'Department'])

    ex = Expression('JOIN', schema_out, children=[l1,l2],
                    join_attributes=[(1,4)])
    actual = self.evaluator.evaluate_to_bag(ex)

    expected = collections.Counter([e + d for e in self.employee_tuples
                                    for d in self.department_tuples
                                    if e[1] == d[0]])
    self.assertEqual(actual,expected)

  def test_foreach(self):
    l1 = Expression('LOAD', self.employee_schema, path='employees.txt')
    schema_out = relation.Schema.from_strings(['name:string','salary:int'])
    ex = Expression('FOREACH', schema_out, children=[l1],
                    column_indexes=[2,3])
    actual = self.evaluator.evaluate_to_bag(ex)

    expected = collections.Counter([(t[2], t[3]) for t in self.employee_tuples])
    self.assertEqual(actual, expected)

  def test_union(self):
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])
    t1 = [(random.randint(0, 100), random.randint(0, 100))
          for k in range(10)]
    t2 = [(random.randint(0, 100), random.randint(0, 100))
          for k in range(10)]

    c1 = Expression('TABLE', schema, tuple_list=t1)
    c2 = Expression('TABLE', schema, tuple_list=t2)
    ex = Expression('UNION', schema, children=[c1,c2])

    actual = self.evaluator.evaluate_to_bag(ex)
    expected = collections.Counter(t1 + t2)
    self.assertEqual(actual, expected)

  def test_diff(self):
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])

    t0 = [(2*k, 2*k + 1) for k in range(50)]
    t1 = t0 + t0
    t2 = t0[::2]

    c1 = Expression('TABLE', schema, tuple_list=t1)
    c2 = Expression('TABLE', schema, tuple_list=t2)
    ex = Expression('DIFF', schema, children=[c1,c2])

    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(sum(actual.values()), 75)

    expected = collections.Counter(t0 + t0[1::2])
    self.assertEqual(actual, expected)

  def test_intersect(self):
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])

    t1 = [(2*k, 2*k + 1) for k in range(40)]
    t2 = t1[::4]

    c1 = Expression('TABLE', schema, tuple_list=t1)
    c2 = Expression('TABLE', schema, tuple_list=t2)
    ex = Expression('INTERSECT', schema, children=[c1,c2])

    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(sum(actual.values()), 10)

    expected = collections.Counter(t2)
    self.assertEqual(actual, expected)
