"""Detector, migrator, workspace, and env.yaml contract tests for setup-lsz-skills.

The design contract under test: `CONTEXT.md` is deprecated and migrates to
`GLOSSARY.md` (never the reverse). Each test is falsifiable against a reverted
direction or a dropped step.

The RTK tests at the bottom are hermetic on purpose: the engine shells out to
`rtk` and `pi` when they exist, so those tests stub `shutil.which`,
`_run_capture`, and the home directory instead of touching the host.
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

# A PATH with no `rtk` and no `pi`: CLI runs then probe nothing on the host.
_NO_PROBE_PATH = {"PATH": "/usr/bin:/bin"}


def test_toolchain_covers_all_canonical_tools(sd) -> None:
    tools = sd.detect_toolchain()
    expected = {
        "adr",
        "fd",
        "rg",
        "eza",
        "wt",
        "uv",
        "oxlint",
        "oxfmt",
        "basedpyright",
        "rtk",
    }
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


def test_write_env_yaml_is_compact_yaml_not_json(sd, tmp_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(sd.shutil, "which", _no_binary)
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


def test_write_env_yaml_dry_run_writes_nothing(sd, tmp_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(sd.shutil, "which", _no_binary)
    state = sd.detect_environment(tmp_repo)
    result = sd.write_env_yaml(tmp_repo, state, dry_run=True)
    assert result["written"] is False
    assert not (tmp_repo / "docs" / "agents" / "env.yaml").exists()


def test_detect_environment_reports_deprecated_direction(sd, tmp_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(sd.shutil, "which", _no_binary)
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
    result = run_cli(tmp_repo, "detect", "--write-env", env=_NO_PROBE_PATH)
    assert result.returncode == 0, result.stderr
    loaded = yaml.safe_load((tmp_repo / "docs" / "agents" / "env.yaml").read_text())
    assert loaded["runtime"]["tmp"] == ".lsz/tmp"
    assert loaded["domain_layout"]["glossary"] == "GLOSSARY.md"


def test_cli_workspace_then_migrate_end_to_end(tmp_repo: Path, run_cli) -> None:
    _ = (tmp_repo / "CONTEXT.md").write_text("# Context", encoding="utf-8")
    assert run_cli(tmp_repo, "workspace", env=_NO_PROBE_PATH).returncode == 0
    assert (tmp_repo / ".lsz" / "tmp").is_dir()
    dry = run_cli(tmp_repo, "migrate", "--dry-run", env=_NO_PROBE_PATH)
    assert dry.returncode == 0, dry.stderr
    assert (tmp_repo / "CONTEXT.md").exists()  # dry-run touches nothing
    real = run_cli(tmp_repo, "migrate", env=_NO_PROBE_PATH)
    assert real.returncode == 0, real.stderr
    assert not (tmp_repo / "CONTEXT.md").exists()
    assert (tmp_repo / "GLOSSARY.md").is_file()


def test_cli_render_writes_all_docs(tmp_repo: Path, run_cli) -> None:
    result = run_cli(tmp_repo, "render", env=_NO_PROBE_PATH)
    assert result.returncode == 0, result.stderr
    docs = tmp_repo / "docs" / "agents"
    for name in ("domain.md", "toolchain.md", "issue-tracker.md", "triage-labels.md"):
        assert (docs / name).is_file()


def _no_binary(_name: str) -> None:
    """Stand-in for `shutil.which` that finds nothing (typed, so basedpyright stays clean)."""
    return None


def test_toolchain_resolves_repo_local_node_modules_bin(sd, tmp_repo: Path, monkeypatch) -> None:
    """oxlint/oxfmt are Node devDependencies: PATH alone reports a false gap."""
    monkeypatch.setattr(sd.shutil, "which", _no_binary)
    local_bin = tmp_repo / "node_modules" / ".bin"
    local_bin.mkdir(parents=True)
    for name in ("oxlint", "oxfmt"):
        binary = local_bin / name
        _ = binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        binary.chmod(0o755)

    tools = sd.detect_toolchain(tmp_repo)

    assert tools["oxlint"]["detected"] is True
    assert tools["oxlint"]["path"] == str(local_bin / "oxlint")
    assert tools["oxfmt"]["detected"] is True
    assert tools["uv"]["detected"] is False  # a missing tool stays missing


def test_toolchain_ignores_non_executable_local_bin(sd, tmp_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(sd.shutil, "which", _no_binary)
    local_bin = tmp_repo / "node_modules" / ".bin"
    local_bin.mkdir(parents=True)
    _ = (local_bin / "oxlint").write_text("not a binary", encoding="utf-8")

    tools = sd.detect_toolchain(tmp_repo)

    assert tools["oxlint"]["detected"] is False


def test_toolchain_without_cwd_does_not_probe_node_modules(sd, monkeypatch) -> None:
    monkeypatch.setattr(sd.shutil, "which", _no_binary)
    assert all(tool["detected"] is False for tool in sd.detect_toolchain().values())


# --- RTK integration -------------------------------------------------------

ALL_CANONICAL_EXCLUDES = [
    r"^cat\b",
    r"^head\b",
    r"^tail\b",
    r"^grep\b",
    r"^rg\b",
    r"^wc\b",
]

RTK_AGENT_ENV_VARS = (
    "PI_SESSION_ID",
    "PI_CODING_AGENT_DIR",
    "ANTIGRAVITY_AGENT",
    "ANTIGRAVITY_CONVERSATION_ID",
    "CLAUDECODE",
    "CLAUDE_CODE_CHILD_SESSION",
    "CODEX_SESSION_ID",
    "CODEX_HOME",
)


def _rtk_config_text(patterns: list[str]) -> str:
    """A `config.toml` body in rtk's own style: literal strings, one per line."""
    items = "".join(f"\n    '{pattern}'," for pattern in patterns)
    return f"[hooks]\nexclude_commands = [{items}\n]\n"


def _rtk_config_path(home: Path) -> Path:
    """Mirror `get_rtk_config_path()` against a fake HOME, per platform."""
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "rtk" / "config.toml"
    return home / ".config" / "rtk" / "config.toml"


def _rtk_cli_env(tmp_path: Path) -> tuple[dict[str, str], Path]:
    """Fake HOME/PATH for hermetic `rtk` CLI runs: stub binary, no real rtk or pi."""
    home = tmp_path / "home"
    config = _rtk_config_path(home)
    config.parent.mkdir(parents=True)
    _ = config.write_text(_rtk_config_text(ALL_CANONICAL_EXCLUDES), encoding="utf-8")
    hook = home / ".pi" / "agent" / "extensions" / "rtk.ts"
    hook.parent.mkdir(parents=True)
    _ = hook.write_text("// stub rtk hook\n", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "rtk"
    _ = stub.write_text(
        '#!/bin/sh\nif [ "$1" = "--version" ]; then echo "rtk 0.48.0"; fi\nexit 0\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return {"HOME": str(home), "PATH": f"{bin_dir}:/usr/bin:/bin"}, config


def test_canonical_exclude_commands_are_the_documented_six(sd) -> None:
    assert sd.CANONICAL_EXCLUDE_COMMANDS == ALL_CANONICAL_EXCLUDES


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, None),
        ({"PI_SESSION_ID": "s"}, "pi"),
        ({"PI_CODING_AGENT_DIR": "/d"}, "pi"),
        ({"ANTIGRAVITY_AGENT": "a"}, "agy"),
        ({"ANTIGRAVITY_CONVERSATION_ID": "c"}, "agy"),
        ({"CLAUDECODE": "1"}, "claude"),
        ({"CLAUDE_CODE_CHILD_SESSION": "c"}, "claude"),
        ({"CODEX_SESSION_ID": "s"}, "codex"),
        ({"CODEX_HOME": "/c"}, "codex"),
        # An exported-but-empty variable is a signal the shell cleared: treat it as absent.
        ({"PI_SESSION_ID": ""}, None),
        ({"PI_SESSION_ID": "", "CODEX_HOME": "/c"}, "codex"),
        # Precedence: pi > agy > claude > codex.
        ({"CODEX_HOME": "/c", "CLAUDECODE": "1"}, "claude"),
        ({"CODEX_HOME": "/c", "CLAUDECODE": "1", "ANTIGRAVITY_AGENT": "a"}, "agy"),
        (
            {
                "CODEX_HOME": "/c",
                "CLAUDECODE": "1",
                "ANTIGRAVITY_AGENT": "a",
                "PI_SESSION_ID": "p",
            },
            "pi",
        ),
    ],
)
def test_detect_active_agent(sd, env: dict[str, str], expected: str | None) -> None:
    assert sd.detect_active_agent(env) == expected


def test_detect_active_agent_reads_the_process_env(sd, monkeypatch) -> None:
    for name in RTK_AGENT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    assert sd.detect_active_agent() is None

    monkeypatch.setenv("PI_SESSION_ID", "session-1")
    assert sd.detect_active_agent() == "pi"


def test_merge_rtk_exclude_commands_creates_missing_config(sd, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sd.shutil, "which", _no_binary)  # no real `rtk config --create`
    config = tmp_path / "rtk" / "config.toml"
    assert not config.exists()

    result = sd.merge_rtk_exclude_commands(config)

    assert result["path"] == str(config)
    assert result["created"] is True
    assert result["added"] == ALL_CANONICAL_EXCLUDES
    parsed = tomllib.loads(config.read_text(encoding="utf-8"))
    assert parsed["hooks"]["exclude_commands"] == ALL_CANONICAL_EXCLUDES

    again = sd.merge_rtk_exclude_commands(config)

    assert again["created"] is False
    assert again["added"] == []
    assert (
        tomllib.loads(config.read_text(encoding="utf-8"))["hooks"]["exclude_commands"]
        == ALL_CANONICAL_EXCLUDES
    )


def test_merge_rtk_exclude_commands_preserves_custom_patterns(
    sd, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(sd.shutil, "which", _no_binary)
    config = tmp_path / "config.toml"
    original = (
        "[tracking]\nenabled = true\n\n"
        "# operator note: keep the custom filter\n"
        "[hooks]\nwarn = false\nexclude_commands = [\n    '^cat\\b',\n    '^my-tool',\n]\n\n"
        "[limits]\ngrep_max_results = 200\npassthrough_max_chars = 2000\n"
    )
    _ = config.write_text(original, encoding="utf-8")

    preview = sd.merge_rtk_exclude_commands(config, dry_run=True)

    assert preview["added"] == ALL_CANONICAL_EXCLUDES[1:]
    assert config.read_text(encoding="utf-8") == original  # dry-run writes nothing

    result = sd.merge_rtk_exclude_commands(config)

    assert result["created"] is False
    assert result["added"] == ALL_CANONICAL_EXCLUDES[1:]
    text = config.read_text(encoding="utf-8")
    parsed = tomllib.loads(text)
    assert parsed["hooks"]["exclude_commands"] == [
        "^cat\\b",
        "^my-tool",
        *ALL_CANONICAL_EXCLUDES[1:],
    ]
    assert parsed["hooks"]["warn"] is False
    assert parsed["tracking"] == {"enabled": True}
    assert parsed["limits"] == {"grep_max_results": 200, "passthrough_max_chars": 2000}
    for kept in (
        "# operator note: keep the custom filter",
        "[tracking]",
        "passthrough_max_chars = 2000",
    ):
        assert kept in text

    assert sd.merge_rtk_exclude_commands(config)["added"] == []


def test_rtk_check_clean_and_needs_apply_exit_codes(sd, tmp_path: Path, run_cli) -> None:
    env, config = _rtk_cli_env(tmp_path)

    clean = run_cli(tmp_path, "rtk", "--check", "--agent", "pi", env=env)

    assert clean.returncode == 0, (clean.stdout, clean.stderr)
    assert "status: clean" in clean.stdout

    _ = config.write_text(_rtk_config_text([r"^cat\b"]), encoding="utf-8")

    needs_apply = run_cli(tmp_path, "rtk", "--check", "--agent", "pi", env=env)

    assert needs_apply.returncode == 1, (needs_apply.stdout, needs_apply.stderr)
    assert "needs-apply" in needs_apply.stdout

    no_agent = run_cli(
        tmp_path, "rtk", "--check", env={**env, **dict.fromkeys(RTK_AGENT_ENV_VARS, "")}
    )

    assert no_agent.returncode == 2
    assert "--agent" in no_agent.stderr

    _ = config.write_text(_rtk_config_text(ALL_CANONICAL_EXCLUDES), encoding="utf-8")

    signalled = run_cli(tmp_path, "rtk", "--check", env={**env, "PI_SESSION_ID": "1"})

    assert signalled.returncode == 0, (signalled.stdout, signalled.stderr)
    assert "agent=pi" in signalled.stdout


def _fake_completed(returncode: int = 0, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def _apply_namespace(sd, *, dry_run: bool, remove_pix: bool):
    return sd.argparse.Namespace(
        check=False,
        apply=True,
        agent="pi",
        project=False,
        dry_run=dry_run,
        remove_pix_optimizer=remove_pix,
    )


def test_pix_optimizer_opt_in_removal(sd, tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    settings = home / ".pi" / "agent" / "settings.json"
    settings.parent.mkdir(parents=True)
    installed = '{"packages": ["npm:@xynogen/pix-optimizer"]}\n'
    _ = settings.write_text(installed, encoding="utf-8")
    config = tmp_path / "config.toml"
    _ = config.write_text(_rtk_config_text(ALL_CANONICAL_EXCLUDES), encoding="utf-8")

    calls: list[list[str]] = []

    def fake_run(
        cmd: list[str], timeout: float | None = None, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        if cmd[:2] == ["pi", "remove"]:
            _ = settings.write_text('{"packages": []}\n', encoding="utf-8")
        return _fake_completed()

    def fake_which(name: str) -> str:
        return f"/usr/bin/{name}"

    monkeypatch.setattr(sd, "_pi_settings_path", lambda: settings)
    monkeypatch.setattr(sd, "get_rtk_config_path", lambda: config)
    monkeypatch.setattr(sd.shutil, "which", fake_which)
    monkeypatch.setattr(sd, "_run_capture", fake_run)

    assert sd.detect_pix_optimizer() == {"detected": True, "source": "settings.json"}

    dry = sd._run_rtk_command(_apply_namespace(sd, dry_run=True, remove_pix=True), tmp_path)

    assert dry == 0
    assert calls == []
    assert sd.detect_pix_optimizer()["detected"] is True

    without_flag = sd._run_rtk_command(
        _apply_namespace(sd, dry_run=False, remove_pix=False), tmp_path
    )

    assert without_flag == 0
    assert any("init" in " ".join(call) for call in calls)
    assert not any("remove" in " ".join(call) for call in calls)
    assert settings.read_text(encoding="utf-8") == installed
    assert sd.detect_pix_optimizer()["detected"] is True

    calls.clear()
    with_flag = sd._run_rtk_command(_apply_namespace(sd, dry_run=False, remove_pix=True), tmp_path)

    assert with_flag == 0
    assert "pi remove npm:@xynogen/pix-optimizer" in [" ".join(call) for call in calls]
    assert sd.detect_pix_optimizer()["detected"] is False


def test_rtk_reports_an_unparseable_config_instead_of_success(tmp_path: Path, run_cli) -> None:
    env, config = _rtk_cli_env(tmp_path)
    unparseable = "hooks = [\n"  # unterminated array: not valid TOML
    _ = config.write_text(unparseable, encoding="utf-8")

    checked = run_cli(tmp_path, "rtk", "--check", "--agent", "pi", env=env)

    assert checked.returncode == 1, (checked.stdout, checked.stderr)
    assert "cannot parse" in checked.stdout

    preview = run_cli(tmp_path, "rtk", "--apply", "--agent", "pi", "--dry-run", env=env)

    assert preview.returncode == 0  # dry-run never writes, so it stays exit 0
    assert "merge would fail: cannot parse" in preview.stdout
    assert config.read_text(encoding="utf-8") == unparseable

    applied = run_cli(tmp_path, "rtk", "--apply", "--agent", "pi", env=env)

    assert applied.returncode == 1, (applied.stdout, applied.stderr)
    assert "cannot parse" in (applied.stdout + applied.stderr)
    assert config.read_text(encoding="utf-8") == unparseable


def test_rtk_apply_reports_a_failed_config_creation(tmp_path: Path, run_cli) -> None:
    env, config = _rtk_cli_env(tmp_path)
    config.unlink()  # fresh machine: no config.toml yet
    inline = "hooks = { exclude_commands = [] }\n"
    stub = tmp_path / "bin" / "rtk"
    _ = stub.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo "rtk 0.48.0"; fi\n'
        'if [ "$1" = "config" ] && [ "$2" = "--create" ]; then\n'
        "  echo 'hooks = { exclude_commands = [] }' > \"$RTK_CREATE_PATH\"\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )

    applied = run_cli(
        tmp_path, "rtk", "--apply", "--agent", "pi", env={**env, "RTK_CREATE_PATH": str(config)}
    )

    assert applied.returncode == 1, (applied.stdout, applied.stderr)
    assert "cannot write" in (applied.stdout + applied.stderr)
    assert config.read_text(encoding="utf-8") == inline
