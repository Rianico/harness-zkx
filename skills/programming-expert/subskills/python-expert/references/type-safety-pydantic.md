# Type Safety with Pydantic — Deep Patterns

> Companion to SKILL.md §1. Load when generic constraints, protocol design, or strict-mode tracing needs more than the inline summary.

## Generic Repository and Bounded TypeVar

```python
from typing import TypeVar, Generic
from abc import ABC, abstractmethod
from pydantic import BaseModel

T = TypeVar("T")
ID = TypeVar("ID")
ModelT = TypeVar("ModelT", bound=BaseModel)

class Repository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get(self, id: ID) -> T | None: ...
    @abstractmethod
    async def save(self, entity: T) -> T: ...
    @abstractmethod
    async def delete(self, id: ID) -> bool: ...

class UserRepository(Repository[User, str]):
    async def get(self, id: str) -> User | None:
        row = await self._db.fetchrow("SELECT * FROM users WHERE id=$1", id)
        return User(**row) if row else None

def validate_and_create(model_cls: type[ModelT], data: dict) -> ModelT:
    return model_cls.model_validate(data)

user = validate_and_create(User, {"name": "Alice", "email": "a@b.com"})  # User
```

## Protocols — Structural Typing

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Serializable": ...

class Closeable(Protocol):
    def close(self) -> None: ...
class AsyncCloseable(Protocol):
    async def close(self) -> None: ...
class HasId(Protocol):
    @property
    def id(self) -> str: ...
class Comparable(Protocol):
    def __lt__(self, other: "Comparable") -> bool: ...
```

Protocols need no inheritance — any class implementing the shape satisfies the checker. Add `@runtime_checkable` only when you need `isinstance(obj, Proto)`.

## Type Aliases

```python
# 3.12+ (PEP 695)
type UserId = str
type Handler[T] = Callable[[Request], T]
type AsyncHandler[T] = Callable[[Request], Awaitable[T]]

# 3.10/3.11 compat
from typing import TypeAlias
UserIdCompat: TypeAlias = str
HandlerCompat: TypeAlias = Callable[[Request], Response]
```

## Callable and Callback Types

```python
from collections.abc import Callable, Awaitable
from typing import Protocol

ProgressCallback = Callable[[int, int], None]
AsyncHandler = Callable[[Request], Awaitable[Response]]

class OnProgress(Protocol):
    def __call__(self, current: int, total: int, *, message: str = "") -> None: ...

def process_items(items: list[Item], on_progress: ProgressCallback | None = None) -> list[Result]:
    for i, item in enumerate(items):
        if on_progress:
            on_progress(i, len(items))
        ...
```

## Result[T, E] — Typed Success/Failure

```python
from typing import TypeVar, Generic
T = TypeVar("T")
E = TypeVar("E", bound=Exception)

class Result(Generic[T, E]):
    def __init__(self, value: T | None = None, error: E | None = None) -> None:
        if (value is None) == (error is None):
            raise ValueError("Exactly one of value or error must be set")
        self._value = value
        self._error = error
    @property
    def is_success(self) -> bool: return self._error is None
    def unwrap(self) -> T:
        if self._error is not None: raise self._error
        return self._value  # type: ignore[return-value]
    def unwrap_or(self, default: T) -> T:
        return default if self._error is not None else self._value  # type: ignore[return-value]

def parse_config(path: str) -> Result[Config, ConfigError]:
    try: return Result(value=Config.from_file(path))
    except ConfigError as e: return Result(error=e)
```

## Strict Mode Checklist

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
no_implicit_optional = true
```

Incremental adoption for existing codebases: per-module `[[tool.mypy.overrides]]` with `module = "legacy.*"` and relaxed flags, or `# mypy: strict-optional` header per file. Target: every public param/return/class-attribute annotated, `list[str]` not bare `list`, minimal `Any`.

## Tracing Unknown

When `reportUnknownVariableType` fires: hover → go-to-definition → find callers → check spec/schema → build Pydantic model from spec. Never suppress an `Unknown` in business logic — trace it to its `object` source and wrap it at the boundary.

## Sources

- `plugins/python-development/skills/python-type-safety/SKILL.md` + `references/details.md` (wshobson/agents)
- `skills/programming-expert/subskills/basedpyright-expert` for checker knobs
