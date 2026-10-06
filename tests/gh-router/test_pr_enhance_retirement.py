"""Guard: pr-enhance diff analysis stays retired; the digest is the change-fact source.

The git-diff-digest brief owns change facts. `analyze-pr.py` keeps only the
read-only drafting-schema seam (`--print-template`); no doc may instruct
running the analyser as a change-fact source.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_ENHANCE_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-enhance/scripts"
TOUCHED_DOCS = [
    REPO_ROOT / "skills/gh-router/subskills/pr-enhance/SKILL.md",
    REPO_ROOT / "skills/gh-router/subskills/pr-land/SKILL.md",
    REPO_ROOT / "skills/gh-router/SKILL.md",
    REPO_ROOT / "skills/dynamic-workflow-wrapper/references/agents/merger.md",
]

RETIRED_SYMBOLS = [
    "PRAnalyzer",
    "analyze_changes",
    "_get_changed_files",
    "_get_change_stats",
    "categorize",
    "_infer_base",
    "_is_pr_target",
    "_analyze_pr_via_gh",
]
RETIRED_GIT_STRINGS = ["git diff --name-status", "--shortstat"]


def _script_texts() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(PR_ENHANCE_SCRIPTS.glob("*.py"))}


def test_no_diff_analysis_symbols_in_pr_enhance_scripts() -> None:
    texts = _script_texts()
    assert texts, "pr-enhance scripts directory must still carry analyze-pr.py"
    offenders = [
        f"{name} contains retired symbol {symbol!r}"
        for name, text in texts.items()
        for symbol in RETIRED_SYMBOLS
        if symbol in text
    ]
    assert not offenders, "\n".join(offenders)


def test_no_git_diff_plumbing_strings_in_pr_enhance_scripts() -> None:
    texts = _script_texts()
    offenders = [
        f"{name} contains retired plumbing {needle!r}"
        for name, text in texts.items()
        for needle in RETIRED_GIT_STRINGS
        if needle in text
    ]
    assert not offenders, "\n".join(offenders)


def test_no_analyser_as_change_fact_source_in_docs() -> None:
    offenders = []
    for doc in TOUCHED_DOCS:
        assert doc.is_file(), f"touched doc missing: {doc}"
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            if "analyze-pr.py" in line and "--print-template" not in line:
                offenders.append(f"{doc.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, "\n".join(offenders)
