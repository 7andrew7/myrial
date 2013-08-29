
import parser

import unittest
import StringIO

"""
Unit tests of parsing + evaluation
"""

class ParserTests(unittest.TestCase):
  def setUp(self):
    self.output = StringIO.StringIO()
    self.parser = parser.Parser(out=self.output)

  def test_employees(self):
    with open('emp.myl') as fh:
      self.parser.parse(fh.read())

    expected = '''[(1, 2, 'Bill Howe', 25000, 2, 'human resources', 2),(2, 1, 'Dan Halperin', 90000, 1, 'accounting', 5),(3, 1, 'Andrew Whitaker', 5000, 1, 'accounting', 5),(4, 2, 'Shumo Chu', 150000, 2, 'human resources', 2),(5, 1, 'Victor Almeida', 50102, 1, 'accounting', 5),(6, 3, 'Dan Suciu', 51211, 3, 'engineering', 2),(7, 1, 'Magdalena Balazinska', 98121, 1, 'accounting', 5)]
DeptOf : (emp_name:string,dept_name:string)
[('Bill Howe', 'human resources'),('Dan Halperin', 'accounting'),('Andrew Whitaker', 'accounting'),('Shumo Chu', 'human resources'),('Victor Almeida', 'accounting'),('Dan Suciu', 'engineering'),('Magdalena Balazinska', 'accounting')]
Salary : (dept_name:string,salary:int)
[('human resources', 25000),('accounting', 90000),('accounting', 5000),('human resources', 150000),('accounting', 50102),('engineering', 51211),('accounting', 98121)]
'''

    self.assertEqual(self.output.getvalue(), expected)

  def test_fof(self):
    with open('fof.myl') as fh:
      self.parser.parse(fh.read())

    expected = '''FoF : (source:int,dest:int)
[(1, 3),(3, 5),(8, 1),(2, 4),(2, 4),(3, 5),(4, 6),(5, 7),(5, 8),(6, 9),(9, 2)]
'''
    self.assertEqual(self.output.getvalue(), expected)

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

