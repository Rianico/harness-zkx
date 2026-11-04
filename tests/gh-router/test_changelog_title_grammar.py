"""One corpus pins the four homes of the Conventional Commit title grammar (H1, #307).

Four regexes parse a squash title: `HIDDEN_TITLE_RE` and `TITLE_SCOPE_RE` in
`scripts/changelog-gate.py`, `_HIDDEN_TITLE_RE` in `_changelog.py`, and
`SQUASH_TITLE_RE` in `_squash.py`. Before #307 the gate's two copies put `!`
before the optional scope, so a canonical `feat(store)!:` parsed as nothing:
`_title_bump` returned `None` and the bump audit opted out silently while
`warn_ledger_gap` still saw a hidden type. A single corpus here keeps the copies
in step, so a future edit to one home fails this test instead of the ledger.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import _changelog
import _squash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GATE = REPO_ROOT / "scripts" / "changelog-gate.py"

# Every shape the four homes must read: scoped and scopeless, breaking and not.
CORPUS: tuple[str, ...] = (
    "feat(store)!: break a thing",
    "fix(store)!: break a thing",
    "feat!: break a thing",
    "perf(store): speed a thing",
    "docs(store): describe a thing",
    "feat(store): add a thing",
)


def _gate_module() -> ModuleType:
    """Load `scripts/changelog-gate.py` as a module (its filename is not importable)."""
    spec = importlib.util.spec_from_file_location("changelog_gate_under_test", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_every_corpus_title_licenses_a_release_level() -> None:
    """The audit must never opt out: each corpus title parses to a bump, not None (#309)."""
    gate = _gate_module()
    for title in CORPUS:
        assert gate._title_bump(title) is not None, title


def test_hidden_title_grammars_agree_on_the_corpus() -> None:
    """The gate and `_changelog` must read `type`/`bang` identically, scope included."""
    gate = _gate_module()
    for title in CORPUS:
        gate_match = gate.HIDDEN_TITLE_RE.match(title)
        ours = _changelog._HIDDEN_TITLE_RE.match(title)
        assert gate_match is not None, title
        assert ours is not None, title
        assert gate_match.group("type") == ours.group("type"), title
        assert gate_match.group("bang") == ours.group("bang"), title


def test_scope_grammars_agree_on_the_corpus() -> None:
    """`TITLE_SCOPE_RE` and `SQUASH_TITLE_RE` must read the same scope and bang."""
    gate = _gate_module()
    for title in CORPUS:
        gate_match = gate.TITLE_SCOPE_RE.match(title)
        squash_match = _squash.SQUASH_TITLE_RE.match(title)
        bang_match = gate.HIDDEN_TITLE_RE.match(title)
        assert gate_match is not None, title
        assert squash_match is not None, title
        assert bang_match is not None, title
        assert gate_match.group("scope") == squash_match.group("scope"), title
        # Cross-assert the bang: `HIDDEN_TITLE_RE` is the independent oracle, so a
        # shared slip in `TITLE_SCOPE_RE` and `SQUASH_TITLE_RE` cannot hide here.
        assert (squash_match.group("breaking") is not None) == bool(bang_match.group("bang")), title
