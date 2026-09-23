"""Tests for scripts/changelog-gate.py — the deterministic changelog-ledger floor.

Each floor check is covered by a minimal failing input, not only a passing case.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "changelog-gate.py"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def _repo(tmp_path: Path, changelog_text: str | None, subjects: list[str]) -> Path:
    """A repo whose HEAD carries `subjects` on top of `main`."""
    repo = tmp_path / "repo"
    repo.mkdir()
    if changelog_text is not None:
        _ = (repo / "CHANGELOG.md").write_text(changelog_text, encoding="utf-8")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "chore: init")
    _git(repo, "switch", "-q", "-c", "feature")
    for subject in subjects:
        _git(repo, "commit", "-q", "--allow-empty", "-m", subject)
    return repo


def _ledger(*entries: str, section: str = "Features") -> str:
    body = "\n".join(entries)
    return f"# Changelog\n\n## [Unreleased]\n\n### {section}\n\n{body}\n"


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True
    )


def _ledger_check(repo: Path) -> subprocess.CompletedProcess[str]:
    return _run(repo, "ledger")


# --- the passing case ---------------------------------------------------------------------


def test_ledger_passes_on_a_well_formed_ledger(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ledger: pass"


# --- well-formedness ----------------------------------------------------------------------


def test_ledger_blocks_a_dash_bullet(tmp_path: Path) -> None:
    """The renderer writes `*`; `-` is not something `update` could have produced."""
    repo = _repo(tmp_path, _ledger("- **thing:** add a thing"), ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "well-formedness" in result.stderr


def test_ledger_blocks_an_empty_bullet(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("*"), ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "empty bullet" in result.stderr


def test_ledger_blocks_a_scoped_bullet_with_no_subject(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:**"), ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "bullet grammar" in result.stderr


# --- section integrity --------------------------------------------------------------------


def test_ledger_blocks_an_entry_outside_any_section(tmp_path: Path) -> None:
    orphan = "# Changelog\n\n## [Unreleased]\n\n* **thing:** add a thing\n"
    repo = _repo(tmp_path, orphan, ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "outside any section" in result.stderr


def test_ledger_blocks_an_unknown_section(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path, _ledger("* **thing:** add a thing", section="Nonsense"), ["feat(thing): add a thing"]
    )

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "unknown section" in result.stderr


def test_ledger_blocks_a_missing_unreleased_block(tmp_path: Path) -> None:
    released_only = "# Changelog\n\n## [1.0.0](x) (2026-01-01)\n\n* done\n"
    repo = _repo(tmp_path, released_only, ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "## [Unreleased]" in result.stderr


def test_ledger_needs_a_human_when_the_changelog_is_missing(tmp_path: Path) -> None:
    repo = _repo(tmp_path, None, ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 2, result.stderr
    assert "missing" in result.stderr


# --- duplicate identities -----------------------------------------------------------------


def test_ledger_blocks_duplicate_identities(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing", "* **thing:** add a thing"),
        ["feat(thing): add a thing", "fix(thing): fix a thing"],
    )

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "duplicate-identity" in result.stderr


def test_ledger_blocks_a_duplicate_that_differs_only_by_its_pr_number(tmp_path: Path) -> None:
    """GitHub appends `(#N)` on squash; identity must ignore it, as the generator does."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing", "* **thing:** add a thing (#99)"),
        ["feat(thing): add a thing", "fix(thing): fix a thing"],
    )

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "duplicate-identity" in result.stderr


# --- placeholders -------------------------------------------------------------------------


def test_ledger_blocks_a_tbd_placeholder(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** TBD"), ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "placeholders" in result.stderr


def test_ledger_blocks_an_angle_bracket_placeholder(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** <describe the thing>"), ["feat(thing): add a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "placeholders" in result.stderr


# --- accounting ---------------------------------------------------------------------------


def test_ledger_blocks_a_scope_with_more_entries_than_commits(tmp_path: Path) -> None:
    """Two `thing` entries against one `thing` commit; unrelated commits keep the global bound green."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing", "* **thing:** fix a thing"),
        ["feat(thing): add a thing", "feat(other): a", "feat(other): b"],
    )

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "scope 'thing': 2 entries > 1 commits" in result.stderr
    assert "global pre-filter" not in result.stderr, "the global bound must not be the check here"


def test_ledger_blocks_a_global_pre_filter_violation(tmp_path: Path) -> None:
    """Unscoped entries have no per-scope home, so the coarse global bound is what fires."""
    repo = _repo(
        tmp_path,
        _ledger("* add a thing", "* add another thing"),
        ["feat(thing): add a thing"],
    )

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "global pre-filter" in result.stderr


MEASURED_LEDGER = """\
# Changelog

## [Unreleased]

### Features

* **herdr:** add herdr-overview for a compact session view
* **herdr:** add herdr-prompt for byte-exact payload delivery
* **herdr:** add herdr-label to name a pane and its agent together
* **herdr:** let herdr-prompt target a pane by its label
* **herdr:** conform herdr_pane.py to PEP 723
* **herdr:** order the helper sections by workflow
* **herdr:** correct the handoff guidance to lead with the label
* **herdr:** document herdr-overview and the name/label split
* **herdr:** document the herdr-prompt helper
* **herdr:** apply progressive disclosure and document transcript reads
* **herdr:** add a wait barrier and transcript helpers
* **herdr:** repair the skill's link and observation gaps
* **gh-router:** split libs and harden PR gates
* **gh-router:** split libs and harden PR gates
* **gh-router:** give repo identity one authority and split shared code by concern (#35)
* **gh-router:** give repo identity one authority and split shared code by concern
"""


def test_ledger_blocks_the_measured_main_inflation(tmp_path: Path) -> None:
    """The ledger ADR-0016 measures: 16 entries, 16 projected commits, two scopes inflated.

    The global bound passes (16 ≤ 16) while `herdr` carries 12 entries against 3 commits and
    two identities are duplicated — the failure the per-scope bound exists to catch.
    """
    commits = (
        ["feat(herdr): a", "fix(herdr): b", "feat(herdr): c"]
        + ["feat(gh-router): d", "feat(gh-router): e"]
        + [f"feat(bulk): {n}" for n in range(11)]
    )
    repo = _repo(tmp_path, MEASURED_LEDGER, commits)

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "scope 'herdr': 12 entries > 3 commits" in result.stderr
    assert "duplicate-identity" in result.stderr
    assert "global pre-filter" not in result.stderr, "the global bound passes on this ledger"


# --- read-only guarantee ------------------------------------------------------------------


def test_a_failing_ledger_check_does_not_mutate_the_tree(tmp_path: Path) -> None:
    changelog = _ledger("* **thing:** add a thing", "* **thing:** add a thing")
    repo = _repo(tmp_path, changelog, ["feat(thing): add a thing", "fix(thing): fix a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == changelog
    assert _git(repo, "status", "--porcelain").stdout == ""


# --- the merge boundary (squash) ----------------------------------------------------------


def test_squash_passes_for_one_conventional_commit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): add a thing"])

    result = _run(repo, "squash", "--base", "main")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "squash: pass"


def test_squash_blocks_a_non_conventional_subject(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["added a thing"])

    result = _run(repo, "squash", "--base", "main")

    assert result.returncode == 1, result.stderr
    assert "conventional-subject" in result.stderr


def test_squash_blocks_a_hidden_subject_that_projects_no_entry(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["chore: tidy up"])

    result = _run(repo, "squash", "--base", "main")

    assert result.returncode == 1, result.stderr
    assert "single-entry" in result.stderr


def test_squash_needs_a_human_when_head_is_not_one_commit(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing"),
        ["feat(thing): add a thing", "feat(thing): add another"],
    )

    result = _run(repo, "squash", "--base", "main")

    assert result.returncode == 2, result.stderr
    assert "expects exactly one" in result.stderr


def test_squash_needs_a_human_when_the_base_ref_is_unknown(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): add a thing"])

    result = _run(repo, "squash", "--base", "no-such-branch")

    assert result.returncode == 2, result.stderr
    assert "does not resolve" in result.stderr
