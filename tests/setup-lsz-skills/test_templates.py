"""Template rendering tests for setup-lsz-skills.

The renderer runs under `StrictUndefined`, so a missing context variable raises
during render: these tests double as the contract that `build_template_context`
supplies every variable the six `.j2` templates reference.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

TEMPLATE_NAMES = [
    "domain.md.j2",
    "toolchain.md.j2",
    "issue-tracker-github.md.j2",
    "issue-tracker-gitlab.md.j2",
    "issue-tracker-local.md.j2",
    "triage-labels.md.j2",
]

# Fixture data only: the canonical exclude list is asserted in test_detect.py.
EXCLUDE_PATTERNS = [
    r"^cat\b",
    r"^head\b",
    r"^tail\b",
    r"^grep\b",
    r"^rg\b",
    r"^wc\b",
]


def _state(provider: str = "github", has_context_map: bool = False) -> dict[str, Any]:
    tool = {
        "detected": True,
        "path": "/usr/bin/tool",
        "purpose": "does work",
        "fallback": "plain tool",
    }
    toolchain: dict[str, dict[str, Any]] = {
        name: dict(tool)
        for name in ("adr", "fd", "rg", "eza", "wt", "uv", "oxlint", "oxfmt", "basedpyright")
    }
    toolchain["rtk"] = {
        "detected": True,
        "path": "/opt/homebrew/bin/rtk",
        "purpose": "Token-optimized CLI proxy for shell commands",
        "fallback": "direct command execution",
    }
    return {
        "cwd": "/repo",
        "project_name": "demo-proj",
        "git": {"remote_url": "https://github.com/acme/demo-proj.git", "provider": provider},
        "provider": provider,
        "steering_file": "AGENTS.md",
        "has_agents_md": True,
        "has_claude_md": False,
        "has_context_md": False,
        "has_context_map": has_context_map,
        "has_glossary_md": True,
        "has_adr_dir": True,
        "existing_docs_agents": [],
        "stale_files": {},
        "toolchain": toolchain,
        "rtk": {
            "installed": True,
            "path": "/opt/homebrew/bin/rtk",
            "version": "0.48.0",
            "version_ok": True,
            "active_agent": "pi",
            "hook_installed": True,
            "exclude_commands": {"present": list(EXCLUDE_PATTERNS), "missing": []},
        },
    }


def test_all_six_templates_exist(templates_dir: Path) -> None:
    assert sorted(p.name for p in templates_dir.glob("*.j2")) == sorted(TEMPLATE_NAMES)


@pytest.mark.parametrize("provider", ["github", "gitlab", "local", "other"])
def test_render_produces_the_four_docs(
    sd, tmp_repo: Path, templates_dir: Path, provider: str
) -> None:
    state = _state(provider)
    result = sd.render_docs(tmp_repo, state, templates_dir)
    assert result["rendered"] == [
        "domain.md",
        "toolchain.md",
        "issue-tracker.md",
        "triage-labels.md",
    ]
    out_dir = tmp_repo / "docs" / "agents"
    for name in result["rendered"]:
        assert (out_dir / name).is_file()
    # "other" must fall back to the local tracker template, never a missing file.
    assert result["provider"] == ("local" if provider == "other" else provider)


def test_github_tracker_doc_uses_gh_cli(sd, tmp_repo: Path, templates_dir: Path) -> None:
    sd.render_docs(tmp_repo, _state("github"), templates_dir)
    text = (tmp_repo / "docs" / "agents" / "issue-tracker.md").read_text()
    assert "Issue tracker: GitHub" in text
    assert "gh issue create" in text


def test_gitlab_tracker_doc_uses_glab_cli(sd, tmp_repo: Path, templates_dir: Path) -> None:
    sd.render_docs(tmp_repo, _state("gitlab"), templates_dir)
    text = (tmp_repo / "docs" / "agents" / "issue-tracker.md").read_text()
    assert "Issue tracker: GitLab" in text
    assert "glab issue create" in text


def test_local_tracker_doc_has_no_hosted_cli(sd, tmp_repo: Path, templates_dir: Path) -> None:
    sd.render_docs(tmp_repo, _state("local"), templates_dir)
    text = (tmp_repo / "docs" / "agents" / "issue-tracker.md").read_text()
    assert "Issue tracker: Local" in text
    assert "gh " not in text


def test_domain_doc_points_at_canonical_glossary(sd, tmp_repo: Path, templates_dir: Path) -> None:
    sd.render_docs(tmp_repo, _state(), templates_dir)
    text = (tmp_repo / "docs" / "agents" / "domain.md").read_text()
    assert "GLOSSARY.md" in text
    assert "docs/adr/" in text
    assert "CONTEXT.md" not in text


def test_domain_doc_adds_map_line_only_for_multi_context(
    sd, tmp_repo: Path, templates_dir: Path
) -> None:
    sd.render_docs(tmp_repo, _state(has_context_map=False), templates_dir)
    single = (tmp_repo / "docs" / "agents" / "domain.md").read_text()
    assert "GLOSSARY-MAP.md" not in single

    sd.render_docs(tmp_repo, _state(has_context_map=True), templates_dir)
    multi = (tmp_repo / "docs" / "agents" / "domain.md").read_text()
    assert "GLOSSARY-MAP.md" in multi


def test_toolchain_doc_lists_every_tool_with_status_and_fallback(
    sd, tmp_repo: Path, templates_dir: Path
) -> None:
    state = _state()
    state["toolchain"]["oxlint"] = {
        "detected": False,
        "path": None,
        "purpose": "linter",
        "fallback": "ruff / eslint",
    }
    sd.render_docs(tmp_repo, state, templates_dir)
    text = (tmp_repo / "docs" / "agents" / "toolchain.md").read_text()
    for name in state["toolchain"]:
        assert f"| `{name}` |" in text
    assert "| `oxlint` | missing | ruff / eslint |" in text
    assert "| `uv` | found |" in text
    assert "| `rtk` | found | direct command execution |" in text


def test_triage_doc_has_the_canonical_five_labels(sd, tmp_repo: Path, templates_dir: Path) -> None:
    sd.render_docs(tmp_repo, _state(), templates_dir)
    text = (tmp_repo / "docs" / "agents" / "triage-labels.md").read_text()
    for label in ("needs-triage", "needs-info", "ready-for-agent", "ready-for-human", "wontfix"):
        assert f"| `{label}` | `{label}` |" in text


def test_render_dry_run_writes_nothing(sd, tmp_repo: Path, templates_dir: Path) -> None:
    result = sd.render_docs(tmp_repo, _state(), templates_dir, dry_run=True)
    assert result["rendered"]
    assert not (tmp_repo / "docs" / "agents" / "domain.md").exists()


def test_templates_honor_the_canonical_jinja_settings(
    sd, tmp_repo: Path, templates_dir: Path
) -> None:
    # keep_trailing_newline: every rendered doc ends with exactly one newline.
    sd.render_docs(tmp_repo, _state(), templates_dir)
    for name in ("domain.md", "toolchain.md", "issue-tracker.md", "triage-labels.md"):
        text = (tmp_repo / "docs" / "agents" / name).read_text()
        assert text.endswith("\n")
        assert not text.endswith("\n\n")
    # trim_blocks/lstrip_blocks: the toolchain table has no blank lines between rows.
    table = (tmp_repo / "docs" / "agents" / "toolchain.md").read_text()
    rows = [line for line in table.splitlines() if line.startswith("| `")]
    assert len(rows) == 10


def test_toolchain_doc_renders_the_rtk_section(sd, tmp_repo: Path, templates_dir: Path) -> None:
    sd.render_docs(tmp_repo, _state(), templates_dir)
    text = (tmp_repo / "docs" / "agents" / "toolchain.md").read_text()
    assert "## RTK (Token Killer)" in text
    assert "rtk rewrite" in text
    assert "| Version | 0.48.0 |" in text
    assert "| Active agent | pi |" in text
    assert "| Hook | installed |" in text
    for token in ("exclude_commands", "2,000 lines", "50 KB", "cat -vet", "cat -A"):
        assert token in text


def test_toolchain_doc_renders_without_rtk_state(sd, tmp_repo: Path, templates_dir: Path) -> None:
    state = _state()
    del state["rtk"]
    sd.render_docs(tmp_repo, state, templates_dir)  # StrictUndefined: must not raise
    text = (tmp_repo / "docs" / "agents" / "toolchain.md").read_text()
    assert "## RTK" not in text
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_env_yaml_rtk_section_is_agent_agnostic(sd) -> None:
    document = sd.build_env_document(_state())
    rtk = document["rtk"]
    assert set(rtk) == {"installed", "version"}
    assert rtk["installed"] is True
    assert rtk["version"] == "0.48.0"
    assert document["toolchain"]["rtk"] == {
        "detected": True,
        "fallback": "direct command execution",
    }
