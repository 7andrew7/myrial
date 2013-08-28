#!/usr/bin/python

import types

class SchemaTypeException(Exception):
    pass

class Column:
    mappings = {'int' : types.IntType, 'string' : types.StringType}

    def __init__(self, name, _type):
        assert _type in Column.mappings.keys()

        self.name = name
        self.type = _type

    def __str__(self):
        return self.name + ':' + str(self.type)

    @classmethod
    def from_string(cls, s):
        '''Create a column from a colon-delimited input string

        For example: Column.from_string('salary:int')
        '''

        toks = s.split(':')
        assert len(toks) == 2
        return cls(*toks)

    def get_python_type(self):
        return Column.mappings[self.type]

    def atom_from_string(self, s):
        '''Convert the string argument into a python primitive'''
        return self.get_python_type()(s)

class Schema:
    def __init__(self, columns=[]):
        self.columns = columns

    @classmethod
    def from_strings(cls, strs):
        '''Create a schema from an iterable set of strings

        For example: Schema.from_strings(['salary:int', 'name:string'])
        '''
        return cls([Column.from_string(x) for x in strs])

    def __str__(self):
        cstrs = [str(c) for c in self.columns]
        return '(%s)' % ','.join(cstrs)

    def __eq__(self, other):
        return self.columns == other.columns

    def tuple_from_string(self, s, delimeter='\t'):
        '''Convert a string into a tuple with the given schema'''
        toks = s.split(delimeter)
        if len(toks) != len(self.columns):
            raise SchemaTypeException(
                'Bad column count: schema=%s ; input=(%s)' % (str(self),
                                                              ','.join(toks)))

        x = (column.atom_from_string(tok) for (column, tok) in
             zip(self.columns, toks))
        return tuple(x)

    def compatible(self, other):
        '''Return whether two schemas are compatible.

        Compatible means that the schemas have the same number of columns,
        each having the same type.  Column names are ignored
        '''
        if len(self.columns) != len(other.columns):
            return False
        for c1, c2 in zip(self.columns, other.columns):
            if c1.type != c2.type:
                print '%s  %s' % (c1.type, c2.type)
                return False
        return True

    def project(self, column_names):
        '''Return a subset of a schema, as identified by column names'''

        # Make sure column names are legit
        all_column_names = [c.name for c in self.columns]
        for name in column_names:
            assert name in all_column_names

        # project out a subset of the columns
        cols = [c for c in self.columns if c.name in column_names]
        return Schema(cols)

    @staticmethod
    def join(schemas, prefixes):
        '''Create a new schema by merging multiple schemas together.

        Column names are renamed by prepending the strings in the prefix array.
        '''
        columns = []
        for schema, prefix in zip(schemas, prefixes):
            for column in schema.columns:
               columns.append(Column(prefix + '.' + column.name, column.type))
        return Schema(columns)

if __name__ == "__main__":
    s1 = Schema.from_strings(['salary:int', 'name:string', 'id:int'])
    print s1
    print s1 == s1
    print s1.compatible(s1)

    s2 = Schema.from_strings(['salary1:int', 'name2:string', 'id2:int'])

    print s2
    print s1 == s2
    print s1.compatible(s2)
    print s2.compatible(s1)

    s3 = Schema.join([s1, s2], ['A', 'B'])
    print s3

    t = s2.tuple_from_string('-23423\tBob Rosencrantz\t32003')
    print t
