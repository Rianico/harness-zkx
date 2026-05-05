---
name: python-expert
description: Python domain expertise for async patterns, testing strategy, Django architecture, PyTorch workflows, and complex type scenarios including type boundary enforcement. Use for non-obvious patterns, framework gotchas, and architectural decisions beyond baseline knowledge. TRIGGER when: designing type boundaries between external data and internal code; choosing between object and Any at API boundaries; implementing single-gateway validation patterns.
argument-hint: "[async|testing|django|pytorch|typing]"
---

# Python Expert Skill

Deep domain knowledge for complex Python scenarios. Invoke when baseline rules are insufficient.

## Async & Concurrency

**Blocking the Event Loop:**
Never put blocking I/O inside `async def`. It blocks the entire event loop.
```python
# BAD
async def fetch():
    response = requests.get(url)  # Blocks!

# GOOD
async def fetch():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

# GOOD (for legacy blocking code)
async def fetch():
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, url)
```

**Context Variables:**
Use `contextvars` instead of `threading.local()` for async state:
```python
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar('request_id')
```

**FastAPI Dependency Injection:**
Use `Depends()` heavily for testability:
```python
async def get_user(token: str = Depends(oauth2_scheme)):
    ...

@app.get("/items")
async def items(user: User = Depends(get_user)):
    ...
```

## Testing Strategy

**Pytest over unittest:**
- Fixtures over `setUp`/`tearDown`
- `pytest-asyncio` for async tests

**Mock Philosophy:**
Minimize `unittest.mock`. Prefer:
- Containerized dependencies (test databases)
- `responses` or VCR for HTTP
- Real implementations when fast enough

```python
# Prefer real DB in container
@pytest.fixture
async def db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_session
    await test_engine.dispose()

# Over mocking
@patch("module.get_user")  # Avoid when possible
async def test_something(mock_get):
    ...
```

## Django Architecture

**Fat Models, Skinny Views:**
Views handle HTTP routing and permissions. Business logic belongs in models or service layer.

**N+1 Query Audit:**
```python
# BAD: N+1 queries
for post in Post.objects.all():
    print(post.author.name)  # Query per post

# GOOD: Join
for post in Post.objects.select_related('author'):
    print(post.author.name)

# GOOD: Many-to-many
for post in Post.objects.prefetch_related('tags'):
    print([t.name for t in post.tags])
```

**DRF Serialization:**
Always use serializers for API I/O. Never return raw model dicts.

## PyTorch Patterns

**Device Agnosticism:**
```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
```

**Memory Management:**
```python
optimizer.zero_grad()  # Before backprop

with torch.no_grad():  # Evaluation
    outputs = model(inputs)

with torch.inference_mode():  # Even faster, read-only
    outputs = model(inputs)
```

**Reproducibility:**
```python
import random
import numpy as np

random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(42)
```

## Type Checking Scenarios

**Type Boundary Enforcement:**
External data (JSON, network, user input) enters as `object`, not `Any`. Validate at a single gateway with Pydantic.

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

**Why `object` over `Any` at boundaries:**
- `object` is a type error waiting to happen — forces validation
- `Any` silently propagates, infecting everything downstream
- Single gateway pattern: only one module imports raw transport

**Single Gateway Architecture:**
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

**Complex Generic Constraints:**
```python
from typing import TypeVar, Generic

T = TypeVar('T', bound='BaseModel')

class Repository(Generic[T]):
    def get(self, id: int) -> T:
        ...
```

**Protocol for Duck Typing:**
```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

def render(obj: Drawable) -> None:
    obj.draw()
```

**Overloads for Complex Signatures:**
```python
from typing import overload

@overload
def process(data: str) -> str: ...
@overload
def process(data: bytes) -> str: ...
def process(data: str | bytes) -> str:
    ...
```
