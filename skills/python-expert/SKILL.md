---
name: python-expert
description: >-
  Python domain expertise for async, testing, Django, and PyTorch. Use for non-obvious patterns, framework gotchas, and architectural decisions beyond baseline. For type checker config, diagnostics, suppressions, and stubs, use the basedpyright-expert skill.
argument-hint: |-
  [async|testing|django|pytorch]
---

# Python Expert Skill

Deep domain knowledge for complex Python scenarios. Invoke when baseline rules are insufficient.

## Type Checker & Diagnostics

For type checker configuration, diagnostic resolution, suppression scope decisions, and stub file (.pyi) authoring, use the **basedpyright-expert** skill.

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
