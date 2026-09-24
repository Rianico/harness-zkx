"""The typecheck budget: errors always fail, warnings may only shrink.

`basedpyright` fails on warnings, so before this the debt could only surface as a blocked release.
The budget makes it visible per-PR and forbids growth, which is the whole contract — so these tests
exercise the refusals, not the happy path alone.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "typecheck-budget.py"


class _Budget(Protocol):
    """The loaded script's surface, so the module handle stops leaking `Any`."""

    REPO_ROOT: Path

    def main(self, argv: list[str] | None = None) -> int: ...


def _load() -> _Budget:
    spec = importlib.util.spec_from_file_location("typecheck_budget", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["typecheck_budget"] = module
    spec.loader.exec_module(module)
    return cast(_Budget, cast(object, module))


budget = _load()


def diagnostic(
    severity: str, rule: str | None, file: str = "a.py", line: int = 1
) -> dict[str, object]:
    return {
        "severity": severity,
        "rule": rule,
        "file": file,
        "message": "boom",
        "range": {"start": {"line": line, "character": 0}},
    }


@pytest.fixture
def report(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    def install(*diagnostics: dict[str, object]) -> None:
        monkeypatch.setattr(
            budget, "run_typecheck", lambda: {"generalDiagnostics": list(diagnostics)}
        )

    return install


@pytest.fixture
def baseline(tmp_path: Path) -> Path:
    path = tmp_path / "budget.txt"
    _ = path.write_text("# note\n1\ta.py\treportAny\n", encoding="utf-8")
    return path


def test_budgeted_warning_passes(report: Callable[..., None], baseline: Path):
    report(diagnostic("warning", "reportAny"))
    assert budget.main(["--baseline", str(baseline)]) == 0


def test_growth_fails_and_leaves_the_budget_alone(report: Callable[..., None], baseline: Path):
    report(diagnostic("warning", "reportAny"), diagnostic("warning", "reportAny", line=2))
    assert budget.main(["--baseline", str(baseline)]) == 1
    assert baseline.read_text(encoding="utf-8").count("reportAny") == 1


def test_a_new_file_is_growth_not_slack(report: Callable[..., None], baseline: Path):
    """A key the budget never saw is new debt, not headroom borrowed from another file."""
    report(diagnostic("warning", "reportAny", file="b.py"))
    assert budget.main(["--baseline", str(baseline)]) == 1


def test_errors_are_never_budgeted(report: Callable[..., None], baseline: Path):
    report(diagnostic("error", "reportUndefinedVariable"))
    assert budget.main(["--baseline", str(baseline), "--update-baseline"]) == 1


def test_update_baseline_retires_entries_that_are_gone(report: Callable[..., None], baseline: Path):
    report(diagnostic("warning", "reportAny"))
    other = baseline.parent / "shrunk.txt"
    _ = other.write_text("# note\n1\ta.py\treportAny\n1\tgone.py\treportAny\n", encoding="utf-8")
    assert budget.main(["--baseline", str(other), "--update-baseline"]) == 0
    assert "gone.py" not in other.read_text(encoding="utf-8")


def test_update_baseline_refuses_to_absorb_new_warnings(
    report: Callable[..., None], baseline: Path
):
    before = baseline.read_text(encoding="utf-8")
    report(diagnostic("warning", "reportAny", file="b.py"))
    assert budget.main(["--baseline", str(baseline), "--update-baseline"]) == 1
    assert baseline.read_text(encoding="utf-8") == before


def test_absolute_paths_are_keyed_relative_to_the_repo(report: Callable[..., None], tmp_path: Path):
    """The budget is committed, so it must not carry a machine-specific prefix."""
    report(diagnostic("warning", "reportAny", file=str(budget.REPO_ROOT / "a.py")))
    assert budget.main(["--baseline", str(tmp_path / "missing.txt")]) == 1


def test_seed_records_the_current_state(report: Callable[..., None], tmp_path: Path):
    """Bootstrapping is explicit: a missing budget must not read as permission to grow."""
    report(diagnostic("warning", "reportAny"))
    path = tmp_path / "seeded.txt"
    assert budget.main(["--baseline", str(path), "--seed"]) == 0
    assert "1\ta.py\treportAny" in path.read_text(encoding="utf-8")


def test_a_malformed_budget_fails_loudly(tmp_path: Path):
    path = tmp_path / "bad.txt"
    _ = path.write_text("not-a-row\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="count<TAB>path<TAB>rule"):
        _ = budget.main(["--baseline", str(path)])


def test_a_report_that_is_not_json_fails_loudly(monkeypatch: pytest.MonkeyPatch):
    def broken() -> dict[str, object]:
        raise SystemExit("basedpyright report is not JSON")

    monkeypatch.setattr(budget, "run_typecheck", broken)
    with pytest.raises(SystemExit, match="not JSON"):
        _ = budget.main([])
