from adt import F2, map2
from hypothesis import given 
from hypothesis.strategies import text, integers
import json
from topic import Foo, FooJson

@given(text(), integers()) # type: ignore
def test_foo_serialize_round_trip(s: str, i: int) -> None:
  sz = FooJson()
  assert sz.deserialize(sz.serialize(Foo(s, i))) == F2(Foo(s, i))
  js = json.dumps({"bar": s, "baz": i}, # type: ignore
    separators=(',', ':')) # type: ignore
  assert map2(sz.deserialize(js), sz.serialize) == F2(js)
