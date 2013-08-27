#!/usr/bin/python

import types

class PrimitiveType:
    mappings = {'int' : types.IntType, 'string' : types.StringType}

    def __init__(self, type):
        assert type in PrimitiveType.mappings.keys()
        self.type = type

    def __str__(self):
        return self.type

    def __eq__(self, other):
        return self.type == other.type

    def __ne__(self, other):
        return self.type != other.type

    def get_python_type(self):
        return PrimitiveType.mappings[self.type]

class Column:
    def __init__(self, name, _type):
        self.name = name
        self.type = _type

    def __str__(self):
        return self.name + ':' + str(self.type)

    @classmethod
    def from_string(cls, s):
        toks = s.split(':')
        assert len(toks) == 2
        return cls(*toks)

    def get_python_type(self):
        return self.type.get_python_type()

class Schema:
    def __init__(self, columns=[]):
        self.columns = columns

    def __str__(self):
        cstrs = [str(c) for c in self.columns]
        return '(%s)' % ','.join(cstrs)

    def __eq__(self, other):
        return self.columns == other.columns

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
    colstrs1 = ['salary:int', 'name:string', 'id:int']
    cols1 = [Column.from_string(x) for x in colstrs1]

    s1 = Schema(cols1)
    print s1
    print s1 == s1
    print s1.compatible(s1)

    colstrs2 = ['salary1:int', 'name2:string', 'id2:int']
    cols2 = [Column.from_string(x) for x in colstrs2]
    s2 = Schema(cols2)

    print s2
    print s1 == s2
    print s1.compatible(s2)
    print s2.compatible(s1)

    s3 = Schema.join([s1, s2], ['A', 'B'])
    print s3
