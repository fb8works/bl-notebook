from .version import Version


def test_version_equal():
    a1 = Version("3.4.1")
    a2 = Version("3.4.1")
    b = Version("3.4.2")
    c = Version("3.4")
    assert a1 == a2
    assert a1 != b
    assert a1 != c


def test_version_compare():
    a = Version("3.4.1")
    b = Version("3.4.1a")
    assert a != b
    assert a < b
    assert a <= b
    assert not a >= b
    assert not a > b


def test_version_contains():
    a = Version("3.4.1")
    b = Version("3.4")
    c = Version("3")
    d = Version("4")
    assert a in b
    assert b not in a
    assert a in c
    assert a not in d


def test_version_sort():
    a = Version("3.4")
    b = Version("3.4.0")
    c = Version("3.4.0a")
    d = Version("3.4.0b")
    expected = [a, b, c, d]
    value = [d, b, a, c]
    result = sorted(value)
    assert result == expected
