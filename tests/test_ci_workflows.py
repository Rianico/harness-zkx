"""Pins the harness CI triggers that keep changelog drift visible on `main`.

`changelog-check.yml` triggered on `pull_request` only, so `main` itself was never checked:
its Unreleased section could sit stale until an unrelated PR happened to trip the hook, which
is how one PR's entries stayed un-regenerated until the next PR's push. The check now also
runs on push to `main`, so main reports its own staleness where it happens.

The pinned invariants below extend that: a draft->ready flip must rerun CI (an unspecified
`types:` list defaults to opened/synchronize/reopened and never fires `ready_for_review`),
draft PRs must not spend runner minutes, and `tests.yml` must gate its slow suites behind a
verbatim copy of the ledger floor so a waived PR cannot pass one gate and fail the other.
Because that copy's durable branch (empty PR_NUMBER) only resolves on `main`, `tests.yml`
must keep its `push` trigger main-scoped.
"""

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
CHANGELOG_CHECK = WORKFLOWS / "changelog-check.yml"
TESTS_YML = WORKFLOWS / "tests.yml"
TWIN_CHANGELOG_CHECK = ROOT / "skills/scaffold/templates/git/.github/workflows/changelog-check.yml"

DRAFT_GUARD = "github.event_name == 'push' || github.event.pull_request.draft == false"


def _text() -> str:
    return CHANGELOG_CHECK.read_text(encoding="utf-8")


def _doc(path: Path) -> dict[Any, Any]:
    # A workflow root is always a mapping; keys can be str or the bool True (`on:`).
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def _triggers(doc: dict[Any, Any]) -> dict[Any, Any]:
    # YAML 1.1 parses the bare `on:` mapping key as the boolean True.
    triggers = doc.get("on") or doc.get(True)
    assert triggers is not None
    return triggers


def _pull_request_types(doc: dict[Any, Any]) -> list[str]:
    return _triggers(doc)["pull_request"]["types"]


def test_tests_workflow_push_trigger_is_main_scoped() -> None:
    """The verbatim ledger-floor copy treats an empty `PR_NUMBER` as the durable run,
    which demands every entry resolve to a commit reachable from HEAD: only true on
    `main`. An unscoped push trigger reads green PRs red, so push must stay main-scoped
    with its path filter, while PRs stay covered by `pull_request`, including the
    `ready_for_review` flip that `pr.py --watch` polls."""
    push = _triggers(_doc(TESTS_YML))["push"]
    assert push["branches"] == ["main"], "tests.yml push trigger must be scoped to main"
    assert push["paths"], "tests.yml push trigger lost its path filter"
    assert "ready_for_review" in _pull_request_types(_doc(TESTS_YML))


def test_changelog_check_runs_on_main_push() -> None:
    """A `pull_request`-only trigger leaves `main` unchecked between merges."""
    assert "  push:\n    branches: [main]\n" in _text(), _text()


def test_changelog_check_concurrency_group_covers_push() -> None:
    """A push run has no pull-request number, so the group must fall back to a ref."""
    assert "github.event.pull_request.number || github.ref" in _text()


def test_changelog_check_comment_step_is_pr_only() -> None:
    """A push run has no PR to comment on; the script would fail on a null issue number."""
    assert "if: failure() && github.event_name == 'pull_request'" in _text()


def test_both_workflows_trigger_on_ready_for_review() -> None:
    """Without `types:`, Actions defaults to opened/synchronize/reopened: a draft that
    becomes ready triggers no run, so neither CI ever sees the mergeable state."""
    for path in (TESTS_YML, CHANGELOG_CHECK, TWIN_CHANGELOG_CHECK):
        types = _pull_request_types(_doc(path))
        assert "ready_for_review" in types, f"{path} does not rerun CI on a ready flip"


def test_every_tests_workflow_job_carries_the_draft_guard() -> None:
    """Drafts must not spend runner minutes on the full pipeline."""
    jobs = _doc(TESTS_YML)["jobs"]
    assert jobs, "tests.yml declares no jobs"
    for name, job in jobs.items():
        assert job.get("if") == DRAFT_GUARD, f"job {name} lost the draft guard"


def test_changelog_check_and_twin_carry_the_draft_guard() -> None:
    for path in (CHANGELOG_CHECK, TWIN_CHANGELOG_CHECK):
        job = _doc(path)["jobs"]["check"]
        assert job.get("if") == DRAFT_GUARD, f"{path}: check job lost the draft guard"


def test_tests_workflow_needs_chain() -> None:
    """A fast changelog failure must abort before the slow suites, in strict order."""
    jobs = _doc(TESTS_YML)["jobs"]
    assert "needs" not in jobs["changelog-gate"], "changelog-gate must run first, ungated"
    assert jobs["typecheck"]["needs"] == ["changelog-gate"]
    assert jobs["tests"]["needs"] == ["changelog-gate", "typecheck"]


_LEDGER_FLOOR_END = 'python scripts/changelog-gate.py ledger "${args[@]}"'


def _ledger_floor_block(text: str) -> str:
    """The body-extraction + flag-construction + gate-call block, verbatim."""
    start = text.index("- name: Ledger floor")
    end = text.index(_LEDGER_FLOOR_END, start) + len(_LEDGER_FLOOR_END)
    return text[start:end]


def _ledger_floor_step(jobs: dict[Any, Any], job: str) -> dict[Any, Any]:
    matches = [s for s in jobs[job]["steps"] if s.get("name") == "Ledger floor"]
    assert len(matches) == 1, f"no single 'Ledger floor' step under jobs.{job}.steps"
    return matches[0]


def test_changelog_gate_copies_the_verbatim_ledger_floor_block() -> None:
    """`tests.yml changelog-gate` replicates `changelog-check.yml check`.

    `--waiver` and `--landing` are passed only when the PR body declares them, so any
    drift in the extraction shell lets one gate waive a PR the other gate fails. The
    copies must stay byte-identical over the whole block, and the copy must live under
    `jobs.changelog-gate.steps`: a block merely present somewhere in the file pins
    nothing once the main-scoped push trigger routes the durable branch.
    """
    block = _ledger_floor_block(_text())
    tests_text = TESTS_YML.read_text(encoding="utf-8")
    assert block in tests_text, "tests.yml drifted from the changelog-check.yml ledger floor"
    assert block in TWIN_CHANGELOG_CHECK.read_text(encoding="utf-8")
    for flag in ('args=(--pr "$PR_NUMBER")', "--waiver", "--landing"):
        assert flag in block and flag in tests_text, f"flag {flag!r} missing from a copy"
    jobs = _doc(TESTS_YML)["jobs"]
    floor = _ledger_floor_step(jobs, "changelog-gate")
    source = _ledger_floor_step(_doc(CHANGELOG_CHECK)["jobs"], "check")
    assert floor["run"] == source["run"]
    assert floor["env"] == source["env"]
    names = [s.get("name") for job in jobs.values() for s in job["steps"] if isinstance(s, dict)]
    assert names.count("Ledger floor") == 1, (
        "ledger floor block must live only under changelog-gate"
    )
