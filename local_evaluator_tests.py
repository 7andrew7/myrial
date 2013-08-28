import evaluate
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

  def test_join(self):
    l1 = Expression('LOAD', self.employee_schema, path='employees.txt')
    l2 = Expression('LOAD', self.department_schema, path='departments.txt')
    schema_out = relation.Schema.join(
      [self.employee_schema, self.department_schema],
      ['Employee', 'Department'])

    ex = Expression('JOIN', schema_out, children=[l1,l2],
                    join_attributes=[('dept_id'),('id')])
    actual = self.evaluator.evaluate_to_bag(ex)

    expected = collections.Counter([e + d for e in self.employee_tuples,
                                    d in self.department_tuples if
                                    e[1] == d[0]])
    self.assertEqual(actual,expected)
