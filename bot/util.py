import numpy

# elementwise sum of two tuples
def tuple_sum(a: tuple, b: tuple):
    return [sum(x) for x in zip(a, b)]

# elementwise subtraction of tuple b from tuple a
def tuple_sub(a: tuple, b: tuple):
    assert a.__len__() == b.__len__()
    return tuple(numpy.subtract(a, b))