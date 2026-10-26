---
name: python-expert
description: >-
  Comprehensive Python engineering for Pydantic type safety, async, and packaging. Use when developing typed APIs, debugging async queues, structured logging, or hardening production services.
argument-hint: |-
  [type-safety|async|testing|design|style|structure|error|resilience|observability|config|resources|jobs|packaging|production]
metadata:
  managed-by: programming-expert
---

# Python Expert Skill

Domain knowledge for production Python — typed, observable, resilient, well-structured. Scale Pydantic-first type safety outward through boundaries, concurrency, persistence, and delivery.

> **Pydantic-first type safety is the spine.** Every other section assumes it. For checker config, diagnostic scope, and stub authoring, delegate to **basedpyright-expert** (lives beside this skill, not inside it).

## When to Use — Trigger Matrix

| Trigger in your task                                                           | Load this section         |
| ------------------------------------------------------------------------------ | ------------------------- |
| type hints, generics, `Protocol`, `TypeVar`, `TypeAlias`, `Pydantic`, `strict` | §1 Type Safety            |
| `BaseSettings`, `.env`, secrets, env vars, config validation                   | §2 Configuration          |
| `async`/`await`, `asyncio`, `TaskGroup`, `Semaphore`, `ContextVar`             | §3 Async                  |
| `Celery`, `RQ`, task queue, job state, idempotency, webhook                    | §4 Background Jobs        |
| `with`/`async with`, `__enter__`/`__exit__`, `contextmanager`, `ExitStack`     | §5 Resources              |
| `try`/`except`, `ValidationError`, `HttpError`, retries, backoff, `tenacity`   | §6 Errors & Resilience    |
| `structlog`, JSON logs, metrics, tracing, correlation ID, Prometheus           | §7 Observability          |
| `pytest`, fixtures, `conftest`, mocking, `freezegun`, coverage, TDD            | §8 Testing                |
| SRP, composition, KISS, DDD, layering, dependency injection                    | §9 Design & Structure     |
| `ruff`, `mypy`/`pyright`, PEP 8, docstrings, naming, imports                   | §10 Style & Anti-patterns |
| `pyproject.toml`, `src/` layout, `py.typed`, `wheel`, `pip`/`uv` publish       | §11 Packaging             |
| singleton client, batch/OData, chunked upload, audit trail, production         | §12 Production            |
| pre-commit gate, ruff check, typecheck, pytest verification                    | §13 Verification          |

If your task matches two rows, read both sections plus `references/` for the overlapping pattern.

Upstream synthesis: python-type-safety, python-configuration, async-python-patterns, python-background-jobs, python-resource-management, python-error-handling, python-resilience, python-observability, python-testing-patterns, temporal-python-testing, python-design-patterns, python-project-structure, python-code-style, python-anti-patterns, python-packaging, dataverse-python-production-code, dataverse-python-advanced-patterns, dataverse-python-usecase-builder.

## 1. Type Safety with Pydantic — Most Important

> Read this section on every invocation. The other sections degrade without it.

**Rule: validate once at admission, trust inside.** External `object` → Pydantic `model_validate` → typed model. Internal code never calls `dict.get` or `getattr` on untyped data. Serialize only at transport/IPC/file boundaries (`model_dump` there, nowhere else).

### 1.1 Annotate all public signatures

```python
# Prefer X | None over Optional[X] on 3.10+
def get_user(user_id: str) -> User | None: ...
def process(items: list[Item], max_workers: int = 4) -> BatchResult[ProcessedItem]: ...
# Never mutable defaults — use None sentinel or Field(default_factory=list)
def append_item(item: str, target: list[str] | None = None) -> list[str]: ...

class UserRepository:
    def __init__(self, db: Database) -> None: ...
    async def find_by_id(self, user_id: str) -> User | None: ...
```

Run `basedpyright --strict` or `mypy --strict` in CI. For legacy, enable strict incrementally via per-module `pyproject.toml` overrides — never relax the target.

### 1.2 Pydantic as typed boundary

```python
from pydantic import BaseModel, Field, field_validator

class CreateUserInput(BaseModel):
    email: str = Field(..., min_length=5)
    name: str = Field(..., min_length=1)
    age: int = Field(ge=0, le=150)
    tags: list[str] = Field(default_factory=list)  # default_factory, never []

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower().strip()

# Admission boundary — one place, one time
validated = CreateUserInput.model_validate(raw_json)  # object → typed
user = User.from_input(validated)  # typed throughout
```

- Anti-pattern: `data: dict[str, object] = model.model_dump(); langs = data.get("languages")` — loses types that `model.languages.items()` preserves.
- `Any` at boundaries silences the checker. `object` forces validation. Reserve `Any` for truly dynamic data or designated Any zones (transport/IPC).
- Never mutable default arguments: use `x: list[T] | None = None` sentinel in functions or `Field(default_factory=list)` in Pydantic.

### 1.3 Modern type vocabulary

```python
# Union — X | None (3.10+), X | Y | Z for multi-way
def parse(v: str) -> int | float | str: ...

# Type aliases — `type` statement on 3.12+, TypeAlias on 3.10/3.11
type UserId = str  # 3.12+
UserId2: TypeAlias = str  # 3.10 compat

# Generics (PEP 695, Python 3.12+) — preserve type across containers
class Repository[T: BaseModel]:
    def get(self, id: str) -> T | None: ...

def get[T](id: str) -> T | None: ...

# Protocol — structural typing without inheritance
from typing import Protocol, runtime_checkable
@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict[str, object]: ...
    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Serializable": ...

# Type narrowing — guard, then checker knows
user = find_user(uid)
if user is None:
    raise NotFound(uid)
print(user.name)  # User, not User | None
valid = [x for x in items if x is not None]  # list[Item] narrowed
```

See [type-safety-pydantic.md](references/type-safety-pydantic.md) for `TypeVar` bounds, `@overload`, `Callable`/`Awaitable` protocols, generic `Result[T,E]`, and the strict-mode checklist. For layering violations, premature `model_dump`, and `Any` vs `object` patterns, see [type-safety-patterns.md](references/type-safety-patterns.md). For checker knobs and the suppression ladder, use **basedpyright-expert**.

## 2. Configuration — Typed Settings, Fail Fast

```python
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError
import sys

class Settings(BaseSettings):
    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    api_secret: str = Field(alias="API_SECRET")  # required — no default
    debug: bool = Field(default=False, alias="DEBUG")
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

try:
    settings = Settings()  # singleton at import
except ValidationError as e:
    print(f"Config error: {e}")
    sys.exit(1)
```

- Externalize every env-specific value. Validating at boot catches missing config before a request does.
- Use `alias` for `SCREAMING_SNAKE` env vars while keeping `snake_case` fields. Provide defaults only for safe local-dev values.
- Keep secrets out of code, logs, and errors. Load them from env or a secret manager.

See `[configuration.md](references/configuration.md)`.

## 3. Async & Concurrency

```python
import asyncio, httpx
from contextvars import ContextVar

# Structured concurrency (Python 3.11+ TaskGroup) — cancels siblings on error, zero task leakage
async def fetch_all(urls: list[str]) -> list[dict[str, object]]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(u)) for u in urls]
    return [t.result() for t in tasks]

# Concurrent with backpressure — Semaphore
sem = asyncio.Semaphore(5)
async def bounded_fetch(url: str) -> dict[str, object]:
    async with sem:
        return await fetch(url)

# Context that survives async hops — ContextVar, not thread-local
request_id: ContextVar[str] = ContextVar("request_id")
```

- Prefer `asyncio.TaskGroup` over `asyncio.gather` (`gather` leaks uncancelled orphan tasks on unhandled exceptions).
- Stay fully sync or fully async per call path. Never call sync DB drivers or blocking I/O in `async def` — blocks the whole event loop.
- For CPU work or legacy sync calls, offload with `await asyncio.to_thread(sync_fn, arg)`.
- See producer/consumer queues, async iterators, timeouts, cancellation, and `async with`/`async for` in `[async-patterns.md](references/async-patterns.md)`.

## 4. Background Jobs & Task Queues

- **Pattern:** `POST /jobs` → persist `Job(status=pending)` → enqueue task → return `202 {job_id, poll_url}` immediately → worker updates state (`running → succeeded|failed`).
- **Idempotency & at-least-once delivery:** worker failures trigger retries. Design every task for duplicate execution, using deduplication keys or idempotency tokens.
- **Engines:** Celery (`task_acks_late=True`, `task_reject_on_worker_lost=True`), RQ, Dramatiq, or `asyncio.Queue` for in-process backgrounding.

See full Celery worker setup, failure recovery, and idempotency recipes in `[background-jobs.md](references/background-jobs.md)`.

## 5. Resource Management

```python
from contextlib import contextmanager, AsyncExitStack

# Class-based sync context manager
class DbConn:
    def __enter__(self) -> "DbConn": ...
    def __exit__(self, t, v, tb) -> None: self.close()

with DbConn(dsn) as db:
    db.execute(query)

# Factory with contextmanager decorator
@contextmanager
def managed_file(path: str):
    f = open(path)
    try: yield f
    finally: f.close()

# Async + stacked cleanup
async with AsyncExitStack() as stack:
    conn = await stack.enter_async_context(acquire_conn())
    tmp = stack.enter_context(tempfile.TemporaryDirectory())
```

- `__exit__` always runs — put cleanup there. Return `False` to propagate. Return `True` only to suppress intentionally.
- Streaming with accumulated state: yield chunks, finalize in `finally`/`__exit__`.

See `[resource-management.md](references/resource-management.md)`.

## 6. Error Handling & Resilience

### 6.1 Validate early, fail with context

```python
def process_order(order_id: str, qty: int) -> OrderResult:
    if not order_id:
        raise ValueError("'order_id' required")
    if qty <= 0:
        raise ValueError(f"'qty' must be >0, got {qty}")
    return _process(order_id, qty)
```

Map to the narrowest built-in: `ValueError` (bad value), `TypeError` (wrong type), `FileNotFoundError`, `PermissionError`, `TimeoutError`. Chain with `raise X from e`.

### 6.2 Custom exception hierarchy

```python
class AppError(Exception): ...
class NotFoundError(AppError): ...
class ValidationError(AppError): ...
```

Carry structured fields (`status_code`, `retry_after`) for callers that branch on them.

### 6.3 Pydantic errors at boundaries

Catch `ValidationError` once at admission and return `e.errors()` (field-level detail) — don't stringify and lose structure.

### 6.4 Retry — bounded, jittered, selective

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
RETRYABLE = (ConnectionError, TimeoutError)

@retry(retry=retry_if_exception_type(RETRYABLE),
       stop=stop_after_attempt(5), wait=wait_exponential_jitter(1, 10))
def fetch(url: str) -> dict[str, object]: ...
```

- Never retry `ValueError`, `TypeError`, or auth failures. Do retry `429`, `502`, `503`, `504`, and transient network errors.
- Add jitter to backoff to avoid the thundering herd. Cap attempts *and* total wall time.
- For HTTP status retries, inspect `response.status_code`. For mixed exception+status, combine `retry_if_exception_type` with `retry_if_result`.

### 6.5 Partial failures in batches

```python
def process_batch(items: list[Item]) -> BatchResult[Item, Exception]:
    ok: dict[int, Item] = {}
    failed: dict[int, Exception] = {}
    for i, item in enumerate(items):
        try: ok[i] = process(item)
        except Exception as e: failed[i] = e
    return BatchResult(ok, failed)  # never abort whole batch on one item
```

See `[error-handling.md](references/error-handling.md)` and `[resilience.md](references/resilience.md)`.

## 7. Observability — Logs, Metrics, Traces

```python
import structlog, logging
structlog.configure(processors=[
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.JSONRenderer(),
], logger_factory=structlog.PrintLoggerFactory())

logger = structlog.get_logger()
logger.info("request.completed", correlation_id=cid.get(), status=200, duration_ms=42)
```

- Emit JSON in prod (`TimeStamper` + `JSONRenderer`). Human-readable logs are fine locally.
- Every log carries `correlation_id` (via `ContextVar`) + `method`/`path`/`status_code` — enables end-to-end trace.
- Levels: `DEBUG` dev only, `INFO` lifecycle, `WARNING` recoverable, `ERROR` needs attention.
- Metrics: Prometheus with bounded label cardinality — a `user_id` label is banned. Trace with `trace_id` propagated via context.
- Golden signals: latency, traffic, errors, saturation per boundary.

See `[observability.md](references/observability.md)`.

## 8. Testing Strategy

```
tests/
  conftest.py
  test_unit/  test_models.py  test_utils.py
  test_integration/  test_api.py  test_db.py
  test_e2e/  test_workflows.py
```

```python
# Fixtures over setUp/tearDown; real deps in containers, not mocks
@pytest.fixture
async def db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_session

# AAA: Arrange / Act / Assert
def test_create_user_with_valid_data_returns_user():
    data = {"email": "a@b.com", "name": "Alice"}
    user = service.create(CreateUserInput.model_validate(data))
    assert user.id is not None

def test_create_user_with_invalid_email_raises():
    with pytest.raises(ValidationError, match="email"):
        service.create(CreateUserInput.model_validate({"email": "bad"}))

# Markers & coverage
@pytest.mark.slow
@pytest.mark.asyncio
async def test_fetch_with_timeout(): ...

# pytest --cov=myapp --cov-fail-under=80 --cov-report=term-missing
```

- Prefer real DB/queue in containers (`responses` for HTTP). Minimize mocks to contracts.
- Temporal workflows: `WorkflowEnvironment.start_time_skipping()` for unit, mock activities for integration, replay histories for determinism — see `[temporal-testing.md](references/temporal-testing.md)`.
- Details: parametrization, `monkeypatch`, `freezegun` for time, property-based tests in `[testing-patterns.md](references/testing-patterns.md)`.
- **Refutation by counterexample & small-input oracle tests:** supply concrete evidence for algorithmic or state-machine defects. When debugging or reviewing, produce a minimal failing input (`input -> expected vs observed`). Test combinatorial logic with exhaustive oracle tables or property-based tests (`hypothesis`).

## 9. Design & Project Structure

**Layered layout — dependencies point down:**

```
myapp/
  api/           # handlers, routes, middleware
  services/      # business logic (pure, typed)
  repositories/  # data access
  models/        # domain entities (Pydantic)
  schemas/       # API I/O schemas
  config/        # Settings
  __init__.py    # public surface via __all__
```

**Core rules:**

- **KISS + SRP** — one reason to change. Delete before you abstract. Apply the Rule of Three against premature abstraction.
- **Deep modules over classitis** — Python functions and modules are first-class namespaces. Do not introduce classes solely to wrap a single function or create 5-line DTO mappers. A module with an explicit `__all__` should present a narrow, ergonomic interface while absorbing internal complexity (validation, atomic DB transactions, caching, error translation).
- **Design deepening vs. scope creep** — decomposing monolithic files into private submodules (`_submodule.py`, `_internal/`) cures Divergent Change and God modules. That decomposition is permitted design deepening. Add architectural regression tests (`tests/test_arch.py`) to enforce layering and boundary invariants. Never widen `__all__` or public exports without mandate.
- **Transactional atomicity (`BEGIN IMMEDIATE`)** — multi-step mutations across multiple models or tables run in one atomic transaction (`async with session.begin():`). Fragmenting them across loose commits is a defect. Hybrid disk+DB operations must report desyncs explicitly.
- **Composition over inheritance** — combine behaviors. Protocols define the seam when you need polymorphism.
- **Dependency injection** — constructor injection for testability. A class with 7+ `__init__` params is too large. Split it.
- **Explicit public API** — every package defines `__all__`. Consumers import from the package, never its internals.
- **Flat over deep** — `project/services/user_service.py` beats `project/core/internal/services/impl/user/`. Use absolute imports only.

See `[design-patterns.md](references/design-patterns.md)` and `[project-structure.md](references/project-structure.md)`.

## 10. Code Style & Anti-patterns

**Tooling — one `pyproject.toml`:**

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
[tool.ruff.lint]
select = ["E","W","F","I","B","C4","UP","SIM"]
[tool.ruff.format]
quote-style = "double"

[tool.mypy]
strict = true
warn_return_any = true
```

```bash
ruff check --fix . && ruff format . && basedpyright
```

**Style:** snake_case modules, `PascalCase` classes, `SCREAMING_SNAKE_CASE` constants. Use absolute imports. Write Google-style docstrings on every public API. Keep 120-char lines with explicit breaks. Naming and import detail: [code-style.md](references/code-style.md).

**Anti-patterns** (scan before merge):

- Classitis and shallow pass-through wrappers — single-function classes, 5-line DTO mapping layers.
- Mutable defaults (`def f(x=[])`). Use a `None` sentinel or `Field(default_factory=list)`.
- Late-binding closures in loops (`lambda i=i:`, `functools.partial`).
- Unchained exceptions — `raise ... from e` missing.
- Scattered or doubled timeout/retry logic.
- Hardcoded secrets.
- ORM models leaking to the API.
- Mixed I/O and logic.
- Bare `except Exception: pass`.
- Aborted batches and unclosed resources.
- Blocking sync calls in `async`.
- Missing type hints and untyped collections.

Full checklist with recovery actions: [anti-patterns.md](references/anti-patterns.md).

## 11. Packaging — `src` Layout, `pyproject.toml`, Distribution

```
my-package/
  pyproject.toml  README.md  LICENSE
  src/my_package/__init__.py  core.py  py.typed
  tests/test_core.py
```

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatch.build"

[project]
name = "my-package"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = ["pydantic>=2.0", "httpx>=0.27"]

[project.optional-dependencies]
dev = ["pytest>=9", "ruff", "basedpyright"]

[tool.setuptools.packages.find]  # if setuptools backend
where = ["src"]
```

- Prefer the `src/` layout (prevents accidental `import src`), `hatchling` or `setuptools>=61`, and PEP 621 `pyproject.toml`. Include the `py.typed` marker for typed libraries.
- Build with `python -m build`. Publish with `twine upload --repository testpypi`, then `pypi`.

See `[packaging.md](references/packaging.md)`.

## 12. Production Readiness

SDK and service integrations require production hygiene. Manage singleton clients. Retry transient errors (`429`, `503`, timeouts) with exponential backoff. Filter server-side (`filter`, `select`, `top`). Chunk uploads (4 MiB). Invalidate metadata caches.

- For full singleton client patterns, OData/batch architectures, and retry hierarchies, see [production-patterns.md](references/production-patterns.md).
- Legacy Django deep dives: [django-patterns.md](references/django-patterns.md), [django-security.md](references/django-security.md), [django-tdd.md](references/django-tdd.md), [django-verification.md](references/django-verification.md). PyTorch: [pytorch-patterns.md](references/pytorch-patterns.md). Use only when those frameworks apply.

## Type Checker Routing

For `basedpyright`/`pyright` config, `typeCheckingMode`, `baseline.json`, `report*` diagnostics, `py.typed`, and mypy migration, use **basedpyright-expert** directly. That material stays out of this skill. Local deep dives: [diagnostic-resolution.md](references/diagnostic-resolution.md) — decision framework for basedpyright and ruff warnings. [stub-files.md](references/stub-files.md) — `.pyi` authoring guide.

## 13. Verification

```bash
uv run ruff check . && uv run basedpyright && uv run pytest
# LSP-wide stale check
uv run python -m basedpyright --stats
```

- **Fix > suppress.** Suppression ladder: 1) fix the code. 2) line `# pyright: ignore[rule]` + reason. 3) file-level. 4) config category. Global disable is banned.
- Designated Any zones: `rg "# pyright: ignore" src/` must only hit transport/IPC bottom layers.
