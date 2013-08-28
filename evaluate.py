#!/usr/bin/python

import relation

import collections
import itertools

class Expression:
    '''Representation of a myrial expression '''
    def  __init__(self, _type, schema, children=[], **kwargs):
        self.type = _type
        self.schema = schema
        self.children = children
        self.kwargs = kwargs

    def __str__(self):
        child_strs = [str(c) for c in self.children]
        return "{%s kwargs=%s schema=%s children=[%s]}" % (
            self.type, str(self.kwargs), self.schema, ','.join(child_strs))

class Evaluator:
    def evaluate(self, expr):
        '''Evaluate an expression

        The return value is an iterator over tuples that match the schema
        in expr.schema.
        '''
        method = getattr(self, expr.type.lower())
        return method(expr, **expr.kwargs)

    def evaluate_to_bag(self, expr):
        '''Return a bag (collections.Counter instance) for the expression'''
        return collections.Counter(self.evaluate(expr))

    # "abstract" evaluation methods below here
    def load(self, expr, path):
        raise NotImplementedError()

    def join(self, expr, join_attributes):
        raise NotImplementedError()

    def foreach(self, expr, column_indexes):
        raise NotImplementedError()

def columns_match(tpl, column_pairs):
    '''Return whether tuple fields agree on a list of column pairs'''
    for x,y in column_pairs:
        if tpl[x] != tpl[y]:
            return False
    return True

class LocalEvaluator(Evaluator):
    '''A local evaluator implemented entirely in python'''

    def __init__(self):
        pass

    @staticmethod
    def valid_input_str(x):
        y = x.strip()
        if len(y) == 0:
            return False
        if y.startswith('#'):
            return False
        return True

    def __evaluate_children(self, children):
        return [self.evaluate(c) for c in children]

    def load(self, expr, path):
        for line in open(path):
            if LocalEvaluator.valid_input_str(line):
                yield expr.schema.tuple_from_string(line[:-1])

    def table(self, expr, tuple_list):
        return (t for t in tuple_list)

    def join(self, expr, join_attributes):
        assert len(expr.children) == 2

        # Compute the cross product of the children and flatten
        cis = self.__evaluate_children(expr.children)
        p1 = itertools.product(*cis)
        p2 = (x + y for (x,y) in p1)

        # Return tuples that match on the join conditions
        return (tpl for tpl in p2 if columns_match(tpl, join_attributes))

    def foreach(self, expr, column_indexes):
        assert len(expr.children) == 1
        cis = self.__evaluate_children(expr.children)
        return (tuple([tpl[i] for i in column_indexes]) for tpl in cis[0])

    def union(self, expr):
        assert len(expr.children) == 2
        cis = self.__evaluate_children(expr.children)
        return itertools.chain(*cis)

if __name__ == "__main__":
    ev = LocalEvaluator()

    schema = relation.Schema.from_strings(['id:int','dept_id:int',
                                           'name:string','salary:int'])
    ex = Expression('LOAD', schema, path='employees.txt')
    print(ev.evaluate_to_bag(ex))
