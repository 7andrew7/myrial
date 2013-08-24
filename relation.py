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

    def get_python_type(self):
        return PrimitiveType.mappings[self.type]

class Column:
    def __init__(self, name, _type):
        self.name = name
        self.type = PrimitiveType(_type.lower())

    def __str__(self):
        return self.name + ':' + str(self.type)

    @classmethod
    def from_string(cls, s):
        toks = s.split(':')
        assert len(toks) == 2
        return cls(*toks)

    def get_python_type(self):
        return self.type.get_python_type()

class TupleSizeException(Exception):
    pass

class TypeMismatchException(Exception):
    pass

class TableLiteral:
    def __init__(self, columns, tuples):
        """
        Create a relation from a schema (columns) and tuples.  Do
        type checking of the tuple fields
        """

        num_columns = len(columns)
        expected_types = [x.get_python_type() for x in columns]

        for tup in tuples:
            if len(tup) != num_columns:
                raise TupleSizeException("Bad column count: " + str(tup))

            actual_types = [type(x) for x in tup]
            if expected_types != actual_types:
                cstrs = [str(c) for c in columns]
                raise TypeMismatchException("%s : schema: (%s)" %
                                            (str(tup), ','.join(cstrs)))

        self.columns = columns
        self.tuples = tuples

    def __str__(self):
        cstrs = [str(c) for c in self.columns]
        tstrs = [str(t) for t in self.tuples]

        return '(%s)\n[%s]' % (','.join(cstrs), ','.join(tstrs))

if __name__ == "__main__":
    colstrs = ['salary:int', 'name:string', 'id:int']
    cols = [Column.from_string(x) for x in colstrs]

    tuples = [(3,'bob', 4), (5, 'fred', 77), (45, 'asdf', 23)]

    r = TableLiteral(cols, tuples)
    print r

# TODO: Add failing test cases
    # tuple type exception
#    tuples = [(3,'bob', 4), (5, 'fred', 'sam'), (45, 'asdf', 23)]
#    r = TableLiteral(cols, tuples)
#    print r

    # tuple size exception
#    tuples = [(3,'bob', 4), (5, 'fred'), (45, 'asdf', 23)]
#    r = TableLiteral(cols, tuples)
#    print r
