import random

from collections import namedtuple
from dataclasses import dataclass
from tabulated import Tabulated
from tabulated.constants import PANDAS, SQLITE


az = "qwertyuiopasdfghjklzxcvbnm"
ten = list(range(10))


@dataclass
class Thing:
    x: int
    y: float
    s: str
    b: bool


def make_thing():
    s = []
    for i in range(5):
        s.append(random.choice(az))
    return Thing(
        x=random.choice(ten),
        y=random.random(),
        s="".join(s),
        b=random.choice([False, True]),
    )


def test_create_insert_find(engine):
    ri = Tabulated(on={"x": int, "y": float, "s": str}, engine=engine)
    obj_to_find = make_thing()
    obj_to_find.x = 8
    not_this_one = make_thing()
    not_this_one.x = 0
    ri.add(obj_to_find)
    ri.add(not_this_one)
    found_objs = ri.find("x > 5")
    assert found_objs == [obj_to_find]


def test_delete(engine):
    ri = Tabulated(on={"x": int, "y": float, "s": str}, engine=engine)
    t = make_thing()
    ri.add(t)
    found_objs = ri.find()
    assert found_objs == [t]
    ri.remove(t)
    found_objs = ri.find([])
    assert found_objs == []


def test_update(engine):
    ri = Tabulated(on={"x": int, "y": float, "s": str}, engine=engine)
    t = make_thing()
    t.x = 2
    ri.add(t)
    objs = ri.find("x >= 2")
    assert objs == [t]
    ri.update(t, {"x": 0})
    objs = ri.find("x >= 2")
    assert objs == []
    objs = ri.find("x < 2")
    assert objs == [t]
    assert t.x == 0  # check that the update was applied to the obj as well


def test_find_equal(engine):
    ri = Tabulated(on={"x": int, "y": float, "s": str, "b": bool}, engine=engine)
    t = make_thing()
    ri.add(t)
    int_result = ri.find(f"x == {t.x}")
    float_result = ri.find(f"y == {t.y}")
    str_result = ri.find(f"s == '{t.s}'")
    bool_result = ri.find(f"b == {t.b}")
    assert [t] == int_result
    assert [t] == float_result
    assert [t] == str_result
    assert [t] == bool_result


def test_find_null(engine):
    ri = Tabulated(on={"x": int, "y": float, "s": str, "b": bool}, engine=engine)
    t = Thing(x=None, y=None, s=None, b=None)
    ri.add(t)
    if engine == PANDAS:
        int_result = ri.find(f"x != x")
        float_result = ri.find(f"y != y")
        str_result = ri.find(f"s != s")
        bool_result = ri.find(f"b != b")
    elif engine == SQLITE:
        int_result = ri.find(f"x is null")
        float_result = ri.find(f"y is null")
        str_result = ri.find(f"s is null")
        bool_result = ri.find(f"b is null")
    assert [t] == int_result
    assert [t] == float_result
    assert [t] == str_result
    assert [t] == bool_result


def test_add_many(engine):
    ten_things = [make_thing() for _ in range(10)]
    ri = Tabulated(ten_things, on={"x": int, "y": float, "s": str}, engine=engine)
    found = ri.find()
    assert len(found) == len(ten_things)


def test_parens_and_ors(engine):
    things = [make_thing() for _ in range(10)]
    for i, t in enumerate(things):
        t.x = i
    things[0].y = 1000
    ri = Tabulated(things, on={"x": int, "y": float, "s": str}, engine=engine)
    found = ri.find("(x == 0 and y == 1000) or x == 9")
    assert len(found) == 2


def test_contains(engine):
    things = [make_thing() for _ in range(5)]
    ri = Tabulated(things, on={"x": int})
    assert all(t in ri for t in things)
    t_not = make_thing()
    assert t_not not in ri


def test_iteration(engine):
    things = [make_thing() for _ in range(5)]
    ri = Tabulated(things, on={"x": int, "y": float, "s": str}, engine=engine)
    ls = []
    for obj in ri:
        ls.append(obj)
    assert len(ls) == 5
    assert all(obj in ls for obj in things)


def test_index_namedtuple(engine):
    Point = namedtuple("Point", "x")
    pt = Point(random.random())
    ri = Tabulated(on={"x": float, "y": float}, engine=engine)
    ri.add(pt)
    ls = ri.find("x <= 1")
    assert ls == [pt]


def test_index_dict(engine):
    d1 = {"a": 1, "b": 2.2}
    d2 = {"a": 0, "b": 4.4}
    ds = [d1, d2]
    ri = Tabulated(ds, on={"a": int, "b": float})
    ls = ri.find("b == 4.4")
    assert ls == [d2]


def test_update_dict(engine):
    d1 = {"a": 1, "b": 2.2}
    d2 = {"a": 0, "b": 4.4}
    ds = [d1, d2]
    ri = Tabulated(ds, on={"a": int, "b": float})
    ri.update(d2, {"b": 5.5})
    ls = ri.find("b == 5.5")
    assert ls == [d2]
    assert d2["b"] == 5.5
