"""Lock the tool-preference split between the two rule files.

`rules/common/tool-preferences-bash.md` carries binary choices only, so a harness
tree can omit it whole. `rules/common/tool-preferences.md` keeps every preference
that a binary check cannot enforce: version pinning, workspaces, and the rest.
The bash file scopes itself to the non-pi harnesses; the shared file stays
unscoped.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMON = REPO_ROOT / "rules" / "common"
SHARED = COMMON / "tool-preferences.md"
BASH = COMMON / "tool-preferences-bash.md"


def _frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    block = text.split("---\n", 2)[1]
    data: object = yaml.safe_load(block)
    return data if isinstance(data, dict) else {}


BINARY_CHOICES = (
    "Prefer `rg` over `grep`",
    "Prefer `fd` over `find`",
    "Prefer `eza` over `ls`",
    "Prefer `uv` over `pip`",
    "Prefer `pnpm` over `npm`",
    "Prefer `tsx` over `ts-node`",
    "Use `oxlint` and `oxfmt`",
)

WORKFLOW_RULES = (
    "Respect `.python-version` and `.tool-versions`",
    "Use `pnpm -r` workspaces",
    "Read pinned versions from `packageManager` and `.nvmrc`",
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


def test_binary_choices_live_in_one_file() -> None:
    bash = BASH.read_text(encoding="utf-8")
    shared = SHARED.read_text(encoding="utf-8")
    for phrase in BINARY_CHOICES:
        assert phrase in bash, phrase
        assert phrase not in shared, phrase


def test_shared_file_keeps_droppable_workflow_rules() -> None:
    bash = BASH.read_text(encoding="utf-8")
    shared = SHARED.read_text(encoding="utf-8")
    for phrase in WORKFLOW_RULES:
        assert phrase in shared, phrase
        assert phrase not in bash, phrase
    assert "- **Python:**" in shared
    assert "- **TypeScript / Node:**" in shared


def test_shared_file_keeps_non_bash_advice() -> None:
    shared = SHARED.read_text(encoding="utf-8")
    for phrase in SHARED_ADVICE:
        assert phrase in shared, phrase
    assert "tool-preferences-bash.md" in shared


def test_bash_file_scopes_to_non_pi_harnesses() -> None:
    agents = _frontmatter(BASH).get("agents")
    assert isinstance(agents, list)
    assert agents == ["claude", "codex", "agy"]
    assert "pi" not in agents


def test_shared_file_declares_no_agents_key() -> None:
    assert "agents" not in _frontmatter(SHARED)
