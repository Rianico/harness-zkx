# Python Stub Files (.pyi) Guide

> **For type checker configuration, stub generation workflows, and diagnostic resolution, see the basedpyright-expert skill.**

Stub files provide type information for Python modules without implementation. They're essential for type-checking third-party libraries, distributing type hints separately from runtime code, and maintaining backwards compatibility.

## When to Use Stub Files

| Scenario | Approach |
|----------|----------|
| Third-party library without types | Create stubs in `typings/` or contribute to typeshed |
| Library maintainer distributing types | Ship `.pyi` alongside `.py` or use inline annotations |
| Complex type logic obscuring code | Move types to stub, keep runtime simple |
| Multiple Python version support | Stubs can use newer syntax regardless of runtime version |

## Generation & Maintenance Tools

```bash
# Generate stubs from implementation
stubgen -p my_package           # mypy's stub generator
pyright --createstub my_package # pyright's generator
monkeytype run tests/           # runtime type collection
monkeytype stub my_package      # generate from collected types

# Validate stubs match implementation
stubtest my_package             # finds mismatches

# Lint stubs
flake8-pyi                      # stub-specific linter
```

## Syntax Conventions

### Body Style
```python
# Use ellipsis for all bodies
def foo(x: int) -> str: ...
class Bar:
    def method(self) -> int: ...
    attr: str
```

### Line Length
Maximum 130 characters per line (longer than standard 80/88).

### Modern Type Syntax
Use latest Python syntax regardless of target version:
```python
# GOOD: PEP 604 unions (works in stubs for all Python versions)
def foo(x: int | str) -> list[int]: ...

# GOOD: PEP 585 built-in generics
x: dict[str, list[int]]

# BAD: Old typing module imports (unless pre-3.9 runtime compatibility needed)
from typing import List, Dict
x: List[int]
```

**Exception:** Do not use `type` soft keyword (PEP 695) until Python 3.11 EOL (October 2027).

## Type Annotations

### Built-in Generics Over typing Module
```python
# GOOD
def foo(items: list[int]) -> dict[str, float]: ...

# BAD
from typing import List, Dict
def foo(items: List[int]) -> Dict[str, float]: ...
```

### Union Syntax
```python
# GOOD: Pipe syntax
x: int | str | None

# BAD: Union (unless pre-3.10 compatibility critical)
from typing import Union
x: Union[int, str, None]
```

### Type Aliases
```python
# Prefix internal aliases with underscore
_T = TypeVar("_T")
_DictList: TypeAlias = dict[str, list[int | None]]
```

### Avoid Any — Use Incomplete
```python
from _typeshed import Incomplete

# GOOD: Signals "not fully typed yet"
def foo(x: Incomplete) -> list[Incomplete]: ...

# BAD: Any implies "anything goes"
def foo(x: Any) -> Any: ...
```

### Parameter Types
```python
# Use abstract collections for parameters
from collections.abc import Mapping, Sequence

def process(items: Sequence[int]) -> list[int]: ...
def lookup(table: Mapping[str, int]) -> int: ...

# AVOID invariant types in parameters
def process(items: list[int]) -> ...  # Too restrictive
```

### Numeric Types
```python
# Use float for numeric parameters (int is implicitly acceptable)
def scale(value: float) -> float: ...

# AVOID
def scale(value: int | float) -> float: ...  # Redundant
```

## Overloaded Functions

All variants require `@overload` decorator — the implementation's final definition is excluded:

```python
from typing import overload, Literal

@overload
def open(name: str, mode: Literal["r"] = "r") -> Reader: ...
@overload
def open(name: str, mode: Literal["w"]) -> Writer: ...
@overload
def open(name: str, mode: Literal["a"]) -> Appender: ...
# No implementation signature in stub
```

### Keyword-Only Overloads
For optional first arguments, add an overload with keyword-only syntax:

```python
@overload
def parse(data: str) -> Result: ...
@overload
def parse(data: str, *, format: str) -> Result: ...
```

## Protocols (Structural Types)

Use `@type_check_only` for stub-only protocols:

```python
from typing import Protocol, type_check_only

@type_check_only
class Readable(Protocol):
    def read(self) -> str: ...

def get_reader() -> Readable: ...
```

## Dynamic Attribute Access

### __getattr__ for Any Name
```python
class Dynamic:
    def __getattr__(self, name: str) -> Incomplete: ...
```

### __setattr__ with Restrictions
```python
class Config:
    def __setattr__(self, name: str, value: str | int) -> None: ...
```

**Note:** Omit `__delattr__` in stubs.

## Context Managers

```python
class File:
    def __enter__(self) -> File: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool | None: ...
```

## Constants and Final

```python
from typing import Final

DAY_FLAG: Final = 0x01
MAX_SIZE: Final[int] = 1024
```

## NamedTuple and TypedDict

Use class-based syntax:

```python
class Point(NamedTuple):
    x: float
    y: float

class Config(TypedDict):
    host: str
    port: int
    debug: NotRequired[bool]
```

## Self and Class Annotations

Do NOT annotate `self` or `cls` unless referencing type variables:

```python
# GOOD
class Foo:
    def method(self) -> int: ...

# GOOD: Type variable reference
_T = TypeVar("_T", bound="Base")

class Base:
    def create(cls: type[_T]) -> _T: ...

# BAD: Redundant annotation
class Foo:
    def method(self: "Foo") -> int: ...
```

## Special Values

### Ellipsis for Complex Defaults
```python
def foo(
    x: int = ...,  # Complex default, check docs
    y: str = ...,
) -> None: ...
```

### The "Any Trick" for Optional Returns
Use `_typeshed.MaybeNone` to avoid forcing None checks when None is possible but not guaranteed:

```python
from _typeshed import MaybeNone

class Match:
    def group(self, group: str | int, /) -> str | MaybeNone: ...
```

## Platform-Dependent APIs

```python
import sys

if sys.platform == 'win32':
    def win_only() -> None: ...
elif sys.platform == 'linux':
    def linux_only() -> None: ...
```

## What to Include

| Include | Exclude |
|---------|---------|
| All documented objects | Implementation details |
| Objects in `__all__` | Non-importable modules |
| Public API | Protected modules (`_` prefix) |
| | Test modules |

### Marking Undocumented Objects
```python
def internal_helper(x: int) -> str: ...  # undocumented
```

## Stub-Only Objects

Prefix with `_` unless intentionally exposed:

```python
# Internal helper - not for users
def _helper() -> None: ...

# Exposed via @type_check_only
@type_check_only
class Proxy:
    def call(self) -> int: ...
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `Any` for untyped values | Use `_typeshed.Incomplete` |
| Annotating `self`/`cls` unnecessarily | Remove annotation |
| Using `typing.List` instead of `list` | Use built-in generic |
| Forward reference quotes | Remove quotes |
| `from __future__ import annotations` | Remove (stubs use modern syntax by default) |
| Including implementation signature in overload set | Remove final non-decorated overload |
| Union return types | Consider `MaybeNone` or redesign |

## Distribution Options

| Approach | When to Use |
|----------|-------------|
| Inline annotations | Library code, full control |
| `.pyi` alongside `.py` | Complex types, backwards compat |
| Separate `types-` package | Third-party contributions |
| Typeshed contribution | Standard library, major packages |

## Validation Workflow

```bash
# 1. Generate initial stubs
stubgen -p my_package -o typings/

# 2. Refine stubs manually (add overloads, protocols, etc.)

# 3. Validate against implementation
stubtest my_package

# 4. Lint
flake8-pyi typings/my_package/
```
