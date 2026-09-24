"""The scaffold's changelog script must never drift from the canonical copy, and the ledger
it ships must pass the gate the scaffold ships with it.

`converge-tasks` gates on `scripts/changelog-unreleased.py check`; the scaffold
ships that script to every target repo, so a template missing the `check`
subcommand blocks every downstream run with an argparse usage error (#47).
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"
CANONICAL = REPO_ROOT / "scripts" / "changelog-unreleased.py"
SHIPPED = SKILL_DIR / "scripts" / "changelog-unreleased.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_changelog_sync", SCRIPT)


def test_shipped_script_is_byte_identical_to_canonical():
    assert SHIPPED.read_bytes() == CANONICAL.read_bytes(), (
        "sync skills/scaffold/scripts/changelog-unreleased.py with "
        "scripts/changelog-unreleased.py — the gate calls `check`"
    )


def test_shipped_script_supports_check():
    shipped = _load("shipped_changelog", SHIPPED)
    assert hasattr(shipped, "check_changelog"), "shipped copy lost the `check` subcommand"
    assert hasattr(shipped, "render_updated_changelog"), (
        "`check` must share `update`'s pure render so the two can never disagree"
    )


def test_git_flavor_ships_the_check_capable_bytes(tmp_path):
    scaffold.do_git(tmp_path, "demo", dry_run=False)
    shipped = (tmp_path / "scripts" / "changelog-unreleased.py").read_text(encoding="utf-8")
    assert '"check"' in shipped or "'check'" in shipped
    assert shipped == CANONICAL.read_text(encoding="utf-8")


def _scaffolded_repo(tmp_path):
    """A `git`-flavor scaffold with one commit, on a topic branch."""
    scaffold.do_git(tmp_path, "demo", dry_run=False)
    git = ["git", "-C", str(tmp_path), "-c", "user.email=t@example.com", "-c", "user.name=t"]
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "chore: init"]):
        subprocess.run([*git, *args], check=True, capture_output=True)
    subprocess.run([*git, "switch", "-qc", "feat/x"], check=True, capture_output=True)
    return git


def _floor(tmp_path):
    return subprocess.run(
        [
            sys.executable,
            "scripts/changelog-gate.py",
            "ledger",
            "--pr",
            "1",
            "--landing",
            "squash",
            "--base",
            "main",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def test_scaffolded_ledger_passes_the_floor(tmp_path):
    """A scaffolded repo must pass the floor the scaffold ships, before its first entry.

    The template ships the gate, so it must ship the ledger that gate reads: with no
    `## [Unreleased]` block the first PR fails `no '## [Unreleased]' block to check`.
    """
    git = _scaffolded_repo(tmp_path)
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        changelog.read_text(encoding="utf-8") + "\n### Features\n\n* **demo:** a thing (#1)\n",
        encoding="utf-8",
    )
    subprocess.run([*git, "add", "-A"], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-q", "-m", "docs: ledger"], check=True, capture_output=True)
    result = _floor(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_scaffolded_gate_names_the_accepted_sections(tmp_path):
    """A Keep-a-Changelog heading is rejected — the ledger's vocabulary is the commit types — and
    the message must name that vocabulary, or the first entry a user writes is unactionable."""
    git = _scaffolded_repo(tmp_path)
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        changelog.read_text(encoding="utf-8") + "\n### Added\n\n* **demo:** a thing (#1)\n",
        encoding="utf-8",
    )
    subprocess.run([*git, "add", "-A"], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-q", "-m", "docs: ledger"], check=True, capture_output=True)
    result = _floor(tmp_path)
    report = result.stdout + result.stderr
    assert result.returncode == 1, report
    assert "unknown section '### Added'" in report
    assert "Features" in report, "the rejection must name the accepted sections"
