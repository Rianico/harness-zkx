"""Guard: pr-enhance diff analysis stays retired; the digest is the change-fact source.

The git-diff-digest brief owns change facts. `analyze-pr.py` keeps only the
read-only drafting-schema seam (`--print-template`); no doc may instruct
running the analyser as a change-fact source.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_ENHANCE_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-enhance/scripts"
PR_ENHANCE_SKILL = REPO_ROOT / "skills/gh-router/subskills/pr-enhance/SKILL.md"
PR_LAND_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
DRAFT_MODULE = PR_LAND_SCRIPTS / "_draft.py"
TOUCHED_DOCS = [
    PR_ENHANCE_SKILL,
    REPO_ROOT / "skills/gh-router/subskills/pr-land/SKILL.md",
    REPO_ROOT / "skills/gh-router/SKILL.md",
    REPO_ROOT / "retired/dynamic-workflow-wrapper/references/agents/merger.md",
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


_SUBPROCESS_RUNNERS = ("run", "call", "check_call", "check_output", "Popen")
_DIFF_TOKENS = ("diff", "log")


def _argv_literals(call: ast.Call) -> list[str]:
    literals: list[str] = []
    positional = list(call.args) + [keyword.value for keyword in call.keywords]
    for arg in positional:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            literals.append(arg.value)
        elif isinstance(arg, (ast.List, ast.Tuple)):
            literals.extend(
                element.value
                for element in arg.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )
    return literals


def _is_process_call(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if not isinstance(func.value, ast.Name):
        return False
    if func.value.id == "os" and func.attr == "system":
        return True
    return func.value.id == "subprocess" and func.attr in _SUBPROCESS_RUNNERS


def test_no_tokenized_git_diff_calls_in_pr_enhance_scripts() -> None:
    offenders = []
    for path in sorted(PR_ENHANCE_SCRIPTS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not _is_process_call(node):
                continue
            blob = "\n".join(_argv_literals(node))
            if "git" in blob and any(token in blob for token in _DIFF_TOKENS):
                offenders.append(f"{path.name}:{node.lineno}: tokenized git diff/log call")
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


def _artifact_prefix() -> str:
    """`pr.py --check`'s tool-owned scaffold prefix, read from the `_status` sibling.

    ADR-0021 moved the scaffold leaf under `.lsz/gh-router/` with the head-ref
    slug as the default leaf; pr-enhance drafts into the same prefix.
    """
    source = (PR_LAND_SCRIPTS / "_status.py").read_text(encoding="utf-8")
    found = False
    value: ast.expr | None = None
    for node in ast.parse(source).body:
        if not (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)):
            continue
        if node.targets[0].id != "ARTIFACT_PREFIX":
            continue
        value = node.value
        found = True
    assert found, "_status.py no longer defines ARTIFACT_PREFIX"
    assert isinstance(value, ast.BinOp) and isinstance(value.op, ast.Div)
    assert isinstance(value.left, ast.Call)
    return f"{ast.literal_eval(value.left.args[0])}/{ast.literal_eval(value.right)}"


def test_pr_enhance_drafts_the_body_where_pr_check_writes_it() -> None:
    """The drafted body and `pr.py --check`'s scaffold leaf share the tool-owned prefix."""
    prefix = _artifact_prefix()
    assert prefix == ".lsz/gh-router"
    text = PR_ENHANCE_SKILL.read_text(encoding="utf-8")
    assert f"`{prefix}/<slug>.md`" in text, "pr-enhance must draft into the scaffold prefix"
    assert "`.lsz/tmp/pr_body.md`" not in text, "the fixed tmp path names the file nobody reads"
    assert "--out-dir" not in text
