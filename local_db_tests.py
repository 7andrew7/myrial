import db
import random
import relation
from db import Operation

import collections
import unittest

"""
Unit tests of various expression evaluators
"""

class LocalDatabaseTests(unittest.TestCase):
  def setUp(self):
    self.evaluator = db.LocalDatabase()
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
    ex = Operation('LOAD', self.employee_schema, path='employees.txt')
    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(actual,self.employee_tuples)

    ex = Operation('LOAD', self.department_schema, path='departments.txt')
    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(actual,self.department_tuples)

  def test_table(self):
    tuples = [(random.randint(0, 100), random.randint(0, 100))
              for k in range(10)]
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])

    ex = Operation('TABLE', schema, tuple_list=tuples)
    actual = self.evaluator.evaluate_to_bag(ex)
    expected = collections.Counter(tuples)
    self.assertEqual(actual,expected)

  def test_join(self):
    l1 = Operation('LOAD', self.employee_schema, path='employees.txt')
    l2 = Operation('LOAD', self.department_schema, path='departments.txt')
    schema_out = relation.Schema.join(
      [self.employee_schema, self.department_schema],
      ['Employee', 'Department'])

    ex = Operation('JOIN', schema_out, children=[l1,l2],
                    join_attributes=[(1,4)])
    actual = self.evaluator.evaluate_to_bag(ex)

    expected = collections.Counter([e + d for e in self.employee_tuples
                                    for d in self.department_tuples
                                    if e[1] == d[0]])
    self.assertEqual(actual,expected)

  def test_foreach(self):
    l1 = Operation('LOAD', self.employee_schema, path='employees.txt')
    schema_out = relation.Schema.from_strings(['name:string','salary:int'])
    ex = Operation('FOREACH', schema_out, children=[l1],
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

    c1 = Operation('TABLE', schema, tuple_list=t1)
    c2 = Operation('TABLE', schema, tuple_list=t2)
    ex = Operation('UNION', schema, children=[c1,c2])

    actual = self.evaluator.evaluate_to_bag(ex)
    expected = collections.Counter(t1 + t2)
    self.assertEqual(actual, expected)

  def test_diff(self):
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])

    t0 = [(2*k, 2*k + 1) for k in range(50)]
    t1 = t0 + t0
    t2 = t0[::2]

    c1 = Operation('TABLE', schema, tuple_list=t1)
    c2 = Operation('TABLE', schema, tuple_list=t2)
    ex = Operation('DIFF', schema, children=[c1,c2])

    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(sum(actual.values()), 75)

    expected = collections.Counter(t0 + t0[1::2])
    self.assertEqual(actual, expected)

  def test_intersect(self):
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])

    t1 = [(2*k, 2*k + 1) for k in range(40)]
    t2 = t1[::4]

    c1 = Operation('TABLE', schema, tuple_list=t1)
    c2 = Operation('TABLE', schema, tuple_list=t2)
    ex = Operation('INTERSECT', schema, children=[c1,c2])

    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(sum(actual.values()), 10)

    expected = collections.Counter(t2)
    self.assertEqual(actual, expected)

  def test_limit(self):
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])
    t1 = [(2*k, 2*k + 1) for k in range(40)]
    c1 = Operation('TABLE', schema, tuple_list=t1)

    ex = Operation('LIMIT', schema, children=[c1], count=8)

    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(sum(actual.values()), 8)

    expected = collections.Counter(t1[:8])
    self.assertEqual(actual, expected)

  def test_distinct(self):
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])
    t1 = [(2*k, 2*k + 1) for k in range(40)]
    t2 = t1 * 2
    c1 = Operation('TABLE', schema, tuple_list=t2)

    ex = Operation('DISTINCT', schema, children=[c1])

    actual = self.evaluator.evaluate_to_bag(ex)
    self.assertEqual(sum(actual.values()), len(t1))
    expected = collections.Counter(t1)
    self.assertEqual(actual, expected)

  def test_insert_replace_scan(self):
    schema = relation.Schema.from_strings(['f1:int', 'f2:int'])
    t1 = [(2*k, 2*k + 1) for k in range(40)]
    e1 = Operation('TABLE', schema, tuple_list=t1)
    key = db.RelationKey('andrew', 'foo.exe', 'table1')

    # Perform an initial insertion to create the table
    i1 = Operation('INSERT', schema=None, children=[e1], relation_key=key)
    self.evaluator.evaluate(i1)

    self.assertEqual(self.evaluator.get_schema(key), schema)

    s1 = Operation('SCAN', schema, relation_key=key)
    a1 = self.evaluator.evaluate_to_bag(s1)
    self.assertEqual(a1, collections.Counter(t1))

    # Add some more stuff
    t2 = [(2*k, 2*k + 1) for k in range(100, 140)]
    e2 = Operation('TABLE', schema, tuple_list=t2)
    i2 = Operation('INSERT', schema=None, children=[e2], relation_key=key)
    self.evaluator.evaluate(i2)

    self.assertEqual(self.evaluator.get_schema(key), schema)
    a2 = self.evaluator.evaluate_to_bag(s1)
    self.assertEqual(a2, collections.Counter(t1 + t2))

    # Outright replacement
    t3 = [(2*k, 2*k + 1) for k in range(200, 210)]
    e3 = Operation('TABLE', schema, tuple_list=t3)
    r3 = Operation('REPLACE', schema=None, children=[e3], relation_key=key)
    self.evaluator.evaluate(r3)

    self.assertEqual(self.evaluator.get_schema(key), schema)
    a3 = self.evaluator.evaluate_to_bag(s1)
    self.assertEqual(a3, collections.Counter(t3))
