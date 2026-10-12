"""Detector, migrator, workspace, and env.yaml contract tests for setup-lsz-skills.

The design contract under test: `CONTEXT.md` is deprecated and migrates to
`GLOSSARY.md` (never the reverse). Each test is falsifiable against a reverted
direction or a dropped step.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def test_toolchain_covers_all_canonical_tools(sd) -> None:
    tools = sd.detect_toolchain()
    expected = {"adr", "fd", "rg", "eza", "wt", "uv", "oxlint", "oxfmt", "basedpyright"}
    assert expected == set(tools)
    for tool in tools.values():
        assert set(tool) == {"detected", "path", "purpose", "fallback"}


def test_uv_detected_in_harness_env(sd) -> None:
    assert sd.detect_toolchain()["uv"]["detected"] is True


def test_detect_stale_files_finds_deprecated_context(sd, tmp_repo: Path) -> None:
    _ = (tmp_repo / "CONTEXT.md").write_text("# Context", encoding="utf-8")
    _ = (tmp_repo / "CONTEXT-MAP.md").write_text("# Map", encoding="utf-8")
    stale = sd.detect_stale_files(tmp_repo)
    assert stale == {"CONTEXT.md": "GLOSSARY.md", "CONTEXT-MAP.md": "GLOSSARY-MAP.md"}


def test_detect_stale_files_ignores_canonical_glossary(sd, tmp_repo: Path) -> None:
    _ = (tmp_repo / "GLOSSARY.md").write_text("# Glossary", encoding="utf-8")
    assert sd.detect_stale_files(tmp_repo) == {}


def test_migration_renames_context_to_glossary(sd, tmp_repo: Path) -> None:
    _ = (tmp_repo / "CONTEXT.md").write_text("# Domain Glossary\nTerms here", encoding="utf-8")
    result = sd.execute_migration(tmp_repo, dry_run=False, init_adr=False)
    assert not (tmp_repo / "CONTEXT.md").exists()
    assert (tmp_repo / "GLOSSARY.md").read_text().startswith("# Domain Glossary")
    assert {"source": "CONTEXT.md", "target": "GLOSSARY.md"} in result["migrated"]
    assert result["merge_required"] == []


def test_migration_dry_run_touches_nothing(sd, tmp_repo: Path) -> None:
    _ = (tmp_repo / "CONTEXT.md").write_text("# Context", encoding="utf-8")
    result = sd.execute_migration(tmp_repo, dry_run=True, init_adr=False)
    assert (tmp_repo / "CONTEXT.md").exists()
    assert not (tmp_repo / "GLOSSARY.md").exists()
    assert result["migrated"]  # reports intent without acting


def test_migration_stages_merge_when_both_exist_and_never_clobbers(sd, tmp_repo: Path) -> None:
    _ = (tmp_repo / "CONTEXT.md").write_text("# Legacy terms", encoding="utf-8")
    _ = (tmp_repo / "GLOSSARY.md").write_text("# Current terms", encoding="utf-8")
    result = sd.execute_migration(tmp_repo, dry_run=False, init_adr=False)
    # Existing canonical content survives untouched.
    assert (tmp_repo / "GLOSSARY.md").read_text() == "# Current terms"
    assert result["migrated"] == []
    assert len(result["merge_required"]) == 1
    staged = result["merge_required"][0]["staged_as"]
    assert (tmp_repo / staged).read_text() == "# Legacy terms"


def test_migration_creates_adr_dir_when_enabled(sd, tmp_repo: Path) -> None:
    _ = (tmp_repo / "CONTEXT.md").write_text("# Context", encoding="utf-8")
    result = sd.execute_migration(tmp_repo, dry_run=False, init_adr=True)
    assert (tmp_repo / "docs" / "adr").is_dir()
    assert result["adr"]["exists"] is True


def test_project_name_prefers_remote_then_pyproject_then_package_then_dir(
    sd, git_repo: Path, tmp_repo: Path
) -> None:
    assert sd.detect_project_name(git_repo) == "widget"

    _ = (tmp_repo / "pyproject.toml").write_text(
        '[project]\nname = "from-pyproject"\n', encoding="utf-8"
    )
    assert sd.detect_project_name(tmp_repo) == "from-pyproject"

    (tmp_repo / "pyproject.toml").unlink()
    _ = (tmp_repo / "package.json").write_text('{"name": "from-package"}', encoding="utf-8")
    assert sd.detect_project_name(tmp_repo) == "from-package"


def test_project_name_falls_back_to_directory(sd, tmp_repo: Path) -> None:
    assert sd.detect_project_name(tmp_repo) == tmp_repo.resolve().name


def test_git_remote_classifies_provider(sd, git_repo: Path, tmp_repo: Path) -> None:
    assert sd.detect_git_remote(git_repo)["provider"] == "github"
    assert sd.detect_git_remote(tmp_repo)["provider"] == "local"
    assert sd.detect_git_remote(tmp_repo)["remote_url"] is None


def test_workspace_creates_tmp_and_ignores_it(sd, tmp_repo: Path) -> None:
    result = sd.ensure_lsz_workspace(tmp_repo)
    assert (tmp_repo / ".lsz" / "tmp").is_dir()
    ignore = (tmp_repo / ".gitignore").read_text()
    assert ".lsz/*" in ignore
    assert "!.lsz/config.yaml" in ignore
    assert result["created_dir"] is True


def test_workspace_is_idempotent(sd, tmp_repo: Path) -> None:
    sd.ensure_lsz_workspace(tmp_repo)
    second = sd.ensure_lsz_workspace(tmp_repo)
    assert second["created_dir"] is False
    assert second["added_ignore_lines"] == []
    body = (tmp_repo / ".gitignore").read_text()
    assert body.count(".lsz/*") == 1


def test_write_env_yaml_is_compact_yaml_not_json(sd, tmp_repo: Path) -> None:
    _ = (tmp_repo / "CONTEXT.md").write_text("# Context", encoding="utf-8")
    state = sd.detect_environment(tmp_repo)
    sd.write_env_yaml(tmp_repo, state)
    out = tmp_repo / "docs" / "agents" / "env.yaml"
    assert out.is_file()
    text = out.read_text()
    assert "{" not in text.split("stale_files")[0]  # block style, not inline JSON
    loaded = yaml.safe_load(text)
    assert loaded["provider"] in {"github", "gitlab", "local", "other"}
    assert loaded["domain_layout"]["glossary"] == "GLOSSARY.md"
    assert loaded["domain_layout"]["stale_files"] == {"CONTEXT.md": "GLOSSARY.md"}
    assert loaded["runtime"]["tmp"] == ".lsz/tmp"
    assert "adr" in loaded["toolchain"] and "basedpyright" in loaded["toolchain"]


def test_write_env_yaml_dry_run_writes_nothing(sd, tmp_repo: Path) -> None:
    state = sd.detect_environment(tmp_repo)
    result = sd.write_env_yaml(tmp_repo, state, dry_run=True)
    assert result["written"] is False
    assert not (tmp_repo / "docs" / "agents" / "env.yaml").exists()


def test_detect_environment_reports_deprecated_direction(sd, tmp_repo: Path) -> None:
    _ = (tmp_repo / "AGENTS.md").write_text("# Agents", encoding="utf-8")
    _ = (tmp_repo / "CONTEXT.md").write_text("# Context", encoding="utf-8")
    (tmp_repo / "docs" / "adr").mkdir(parents=True)
    (tmp_repo / "docs" / "agents").mkdir(parents=True)
    state = sd.detect_environment(tmp_repo)
    assert state["steering_file"] == "AGENTS.md"
    assert state["has_context_md"] is True
    assert state["has_adr_dir"] is True
    assert state["stale_files"] == {"CONTEXT.md": "GLOSSARY.md"}


def test_cli_detect_write_env(tmp_repo: Path, run_cli) -> None:
    result = run_cli(tmp_repo, "detect", "--write-env")
    assert result.returncode == 0, result.stderr
    loaded = yaml.safe_load((tmp_repo / "docs" / "agents" / "env.yaml").read_text())
    assert loaded["runtime"]["tmp"] == ".lsz/tmp"
    assert loaded["domain_layout"]["glossary"] == "GLOSSARY.md"


def test_cli_workspace_then_migrate_end_to_end(tmp_repo: Path, run_cli) -> None:
    _ = (tmp_repo / "CONTEXT.md").write_text("# Context", encoding="utf-8")
    assert run_cli(tmp_repo, "workspace").returncode == 0
    assert (tmp_repo / ".lsz" / "tmp").is_dir()
    dry = run_cli(tmp_repo, "migrate", "--dry-run")
    assert dry.returncode == 0, dry.stderr
    assert (tmp_repo / "CONTEXT.md").exists()  # dry-run touches nothing
    real = run_cli(tmp_repo, "migrate")
    assert real.returncode == 0, real.stderr
    assert not (tmp_repo / "CONTEXT.md").exists()
    assert (tmp_repo / "GLOSSARY.md").is_file()


def test_cli_render_writes_all_docs(tmp_repo: Path, run_cli) -> None:
    result = run_cli(tmp_repo, "render")
    assert result.returncode == 0, result.stderr
    docs = tmp_repo / "docs" / "agents"
    for name in ("domain.md", "toolchain.md", "issue-tracker.md", "triage-labels.md"):
        assert (docs / name).is_file()
