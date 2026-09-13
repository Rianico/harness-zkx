"""Contract tests for the scaffold's changelog bullet style.

`CHANGELOG.md` has two writers that already agree and two normalizers that do not:
`@semantic-release/changelog` inserts the preset's `*` notes and
`scripts/changelog-unreleased.py` emits `*`, while pi-lens runs `markdownlint-cli2 --fix`
(MD004, stock `consistent` — keyed on the first bullet in the file) and `oxfmt` rewrites
bullets to `-`. The shipped file therefore pins MD004 to `asterisk` and tells the JS/TS
formatter to skip it. These tests hold both halves: delete either and the whole file
rewrites itself on the next markdown touch.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"
SYNC_SCRIPT = SKILL_DIR / "scripts" / "changelog-unreleased.py"

PIN_RE = re.compile(r"markdownlint-configure-file\s*(\{.*?\})\s*-->", re.DOTALL)
BULLET_FOR_STYLE = {"asterisk": "*", "dash": "-", "plus": "+"}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_bullets", SCRIPT)
sync_mod = _load("changelog_unreleased_mod_bullets", SYNC_SCRIPT)


def _pinned_style(changelog: str) -> str:
    match = PIN_RE.search(changelog)
    assert match is not None, "no markdownlint-configure-file pin in the shipped CHANGELOG.md"
    config = json.loads(match.group(1))
    return config["MD004"]["style"]


# --- the shipped file pins the style -----------------------------------------


def test_changelog_template_pins_md004_to_asterisk():
    assert _pinned_style(scaffold.CHANGELOG_MD) == "asterisk"


def test_generated_changelog_carries_the_pin(tmp_path: Path):
    """The pin reaches generated repos — `--flavor git` writes `CHANGELOG_MD` verbatim."""
    scaffold.write_generated(tmp_path / "CHANGELOG.md", scaffold.CHANGELOG_MD, dry_run=False)
    assert _pinned_style((tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")) == "asterisk"


# --- the writers emit the pinned style ---------------------------------------


def test_writer_bullets_match_the_pin():
    """Every entry `update` generates starts with the bullet the pin enforces."""
    bullet = BULLET_FOR_STYLE[_pinned_style(scaffold.CHANGELOG_MD)]
    sections = sync_mod.commits_to_sections(
        [
            ("feat(alpha): add an alpha", ""),
            ("fix: repair the thing", ""),
            ("feat!: drop the legacy field", ""),
        ]
    )
    entries = [entry for group in sections.values() for entry in group]
    assert entries, "expected generated entries"
    assert all(entry.startswith(f"{bullet} ") for entry in entries), entries


# --- the JS/TS formatter is told to skip the file ----------------------------


def test_oxfmt_ignores_the_changelog():
    config = json.loads(scaffold.OXFMT_JSON)
    assert "CHANGELOG.md" in config["ignorePatterns"]
