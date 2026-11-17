# Crux Review Rubric & Heuristics

This reference details the patterns and anti-patterns evaluated during multi-agent code review.

---

## 1. Epistemic Truth & Test Refutability (VDD)[^addy-quality]

### The Paper Tiger Anti-Pattern
A test that passes without exercising system state transitions provides zero information.

```python
# REJECT (Paper Tiger): Mocking the method under test
def test_user_creation(mocker):
    mocker.patch("service.UserService.create_user", return_value=User(id=1))
    service = UserService()
    user = service.create_user("alice")
    assert user.id == 1  # Proves nothing about UserService.create_user!

# APPROVE (Refutable Behavioral Test): Real component, mocked IO boundary
def test_user_creation(db_session):
    service = UserService(repo=SQLUserRepository(db_session))
    user = service.create_user("alice")
    assert user.id is not None
    assert db_session.query(UserModel).filter_by(name="alice").one()
```

### The Tautological Assertion Anti-Pattern
```python
# REJECT: Asserting mock calls without state validation
def test_send_notification(mocker):
    mock_notifier = mocker.patch("notifier.send")
    dispatch_alert("alert_id")
    mock_notifier.assert_called_once()  # Did alert serialize correctly?

# APPROVE: Asserting payload schema and negative rejection
def test_send_notification(fake_transport):
    dispatch_alert(Alert(severity="CRITICAL", message="out of memory"))
    sent = fake_transport.pop_message()
    assert sent.severity == "CRITICAL"
    assert "out of memory" in sent.body
```

### Mock Surface Enumeration
```typescript
// REJECT: Hand-enumerating exports; unmocked helpers return undefined
vi.mock('./logger', () => ({
  log: vi.fn(),
}));

// APPROVE: Factory preserving module surface and types
vi.mock('./logger', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./logger')>()),
  log: vi.fn(),
}));
```

---

## 2. Intent Alignment & State Safety (EDD)[^mattpocock]

### Hardcoded Test Passes
```python
# REJECT: Hardcoding input to pass the unit test
def calculate_discount(order):
    if order.total == 100:  # Matches fixture exactly!
        return 10
    return 0

# APPROVE: General rule based on domain policy
def calculate_discount(order: Order, policy: DiscountPolicy) -> Money:
    return policy.evaluate(order)
```

### Silent Error Swallowing
```python
# REJECT: Blanking out exceptions, hiding failure state
try:
    process_payment(payment_id)
except Exception:
    pass  # Transaction left in undefined state!

# APPROVE: Explicit handling, logged, domain exception raised
try:
    process_payment(payment_id)
except GatewayTimeoutError as err:
    logger.error("Payment timeout for %s: %s", payment_id, err)
    raise PaymentProcessingFailed(f"Gateway unavailable: {err}") from err
```

### Material Spec Drift & Scope Creep
```python
# REJECT (Material Drift): Spec demanded backward-compat migration fallback, diff dropped it
def load_session(session_id: str):
    return new_store.load(session_id)  # Breaks legacy sessions!

# REJECT (Scope Creep): Ticket asked for bugfix in token refresh; diff rewrote auth caching layer
# (Adds unreviewed risk and speculative abstractions)

# APPROVE (Pragmatic Tolerance): Internal helper differs from draft sketch, but contracts hold
def _normalize_token_expiry(token: Token) -> Timestamp: ...
```

### Ratchet Baseline Widening vs Strict Non-Increasing Count
```markdown
# REJECT: Widening baseline or increasing suppression count
- baseline_errors: 12
+ baseline_errors: 15  # Added 3 new unaddressed suppressions!

# APPROVE: Strict non-increasing count with updated identities
- baseline_errors: 12 (id1, id2, id3, ...)
+ baseline_errors: 10 (id1, id3, ...)  # 2 suppressions cured
```

---

## 3. Structural Topology & Seams (`keel`[^keel], `programming-expert`[^programming-expert])

### The Dependency Rule Breach
Core business domain importing delivery mechanisms.

```python
# REJECT: Domain entity depends on SQLAlchemy ORM model and FastAPI
from fastapi import HTTPException
from models.orm import UserORM

class User:
    def to_orm(self) -> UserORM: ...
    def validate_or_400(self):
        raise HTTPException(status_code=400, detail="Invalid")

# APPROVE: Pure domain entities; boundary adapters handle translation
class User:
    def __init__(self, user_id: UserId, name: str):
        if not name.strip():
            raise DomainValidationError("User name cannot be blank")
        self.id = user_id
        self.name = name
```

### Primitive Obsession in Invariants
```python
# REJECT: Untyped values without validation guarantees
def transfer(amount: float, currency: str, account_id: str):
    ... # What if amount < 0 or currency is invalid?

# APPROVE: Value objects guaranteeing invariants at instantiation
def transfer(amount: PositiveMoney, destination: AccountId):
    ... # Cannot be instantiated with invalid values
```

### Deep Interfaces vs. Shallow Classitis[^addy-simplify]
```python
# REJECT (Classitis): Shallow classes that add indirection without hiding complexity
class TextTokenStreamReader:
    def __init__(self, reader: FileReader): self.reader = reader
class TextTokenStreamParser:
    def __init__(self, stream: TextTokenStreamReader): self.stream = stream
class ConfigFileLoader:
    def load(self, path: str):
        return TextTokenStreamParser(TextTokenStreamReader(FileReader(path))).parse()

# APPROVE (Deep Interface): Simple facade hiding file IO, parsing, and caching
class Config:
    @classmethod
    def load(cls, path: str | Path) -> Config:
        """Parse configuration, validate invariants, and return typed settings."""
        ...
```

### Size Triage Trigger Heuristics
Line count alone is never a defect.
Large units trigger architectural inspection:
- **Function > 60 lines**: Check for multiple responsibilities, deeply nested branches, or mixed abstraction levels.
- **File > 400 lines**: Check for god objects, state leakage across unrelated features, or missing subsystem boundaries.
If responsibilities are cohesive and state is encapsulated, approve the code regardless of length.

---

## 4. Security Hardening Anti-Patterns[^addy-security]

### Concurrency & Rate Limiting Failure Direction
```typescript
// REJECT: Fail-open on security boundary
async function checkRateLimit(userId: string): Promise<boolean> {
  try {
    return await redis.checkLimit(userId);
  } catch (err) {
    return true; // Flaw: Redis outage allows unlimited traffic!
  }
}

// APPROVE: Fail-closed on security boundary
async function checkRateLimit(userId: string): Promise<boolean> {
  try {
    return await redisWithTimeout(userId, 200);
  } catch (err) {
    logger.error("Rate limit check failed", err);
    return false; // Safe: fail-closed under security boundary
  }
}
```

### Unsanitized Input & Injection Vulnerabilities
```python
# REJECT: Raw string formatting into SQL query or shell command
def get_user_records(user_input: str):
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    return db.execute(query)

# APPROVE: Parameterized queries isolating untrusted data from execution
def get_user_records(user_input: str):
    query = "SELECT * FROM users WHERE username = :name"
    return db.execute(query, {"name": user_input})
```

---

## 5. ADR-0009 Design-Implementation Sync Checklist

When reviewing code against `design.md`:
1. **File Locations & Names**: Did implementation place files in different directories than planned?
2. **Interface Signatures**: Did method names, arguments, or return types change from the design?
3. **Data Models & Schemas**: Were fields added, renamed, or omitted compared to specification?
4. **CLI Flags & Arguments**: Did command-line arguments diverge?

*Rule*: If any divergence occurred, the review must flag `SOT Drift Detected` and list required amendments to `design.md`.

---

## Footnote References

[^mattpocock]: https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md
[^addy-quality]: https://github.com/addyosmani/agent-skills/tree/main/skills/code-review-and-quality
[^addy-simplify]: https://github.com/addyosmani/agent-skills/tree/main/skills/code-simplification
[^addy-security]: https://github.com/addyosmani/agent-skills/tree/main/skills/security-and-hardening
[^superpowers]: https://github.com/obra/superpowers/tree/main/skills/subagent-driven-development/scripts/review-package
[^keel]: skills/keel/SKILL.md
[^coding-protocol]: skills/coding-protocol/SKILL.md
[^programming-expert]: skills/programming-expert/SKILL.md
