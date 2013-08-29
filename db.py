#!/usr/bin/python

import relation

import collections
import itertools

class Operation:
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


RelationKey = collections.namedtuple('RelationKey',
                                     ['user', 'program', 'relation'])

StoredRelation = collections.namedtuple('StoredRelation', ['bag', 'schema'])

class Database:
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

def columns_match(tpl, column_pairs):
    '''Return whether tuple fields agree on a list of column pairs'''
    for x,y in column_pairs:
        if tpl[x] != tpl[y]:
            return False
    return True

class LocalDatabase(Database):
    '''A local evaluator implemented entirely in python'''

    def __init__(self):
        # Mapping from RelationKey to StoredRelation instances
        self.db = {}

    @staticmethod
    def __valid_input_str(x):
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
            if LocalDatabase.__valid_input_str(line):
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

    def limit(self, expr, count):
        assert len(expr.children) == 1
        cis = self.__evaluate_children(expr.children)
        return itertools.islice(cis[0], count)

    def foreach(self, expr, column_indexes):
        assert len(expr.children) == 1
        cis = self.__evaluate_children(expr.children)
        return (tuple([tpl[i] for i in column_indexes]) for tpl in cis[0])

    def union(self, expr):
        assert len(expr.children) == 2
        cis = self.__evaluate_children(expr.children)
        return itertools.chain(*cis)

    def intersect(self, expr):
        assert len(expr.children) == 2
        cis = self.__evaluate_children(expr.children)
        bags = [collections.Counter(ci) for ci in cis]
        return (bags[0] & bags[1]).elements()

    def diff(self, expr):
        assert len(expr.children) == 2
        cis = self.__evaluate_children(expr.children)

        bags = [collections.Counter(ci) for ci in cis]
        return (bags[0] - bags[1]).elements()

    def scan(self, expr, relation_key):
        assert len(expr.children) == 0
        bag = self.db[relation_key].bag
        return bag.elements()

    def get_schema(self, relation_key):
        return self.db[relation_key].schema

    def replace(self, expr, relation_key):
        assert len(expr.children) == 1
        bag = self.evaluate_to_bag(expr.children[0])
        self.db[relation_key] = StoredRelation(
            bag=bag, schema=expr.children[0].schema)

    def insert(self, expr, relation_key):
        assert len(expr.children) == 1

        if not relation_key in self.db:
            self.db[relation_key] = StoredRelation(
                bag=collections.Counter(), schema=expr.children[0].schema)

        bag, schema = self.db[relation_key]
        assert schema.compatible(expr.children[0].schema)

        bag.update(self.evaluate_to_bag(expr.children[0]))
