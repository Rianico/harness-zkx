---
name: python-expert
description: >-
  Comprehensive Python engineering — Pydantic type safety, async, testing, design, observability, resilience, resources, jobs, packaging, production. Use for typed APIs, strict checking, async/queues, structured logging, retries, layout. TRIGGER: Pydantic, type safety, async, pytest
argument-hint: |-
  [type-safety|async|testing|design|style|structure|error|resilience|observability|config|resources|jobs|packaging|production]
metadata:
  managed-by: programming-expert
---

# Python Expert Skill

Domain knowledge for production Python — typed, observable, resilient, well-structured. Scale Pydantic-first type safety outward through boundaries, concurrency, persistence, and delivery.

> **Pydantic-first type safety is the spine.** Every other section assumes it. For checker config, diagnostic scope, and stub authoring, delegate to **basedpyright-expert** (lives beside this skill, not inside it).

## When to Use — Trigger Matrix

| Trigger in your task                                                           | Load this section         | Source skills                                                                                          |
| ------------------------------------------------------------------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------ |
| type hints, generics, `Protocol`, `TypeVar`, `TypeAlias`, `Pydantic`, `strict` | §1 Type Safety            | python-type-safety                                                                                     |
| `BaseSettings`, `.env`, secrets, env vars, config validation                   | §2 Configuration          | python-configuration                                                                                   |
| `async`/`await`, `asyncio`, `gather`, `Semaphore`, `ContextVar`                | §3 Async                  | async-python-patterns                                                                                  |
| `Celery`, `RQ`, task queue, job state, idempotency, webhook                    | §4 Background Jobs        | python-background-jobs                                                                                 |
| `with`/`async with`, `__enter__`/`__exit__`, `contextmanager`, `ExitStack`     | §5 Resources              | python-resource-management                                                                             |
| `try`/`except`, `ValidationError`, `HttpError`, retries, backoff, `tenacity`   | §6 Errors & Resilience    | python-error-handling, python-resilience                                                               |
| `structlog`, JSON logs, metrics, tracing, correlation ID, Prometheus           | §7 Observability          | python-observability                                                                                   |
| `pytest`, fixtures, `conftest`, mocking, `freezegun`, coverage, TDD            | §8 Testing                | python-testing-patterns, temporal-python-testing                                                       |
| SRP, composition, KISS, DDD, layering, dependency injection                    | §9 Design & Structure     | python-design-patterns, python-project-structure                                                       |
| `ruff`, `mypy`/`pyright`, PEP 8, docstrings, naming, imports                   | §10 Style & Anti-patterns | python-code-style, python-anti-patterns                                                                |
| `pyproject.toml`, `src/` layout, `py.typed`, `wheel`, `pip`/`uv` publish       | §11 Packaging             | python-packaging                                                                                       |
| singleton client, batch/OData, chunked upload, audit trail, production         | §12 Production            | dataverse-python-production-code, dataverse-python-advanced-patterns, dataverse-python-usecase-builder |

If your task matches two rows, read both sections plus `references/` for the overlapping pattern.

## 1. Type Safety with Pydantic — Most Important

> Read this section on every invocation. The other sections degrade without it.

**Rule: validate once at admission, trust inside.** External `object` → Pydantic `model_validate` → typed model → internal code never calls `dict.get` or `getattr` on untyped data. Serialize only at transport/IPC/file boundaries (`model_dump` there, nowhere else).

### 1.1 Annotate all public signatures

```python
# Prefer X | None over Optional[X] on 3.10+
def get_user(user_id: str) -> User | None: ...
def process(items: list[Item], max_workers: int = 4) -> BatchResult[ProcessedItem]: ...

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
- `Any` at boundaries silences the checker; `object` forces validation. Reserve `Any` for truly dynamic data or designated Any zones (transport/IPC).

### 1.3 Modern type vocabulary

```python
# Union — X | None (3.10+), X | Y | Z for multi-way
def parse(v: str) -> int | float | str: ...

# Type aliases — `type` statement on 3.12+, TypeAlias on 3.10/3.11
type UserId = str  # 3.12+
UserId2: TypeAlias = str  # 3.10 compat

# Generics — preserve type across containers
from typing import TypeVar, Generic
T = TypeVar("T", bound=BaseModel)
class Repository(Generic[T]):
    def get(self, id: str) -> T | None: ...

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

See `[type-safety-patterns.md](references/type-safety-pydantic.md)` for `TypeVar` bounds, `@overload`, `Callable`/`Awaitable` protocols, generic `Result[T,E]`, and the strict-mode checklist. For checker knobs and suppression ladder, use **basedpyright-expert**.

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

- Externalize every env-specific value; `model_validate` at boot catches missing config before a request does.
- Use `alias` for `SCREAMING_SNAKE` env vars while keeping `snake_case` fields. Provide defaults only for safe local-dev values.
- Keep secrets out of code/logs/errors; load from env or secret manager.

See `[configuration.md](references/configuration.md)`.

## 3. Async & Concurrency

```python
import asyncio, httpx

# Never block the loop
async def fetch(url: str) -> dict[str, object]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()  # type: ignore[no-any-return]

# Concurrent with backpressure — gather + Semaphore
sem = asyncio.Semaphore(5)
async def bounded_fetch(url: str) -> dict[str, object]:
    async with sem:
        return await fetch(url)
results = await asyncio.gather(*(bounded_fetch(u) for u in urls))

# Context that survives async hops — ContextVar, not thread-local
from contextvars import ContextVar
request_id: ContextVar[str] = ContextVar("request_id")
```

- Stay fully sync or fully async per call path. Mixing `requests`/`time.sleep` inside `async def` blocks the loop.
- For CPU work inside async, offload with `await asyncio.to_thread(cpu_bound)`.
- See producer/consumer queues, async iterators, timeouts, cancellation, and `async with`/`async for` in `[async-patterns.md](references/async-patterns.md)`.

## 4. Background Jobs & Task Queues

```python
from celery import Celery
app = Celery("tasks", broker="redis://localhost:6379")
app.conf.update(task_acks_late=True, task_reject_on_worker_lost=True,
                worker_prefetch_multiplier=1)

@app.task(bind=True, max_retries=3, autoretry_for=(ConnectionError, TimeoutError))
def send_email(self, to: str, subject: str, body: str) -> None:
    email_client.send(to, subject, body)

# API returns job ID immediately; worker runs async
@app.task  # enqueue: send_email.delay(to, subject, body)
def noop(): ...
```

- Pattern: `POST /jobs` → persist `Job(status=pending)` → `enqueue` → `202 {job_id, poll_url}` → worker updates `running → succeeded/failed`.
- Idempotent tasks, at-least-once delivery → guard against duplicate execution; job state machine `pending → running → succeeded|failed`.
- Alternatives: RQ, Dramatiq, `asyncio.Queue`, cloud queues — same state/idempotency rules.

See `[background-jobs.md](references/background-jobs.md)`.

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

- `__exit__` always runs — put cleanup there; return `False` to propagate, `True` only to suppress intentionally.
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

- Never retry `ValueError`/`TypeError`/auth failures; do retry `429`, `502`, `503`, `504` and transient network errors.
- Add jitter to backoff to avoid thundering herd; cap attempts _and_ total wall time.
- For HTTP status retries, inspect `response.status_code`; for mixed exception+status, combine `retry_if_exception_type` + `retry_if_result`.

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

- Emit JSON in prod (`TimeStamper` + `JSONRenderer`); human-readable locally is fine.
- Every log carries `correlation_id` (via `ContextVar`) + `method`/`path`/`status_code` — enables end-to-end trace.
- Levels: `DEBUG` dev only, `INFO` lifecycle, `WARNING` recoverable, `ERROR` needs attention.
- Metrics: Prometheus with bounded label cardinality (never `user_id` as label); trace with `trace_id` propagated via context.
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

- Prefer real DB/queue in containers (`responses` for HTTP); minimize mocks to contracts.
- Temporal workflows: `WorkflowEnvironment.start_time_skipping()` for unit, mock activities for integration, replay histories for determinism — see `[temporal-testing.md](references/temporal-testing.md)`.
- Details: parametrization, `monkeypatch`, `freezegun` for time, property-based tests in `[testing-patterns.md](references/testing-patterns.md)`.

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

- **KISS + SRP** — one reason to change; delete before you abstract; Rule of Three for premature abstraction.
- **Composition over inheritance** — combine behaviors; Protocols define the seam when you need polymorphism.
- **Dependency injection** — constructor injection for testability; if `__init__` has 7+ params, the class is too large — split it.
- **Explicit public API** — every package defines `__all__`; consumers import from the package, not internals.
- **Flat over deep** — `project/services/user_service.py` beats `project/core/internal/services/impl/user/`; absolute imports only.

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

**Style:** snake_case modules, `PascalCase` classes, `SCREAMING_SNAKE_CASE` constants; absolute imports; Google-style docstrings on every public API; 120-char lines with explicit breaks.

**Anti-patterns checklist** (scan before merge):

- Scattered timeout/retry, double retry at two layers, hardcoded secrets, leaking ORM models to API, mixed I/O+logic, bare `except Exception: pass`, aborted batches, unclosed resources, blocking `time.sleep`/`requests` in `async`, missing type hints, untyped `list` — see `[anti-patterns.md](references/anti-patterns.md)`.

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
dev = ["pytest>=8", "ruff", "basedpyright"]

[tool.setuptools.packages.find]  # if setuptools backend
where = ["src"]
```

- Prefer `src/` layout (prevents accidental `import src`), `hatchling`/`setuptools>=61`, PEP 621 `pyproject.toml`; include `py.typed` marker for typed libraries.
- Build `python -m build`; publish `twine upload --repository testpypi` then `pypi`.

See `[packaging.md](references/packaging.md)`.

## 12. Production Readiness

Abstracted from Dataverse production patterns — apply to any SDK/service integration:

```python
# Singleton client + typed config
class Service:
    _instance = None
    def __new__(cls, *a, **kw):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self, settings: Settings) -> None:
        if not hasattr(self, "_client"):
            self._client = DataverseClient(settings.org_url, credential)  # replace with your SDK

# Retry with DataverseError-style hierarchy
for attempt in range(3):
    try:
        return client.create(table, records)
    except HttpError as e:
        if attempt == 2 or not e.is_transient: raise
        time.sleep(2 ** attempt)

# Query optimization — push work to server
client.get(table, filter="status eq 1", select=["id","name"], orderby="name", top=500)
# For large payloads: chunked upload / batch create / paged iteration
```

- Idempotency keys, batch with partial-failure handling, `select`/`filter`/`top`/`orderby` pushed server-side, file uploads chunked (4 MiB), metadata cache invalidation on schema change.

See `[production-patterns.md](references/production-patterns.md)`. Legacy Django/PyTorch deep dives remain in `[django-patterns.md](references/django-patterns.md)` / `[pytorch-patterns.md](references/pytorch-patterns.md)` — use only when those frameworks apply.

## References — Progressive Disclosure

| File                                                            | When to follow the pointer                                                                                                                                                            |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [type-safety-pydantic.md](references/type-safety-pydantic.md)   | `TypeVar` bounds, generic `Repository[T,ID]`, `Protocol`/`@runtime_checkable`, `TypeAlias` vs `type`, `Callable`/`Awaitable`, `Result[T,E]`, strict-mode checklist, tracing `Unknown` |
| [type-safety-patterns.md](references/type-safety-patterns.md)   | Premature `model_dump`, layering violation, `Any` vs `object`, IPC `@overload` registry                                                                                               |
| [configuration.md](references/configuration.md)                 | `BaseSettings` env files, local defaults, secret handling, env-specific overrides                                                                                                     |
| [async-patterns.md](references/async-patterns.md)               | `gather`, `Semaphore` rate limiting, producer/consumer `Queue`, `async for`/`async with`, locks, scraping                                                                             |
| [background-jobs.md](references/background-jobs.md)             | Job state machine, Celery config, idempotency, at-least-once handling                                                                                                                 |
| [resource-management.md](references/resource-management.md)     | `__aenter__`/`__aexit__`, `ExitStack`/`AsyncExitStack`, nested cleanup, streaming                                                                                                     |
| [error-handling.md](references/error-handling.md)               | Custom `ApiError` hierarchy, `ValidationError` mapping, partial-failure `BatchResult`                                                                                                 |
| [resilience.md](references/resilience.md)                       | `tenacity` recipes, exception vs status retry, jitter, circuit breaker                                                                                                                |
| [observability.md](references/observability.md)                 | `structlog` JSON setup, consistent fields, Prometheus labels, correlation propagation                                                                                                 |
| [testing-patterns.md](references/testing-patterns.md)           | Fixture design, `monkeypatch`, `freezegun`, parametrization, property-based                                                                                                           |
| [temporal-testing.md](references/temporal-testing.md)           | Temporal `WorkflowEnvironment`, activity mocking, replay, time-skipping                                                                                                               |
| [design-patterns.md](references/design-patterns.md)             | KISS/SRP/composition deep patterns, DI, god-class split heuristics                                                                                                                    |
| [project-structure.md](references/project-structure.md)         | `__all__` APIs, flat vs domain-driven layout, layering violations                                                                                                                     |
| [anti-patterns.md](references/anti-patterns.md)                 | Full checklist — timeout/double-retry/secrets/ORM-leak/ bare `except`/blocking-in-async                                                                                               |
| [packaging.md](references/packaging.md)                         | `src` vs flat, multi-package, `py.typed`, build backends                                                                                                                              |
| [production-patterns.md](references/production-patterns.md)     | Batch, OData, cache flush, chunked files, `PandasODataClient`, use-case builder                                                                                                       |
| [diagnostic-resolution.md](references/diagnostic-resolution.md) | `basedpyright` ignore ladder and category thinking                                                                                                                                    |
| [stub-files.md](references/stub-files.md)                       | `.pyi` authoring                                                                                                                                                                      |
| [django-patterns.md](references/django-patterns.md)             | Django ORM/N+1/security (legacy)                                                                                                                                                      |
| [pytorch-patterns.md](references/pytorch-patterns.md)           | PyTorch device/grad/inference (legacy)                                                                                                                                                |

## Type Checker Routing

For `basedpyright`/`pyright` config, `typeCheckingMode`, `baseline.json`, `report*` diagnostics, `py.typed`, and migration from `mypy`, use **basedpyright-expert** directly — do not duplicate that material here.

## Verification

```bash
ruff check . && ruff format --check . && basedpyright && uv run pytest --cov=myapp --cov-fail-under=80
# LSP-wide stale check
uv run python -m basedpyright --stats
```

- **Fix > suppress.** Suppression ladder: 1 fix code → 2 line `# pyright: ignore[rule]` + reason → 3 file-level → 4 config category → never global disable.
- Designated Any zones: `rg "# pyright: ignore" src/` must only hit transport/IPC bottom layers.
