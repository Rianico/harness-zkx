# Type Safety Patterns

Core patterns for maintaining type safety in Python codebases with Pydantic.

## Core Principles

1. **Fix, don't suppress** — Every diagnostic indicates a real issue
2. **Keep typed models** — Access `model.field` directly; serialize only at output boundaries
3. **Validate at boundaries** — External data → `object` → Pydantic → typed model
4. **Trace to source** — Never assume "unknown"; find definition, check spec, build model

## Common Anti-Patterns

### Premature Serialization

**The #1 cause of typeless propagation.**

```python
# WRONG - loses type information
config_data: dict[str, object] = config_obj.model_dump(mode="json")
languages: object = config_data.get("languages", {})

# RIGHT - keep typed model
for name, lang in config_obj.languages.items():
    cmd: str = lang.command  # Fully typed!
```

**When to call `model_dump()`:** Only at actual serialization boundaries (file, network, JSON response). Never "just in case" for internal processing.

### Serialization in Wrong Layer

**CRITICAL: When type narrowing seems complex, question the function's existence.**

A serialization function in the application layer is often a **layering violation**. The fix is not better typing — it's moving the function to the correct boundary.

```
WRONG:                              CORRECT:
┌─────────────────┐                ┌─────────────────┐
│  LSP Client     │ typed          │  LSP Client     │ typed
│  list[Model]    │                │  list[Model]    │
└────────┬────────┘                └────────┬────────┘
         ↓                                  ↓
┌────────┴────────┐                ┌────────┴────────┐
│  Application    │                │  Application    │
│  serialize() ❌ │ loses types    │  return models  │ keeps types ✓
└────────┬────────┘                └────────┬────────┘
         ↓                                  ↓
┌────────┴────────┐                ┌────────┴────────┐
│  IPC Layer      │                │  IPC Layer      │
│  json.dumps()   │                │  serialize() ✓  │ designated zone
│  send()         │                │  send()         │
└─────────────────┘                └─────────────────┘
```

**Symptom:** Complex `TypeGuard` or `isinstance` chains needed to narrow `list[object]` or `dict[object, object]`.

**Diagnosis:** The function is trying to serialize typed models into untyped dicts one layer too early.

**Fix:** Move `model_dump()` to the actual output boundary (transport, IPC, API response). Delete the premature serialization function.

```python
# WRONG - application layer serialization
async def _send_lsp_request(..., lsp_params: dict[str, object]):
    result = await client.request_document_symbols()  # list[DocumentSymbol]
    return _to_json_serializable(result)  # Why serialize here?

# RIGHT - return typed, serialize at boundary
async def _send_lsp_request(..., lsp_params: DocumentSymbolParams):
    result = await client.request_document_symbols()  # list[DocumentSymbol]
    return {"symbols": result}  # Pass typed model

# In IPC layer (designated zone with file-level suppressions):
def build_response(result: object, request_id: int) -> JSONRPCResponse:
    return JSONRPCResponse(result=_serialize_for_json(result), id=request_id)
```

### `getattr()` Returns `Any`

```python
# WRONG - infects downstream
handler = getattr(self, f"handle_{method}")
result = await handler(...)  # result is Any

# RIGHT - explicit dispatch
if method == "create":
    result = await self.handle_create(...)
elif method == "delete":
    result = await self.handle_delete(...)
else:
    raise ValueError(f"Unknown method: {method}")
```

**Exception:** `getattr()` is acceptable in designated Any zones with proper containment.

### `Any` vs `object` at Boundaries

```python
# WRONG - Any propagates silently
def load_config() -> Any:
    return json.loads(file.read_text())
config = load_config()
name = config["name"]  # OK, but name is Any

# RIGHT - object forces validation
def load_config() -> object:
    return json.loads(file.read_text())
data = Config.model_validate(load_config())
name = data.name  # Fully typed
```

## Type Boundary Architecture

```
External (JSON, network, files) → object
         ↓
VALIDATION BOUNDARY (Pydantic)
         ↓
Typed Models (no Any, no object)
         ↓
INTERNAL CODE
```

### Designated Any Zones

Low-level infrastructure handling raw external data may use `Any` with file-level suppressions. These zones are isolated at the bottom of the architecture.

**Examples of designated zones:**
- Transport/protocol layers (raw JSON-RPC, HTTP clients)
- IPC layers (inter-process communication)
- Stub files for untyped third-party libraries

**Characteristics of designated zones:**
- Single responsibility: receive raw data, return typed data
- File-level suppressions at top of file, never inline
- Any/object never escape upward to business logic

**NOT allowed:** Domain layer, application layer, business logic, project's own type definitions.

## Diagnostic Quick Reference

| Diagnostic | Resolution |
|------------|------------|
| `reportMissingTypeStubs` (internal) | `allowedUntypedLibraries` in config |
| `reportCallInDefaultInitializer` (Typer) | Line-level suppression |
| `reportImplicitStringConcatenation` | Fix code (use f-string or `+`) |
| `reportUnusedParameter` | Use `_param` prefix |
| `reportArgumentType` | Use Pydantic model, not raw dict |
| `reportReturnType` | Align signature with actual return |
| `reportAny` | Annotate container before iteration |
| `reportExplicitAny` | Replace with concrete type |
| `reportUnknownVariableType` | Trace to source, find concrete type |

**Fix over suppress** — Address real issues; suppress only when pattern is intentional. Document every suppression with a comment explaining why.

**Full playbook:** See [diagnostic-resolution.md](diagnostic-resolution.md) for scope hierarchy, category-level thinking, and decision framework.

### `_` Prefix for Unused Parameters

```python
async def handle(self, method: str, _params: dict) -> None:
    pass  # _params indicates intentionally unused
```

## IPC/Transport Patterns

### Method Registry with `@overload`

For type-safe dispatch based on method names:

```python
# Registry mapping method names to types
MethodName = Literal["get", "set", "delete"]
METHOD_TYPES: dict[MethodName, tuple[type[BaseModel], type[BaseModel]]] = {
    "get": (GetParams, GetResult),
    "set": (SetParams, SetResult),
    "delete": (DeleteParams, DeleteResult),
}

# Client with @overload for compile-time safety
class Client:
    @overload
    async def request(self, method: Literal["get"], params: GetParams) -> GetResult: ...

    @overload
    async def request(self, method: Literal["set"], params: SetParams) -> SetResult: ...

    async def request(self, method: MethodName, params: BaseModel) -> BaseModel:
        ...
```

**Benefit:** Compile-time type safety; no `cast()` needed in calling code.

## Verification

Three-layer check for type safety:

1. **Static analysis** — `basedpyright` or `mypy`
2. **LSP diagnostics** — workspace-wide errors from your IDE/LSP
3. **Pattern check** — `rg "# pyright: " src/` should only match designated zone files

**Designated zones check:** Search for suppressions; verify they only exist in infrastructure layers (transport, IPC, external stubs), not in business logic.

## Tracing Unknown Types

When you see `reportUnknownVariableType`:

1. **Hover** — see what the type checker infers
2. **Go to definition** — find where the value is created
3. **Find callers** — trace back to source
4. **Check spec/schema** — build Pydantic model from the spec

**Key insight:** Never assume a diagnostic is "legitimate." Every unknown type has a concrete source — trace it, don't suppress it.
