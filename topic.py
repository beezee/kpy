from abc import ABC, abstractmethod
from adt import append2, fold2, join2, F1, F2, Sum2
from dataclasses import dataclass
import json
from typing import Any, Callable, Generic, TypeVar, Union, Tuple, Type

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')
E = TypeVar('E')
F = TypeVar('F')

Parsed = Sum2[C, A]

@dataclass
class Json(Generic[A]):
  run: A

class MsgFormat(ABC, Generic[A, B, C]):
  @abstractmethod
  def serialize(self, a: A) -> B: pass
  @abstractmethod
  def deserialize(self, b: B) -> Sum2[C, A]: pass

class MsgFormatPF(Generic[A, B, C, D, E, F], MsgFormat[A, B, E]):

  # TODO - make sure this gets memoized
  @abstractmethod
  def orig(self) -> MsgFormat[C, D, F]: pass
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
    return self.map_serialize(self.orig().serialize(self.coserialize(a)))

  def deserialize(self, d: B) -> Parsed[E, A]:
    x = self.orig().deserialize(self.codeserialize(d))
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

class JsonFormat(MsgFormat[Json[Any], str, Exception]):
  def serialize(self, a: Json[Any]) -> str:
    return json.dumps(a.run, separators=(',', ':'))
  def deserialize(self, b: str) -> Parsed[Exception, Json[Any]]:
    try:
      return F2(Json(json.loads(b)))
    except Exception as e:
      return F1(e)

def safe_parse(y: Any, k: str, t: Type[A]) -> Sum2[Exception, A]:
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

def idl(t: Type[A]) -> Callable[[Exception], Parsed[Exception, A]]:
  def x(e: Exception) -> Parsed[Exception, A]:
    return F1(e)
  return x
def idr(t: Type[A]) -> Callable[[A], Parsed[Exception, A]]:
  def x(a: A) -> Parsed[Exception, A]:
    return F2(a)
  return x

class FooJson(MsgFormatContravariant[Foo, str, Json[Any], Exception]):
  def orig(self) -> JsonFormat:
    return JsonFormat()
  def coserialize(self, a: Foo) -> Json[Any]: 
    return Json({"bar": a.bar, "baz": a.baz})
  def map_deserialize(self, c: Json[Any]) -> Parsed[Exception, Foo]: 
    x = fold2(safe_parse(c.run, 'baz', int), (idl(int), idr(int)))
    y = fold2(safe_parse(c.run, 'bar', str), (idl(str), idr(str)))
    def mkFoo(t: Tuple[int, str]) -> Parsed[Exception, Foo]:
      return F2(Foo(t[1], t[0]))
    def bindFoo(i: int) -> Parsed[Exception, Foo]:
      def fromStr(s: str) -> Parsed[Exception, Foo]:
        return mkFoo((i, s))
      return fold2(safe_parse(c.run, 'bar', str), (idl(Foo), fromStr))
    #return fold2(x, (idl(Foo), bindFoo))
    return fold2(append2(x, y), (idl(Tuple[int, str]), mkFoo))

