"""Lock the bash-tool preference split between the two rule files.

Bash binary preferences live alone in `rules/common/tool-preferences-bash.md`.
Its harness-scoping contract is `docs/agents/rules.md`; the shared file keeps the
advice that stays always-on.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMON = REPO_ROOT / "rules" / "common"
SHARED = COMMON / "tool-preferences.md"
BASH = COMMON / "tool-preferences-bash.md"

BASH_PREFERENCES = (
    "Prefer `rg` over `grep`",
    "Prefer `fd` over `find`",
    "Prefer `eza` over `ls`",
    "Prefer `uv` over `pip`",
    "Prefer `pnpm` over `npm`",
    "Prefer `tsx` over `ts-node`",
    "Use `oxlint` and `oxfmt`",
)

SHARED_ADVICE = (
    "Use `read` for files you intend to edit",
    "cat -vet",
    "#176",
    "Use absolute paths only",
    "$SKILL_DIR",
    "cargo clippy",
    "gofumpt",
    "asdf",
)


def test_bash_preferences_live_in_one_file() -> None:
    bash = BASH.read_text(encoding="utf-8")
    shared = SHARED.read_text(encoding="utf-8")
    for phrase in BASH_PREFERENCES:
        assert phrase in bash, phrase
        assert phrase not in shared, phrase


def test_shared_file_keeps_non_bash_advice() -> None:
    shared = SHARED.read_text(encoding="utf-8")
    for phrase in SHARED_ADVICE:
        assert phrase in shared, phrase
    assert "tool-preferences-bash.md" in shared
