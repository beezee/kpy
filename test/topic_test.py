from adt import F2, lift2, liftBind2
from hypothesis import given 
from hypothesis.strategies import text, integers
import json
from topic import Foo, FooJson, idr
from typing import Callable, TypeVar

A = TypeVar('A')
B = TypeVar('B')

def fibrecheck(ab: Callable[[A], B], ba: Callable[[B], A], a: A) -> None:
  res = ab(a)
  assert ab(ba(res)) == res

@given(text(), integers()) # type: ignore
def test_foo_serialize_round_trip(s: str, i: int) -> None:
  sz = FooJson()
  fibrecheck(lift2(Exception, sz.serialize), 
             liftBind2(Exception, sz.deserialize), 
             idr(Foo)(Foo(s, i)))
  js = json.dumps({"bar": s, "baz": i}, # type: ignore
    separators=(',', ':')) # type: ignore
  fibrecheck(liftBind2(Exception, sz.deserialize),
             lift2(Exception, sz.serialize),
             idr(str)(js))
