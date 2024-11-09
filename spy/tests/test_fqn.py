import pytest
from spy.fqn import NSPart, FQN

def test_FQN_init_fullname():
    a = FQN("a.b.c::xxx")
    assert a.fullname == "a.b.c::xxx"
    assert a.modname == "a.b.c"
    assert a.parts == [
        NSPart("a.b.c", []),
        NSPart("xxx", [])
    ]

def test_FQN_init_parts():
    a = FQN(['a.b.c', 'xxx'])
    assert a.fullname == "a.b.c::xxx"
    assert a.modname == "a.b.c"

def test_many_FQNs():
    assert str(FQN("aaa")) == "aaa"
    assert str(FQN("aaa::bbb::ccc")) == "aaa::bbb::ccc"

def test_FQN_str_repr():
    a = FQN("aaa::bbb")
    assert repr(a) == "FQN('aaa::bbb')"
    assert str(a) == 'aaa::bbb'

def test_FQN_hash_eq():
    a = FQN("aaa::bbb")
    b = FQN("aaa::bbb")
    assert a == b
    assert hash(a) == hash(b)

def test_qualifiers():
    a = FQN("a::b[x, y]::c")
    assert a.fullname == "a::b[x, y]::c"
    assert a.modname == "a"
    assert a.parts == [
        NSPart("a", []),
        NSPart("b", [FQN("x"), FQN("y")]),
        NSPart("c", [])
    ]

def test_nested_qualifiers():
    a = FQN("mod::dict[str, unsafe::ptr[mymod::Point]]")
    assert a.fullname == "mod::dict[str, unsafe::ptr[mymod::Point]]"

def test_FQN_join():
    a = FQN("a")
    b = a.join("b")
    assert b.fullname == "a::b"
    c = b.join("c", ["i32"])
    assert c.fullname == "a::b::c[i32]"
    d = a.join("d", [FQN("mod::x")])
    assert d.fullname == "a::d[mod::x]"
    e = a.join("e", ["mod::y"])
    assert e.fullname == "a::e[mod::y]"


def test_FQN():
    a = FQN.make("aaa::bbb", suffix="0")
    assert a.fullname == "aaa::bbb#0"

def test_FQN_str():
    a = FQN.make("aaa::bbb", suffix='0')
    assert str(a) == "aaa::bbb#0"
    assert a.c_name == "spy_aaa$bbb$0"
    b = FQN.make("aaa::bbb", suffix='')
    assert str(b) == "aaa::bbb"
    assert b.c_name == "spy_aaa$bbb"

def test_FQN_hash_eq():
    a = FQN.make("aaa::bbb", suffix="0")
    b = FQN.make("aaa::bbb", suffix="0")
    assert a == b
    assert hash(a) == hash(b)

def test_FQN_c_name_dotted():
    a = FQN.make("a.b.c::xxx", suffix="0")
    assert a.c_name == "spy_a_b_c$xxx$0"


def test_qualifiers_c_name():
    a = FQN.make("a::b[x, y]::c", suffix="0")
    assert a.c_name == "spy_a$b__x_y$c$0"

def test_nested_qualifiers_c_name():
    a = FQN.make("a::list[Ptr[x, y]]::c", suffix="0")
    assert a.c_name == "spy_a$list__Ptr__x_y$c$0"
