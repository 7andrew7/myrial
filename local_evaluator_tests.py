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

  def test_load(self):
    ex = Expression('LOAD', self.employee_schema, path='employees.txt')
    actual = self.evaluator.evaluate_to_bag(ex)
    expected = collections.Counter([
      (1,2,'Bill Howe',25000),
      (2,1,'Dan Halperin',90000),
      (3,1,'Andrew Whitaker',5000),
      (4,2,'Shumo Chu',150000),
      (5,1,'Victor Almeida',50102),
      (6,3,'Dan Suciu',51211),
      (7,1,'Magdalena Balazinska',98121),
    ])
    self.assertEqual(actual,expected)
