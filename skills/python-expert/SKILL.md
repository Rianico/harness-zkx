---
name: python-expert
description: Python domain expertise for async patterns, testing strategy, Django architecture, PyTorch workflows, complex type scenarios including type boundary enforcement and suppression handling, and stub file (.pyi) authoring. Use for non-obvious patterns, framework gotchas, and architectural decisions beyond baseline knowledge. TRIGGER when: designing type boundaries between external data and internal code; choosing between object and Any at API boundaries; implementing single-gateway validation patterns; handling type checker diagnostics; deciding how to fix pyright/mypy errors; deciding suppression scope (line/file/config level); resolving warnings appearing 50+ times (category-level thinking); implementing IPC or transport layers with generic types; seeing reportUnknownVariableType or reportMissingTypeStubs diagnostics; deciding when to call model_dump(); premature serialization causing type loss; tracing types to source definitions; serialization functions in application layer causing complex type narrowing; writing or maintaining stub files (.pyi); generating stubs with stubgen/stubtest; distributing type information for third-party libraries; handling Incomplete vs Any in stubs; creating overloaded function stubs; defining protocols in stubs.
argument-hint: "[async|testing|django|pytorch|typing|stubs]"
---

# Python Expert Skill

Deep domain knowledge for complex Python scenarios. Invoke when baseline rules are insufficient.

## Handling Type Diagnostics

**Fix over suppress** — Address real issues whenever possible; suppress only when pattern is intentional.

**CRITICAL: Never assume a diagnostic is "legitimate"** — trace the calling chain, definitions, and specs to find the concrete type.

| Diagnostic | Resolution |
|------------|------------|
| `reportMissingTypeStubs` (internal) | `allowedUntypedLibraries` in config |
| `reportCallInDefaultInitializer` (Typer) | Line-level suppression |
| `reportImplicitStringConcatenation` | Fix code (use f-string or `+`) |
| `reportUnusedParameter` | Use `_param` prefix |
| `reportArgumentType` | Use Pydantic models |
| `reportReturnType` | Align signatures |
| `reportAny` | Annotate containers |
| `reportExplicitAny` | Use concrete type |
| `reportUnknownVariableType` | Trace to source, find concrete type |

**Decision Framework:**
1. Is it a real bug? → Fix the code
2. Is it a false positive? → Suppress at most precise scope
3. Is it intentional pattern (e.g., Typer)? → Suppress + document why

**Reference:** [diagnostic-resolution.md](references/diagnostic-resolution.md) — Full playbook with scope hierarchy, category-level thinking, and suppression patterns.

```python
# Unused param: use _ prefix
async def handle(self, method: str, _params: dict) -> None:
    pass  # _params indicates intentionally unused

# Type mismatch: use Pydantic model
params = TextDocumentIdentifier(uri=uri).model_dump(mode="json")
result = await transport.send_request("textDocument/definition", params)
```

### Trace Types to Source

When a diagnostic shows "unknown type", don't suppress — trace it:

1. **Hover on the symbol** — see what type the checker infers
2. **Find definition** — where does the value originate?
3. **Check specs/schemas** — is there a known type in the spec?
4. **Build a Pydantic model** — if response has a spec, create a model

```python
# WRONG: Assume it's dynamic, use object
languages: object = config_data.get("languages", {})

# RIGHT: Trace the type - config schema defines it
# From config/schema.py: languages: dict[str, LanguageServerConfig]
for lang_name, lang_conf in config_obj.languages.items():
    root_markers: list[str] = lang_conf.root_markers  # Fully typed!
```

**Reference:** [type-safety-patterns.md](references/type-safety-patterns.md) — Full details on containment patterns, IPC method registry, `@overload` patterns.

## Type Boundaries

External data enters as `object`, validated once at the gateway, returned as typed:

```python
# BAD: Any propagates silently
def get_data() -> Any: ...

# BAD: object returned, caller must validate
def get_data() -> object: ...
data = Model.model_validate(result)  # Every caller must do this!

# GOOD: validate at boundary, return typed
def get_data() -> Model:
    raw = fetch_external()  # object from external source
    return Model.model_validate(raw)  # Validate once, return typed

data = get_data()  # Already typed, no validation needed at call site
```

### Keep Typed Models, Serialize at Boundaries

**The #1 cause of typeless propagation: premature `model_dump()` calls.**

```python
# WRONG - throws away type information
config_data: dict[str, object] = config_obj.model_dump(mode="json")
languages: object = config_data.get("languages", {})  # Lost the type!
if isinstance(languages, dict):
    for lang_name, lang_conf in languages.items():
        # lang_conf is object - must use isinstance everywhere

# RIGHT - keep typed model, access directly
for lang_name, lang_conf in config_obj.languages.items():
    # lang_conf is LanguageServerConfig - fully typed!
    root_markers: list[str] = lang_conf.root_markers
```

**When to call `model_dump()`:** Only at actual serialization boundaries (writing to file, sending over network, returning JSON response). Never "just in case" for internal processing.

### Serialization Belongs at Output Boundaries

**CRITICAL INSIGHT:** When a type issue seems to require complex narrowing or suppressions, ask: *Why does this function exist? Is it in the right layer?*

A serialization function in the application layer is often a **layering violation**. The fix is not better typing — it's moving the function to the correct boundary.

```
WRONG:                           CORRECT:
LSP Client (typed)               LSP Client (typed)
    ↓                                ↓
Application Layer                 Application Layer (return typed)
    ↓ serialize() ❌                    ↓
IPC Layer                        IPC Layer (serialize + send) ✓
    ↓ send                            ↓ send
```

**Designated serialization zones:** Transport layers, IPC handlers, API response builders — code that sits at the edge of the system. Application logic should return typed models and let the boundary serialize.

```python
# WRONG - application layer doing serialization
async def handle_request():
    result = await client.request_document_symbols()
    return _to_json_serializable(result)  # Why does this exist here?

# RIGHT - return typed, let boundary serialize
async def handle_request():
    result = await client.request_document_symbols()  # list[DocumentSymbol]
    return result  # Pass typed model to IPC layer

# In IPC layer (designated zone):
def build_response(result: object) -> dict:
    return {"result": _serialize_for_json(result)}  # Boundary handles this
```

### object Annotation Overuse

When you know the schema, use the concrete type:

```python
# WRONG - forces isinstance checks everywhere
def process_config(config: dict[str, object]) -> None:
    languages = config.get("languages", {})  # object
    if isinstance(languages, dict):
        ...

# RIGHT - trust the validated type
def process_config(config: ClientConfig) -> None:
    for name, lang_conf in config.languages.items():
        # lang_conf is LanguageServerConfig
```

**Reference:** [type-safety-patterns.md](references/type-safety-patterns.md) — Single gateway architecture, designated Any zones.

## Async & Concurrency

**Never block the event loop:**
```python
# BAD
async def fetch():
    response = requests.get(url)  # Blocks!

# GOOD
async def fetch():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
```

**Context variables over thread-local:**
```python
from contextvars import ContextVar
request_id: ContextVar[str] = ContextVar('request_id')
```

## Testing Strategy

- **Pytest over unittest:** Fixtures over `setUp`/`tearDown`
- **Minimize mocks:** Prefer containerized deps, `responses` library for HTTP

```python
# Prefer real DB in container
@pytest.fixture
async def db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_session
```

## Django Architecture

**N+1 Query Audit:**
```python
# BAD: N+1 queries
for post in Post.objects.all():
    print(post.author.name)  # Query per post

# GOOD: Join
for post in Post.objects.select_related('author'):
    print(post.author.name)
```

**Reference:** [django-patterns.md](references/django-patterns.md), [django-security.md](references/django-security.md), [django-tdd.md](references/django-tdd.md)

## PyTorch Patterns

```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

optimizer.zero_grad()  # Before backprop

with torch.inference_mode():  # Read-only, fastest
    outputs = model(inputs)
```

**Reference:** [pytorch-patterns.md](references/pytorch-patterns.md)

## Complex Generic Constraints

```python
from typing import TypeVar, Generic, Protocol, overload

T = TypeVar('T', bound='BaseModel')

class Repository(Generic[T]):
    def get(self, id: int) -> T: ...

class Drawable(Protocol):
    def draw(self) -> None: ...

@overload
def process(data: str) -> str: ...
@overload
def process(data: bytes) -> str: ...
def process(data: str | bytes) -> str: ...
```

## Stub Files (.pyi)

Stub files provide type information without implementation. Use for third-party libraries, distributing types separately, or complex type logic.

**Quick Reference:**

| Task | Tool |
|------|------|
| Generate stubs | `stubgen -p package` or `pyright --createstub package` |
| Validate stubs | `stubtest package` |
| Lint stubs | `flake8-pyi` |

**Key Patterns:**
```python
# Use ellipsis for bodies
def foo(x: int) -> str: ...

# Use Incomplete instead of Any for partial stubs
from _typeshed import Incomplete
def bar(x: Incomplete) -> list[Incomplete]: ...

# All overloads need @overload (no implementation signature)
@overload
def open(name: str, mode: Literal["r"]) -> Reader: ...
@overload
def open(name: str, mode: Literal["w"]) -> Writer: ...

# Stub-only protocols
@type_check_only
class Readable(Protocol):
    def read(self) -> str: ...
```

**Reference:** [stub-files.md](references/stub-files.md) — Full guide on syntax, overloads, protocols, validation workflow.
