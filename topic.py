from abc import ABC, abstractmethod
from adt import append2, bind2, fold2, F1, F2, Sum2
from dataclasses import dataclass
import json
from typing import Any, Callable, cast, Dict, Generic
from typing import List, TypeVar, Union, Tuple, Type

# from https://gist.github.com/catb0t/bd82f7815b7e95b5dd3c3ad294f3cbbf
JsonPrimitive = Union[str, int, bool, None]
JsonType = Union[JsonPrimitive, 'JsonList', 'JsonDict']

# work around mypy#731: no recursive structural types yet
class JsonList(List[JsonType]):
    pass

class JsonDict(Dict[str, JsonType]):
    pass

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')
E = TypeVar('E')
F = TypeVar('F')

Parsed = Sum2[C, A]

def parse_json(j: str) -> Parsed[Exception, JsonType]:
  try:
    x = json.loads(j) # type: ignore
    if isinstance(x, dict): # type: ignore
      return F2(JsonDict(x))
    elif isinstance(x, list): # type: ignore
      return F2(JsonList(x))
    else:
      return F2(cast(JsonPrimitive, x))
  except Exception as e:
    return F1(e)

class MsgFormat(ABC, Generic[A, B, C]):
  @abstractmethod
  def serialize(self, a: A) -> B: pass
  @abstractmethod
  def deserialize(self, b: B) -> Sum2[C, A]: pass

class MsgFormatPF(Generic[A, B, C, D, E, F], MsgFormat[A, B, E]):

  @abstractmethod
  def _orig(self) -> MsgFormat[C, D, F]: pass

  def __init__(self) -> None:
    self.orig = self._orig()

  @abstractmethod
  def coserialize(self, a: A) -> C: pass
  @abstractmethod
  def map_serialize(self, d: D) -> B: pass
  @abstractmethod
  def codeserialize(self, b: B) -> D: pass
  @abstractmethod
  def map_deserialize(self, c: C) -> Parsed[E, A]: pass
  @abstractmethod
  def map_error(self, f: F) -> Parsed[E, A]: pass

  def serialize(self, a: A) -> B:
    return self.map_serialize(self.orig.serialize(self.coserialize(a)))

  def deserialize(self, d: B) -> Parsed[E, A]:
    x = self.orig.deserialize(self.codeserialize(d))
    return fold2(x, (self.map_error, self.map_deserialize))

class MsgFormatContravariantLM(Generic[A, B, C, E, F], 
                               MsgFormatPF[A, B, C, B, E, F]):
  def map_serialize(self, b: B) -> B:
    return b
  def codeserialize(self, b: B) -> B: 
    return b

class MsgFormatContravariant(Generic[A, B, C, E], 
                             MsgFormatContravariantLM[A, B, C, E, E]):
  def map_error(self, e: E) -> Parsed[E, A]: 
    return F1(e)

class JsonFormat(MsgFormat[JsonType, str, Exception]):
  def serialize(self, a: JsonType) -> str:
    return json.dumps(a, separators=(',', ':'))
  def deserialize(self, b: str) -> Parsed[Exception, JsonType]:
    try:
      return parse_json(b)
    except Exception as e:
      return F1(e)

def safe_parse(y: JsonDict, k: str, t: Type[A]) -> Sum2[Exception, A]:
  try:
    x = y[k]
    if isinstance(x, t):
      return F2(x)
    else:
      return F1(TypeError(
        'Could not parse value of type ' + 
        t.__name__ +
        ' from key ' + k))
  except Exception as e:
    return F1(e)

@dataclass
class Foo:
  bar: str
  baz: int

def idr(t: Type[A]) -> Callable[[A], Parsed[Exception, A]]:
  def x(a: A) -> Parsed[Exception, A]:
    return F2(a)
  return x

class FooJson(MsgFormatContravariant[Foo, str, JsonType, Exception]):
  def _orig(self) -> JsonFormat:
    return JsonFormat()
  def coserialize(self, a: Foo) -> JsonType: 
    return JsonDict({"bar": a.bar, "baz": a.baz})
  def map_deserialize(self, j: JsonType) -> Parsed[Exception, Foo]: 
    if not isinstance(j, JsonDict):
      return F1(TypeError('Expecting JSON object'))
    c = cast(JsonDict, j)
    x = bind2(safe_parse(c, 'baz', int), idr(int))
    y = bind2(safe_parse(c, 'bar', str), idr(str))
    return bind2(append2(x, y), 
      lambda t: F2(Foo(t[1], t[0])))
    return bind2(x, 
      lambda i: bind2(safe_parse(c.run, 'bar', str),
        lambda s: F2(Foo(s, i))))
