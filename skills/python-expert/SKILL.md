---
name: python-expert
description: Python domain expertise for async patterns, testing strategy, Django architecture, PyTorch workflows, and complex type scenarios including type boundary enforcement and suppression handling. Use for non-obvious patterns, framework gotchas, and architectural decisions beyond baseline knowledge. TRIGGER when: designing type boundaries between external data and internal code; choosing between object and Any at API boundaries; implementing single-gateway validation patterns; handling type checker diagnostics; deciding how to fix pyright/mypy errors; implementing IPC or transport layers with generic types.
argument-hint: "[async|testing|django|pytorch|typing]"
---

# Python Expert Skill

Deep domain knowledge for complex Python scenarios. Invoke when baseline rules are insufficient.

## Handling Type Diagnostics

**NO INLINE SUPPRESSIONS** - Fix the underlying issue instead of hiding with `# pyright: ignore`.

| Diagnostic | Fix |
|------------|-----|
| `reportUnusedParameter` | Use `_param` prefix |
| `reportArgumentType` | Use Pydantic models |
| `reportReturnType` | Align signatures |
| `reportAny` | Annotate containers |
| `reportExplicitAny` | Use concrete type |

```python
# Unused param: use _ prefix
async def handle(self, method: str, _params: dict) -> None:
    pass  # _params indicates intentionally unused

# Type mismatch: use Pydantic model
params = TextDocumentIdentifier(uri=uri).model_dump(mode="json")
result = await transport.send_request("textDocument/definition", params)
```

**Reference:** [type-safety-patterns.md](references/type-safety-patterns.md) — Full details on containment patterns, IPC method registry, `@overload` patterns.

## Type Boundaries

External data enters as `object`, validated at single gateway:

```python
# BAD: Any propagates silently
def get_data() -> Any: ...

# GOOD: object forces validation
def get_data() -> object: ...
data = Model.model_validate(result)  # Now typed
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
