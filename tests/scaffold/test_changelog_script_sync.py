"""The scaffold's changelog script must never drift from the canonical copy.

`converge-tasks` gates on `scripts/changelog-unreleased.py check`; the scaffold
ships that script to every target repo, so a template missing the `check`
subcommand blocks every downstream run with an argparse usage error (#47).
"""

import importlib.util
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
