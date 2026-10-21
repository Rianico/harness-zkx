"""Tests for scripts/changelog-gate.py — the deterministic changelog-ledger floor.

Each floor check is covered by a minimal failing input, not only a passing case.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

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
    _ = _git(repo, "init", "-q", "-b", "main")
    _ = _git(repo, "config", "user.email", "t@example.invalid")
    _ = _git(repo, "config", "user.name", "t")
    _ = _git(repo, "add", "-A")
    _ = _git(repo, "commit", "-q", "--allow-empty", "-m", "chore: init")
    _ = _git(repo, "switch", "-q", "-c", "feature")
    for subject in subjects:
        _ = _git(repo, "commit", "-q", "--allow-empty", "-m", subject)
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
    repo = _repo(
        tmp_path, _ledger("* **thing:** add a thing (#1)"), ["feat(thing): add a thing (#1)"]
    )

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
        tmp_path,
        _ledger("* **thing:** add a thing", section="Nonsense"),
        ["feat(thing): add a thing"],
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
    repo = _repo(
        tmp_path, _ledger("* **thing:** <describe the thing>"), ["feat(thing): add a thing"]
    )

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "placeholders" in result.stderr


def test_ledger_allows_angle_brackets_inside_a_code_span(tmp_path: Path) -> None:
    """Inline code is verbatim content; `<file>` is a filename, not a placeholder."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** retarget `<file>` paths (#1)"),
        ["feat(thing): a (#1)"],
    )

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ledger: pass"


def test_ledger_allows_multiple_code_spans_in_one_entry(tmp_path: Path) -> None:
    """Stripping removes every span, so several in one bullet stay clean."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** map `<file>` onto `<branch>` (#1)"),
        ["feat(thing): a (#1)"],
    )

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr


def test_ledger_blocks_a_bare_angle_placeholder_next_to_a_code_span(tmp_path: Path) -> None:
    """Stripping is scoped to spans; a bare `<target>` outside backticks still blocks."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** use `<file>` for <target> (#1)"),
        ["feat(thing): a (#1)"],
    )

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "placeholders" in result.stderr


# --- accounting ---------------------------------------------------------------------------


# --- provenance and attribution ------------------------------------------------------------


def test_ledger_blocks_an_entry_with_no_pr_attribution(tmp_path: Path) -> None:
    """Curation appends `(#N)`; an entry that names no PR can never be validated."""
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): add a thing (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "entry carries no (#N)" in result.stderr


def test_unattributed_entry_prints_remediation_hint(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): add a thing (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "[provenance] entry carries no (#N): '**thing:** add a thing'" in result.stderr
    hint = (
        "  → Stamp (#N) into the entry, or run pr-land (pr.py auto-attributes after PR creation)."
    )
    assert hint in result.stderr
    lines = result.stderr.splitlines()
    finding_idx = lines.index("[provenance] entry carries no (#N): '**thing:** add a thing'")
    assert lines[finding_idx + 1] == hint


def test_waived_unattributed_entry_omits_remediation_hint(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): add a thing (#1)"])

    result = _run(repo, "ledger", "--waiver", "legacy debt accepted")

    assert result.returncode == 0, result.stderr
    assert "[waived] [provenance] entry carries no (#N): '**thing:** add a thing'" in result.stderr
    assert "  →" not in result.stderr


def test_other_findings_omit_remediation_hint(tmp_path: Path) -> None:
    (tmp_path / "commit").mkdir()
    repo_commit = _repo(
        tmp_path / "commit", _ledger("* **thing:** add a thing (#99)"), ["feat(thing): a (#1)"]
    )
    res_commit = _ledger_check(repo_commit)
    assert res_commit.returncode == 1, res_commit.stderr
    assert "(#99) resolves to no commit" in res_commit.stderr
    assert "  →" not in res_commit.stderr

    (tmp_path / "dup").mkdir()
    repo_dup = _repo(
        tmp_path / "dup",
        _ledger("* **thing:** add a thing (#1)", "* **thing:** add a thing (#1)"),
        ["feat(thing): a (#1)"],
    )
    res_dup = _ledger_check(repo_dup)
    assert res_dup.returncode == 1, res_dup.stderr
    assert "duplicate-identity" in res_dup.stderr
    assert "  →" not in res_dup.stderr


def test_ledger_blocks_an_attribution_that_resolves_to_no_commit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing (#99)"), ["feat(thing): a (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "(#99) resolves to no commit" in result.stderr


def test_ledger_accepts_a_squash_landing_with_multiple_entries(tmp_path: Path) -> None:
    """A squash landing with multiple curated entries is permitted."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing (#1)", "* **thing:** fix a thing (#1)"),
        ["feat(thing): add and fix (#1)"],
    )

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr
    assert "ledger: pass" in result.stdout


def _merge_landing(repo: Path, pr: str, commits: list[str]) -> None:
    """Land `commits` onto `main` with a synthetic merge commit.

    `git commit-tree` builds it from plumbing, so no `git merge` runs and no hook is involved.
    """
    _ = _git(repo, "checkout", "-q", "-b", f"ticket-{pr}", "main")
    for subject in commits:
        _ = _git(repo, "commit", "-q", "--allow-empty", "-m", subject)
    tip = _git(repo, "rev-parse", "HEAD").stdout.strip()
    base = _git(repo, "rev-parse", "main").stdout.strip()
    _ = _git(repo, "checkout", "-q", "main")
    tree = _git(repo, "rev-parse", f"{tip}^{{tree}}").stdout.strip()
    merge = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        base,
        "-p",
        tip,
        "-m",
        f"Merge pull request #{pr} from contributor/ticket-{pr}",
    ).stdout.strip()
    _ = _git(repo, "update-ref", "refs/heads/main", merge)


def test_ledger_accepts_a_merge_landing_with_multiple_entries(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** a (#1)", "* **thing:** b (#1)", "* **thing:** c (#1)"),
        [],
    )
    _merge_landing(repo, "1", ["feat(thing): a", "feat(thing): b"])

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr


def test_ledger_accepts_the_current_pr_at_its_declared_landing(tmp_path: Path) -> None:
    """At the PR boundary the PR has not landed; its entries are covered by the declaration."""
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing (#96)"), ["feat(thing): a"])

    result = _run(repo, "ledger", "--pr", "96", "--landing", "squash")

    assert result.returncode == 0, result.stderr


def test_ledger_accepts_multiple_entries_for_current_pr(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** a (#96)", "* **thing:** b (#96)", "* **thing:** c (#96)"),
        ["feat(thing): squashed (#96)"],
    )

    result = _run(repo, "ledger", "--pr", "96")

    assert result.returncode == 0, result.stderr
    assert "ledger: pass" in result.stdout


def test_ledger_blocks_when_current_pr_has_no_entries(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** a (#1)"),
        ["feat(thing): a"],
    )

    result = _run(repo, "ledger", "--pr", "96")

    assert result.returncode == 1, result.stderr
    assert "#96 carries no entries" in result.stderr


# --- the hidden-type exemption at the PR boundary ------------------------------------------


def test_ledger_exempts_a_docs_pr_from_the_entry_requirement(tmp_path: Path) -> None:
    """A docs squash owes no ledger entry: the audience change is release-relevant."""
    repo = _repo(tmp_path, _ledger("* **thing:** a (#1)"), ["docs: update readme (#106)"])

    result = _run(repo, "ledger", "--pr", "106", "--squash-title", "docs: update readme")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ledger: pass"


def test_ledger_exempts_a_scoped_chore_pr(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger(), ["chore(deps): update foo (#106)"])

    result = _run(repo, "ledger", "--pr", "106", "--squash-title", "chore(deps): update foo")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ledger: pass"


def test_ledger_requires_entries_for_releasable_titles(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** a (#1)"), ["feat: add bar (#106)"])

    result = _run(repo, "ledger", "--pr", "106", "--squash-title", "feat: add bar")

    assert result.returncode == 1, result.stderr
    assert "#106 carries no entries" in result.stderr


def test_ledger_a_breaking_docs_pr_is_not_exempt(tmp_path: Path) -> None:
    """`docs!:` announces a breaking change to the audience: the ledger owes an entry."""
    repo = _repo(tmp_path, _ledger("* **thing:** a (#1)"), ["docs!: restructure the ledger (#106)"])

    result = _run(repo, "ledger", "--pr", "106", "--squash-title", "docs!: restructure the ledger")

    assert result.returncode == 1, result.stderr
    assert "#106 carries no entries" in result.stderr


def test_ledger_without_a_title_still_requires_entries(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** a (#1)"), ["docs: update readme (#106)"])

    result = _run(repo, "ledger", "--pr", "106")

    assert result.returncode == 1, result.stderr
    assert "#106 carries no entries" in result.stderr


def test_ledger_accepts_pr_without_landing_declaration(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** a (#96)"), ["feat(thing): a"])

    result = _run(repo, "ledger", "--pr", "96")

    assert result.returncode == 0, result.stderr
    assert "ledger: pass" in result.stdout


# --- the migration baseline ---------------------------------------------------------------


def _baseline(repo: Path, *identities: str) -> Path:
    path = repo / ".config" / "changelog-unattributed-baseline.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text("\n".join(identities) + "\n", encoding="utf-8")
    return path


def test_ledger_accepts_a_baselined_unattributed_entry(tmp_path: Path) -> None:
    """Recorded debt is tolerated."""
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): a (#1)"])
    _ = _baseline(repo, "**thing:** add a thing")

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr


def test_ledger_needs_a_human_when_the_baseline_is_missing(tmp_path: Path) -> None:
    """Deleting the baseline is not a reset: the debt stops being tolerated."""
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): a (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "entry carries no (#N)" in result.stderr


def test_ledger_blocks_growth_beyond_the_baseline(tmp_path: Path) -> None:
    """A new unattributed entry is growth: the baseline may not absorb it."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing", "* **thing:** add another thing"),
        ["feat(thing): a (#1)"],
    )
    _ = _baseline(repo, "**thing:** add a thing")

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "entry carries no (#N): '**thing:** add another thing'" in result.stderr


def test_ledger_accepts_pruned_baseline_entry(tmp_path: Path) -> None:
    """When an entry is removed or attributed, stale baseline entries do not block."""
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing (#1)"), ["feat(thing): a (#1)"])
    _ = _baseline(repo, "**thing:** a thing that is gone")

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr


def test_update_baseline_seeds_then_only_shrinks(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing", "* **thing:** add another thing"),
        ["feat(thing): a (#1)"],
    )

    path = repo / ".config" / "changelog-unattributed-baseline.txt"

    seeded = _run(repo, "ledger", "--update-baseline")
    assert seeded.returncode == 0, seeded.stderr
    assert _ledger_check(repo).returncode == 0

    _ = (repo / "CHANGELOG.md").write_text(_ledger("* **thing:** add a thing"), encoding="utf-8")
    shrunk = _run(repo, "ledger", "--update-baseline")
    assert shrunk.returncode == 0, shrunk.stderr
    recorded = path.read_text(encoding="utf-8")
    assert "add a thing" in recorded
    assert "another thing" not in recorded


def test_update_baseline_leaves_a_header_only_file_once_nothing_is_tolerated(
    tmp_path: Path,
) -> None:
    """The migration ends: a header-only file tolerates nothing and stages cleanly."""
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing"), ["feat(thing): a (#1)"])
    path = repo / ".config" / "changelog-unattributed-baseline.txt"
    assert _run(repo, "ledger", "--update-baseline").returncode == 0
    assert "add a thing" in path.read_text(encoding="utf-8")

    _ = (repo / "CHANGELOG.md").write_text(_ledger("* **thing:** a thing (#1)"), encoding="utf-8")
    emptied = _run(repo, "ledger", "--update-baseline")

    assert emptied.returncode == 0, emptied.stderr
    remaining = [
        line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("#")
    ]
    assert remaining == []


# --- the recorded waiver -------------------------------------------------------------------


def test_ledger_waives_a_fixable_finding_with_a_written_reason(tmp_path: Path) -> None:
    """The escape is changelog-scoped and recorded, not a blanket bypass."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing (#1)", "* **thing:** add a thing (#1)"),
        ["feat(thing): a (#1)"],
    )

    blocked = _ledger_check(repo)
    assert blocked.returncode == 1, blocked.stderr

    waived = _run(repo, "ledger", "--waiver", "accepted: the duplicate retires next release")

    assert waived.returncode == 0, waived.stderr
    assert "(waived)" in waived.stdout
    assert "waiver recorded: accepted: the duplicate retires next release" in waived.stderr


def test_ledger_waiver_does_not_rescue_a_needs_human_finding(tmp_path: Path) -> None:
    repo = _repo(tmp_path, None, ["feat(thing): a (#1)"])

    result = _run(repo, "ledger", "--waiver", "because I said so")

    assert result.returncode == 2, result.stderr
    assert "missing" in result.stderr


def test_ledger_refuses_an_empty_waiver(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** a (#1)"), ["feat(thing): a (#1)"])

    result = _run(repo, "ledger", "--waiver", "   ")

    assert result.returncode == 2, result.stderr
    assert "needs a written reason" in result.stderr


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


def test_ledger_blocks_the_measured_main_shape_as_unattributed_entries(tmp_path: Path) -> None:
    """The ledger ADR-0016 measures, under one predicate instead of a scope ratio.

    Fifteen entries predate the `(#N)` rule, so each is unattributed; the sixteenth names
    `#35`, which resolves to no commit here. The old bound reported this as `herdr 12 > 3`.
    """
    repo = _repo(tmp_path, MEASURED_LEDGER, ["feat(herdr): a", "fix(herdr): b"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert result.stderr.count("entry carries no (#N)") == 15
    assert "(#35) resolves to no commit" in result.stderr
    assert "duplicate-identity" in result.stderr


# --- read-only guarantee ------------------------------------------------------------------


def test_a_failing_ledger_check_does_not_mutate_the_tree(tmp_path: Path) -> None:
    changelog = _ledger("* **thing:** add a thing", "* **thing:** add a thing")
    repo = _repo(tmp_path, changelog, ["feat(thing): add a thing", "fix(thing): fix a thing"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == changelog
    assert _git(repo, "status", "--porcelain").stdout == ""


# --- the ticket boundary ------------------------------------------------------------------


def test_ticket_subcommand_is_backward_compatible(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** add a thing (#1)"), ["feat(thing): add a thing"])
    result = _run(repo, "ticket", "--base", "main")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ticket: pass"


def test_ticket_subcommand_passes_a_missing_ledger(tmp_path: Path) -> None:
    """The pre-merge hook runs in repos that never curated a ledger yet: shape gates what exists."""
    repo = _repo(tmp_path, None, ["feat(thing): a"])
    result = _run(repo, "ticket", "--base", "main")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ticket: pass"


def test_ticket_subcommand_runs_the_shape_phase(tmp_path: Path) -> None:
    """The pre-merge audit (wt.toml `[pre-merge] changelog`) gates the shape floor."""
    repo = _repo(tmp_path, _ledger(f"* **thing:** {_words(110)} (#1)"), ["feat(thing): a (#1)"])

    result = _run(repo, "ticket", "--base", "main")

    assert result.returncode == 1, result.stderr
    assert "entry-shape" in result.stderr
    assert "  →" in result.stderr


# --- the entry shape floor -----------------------------------------------------------------


def _words(n: int) -> str:
    return " ".join(f"w{i}" for i in range(n))


def test_ledger_blocks_a_run_on_prose_bullet(tmp_path: Path) -> None:
    """A 500-word thesis is refused with the structure hint, not waved through."""
    repo = _repo(tmp_path, _ledger(f"* **thing:** {_words(110)} (#1)"), ["feat(thing): a (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "entry-shape" in result.stderr
    assert "words (max 100)" in result.stderr
    assert "Evidence section" in result.stderr, "the refusal carries an actionable hint"


def test_ledger_accepts_a_concise_well_formed_entry(tmp_path: Path) -> None:
    entry = (
        "* **thing:** cap the retry budget at three attempts and fail fast; "
        "downstream pollers now converge inside one screen (#1)"
    )
    repo = _repo(tmp_path, _ledger(entry), ["feat(thing): a (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr


def test_ledger_blocks_an_entry_over_the_line_budget(tmp_path: Path) -> None:
    block = (
        "# Changelog\n\n## [Unreleased]\n\n### Features\n\n"
        "* **thing:** a thing (#1)\n"
        "  wrapped line two\n"
        "  wrapped line three\n"
        "  wrapped line four\n"
        "  wrapped line five\n"
    )
    repo = _repo(tmp_path, block, ["feat(thing): a (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "entry-shape" in result.stderr
    assert "spans 5 lines (max 4)" in result.stderr


def test_ledger_accepts_an_entry_inside_the_line_budget(tmp_path: Path) -> None:
    block = (
        "# Changelog\n\n## [Unreleased]\n\n### Features\n\n"
        "* **thing:** a thing (#1)\n  wrapped line two\n  wrapped line three\n  wrapped four\n"
    )
    repo = _repo(tmp_path, block, ["feat(thing): a (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("entry", "needle"),
    [
        ("* **thing:** pool tuning when loadavg 12.4 sat above cores (#1)", "load"),
        ("* **thing:** dashboard shows p95 latency for the fleet (#1)", "p95"),
        ("* **thing:** stream sustains 1200 tokens/s on warm cache (#1)", "tokens/s"),
        ("* **thing:** surface exit=128 from the runner (#1)", "exit=128"),
        ("* **thing:** edit latency probe 3 us then 12 µs then 2us (#1)", "us"),
    ],
)
def test_ledger_blocks_raw_machine_telemetry_in_an_entry(
    tmp_path: Path, entry: str, needle: str
) -> None:
    repo = _repo(tmp_path, _ledger(entry), ["feat(thing): a (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 1, result.stderr
    assert "raw machine telemetry" in result.stderr
    assert needle in result.stderr


def test_ledger_allows_a_single_round_measurement(tmp_path: Path) -> None:
    """One honest number in prose is not a telemetry dump: 120 ms stays, repetition does not."""
    entry = "* **thing:** cut cold start by 120 ms after the warm cache lands (#1)"
    repo = _repo(tmp_path, _ledger(entry), ["feat(thing): a (#1)"])

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr


def test_shape_findings_are_fixable_and_waivable(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** dashboard shows p95 latency for the fleet (#1)"),
        ["feat(thing): a (#1)"],
    )
    assert _ledger_check(repo).returncode == 1

    waived = _run(repo, "ledger", "--waiver", "the percentile names the shipped metric")

    assert waived.returncode == 0, waived.stderr
    assert "[waived] [entry-shape]" in waived.stderr


def test_ledger_blocks_a_current_pr_entry_without_a_scope_label(tmp_path: Path) -> None:
    """The shape structure is `<scope>: <imperative summary> (#N)` for this PR's entries."""
    repo = _repo(tmp_path, _ledger("* add a plain thing (#96)"), ["feat(thing): a"])

    result = _run(repo, "ledger", "--pr", "96")

    assert result.returncode == 1, result.stderr
    assert "entry-shape" in result.stderr
    assert "carries no `**scope:**` label" in result.stderr


def test_ledger_tolerates_scopeless_legacy_entries(tmp_path: Path) -> None:
    """Legacy unscoped bullets are baseline debt, not fresh violations: only PR-bound
    entries must carry the scope label."""
    repo = _repo(
        tmp_path, _ledger("* stop background re-push after auto-amend"), ["feat(a): x (#1)"]
    )
    _ = _baseline(repo, "stop background re-push after auto-amend")

    result = _ledger_check(repo)

    assert result.returncode == 0, result.stderr
    assert "carries no `**scope:**` label" not in result.stderr


# --- the squash-title alignment audit -------------------------------------------------------


def test_ledger_accepts_an_aligned_squash_title(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** a thing (#96)"), ["feat(thing): a"])

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "feat(thing): a thing (#96)")

    assert result.returncode == 0, result.stderr


def test_ledger_blocks_a_squash_title_out_of_scope_with_the_entries(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** a thing (#96)"), ["feat(thing): a"])

    result = _run(
        repo,
        "ledger",
        "--pr",
        "96",
        "--landing",
        "squash",
        "--squash-title",
        "feat(ci): a thing (#96)",
    )

    assert result.returncode == 1, result.stderr
    assert "squash-alignment" in result.stderr
    assert "matches no entry scope" in result.stderr
    assert "retarget the ledger entries" in result.stderr


def test_alignment_matches_nested_entry_scopes(tmp_path: Path) -> None:
    """`feat(gh-router): …` aligns with an entry scoped `gh-router/pr-land`."""
    repo = _repo(tmp_path, _ledger("* **gh-router/pr-land:** a thing (#96)"), ["feat(a): b"])

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "feat(gh-router): a thing (#96)")

    assert result.returncode == 0, result.stderr


def test_alignment_skips_a_scopeless_title(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** a thing (#96)"), ["feat(a): b"])

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "feat: a thing (#96)")

    assert result.returncode == 0, result.stderr


def test_squash_title_flag_needs_pr(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _ledger("* **thing:** a thing (#1)"), ["feat(thing): a (#1)"])

    result = _run(repo, "ledger", "--squash-title", "feat(thing): a thing")

    assert result.returncode == 2, result.stderr
    assert "--squash-title needs --pr" in result.stderr


# --- the bump-vs-ledger audit ----------------------------------------------------------------


def test_ledger_blocks_a_feature_entry_under_a_fix_title(tmp_path: Path) -> None:
    """A `fix` title licenses a patch; a `### Features` entry publishes a minor feature (#282)."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing (#96)"),
        ["fix(thing): repair a thing (#96)"],
    )

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "fix(thing): repair a thing")

    assert result.returncode == 1, result.stderr
    assert "bump-alignment" in result.stderr
    assert "licenses a patch" in result.stderr
    assert "add a thing" in result.stderr
    assert "fix(thing): repair a thing" in result.stderr


def test_ledger_blocks_a_breaking_entry_under_a_non_breaking_title(tmp_path: Path) -> None:
    """A breaking ledger entry needs a major title, never a plain `feat` (#282)."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** break a thing (#96) (BREAKING CHANGE)"),
        ["feat(thing): break a thing (#96)"],
    )

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "feat(thing): break a thing")

    assert result.returncode == 1, result.stderr
    assert "bump-alignment" in result.stderr
    assert "requires a major" in result.stderr
    assert "break a thing" in result.stderr
    assert "feat(thing): break a thing" in result.stderr


def test_ledger_passes_a_hidden_title_that_adds_no_entries(tmp_path: Path) -> None:
    """The hidden-type exemption is unchanged: a chore PR still owes nothing (#282)."""
    repo = _repo(tmp_path, _ledger("* **thing:** a (#1)"), ["chore(thing): tidy (#96)"])

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "chore(thing): tidy")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ledger: pass"


def test_ledger_passes_a_feature_title_under_features_entries(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing (#96)"),
        ["feat(thing): add a thing (#96)"],
    )

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "feat(thing): add a thing")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ledger: pass"


def test_ledger_passes_a_breaking_title_under_a_breaking_entry(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** break a thing (#96) (BREAKING CHANGE)"),
        ["feat(thing)!: break a thing (#96)"],
    )

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "feat(thing)!: break a thing")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ledger: pass"


def test_ledger_blocks_a_feature_entry_under_a_hidden_title(tmp_path: Path) -> None:
    """A `docs` title licenses no release, so it cannot carry a feature entry."""
    repo = _repo(
        tmp_path,
        _ledger("* **thing:** add a thing (#96)"),
        ["docs(thing): add a thing (#96)"],
    )

    result = _run(repo, "ledger", "--pr", "96", "--squash-title", "docs(thing): add a thing")

    assert result.returncode == 1, result.stderr
    assert "bump-alignment" in result.stderr
    assert "licenses no release" in result.stderr
    assert "add a thing" in result.stderr
