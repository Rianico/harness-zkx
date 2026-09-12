# Crux Review Rubric & Heuristics

This reference details the patterns and anti-patterns evaluated during Crux Code Review.

---

## 1. Epistemic Truth (VDD / Refutability)

### The Paper Tiger Anti-Pattern
A test that passes without actually exercising the system under test's state transition.

```python
# REJECT (Paper Tiger): Mocking the very method under test
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
    mock_notifier.assert_called_once()  # Did alert serialize correctly? Did payload contain expected fields?

# APPROVE: Asserting payload schema and negative rejection
def test_send_notification(fake_transport):
    dispatch_alert(Alert(severity="CRITICAL", message="out of memory"))
    sent = fake_transport.pop_message()
    assert sent.severity == "CRITICAL"
    assert "out of memory" in sent.body
```

---

## 2. Ontological Truth (EDD / State Safety & Anti-Laziness)

### Hardcoded Test Passes
```python
# REJECT: Hardcoding input to pass the unit test
def calculate_discount(order):
    if order.total == 100:  # Matches test fixture exactly!
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
# REJECT (Material Drift): Spec demanded backward-compat migration fallback, but diff dropped it
def load_session(session_id: str):
    return new_store.load(session_id)  # Breaks legacy sessions without migration!

# REJECT (Scope Creep): Ticket asked for bugfix in token refresh; diff rewrote auth caching layer
# (Adds unreviewed risk, speculative abstractions, and unrequested diff bloat)

# APPROVE (Pragmatic Tolerance): Internal helper name differs from draft sketch, but contracts and invariants hold
def _normalize_token_expiry(token: Token) -> Timestamp: ...
```

---

## 3. Structural Topology (Clean Architecture & Keel Boundaries)

### The Dependency Rule Breach
Core business domain importing delivery mechanisms (frameworks, databases, external network).

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
# REJECT: Untyped string representing domain concept with invariants
def transfer(amount: float, currency: str, account_id: str):
    ... # What if amount < 0? What if currency is "ZZZ"? What if account_id is empty?

# APPROVE: Value objects guaranteeing invariants at instantiation
def transfer(amount: PositiveMoney, destination: AccountId):
    ... # Cannot be called with negative money or malformed account ID
```

---

## 4. ADR-0009 Design-Implementation Sync Checklist

When reviewing code against `design.md`:
1. **File Locations & Names**: Did implementation place files in different directories than planned in `design.md`?
2. **Interface Signatures**: Did method names, arguments, or return types change from the design?
3. **Data Models & Schemas**: Were fields added, renamed, or omitted compared to the specification?
4. **CLI Flags & Arguments**: Did command-line arguments diverge?

*Rule*: If any divergence occurred, the review MUST flag `SOT Drift Detected` and list required amendments to `design.md`.
