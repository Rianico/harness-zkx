"""Squash-message gate: title shape, the three required body parts, and the strip rules.

The gate is the deterministic half of `pr.py`'s squash message: `check_squash_title`
owns the Conventional Commit title, `check_squash_body` owns Core/Root/Blast Radius/
Evidence/Links, and `clean_squash_body` owns the strip rules. Wording judgment stays
with the model; every refusal here is a shape fact a machine can decide.

`--check` runs the same gate, so a refused draft still writes both files and exits 1.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.git_env import git_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"
TEMPLATE_PATH = REPO_ROOT / ".github" / "pull_request_template.md"

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

from pr import (  # noqa: E402
    RefusalError,
    check_squash_body,
    check_squash_title,
    clean_squash_body,
)


def _filled_template_body() -> str:
    """The shipped PR template with comments dropped and its non-Evidence values filled in.

    The section names and containment labels come from the file itself, so this is exactly
    the shape the repo's own template produces: a `**Door:**` line opening Blast Radius plus
    the `**Rollback / containment:**` statement. The Evidence labels stay bare, and the
    fix-only Root Cause section stays empty, as a non-`fix` author would leave it.
    """
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    body = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
    filled: list[str] = []
    for line in body.splitlines():
        if line.strip() == "-":
            filled.append("- bound the retry loop")
        elif line.strip() == "**Rollback / containment:**":
            filled.append("**Rollback / containment:** revert the squash commit")
        elif line.strip() == "**Door:** one-way / two-way":
            filled.append("**Door:** two-way")
        else:
            filled.append(line)
    body = "\n".join(filled)
    return body.replace("## Summary\n", "## Summary\nbound the retry loop\n", 1)


def _template_with_evidence(evidence: str) -> str:
    """The filled template with its bare Evidence label pair replaced by `evidence`."""
    return _filled_template_body().replace(
        "**Before (command + output):**\n**After (command + output):**", evidence, 1
    )


def _template_shaped_body() -> str:
    """The filled template with a real before -> after pasted into Evidence."""
    return _template_with_evidence("before: 3 failed -> after: 0 failed")


def _fix_template_shaped_body() -> str:
    """The filled template with its fix-only Root Cause section written out."""
    return _template_shaped_body().replace(
        "## Root Cause\n",
        "## Root Cause\nthe error path never released the lock\n",
        1,
    )


# --- title: type(scope): subject, Conventional Commit, <= 100 chars ---


@pytest.mark.parametrize(
    "title",
    [
        "feat(pr-land): tighten the squash gate",
        "fix: release the lock on the error path",
        "refactor!: drop the retired shim",
        "chore(deps): bump ruff",
    ],
)
def test_squash_title_accepts_conventional_shape(title: str) -> None:
    check_squash_title(title, 7)


@pytest.mark.parametrize(
    "title",
    [
        "update docs",
        "feat(scope) missing the colon",
        "Feature: capitalized non-type",
        "feat:",
        "feat:no space after the colon",
        "wip",
    ],
)
def test_squash_title_refuses_non_conventional_shape(
    title: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(RefusalError):
        check_squash_title(title, 7)
    err = capsys.readouterr().err
    assert "Conventional Commit" in err
    assert "rem" in err.lower()


@pytest.mark.parametrize(
    "title",
    [
        "Feat: x",
        "FIX: y",
        "Feat(api): z",
        "FEAT(api): z",
    ],
)
def test_squash_title_accepts_a_mixed_case_type(title: str) -> None:
    """The Convention names the type case-insensitively, so the title gate must fold it.

    Agreement matters: `check_squash_body` already folds the type to decide `fix`,
    so a case-sensitive title gate would refuse `FEAT: y` while the body gate read
    the same title as a fix. One squash message must not be judged two ways.
    """
    check_squash_title(title, 12)


@pytest.mark.parametrize("title", ["fix: y", "FIX: y"])
def test_squash_title_and_body_gate_agree_a_fix_needs_root(title: str) -> None:
    """A `fix` title the gate accepts is a `fix` to the body gate: it must name Root Cause.

    The title gate and the body gate read the same string, so agreement means a title
    accepted as a fix always demands `## Root Cause` — never one without the other.
    """
    check_squash_title(title, 13)
    with pytest.raises(RefusalError):
        check_squash_body("## Summary\nthe lock leaks\n", title=title)


@pytest.mark.parametrize("title", ["feat: x", "Feat: x", "FEAT(api): z"])
def test_squash_title_and_body_gate_agree_a_non_fix_skips_root(title: str) -> None:
    """A non-`fix` type the gate accepts needs no Root Cause: the two gates agree."""
    check_squash_title(title, 14)
    check_squash_body("## Summary\nbound the retry loop\n", title=title)


@pytest.mark.parametrize("title", ["Wip: x", "wip: x", "feat x"])
def test_squash_title_pins_the_non_conventional_refusal_text(
    title: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """A genuinely non-conventional title keeps today's refusal and remediation bytes."""
    with pytest.raises(RefusalError):
        check_squash_title(title, 7)
    expected = (
        "refusing squash merge: commit title is not a Conventional Commit "
        f'"type(scope): subject": {title} (#7)\n'
        "remediation: rename the PR title to `type(scope): subject` "
        "(feat, fix, docs, refactor, test, ...), then re-run\n"
    )
    assert capsys.readouterr().err == expected


def test_squash_title_accepts_the_exact_length_limit() -> None:
    check_squash_title("feat: " + "a" * 89, 7)  # 95 + " (#7)" = 100


def test_squash_title_refuses_one_char_over_the_limit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(RefusalError):
        check_squash_title("feat: " + "a" * 90, 7)
    assert "exceeds 100 chars" in capsys.readouterr().err


# --- Core: required on every path ---


def test_squash_body_refuses_a_body_without_a_core_section(
    capsys: pytest.CaptureFixture[str],
) -> None:
    body = (
        "- Blast Radius: Door: two-way; rollback: revert the squash commit\n"
        "- Evidence: before 3 failed -> after 0 failed\n"
    )
    with pytest.raises(RefusalError):
        check_squash_body(body)
    assert "Core" in capsys.readouterr().err


@pytest.mark.parametrize(
    "body",
    [
        "Just one authored paragraph.\n",
        "## Summary\nwhy the change matters\n",
        "## What Changed\n- one bullet\n",
        "- Core: bound the retry loop\n",
    ],
)
def test_squash_body_accepts_an_authored_core(body: str) -> None:
    check_squash_body(body)


# --- Root: bugfix-only ---


def test_squash_body_requires_root_for_a_fix_title(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(RefusalError):
        check_squash_body("## Summary\nthe lock leaks\n", title="fix(pr-land): leaked lock")
    assert "Root" in capsys.readouterr().err


def test_squash_body_accepts_a_fix_title_with_root() -> None:
    check_squash_body(
        "## Summary\nthe lock leaks\n\n## Root Cause\nthe error path never released it\n",
        title="fix(pr-land): leaked lock",
    )


def test_squash_body_accepts_a_fix_body_built_from_the_shipped_template() -> None:
    """A `fix` PR that follows the shipped template fills the taught `## Root Cause` section."""
    body = _fix_template_shaped_body()
    assert "## Root Cause" in body, "the shipped template teaches the fix-only Root Cause heading"
    check_squash_body(clean_squash_body(body), title="fix(pr-land): leaked lock")


def test_squash_body_refuses_a_fix_template_body_without_the_root_cause_section(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Deleting the template's fix-only Root Cause section from a `fix` body still refuses."""
    without = _fix_template_shaped_body().replace(
        "## Root Cause\nthe error path never released the lock\n", "", 1
    )
    assert "## Root Cause" not in without
    with pytest.raises(RefusalError):
        check_squash_body(clean_squash_body(without), title="fix(pr-land): leaked lock")
    assert "Root" in capsys.readouterr().err


def test_squash_body_prunes_the_empty_root_cause_from_a_non_fix_template_body() -> None:
    """The fix-only section is deletable: left empty it is pruned, so a feat body passes."""
    cleaned = clean_squash_body(_template_shaped_body())
    assert "## Root Cause" not in cleaned
    check_squash_body(cleaned, title="feat(pr-land): bound the retry loop")


@pytest.mark.parametrize("title", ["feat: add the gate", "chore(deps): bump ruff", "docs: note"])
def test_squash_body_never_requires_root_for_other_types(title: str) -> None:
    check_squash_body("## Summary\nsectioned body without root\n", title=title)


def test_squash_body_accepts_a_colon_terminated_root_cause_heading() -> None:
    """`## Root Cause:` with the trailing colon is the same heading as `## Root Cause`."""
    check_squash_body(
        "## Summary\nthe lock leaks\n\n## Root Cause:\nthe error path never released it\n",
        title="fix(pr-land): leaked lock",
    )


def test_squash_body_accepts_an_inline_root_cause_heading() -> None:
    """`## Root Cause: <why>` states Root in the heading itself, not as a bare label."""
    check_squash_body(
        "## Summary\nthe lock leaks\n\n## Root Cause: the error path never released it\n",
        title="fix(pr-land): leaked lock",
    )


def test_squash_body_validates_a_colon_terminated_blast_radius_heading(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A trailing colon never smuggles Blast Radius past the door + rollback gate."""
    with pytest.raises(RefusalError):
        check_squash_body("## Summary\nx\n\n## Blast Radius:\nDoor: one-way\n")
    assert "rollback" in capsys.readouterr().err.lower()


def test_squash_body_accepts_a_colon_terminated_blast_radius_heading() -> None:
    check_squash_body(
        "## Summary\nx\n\n## Blast Radius:\n"
        "Door: two-way\n**Rollback / containment:** revert the squash commit\n"
    )


def test_squash_body_validates_a_colon_terminated_evidence_heading(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A trailing colon never smuggles Evidence past the before -> after gate."""
    with pytest.raises(RefusalError):
        check_squash_body("## Summary\nx\n\n## Evidence:\nuv run pytest tests/gh-router -q\n")
    assert "before" in capsys.readouterr().err.lower()


def test_squash_body_accepts_a_colon_terminated_evidence_heading() -> None:
    check_squash_body("## Summary\nx\n\n## Evidence:\nbefore: 3 failed -> after: 0 failed\n")


def test_squash_body_refuses_a_prose_fix_body_without_root(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Root is required for every `fix` title, a heading-free prose body included."""
    with pytest.raises(RefusalError):
        check_squash_body(
            "The lock leaked on the error path and is released now.\n", title="fix: leak"
        )
    assert "Root" in capsys.readouterr().err


def test_squash_body_accepts_a_prose_fix_body_with_a_root_label() -> None:
    """A prose Core plus a `Root cause:` label states Root without a heading."""
    check_squash_body(
        "The lock leaked on the error path and is released now.\n\n"
        "Root cause: the error path never released it\n",
        title="fix: leak",
    )


# --- Blast Radius: door + rollback when declared ---


def test_squash_body_refuses_blast_radius_without_the_door(
    capsys: pytest.CaptureFixture[str],
) -> None:
    body = "## Summary\nx\n\n## Blast Radius & Safety\nrevert the squash commit\n"
    with pytest.raises(RefusalError):
        check_squash_body(body)
    assert "door" in capsys.readouterr().err.lower()


def test_squash_body_refuses_blast_radius_without_rollback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    body = "## Summary\nx\n\n## Blast Radius & Safety\nDoor: one-way\n"
    with pytest.raises(RefusalError):
        check_squash_body(body)
    assert "rollback" in capsys.readouterr().err.lower()


def test_squash_body_accepts_blast_radius_with_door_and_rollback() -> None:
    check_squash_body(
        "## Summary\nx\n\n## Blast Radius & Safety\n"
        "Door: two-way\n**Rollback / containment:** revert the squash commit\n"
    )


def test_squash_body_accepts_the_legacy_rollback_label_without_a_door() -> None:
    """Older copies and other repos open Blast Radius with the legacy
    `**Rollback / containment:**` label and no `Door:` line; the gate still accepts it."""
    check_squash_body(
        "## Summary\nx\n\n## Blast Radius & Safety\n"
        "**Rollback / containment:** revert the squash commit\n"
    )


def test_squash_body_refuses_the_bare_rollback_label(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The template's own label names containment; it is not a rollback statement."""
    with pytest.raises(RefusalError):
        check_squash_body(
            "## Summary\nx\n\n## Blast Radius & Safety\n**Rollback / containment:**\n"
        )
    assert "rollback" in capsys.readouterr().err.lower()


def test_squash_body_accepts_the_rollback_label_carrying_content() -> None:
    check_squash_body(
        "## Summary\nx\n\n## Blast Radius & Safety\n"
        "**Rollback / containment:** revert the squash commit\n"
    )


def test_squash_body_accepts_a_non_door_rollback_line() -> None:
    """Any non-Door line that states the rollback satisfies the gate."""
    check_squash_body(
        "## Summary\nx\n\n## Blast Radius & Safety\n"
        "Door: two-way\nRollback: revert the squash commit\n"
    )


def test_squash_body_validates_a_bold_blast_radius_label(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A bold `- **Blast Radius:** …` label opens the section, so the gate bites."""
    with pytest.raises(RefusalError):
        check_squash_body("## Summary\nx\n- **Blast Radius:** shipping risk\n")
    assert "door" in capsys.readouterr().err.lower()


def test_squash_body_accepts_a_bold_blast_radius_label_with_door_and_rollback() -> None:
    check_squash_body(
        "## Summary\nx\n- **Blast Radius:** Door: two-way\n"
        "**Rollback / containment:** revert the squash commit\n"
    )
    check_squash_body(
        "## Summary\nx\n- **Blast Radius:** Door: two-way; rollback: revert the squash commit\n"
    )


def test_squash_body_accepts_a_bare_risk_line_as_prose() -> None:
    """`Risk:` is not a Blast Radius alias, so the line stays prose and the gate is skipped."""
    check_squash_body("## Summary\nDocs only.\n- Risk: low, no runtime path\n")


def test_squash_body_accepts_a_real_template_shaped_body() -> None:
    """A body built from the repo's own shipped template passes the gate end to end.

    The template opens Blast Radius with `**Door:**`, so that line satisfies the door
    gate; the legacy `**Rollback / containment:**` label still carries the rollback.
    """
    body = _template_shaped_body()
    assert "Door:" in body, "the shipped template opens Blast Radius with its Door line"
    check_squash_body(clean_squash_body(body), title="feat(pr-land): bound the retry loop")


# --- Evidence: before -> after when declared ---


def test_squash_body_refuses_evidence_without_before_then_after(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(RefusalError):
        check_squash_body("## Summary\nx\n\n## Evidence\nuv run pytest tests/gh-router -q\n")
    assert "before" in capsys.readouterr().err.lower()


@pytest.mark.parametrize(
    "evidence",
    [
        "uv run pytest -q: 3 failed -> 0 failed",
        "before: 2 failed\nafter: 2 passed",
        "was 2 failed, now 2 passed",
    ],
)
def test_squash_body_accepts_evidence_with_before_and_after(evidence: str) -> None:
    check_squash_body(f"## Summary\nx\n\n## Evidence\n{evidence}\n")


def test_squash_body_refuses_the_template_with_bare_evidence_labels(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The template's bare `**Before (command + output):**` pair pastes no output.

    This body passed the gate before the label rule landed: the marker substrings matched
    the bare headings themselves, with nothing pasted under them.
    """
    body = _filled_template_body()
    assert "**Before (command + output):**" in body
    with pytest.raises(RefusalError):
        check_squash_body(clean_squash_body(body), title="feat(pr-land): bound the retry loop")
    assert "before -> after" in capsys.readouterr().err


@pytest.mark.parametrize(
    "evidence",
    [
        "**Before (command + output):**\n$ uv run pytest -q\n3 failed\n"
        "**After (command + output):**\n$ uv run pytest -q\n0 failed",
        "**Before (command + output):** $ uv run pytest -q: 3 failed\n"
        "**After (command + output):** $ uv run pytest -q: 0 failed",
        "**Before:**\n3 failed\n**After:**\n0 failed",
    ],
)
def test_squash_body_accepts_the_evidence_labels_over_pasted_output(evidence: str) -> None:
    check_squash_body(
        clean_squash_body(_template_with_evidence(evidence)),
        title="feat(pr-land): bound the retry loop",
    )


def test_squash_body_refuses_a_bare_before_label_beside_a_filled_after_label(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Output under one label never vouches for the other: each label needs its own output."""
    with pytest.raises(RefusalError):
        check_squash_body(
            "## Summary\nx\n\n## Evidence\n"
            "**Before (command + output):**\n**After (command + output):**\n0 failed\n"
        )
    assert "before -> after" in capsys.readouterr().err


# --- Links: the PR link, plus optional one-issue-per-line Closes ---


def test_squash_body_refuses_a_links_section_without_the_pr_link(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(RefusalError):
        check_squash_body(
            "## Summary\nx\n\n## Links\nCloses #7\n",
            pr_link="https://github.com/o/r/pull/7",
        )
    assert "PR link" in capsys.readouterr().err


def test_squash_body_accepts_a_links_section_with_the_pr_link() -> None:
    check_squash_body(
        "## Summary\nx\n\n## Links\nhttps://github.com/o/r/pull/7\nCloses #7\n",
        pr_link="https://github.com/o/r/pull/7",
    )


def test_squash_body_accepts_a_body_without_any_links_section() -> None:
    check_squash_body("## Summary\nx\n")


def test_squash_body_accepts_standalone_closes_lines() -> None:
    check_squash_body("## Summary\nx\n\nCloses #1\nCloses #2\n")


def test_squash_body_refuses_closes_lines_carrying_two_issues(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(RefusalError):
        check_squash_body("## Summary\nx\n\nCloses #1, #2\n")
    assert "Closes" in capsys.readouterr().err


# --- bullets: at most five ---


def test_squash_body_accepts_five_bullets() -> None:
    check_squash_body("## Summary\n" + "".join(f"- item {i}\n" for i in range(1, 6)))


def test_squash_body_refuses_six_bullets(capsys: pytest.CaptureFixture[str]) -> None:
    body = "## Summary\n" + "".join(f"- item {i}\n" for i in range(1, 7))
    with pytest.raises(RefusalError):
        check_squash_body(body)
    assert "bullets" in capsys.readouterr().err


def test_squash_body_ignores_bullets_inside_a_fence() -> None:
    """A quoted diff or log inside a fence is not the body's bullet list."""
    fenced = "\n".join(f"- removed line {i}" for i in range(1, 7))
    body = (
        "## Summary\nx\n\n## Evidence\nbefore: 3 failed -> after: 0 failed\n\n"
        f"```diff\n{fenced}\n```\n"
    )
    check_squash_body(body)


def test_squash_body_counts_bullets_after_a_fence_closes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Closing the fence restores counting, so the cap still bites outside a quote."""
    body = "## Summary\n```\n- quoted\n- quoted\n```\n" + "".join(
        f"- item {i}\n" for i in range(1, 7)
    )
    with pytest.raises(RefusalError):
        check_squash_body(body)
    assert "bullets" in capsys.readouterr().err


def test_squash_body_refuses_six_numbered_items(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A numbered list is a bullet list: `1.`/`1)` items count toward the cap."""
    body = "## Summary\n" + "".join(f"{i}. item {i}\n" for i in range(1, 7))
    with pytest.raises(RefusalError):
        check_squash_body(body)
    assert "bullets" in capsys.readouterr().err


@pytest.mark.parametrize("marker", [".", ")"])
def test_squash_body_counts_numbered_items_with_either_marker(
    marker: str, capsys: pytest.CaptureFixture[str]
) -> None:
    body = "## Summary\n" + "".join(f"{i}{marker} item {i}\n" for i in range(1, 7))
    with pytest.raises(RefusalError):
        check_squash_body(body)
    assert "bullets" in capsys.readouterr().err


def test_squash_body_refuses_bullets_under_an_unclosed_fence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unclosed fence quotes nothing: the bullets after it still count."""
    body = "## Summary\nx\n```diff\n" + "".join(f"- removed line {i}\n" for i in range(1, 7))
    with pytest.raises(RefusalError):
        check_squash_body(body)
    assert "bullets" in capsys.readouterr().err


def test_squash_body_ignores_six_bullets_in_a_closed_fence() -> None:
    """A closed fence still quotes its content, so six quoted `-` lines stay exempt."""
    fenced = "\n".join(f"- removed line {i}" for i in range(1, 7))
    check_squash_body(f"## Summary\nx\n```diff\n{fenced}\n```\n")


# --- strip rules: checkboxes, mermaid, <details> ---


def test_clean_squash_body_strips_checkboxes_but_keeps_the_prose() -> None:
    raw = "## Summary\n- [x] formatter green\n- [ ] tests green\n- real change\n"
    cleaned = clean_squash_body(raw)
    assert "[x]" not in cleaned
    assert "[ ]" not in cleaned
    assert "- real change" in cleaned


def test_clean_squash_body_strips_mermaid_and_details_from_the_squash_text() -> None:
    raw = (
        "## Summary\nreal\n\n"
        "```mermaid\nflowchart LR\n  A --> B\n```\n\n"
        "<details><summary>log</summary>\ntrace\n</details>\n"
    )
    cleaned = clean_squash_body(raw)
    assert "mermaid" not in cleaned
    assert "flowchart" not in cleaned
    assert "<details>" not in cleaned
    assert "trace" not in cleaned
    assert "real" in cleaned


def test_checkbox_strip_keeps_the_checklist_section_removal_intact() -> None:
    """Procedural prune and the checkbox rule compose: the prose stays, both strips bite."""
    raw = "## Summary\n- [x] formatter green\n- real change\n\n## Checklist\n- [x] tests green\n"
    cleaned = clean_squash_body(raw)
    assert "- real change" in cleaned
    assert "Checklist" not in cleaned
    assert "formatter green" not in cleaned
    assert "[x]" not in cleaned


# --- end to end: --check runs the gate ---

GH_STUB = """#!/usr/bin/env bash
for arg in "$@"; do
  if [[ "$arg" =~ pulls\\?head= ]]; then echo "null"; exit 0; fi
  if [[ "$arg" == "user" ]]; then echo "merger-user"; exit 0; fi
done
exit 0
"""


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=git_env(), check=True)


def _git(repo: Path, *args: str) -> None:
    _ = _run(["git", "-C", str(repo), *args])


def _make_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    _ = _run(["git", "init", "-b", "main", str(repo)])
    for key, value in (
        ("user.name", "Gate Synthetic"),
        ("user.email", "gate@x.io"),
        ("commit.gpgsign", "false"),
    ):
        _ = _run(["git", "-C", str(repo), "config", key, value])
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-m", "chore: base")
    _git(repo, "remote", "add", "origin", "https://github.com/test/gate.git")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _git(repo, "checkout", "-b", "feat-gate")
    _ = (repo / "one.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "one.txt")
    _git(repo, "commit", "-m", "feat: one")


def _gh_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text(GH_STUB, encoding="utf-8")
    gh.chmod(0o755)
    return git_env(PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}")


def _run_check(repo: Path, env: dict[str, str], *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PR_PY), "--check", "--head", "feat-gate", *extra],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )


def test_check_refuses_a_body_without_core_and_still_writes_both_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text(
        "- Blast Radius: Door: two-way; rollback: revert the squash commit\n", encoding="utf-8"
    )

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 1, r.stdout
    assert "Core" in r.stderr
    draft_path = repo / ".lsz" / "tmp" / "draft.json"
    assert draft_path.is_file()
    assert (repo / ".lsz" / "tmp" / "pr_body.md").is_file()
    draft: dict[str, Any] = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft["status"] == "refused"
    assert draft["exit_code"] == 1


def test_check_strips_mermaid_details_and_checkboxes_from_the_squash_body(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text(
        "## Summary\nreal change\n\n"
        "```mermaid\nflowchart LR\n  A --> B\n```\n\n"
        "<details><summary>trace</summary>\nsecret\n</details>\n\n"
        "- [x] tests green\n",
        encoding="utf-8",
    )

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    draft: dict[str, Any] = json.loads(
        (repo / ".lsz" / "tmp" / "draft.json").read_text(encoding="utf-8")
    )
    squash_body = str(draft["squash_body"])
    assert "mermaid" not in squash_body
    assert "flowchart" not in squash_body
    assert "<details>" not in squash_body
    assert "[x]" not in squash_body
    assert "real change" in squash_body
