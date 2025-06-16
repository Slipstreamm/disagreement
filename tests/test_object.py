from disagreement.object import Object


def test_object_int():
    obj = Object(123)
    assert int(obj) == 123


def test_object_equality_and_hash():
    a = Object(1)
    b = Object(1)
    c = Object(2)
    assert a == b
    assert a != c
    assert hash(a) == hash(b)
