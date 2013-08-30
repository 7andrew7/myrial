#!/usr/bin/python

import types

class TupleTypeException(Exception):
    pass

class NoSuchColumnException(Exception):
    pass

class SchemaCompatibilityException(Exception):
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
        # Ensure column names are not duplicated
        strlist = [column.name for column in columns]
        strset = set(strlist)
        assert len(strset) == len(strlist)

        self.columns = columns

    @staticmethod
    def check_columns_compatible(schema1, index1, schema2, index2):
        if schema1.column_type(index1) != schema2.column_type(index2):
            raise SchemaCompatibilityException()

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

    def num_columns(self):
        return len(self.columns)

    def get_column(self, name):
        '''Return a column by name

        Raise a NoSuchColumnException on failure.
        '''
        for c in self.columns:
            if c.name == name:
                return c
        raise NoSuchColumnException(name)

    def column_index(self, name):
        '''Return the index of a column.

        raise a NoSuchColumnException on failure
        '''
        for i in range(len(self.columns)):
            if self.columns[i].name == name:
                return i
        raise NoSuchColumnException(name)

    def column_type(self, index):
        return self.columns[index].type

    def validate_tuple(self, tup):
        '''Validate that a given tuple matches the schema'''
        if len(self.columns) != len(tup):
            raise TupleTypeException(
                'Bad column count: schema=%s; tup=(%s)' % (str(self), str(tup)))
        for atom, column in zip(tup, self.columns):
            if type(atom) != column.get_python_type():
                raise TupleTypeException(
                    'Tuple type mismatch: schema=%s; tup=(%s)' % (
                        str(self), str(tup)))

    def tuple_from_string(self, s, delimeter='\t'):
        '''Convert a string into a tuple with the given schema'''
        toks = s.split(delimeter)
        if len(toks) != len(self.columns):
            raise TupleTypeException(
                'Bad column count: schema=%s ; input=(%s)' % (
                    str(self), ','.join(toks)))

        x = (column.atom_from_string(tok) for (column, tok) in
             zip(self.columns, toks))
        return tuple(x)

    def check_compatible(self, other):
        '''Raise an exception if two schemas are incompatible'''
        if len(self.columns) != len(other.columns):
            raise SchemaCompatibilityException(
                'Unequal column count: %s, %s' % (str(self), str(other)))
        for c1, c2 in zip(self.columns, other.columns):
            if c1.type != c2.type:
                raise SchemaCompatibilityException(
                    'Type mismatch: %s, %s' % (str(self), str(other)))

    def project(self, column_names):
        '''Return a new schema derived from column names'''
        columns = [self.get_column(name) for name in column_names]
        return Schema(columns)

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

    s2 = Schema.from_strings(['salary1:int', 'name2:string', 'id2:int'])

    print s2
    print s1 == s2

    s3 = Schema.join([s1, s2], ['A', 'B'])
    print s3

    t = s2.tuple_from_string('-23423\tBob Rosencrantz\t32003')
    print t
