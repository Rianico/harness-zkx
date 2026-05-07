# Type Safety Patterns

Comprehensive guide for handling type diagnostics, containment patterns, and IPC generic types.

## The #1 Cause of Typeless Propagation: Premature Serialization

**Most type warnings in Pydantic codebases come from calling `model_dump()` too early.**

### Anti-Pattern: Serialize First, Then Use

```python
# WRONG - loses type information immediately
config_obj = ConfigManager.load()
config_data: dict[str, object] = config_obj.model_dump(mode="json") if config_obj else {}
languages: object = config_data.get("languages", {})
if isinstance(languages, dict):
    for lang_name, lang_conf in languages.items():
        if isinstance(lang_conf, dict):
            root_markers = lang_conf.get("root_markers", [])  # object, needs isinstance
```

**Why this fails:** `model_dump()` returns `dict[str, object]` (Pydantic's safe default). Every value becomes `object`, requiring `isinstance` checks everywhere.

### Pattern: Keep Typed Models, Serialize at Boundary

```python
# RIGHT - keep the typed model as long as possible
config_obj = ConfigManager.load()
if config_obj:
    for lang_name, lang_conf in config_obj.languages.items():
        # lang_conf is LanguageServerConfig - fully typed!
        root_markers: list[str] = lang_conf.root_markers  # No isinstance needed
```

**When to call `model_dump()`:**
- Writing to file/DB
- Sending over network
- Returning JSON from API
- **NOT** for internal processing "just in case"

### Why object Overuse Is Dangerous

```python
# Forces defensive programming everywhere
def process(data: dict[str, object]) -> None:
    value = data.get("key")  # object
    if isinstance(value, str):
        # Can't trust the type checker anymore
        ...

# Trust the validated model
def process(config: ClientConfig) -> None:
    value: str = config.key  # Type checker enforces correctness
```

## Never Assume a Diagnostic Is "Legitimate"

**Every diagnostic indicates a gap between your code and the type system.** The gap might be:
1. Missing type annotation → Add it
2. Premature serialization → Keep the model
3. Unknown external data → Build a Pydantic model from the spec

### Example: LSP Response Types

LSP returns JSON, but the LSP 3.17 spec defines exact shapes:

```python
# WRONG: Assume it's dynamic
response: object = await client.request("textDocument/hover", params)
contents = response.get("contents")  # object, need isinstance

# RIGHT: Build model from spec
class Hover(BaseModel):
    contents: MarkupContent | list[MarkedString] | str
    range: Range | None = None

response: Hover = Hover.model_validate(await client.request(...))
value: str = response.contents.value  # Fully typed from spec
```

### Example: Config Schema

If you define the config file, you know the types:

```python
# config/schema.py already defines:
class LanguageServerConfig(BaseModel):
    command: str
    args: list[str] = []
    root_markers: list[str] = []

class ClientConfig(BaseModel):
    languages: dict[str, LanguageServerConfig] = {}

# WRONG: Act like types are unknown
config_data: dict[str, object] = config_obj.model_dump()
languages: object = config_data.get("languages", {})

# RIGHT: Use the schema you defined
for name, lang in config_obj.languages.items():
    cmd: str = lang.command  # From the schema you own
```

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
5. **Keep typed models** - Access `model.field` directly, don't call `model_dump()` early
6. **Trace to source** - Never assume unknown; find definition, check spec, build model

## Using LSP Tools to Trace Types

When you see `reportUnknownVariableType`, use LSP tools to trace the source:

```bash
# 1. Hover to see current type (0-based indexing)
llm-lsp-cli lsp hover src/file.py 25 10 -o json

# 2. Find definition of the type
llm-lsp-cli lsp definition src/file.py 25 10 -o json

# 3. Find callers to trace where value originates (1-based indexing!)
llm-lsp-cli lsp incoming-calls src/file.py 26 10 -o json

# 4. Search for type definitions
llm-lsp-cli lsp workspace-symbol "LanguageServerConfig" -o json
```

**Workflow for unknown types:**
1. Hover → see what checker infers
2. Definition → find where value is created
3. Incoming calls → trace back to source
4. Schema/Spec → build Pydantic model if needed
