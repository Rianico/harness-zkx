"""Pin the single-sourced reply-helper derivation across the herdr helper scripts.

`herdr_bootstrap.py`, `herdr_prompt.py`, and `herdr_reply.py` each render a command that runs
this tree's `herdr_reply.py`. The value is derived once, in the shared seam
`herdr_cli.reply_helper()`, so no module can silently name another worktree's helper.

An `is_file()` check cannot catch the cross-worktree hazard: the foreign helper exists on disk
(the `~/.agents/skills/herdr` symlink resolves into the `main` worktree, whose code is older).
These tests assert the *relationship* instead — the helper is a sibling of the module under
test — and they assert the relationship against the text each module actually renders. A
`tokenize`-based scan closes part of the seam's last gap: no module outside `herdr_cli` may
hold the helper's basename as one string literal, so a re-hand-rolled derivation that spells
the path in a single literal cannot pass unnoticed. The scan is literal-shaped, not
derivation-shaped: a literal split across tokens (an f-string part, or concatenated fragments)
is outside its reach, and correctness there is held by the seam-equality and rendered-text
tests above.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path
from types import ModuleType

import herdr_bootstrap
import herdr_cli
import herdr_prompt
import herdr_reply
import pytest

from tests.herdr.stub import SCRIPTS_DIR

MODULES = (herdr_bootstrap, herdr_prompt, herdr_reply)
MODULE_IDS = ("herdr_bootstrap", "herdr_prompt", "herdr_reply")


def _module_dir(module: ModuleType) -> Path:
    file = module.__file__
    assert file is not None, f"{module.__name__} has no __file__"
    return Path(file).resolve().parent


def _helper_named_by(text: str, pattern: str) -> Path:
    match = re.search(pattern, text)
    assert match is not None, f"no helper path in rendered text:\n{text}"
    return Path(match.group(1))


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_helper_is_a_sibling_of_the_module_under_test(module: ModuleType) -> None:
    """The helper is this module's sibling, not merely some helper that exists somewhere."""
    assert Path(module.REPLY_HELPER).resolve().parent == _module_dir(module)


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_each_module_derives_the_helper_from_the_shared_seam(module: ModuleType) -> None:
    """One derivation in `herdr_cli`, so the three call sites cannot drift apart."""
    assert module.REPLY_HELPER == herdr_cli.reply_helper()


def test_seam_helper_is_a_sibling_of_the_seam() -> None:
    helper = Path(herdr_cli.reply_helper())
    assert helper.name == "herdr_reply.py"
    assert helper.resolve().parent == _module_dir(herdr_cli)


def test_invariant_contract_names_this_trees_helper() -> None:
    text = herdr_bootstrap.render_invariant("impl-1")
    named = _helper_named_by(text, r"`uv run (\S+) <caller> --file <reply\.md>`")
    assert named.resolve().parent == _module_dir(herdr_bootstrap)
    assert named.name == "herdr_reply.py"
    assert named.resolve() == Path(herdr_bootstrap.REPLY_HELPER).resolve()
    assert "~/.agents" not in text


def test_envelope_reply_contract_names_this_trees_helper() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="lane", agent="reviewer")
    text = herdr_prompt.render_reply_contract(sender)
    named = _helper_named_by(text, r'  uv run "([^"]+)" reviewer "<STATUS> <artifacts> <issues>"')
    assert named.resolve().parent == _module_dir(herdr_prompt)
    assert named.name == "herdr_reply.py"
    assert named.resolve() == Path(herdr_prompt.REPLY_HELPER).resolve()
    assert "~/.agents" not in text


def test_recovery_diagnostic_names_this_trees_helper() -> None:
    recovery = {"pane_id": "w1:p1", "kind": "pi"}
    text = herdr_reply.format_reply_recovery_diagnostic("caller", recovery, "reply.md")
    named = _helper_named_by(
        text, r'  1\. Auto-revive & deliver: uv run "([^"]+)" caller --file reply\.md'
    )
    assert named.resolve().parent == _module_dir(herdr_reply)
    assert named.name == "herdr_reply.py"
    assert named.resolve() == Path(herdr_reply.REPLY_HELPER).resolve()
    assert "~/.agents" not in text


# ── single-sourcing: no module outside the seam may name the helper ────────────────────────────

# The seam `herdr_cli.reply_helper()` is the one definition the three rendering modules call. A
# module that spells the helper's basename itself has re-hand-rolled that derivation, so a copy
# can silently name another worktree's helper. The allow-list therefore names the seam alone; a
# second entry would be the signal that the scan has been neutered.
HELPER_NAME_ALLOWLIST = frozenset({"herdr_cli.py"})


def _names_the_helper(source: str) -> bool:
    """True when `source` holds a string literal naming the helper; comments are invisible.

    Only a literal that *is* the helper's basename — `"herdr_reply.py"`, or a path ending in
    `"/herdr_reply.py"` — counts as naming it. `tokenize` skips comments, and prose that merely
    mentions the helper is not a derivation of its path.
    """
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.STRING:
            continue
        try:
            value = ast.literal_eval(token.string)
        except SyntaxError, ValueError:
            continue
        if isinstance(value, str) and (
            value == "herdr_reply.py" or value.endswith("/herdr_reply.py")
        ):
            return True
    return False


def _modules_naming_the_helper() -> set[str]:
    """Basenames of the skill's helper scripts whose code names the helper."""
    return {
        script.name
        for script in sorted(SCRIPTS_DIR.glob("*.py"))
        if _names_the_helper(script.read_text(encoding="utf-8"))
    }


def test_only_the_seam_module_names_the_helper() -> None:
    """No module outside the seam names the helper: a hand-rolled path is exactly the drift."""
    assert set(HELPER_NAME_ALLOWLIST) == {"herdr_cli.py"}, (
        "the allow-list must name the seam alone; a second entry means the scan is neutered"
    )
    naming = _modules_naming_the_helper()
    assert "herdr_cli.py" in naming, (
        "the scan cannot see the seam's own derivation, so it proves nothing"
    )
    offenders = sorted(naming - HELPER_NAME_ALLOWLIST)
    assert offenders == [], "modules naming the helper outside the seam: " + ", ".join(offenders)
