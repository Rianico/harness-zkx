"""Pin the single-sourced reply-helper derivation across the herdr helper scripts.

`herdr_bootstrap.py`, `herdr_prompt.py`, and `herdr_reply.py` each render a command that runs
this tree's `herdr_reply.py`. The value is derived once, in the shared seam
`herdr_cli.reply_helper()`, so no module can silently name another worktree's helper.

An `is_file()` check cannot catch the cross-worktree hazard: the foreign helper exists on disk
(the `~/.agents/skills/herdr` symlink resolves into the `main` worktree, whose code is older).
These tests assert the *relationship* instead — the helper is a sibling of the module under
test — and they assert the relationship against the text each module actually renders.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

import herdr_bootstrap
import herdr_cli
import herdr_prompt
import herdr_reply
import pytest

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
    assert named.resolve() == Path(herdr_bootstrap.REPLY_HELPER).resolve()
    assert "~/.agents" not in text


def test_envelope_reply_contract_names_this_trees_helper() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="lane", agent="reviewer")
    text = herdr_prompt.render_reply_contract(sender)
    named = _helper_named_by(text, r'  uv run "([^"]+)" reviewer "<STATUS> <artifacts> <issues>"')
    assert named.resolve().parent == _module_dir(herdr_prompt)
    assert named.resolve() == Path(herdr_prompt.REPLY_HELPER).resolve()
    assert "~/.agents" not in text


def test_recovery_diagnostic_names_this_trees_helper() -> None:
    recovery = {"pane_id": "w1:p1", "kind": "pi"}
    text = herdr_reply.format_reply_recovery_diagnostic("caller", recovery, "reply.md")
    named = _helper_named_by(
        text, r'  1\. Auto-revive & deliver: uv run "([^"]+)" caller --file reply\.md'
    )
    assert named.resolve().parent == _module_dir(herdr_reply)
    assert named.resolve() == Path(herdr_reply.REPLY_HELPER).resolve()
    assert "~/.agents" not in text
