# Type Safety Patterns

Comprehensive guide for handling type diagnostics, containment patterns, and IPC generic types.

## Handling Type Diagnostics

**NO INLINE SUPPRESSIONS** - Never use `# pyright: ignore` or `# type: ignore` to hide diagnostics.

When a type diagnostic appears, fix the underlying issue:

| Diagnostic | Root Cause | Fix |
|------------|------------|-----|
| `reportUnusedParameter` | Parameter in interface not used | Use `_param` prefix convention |
| `reportArgumentType` | Type mismatch at call site | Use Pydantic models for params |
| `reportReturnType` | Return type doesn't match signature | Align signatures or fix types |
| `reportAny` | Implicit Any from untyped container | Annotate container before iteration |
| `reportExplicitAny` | Explicit Any usage | Replace with concrete type or Protocol |

### `_` Prefix Convention for Unused Parameters

When implementing an interface where certain parameters aren't needed, use the `_` prefix convention:

```python
# Correct - indicates intentionally unused
async def _handle_notification(
    self, method: str, _params: dict[str, object]
) -> None:
    pass  # params intentionally not processed

# Wrong - suppression hides the issue
async def _handle_notification(
    self, method: str, params: dict[str, object]  # pyright: ignore[reportUnusedParameter]
) -> None:
    pass
```

**Why this works:** Type checkers recognize `_name` as intentionally unused and don't report diagnostics.

### Always Use Pydantic Models for Structured Params

When passing structured data to typed interfaces, use Pydantic models instead of raw dicts:

```python
# Correct - typed, validated, serializes to correct format
from llm_lsp_cli.lsp.types import TextDocumentIdentifier, Position, TextDocumentPositionParams

params = TextDocumentPositionParams(
    textDocument=TextDocumentIdentifier(uri=uri),
    position=Position(line=line, character=character),
).model_dump(mode="json", by_alias=True)  # LSP uses camelCase
result = await transport.send_request("textDocument/definition", params)

# Wrong - suppression hides type mismatch
params = {
    "textDocument": {"uri": uri},
    "position": {"line": line, "character": character},
}
result = await transport.send_request(
    "textDocument/definition",
    params,  # pyright: ignore[reportArgumentType]
)
```

**Key insight:** `dict[str, str]` is not `dict[str, object]`. Pydantic's `model_dump()` produces the correct type.

## Type Boundary Enforcement

External data (JSON, network, user input) enters as `object`, not `Any`. Validate at a single gateway with Pydantic.

### Why `object` over `Any` at Boundaries

- `object` is a type error waiting to happen - forces validation
- `Any` silently propagates, infecting everything downstream
- Single gateway pattern: only one module imports raw transport

```python
# BAD: Any scatters everywhere
def get_data() -> Any:
    return json.loads(...)

result = get_data()
name = result["name"]  # OK, but name is Any, propagates downstream

# GOOD: object forces validation
def get_data() -> object:
    return json.loads(...)

result = get_data()
name = result["name"]  # ERROR: object not subscriptable

# Must validate first:
data = Model.model_validate(result)
name = data.name  # Fully typed
```

### Single Gateway Architecture

```
External World (JSON, network) → object
         ↓
VALIDATION BOUNDARY (TypedLSPTransport)
  - model_validate() converts object → Pydantic Model
         ↓
InitializeResult, Hover, etc. (fully typed)
         ↓
INTERNAL CODE (no Any, no object)
```

### Designated Any Containment Zone

Low-level infrastructure (transport, IPC) may use `Any` and file-level suppressions. This is the **only** place they're allowed.

```python
# transport.py - designated Any zone
# File-level suppressions at TOP of file (not inline)

# pyright: reportExplicitAny=false
# pyright: reportAny=false

def send_request(self, method: str, params: dict[str, object]) -> object:
    # Raw JSON-RPC - returns object to force validation upstream
    ...
```

**Key rule:** Any/object never escape the designated zone. All layers above receive concrete types.

## IPC Generic Types with Method Registry

For type-safe IPC/transport layers, use method registry with `@overload` decorators.

### Method Registry Pattern

```python
# ipc/method_registry.py
from typing import Literal, TypeAlias
from pydantic import BaseModel

# Type alias for valid method names (enables IDE autocomplete)
MethodName: TypeAlias = Literal[
    "ping",
    "shutdown",
    "textDocument/definition",
    "textDocument/hover",
    # ... all supported methods
]

# Registry mapping method names to (ParamsType, ResultType)
METHOD_TYPES: dict[MethodName, tuple[type[object], object]] = {
    "ping": (EmptyParams, PingResult),
    "shutdown": (EmptyParams, ShutdownResult),
    "textDocument/definition": (TextDocumentPositionParams, list[Location]),
    "textDocument/hover": (TextDocumentPositionParams, Hover | None),
    # ... additional methods
}
```

### @overload for Compile-Time Type Safety

```python
# ipc/unix_client.py
from typing import overload

class UNIXClient:
    # @overload declarations for each method
    @overload
    async def request(self, method: Literal["ping"], params: EmptyParams) -> PingResult: ...

    @overload
    async def request(
        self, method: Literal["textDocument/definition"],
        params: TextDocumentPositionParams
    ) -> list[Location]: ...

    @overload
    async def request(
        self, method: Literal["textDocument/hover"],
        params: TextDocumentPositionParams
    ) -> Hover | None: ...

    # Generic implementation
    async def request(
        self, method: MethodName, params: BaseModel
    ) -> BaseModel | list[BaseModel] | None:
        params_type, result_type = METHOD_TYPES[method]
        # Runtime validation and return typed result
        ...
```

**Why this pattern:**
- Compile-time: Type checker knows exact return type for each method literal
- Runtime: Registry provides validation and serialization
- No `cast()` needed in calling code

### Propagation to Upper Layers

**daemon_client.py mirrors the overloads:**
```python
class DaemonClient:
    @overload
    async def request(self, method: Literal["ping"], params: EmptyParams) -> PingResult: ...

    # Same overloads as UNIXClient...
```

**Upper layers use typed results directly:**
```python
# No cast() needed - result is typed
result = await daemon_client.request("textDocument/definition", params)
for loc in result:  # result is list[Location], not Any
    print(f"{loc.uri}:{loc.range.start.line}")
```

## Type Safety Principles

1. **Fix, don't suppress** - Every diagnostic indicates a real issue
2. **Use concrete types** - Replace `Any` with specific types or Protocols
3. **Validate at boundaries** - Pydantic models validate external data
4. **Type flows inward** - Inner layers receive validated models, never raw dicts
