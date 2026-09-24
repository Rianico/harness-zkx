"""The release promotes the curated ledger, and the notes are what a human wrote.

`@semantic-release/changelog` regenerated notes from commit subjects and prepended them *above*
`## [Unreleased]`, so the curated ledger was discarded exactly when it mattered. `scripts/release-changelog.mjs`
replaces it: `generateNotes` returns the curated block and `prepare` promotes it in place.

This runs the real plugin, because the failure it guards against is invisible to a byte-pin — a
config that names the right file still regenerates from commits if the plugin is wrong.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "scripts" / "release-changelog.mjs"

DRIVER = """\
import {pathToFileURL} from "node:url";
const [pluginPath, cwd, configJson, version] = process.argv.slice(2);
const plugin = await import(pathToFileURL(pluginPath).href);
const config = JSON.parse(configJson);
const context = {cwd, nextRelease: {version}, logger: {log() {}}};
const notes = await plugin.generateNotes(config, context);
await plugin.prepare(config, context);
process.stdout.write(notes);
"""

CHANGELOG = """\
# Changelog

Intro line.

## [Unreleased]

### Features
* **demo:** a curated entry (#42)

## [1.0.0] - 2025-01-01

### Bug Fixes
* **demo:** an older entry (#7)
"""


@pytest.fixture
def release(tmp_path: Path) -> tuple[str, str]:
    """Run the real plugin over a fixture ledger and return (notes, promoted changelog)."""
    if shutil.which("node") is None:
        pytest.skip("node is required to run the release plugin")

    _ = (tmp_path / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    driver = tmp_path / "driver.mjs"
    _ = driver.write_text(DRIVER, encoding="utf-8")
    proc = subprocess.run(
        ["node", str(driver), str(PLUGIN), str(tmp_path), json.dumps({}), "1.1.0"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout, (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")


def test_promotion_keeps_the_curated_text(release: tuple[str, str]):
    """The entry a human wrote is what ends up under the released heading."""
    _, changelog = release
    assert re.search(r"^## \[1\.1\.0\] - \d{4}-\d{2}-\d{2}$", changelog, re.M)
    promoted = changelog.split("## [1.1.0]")[1].split("## [Unreleased]")[0]
    assert "* **demo:** a curated entry (#42)" in promoted


def test_unreleased_reopens_empty_above_the_release(release: tuple[str, str]):
    """Keep-a-Changelog order: the working area sits above the newest release, not below it."""
    _, changelog = release
    assert changelog.index("## [Unreleased]") < changelog.index("## [1.1.0]")
    body = changelog.split("## [Unreleased]")[1].split("## [1.1.0]")[0]
    assert body.strip() == ""


def test_earlier_releases_survive(release: tuple[str, str]):
    _, changelog = release
    assert "* **demo:** an older entry (#7)" in changelog
    assert changelog.index("## [1.1.0]") < changelog.index("## [1.0.0]")


def test_notes_are_the_curated_block_not_commit_subjects(release: tuple[str, str]):
    """The whole point: release notes come from the ledger, so curation is what readers see."""
    notes, _ = release
    assert "* **demo:** a curated entry (#42)" in notes
    assert "1.0.0" not in notes


def test_the_intro_survives(release: tuple[str, str]):
    _, changelog = release
    assert changelog.startswith("# Changelog\n\nIntro line.")


def test_an_empty_ledger_releases_without_failing(tmp_path: Path):
    """A landing that carries no entry must not block a release on a bookkeeping gap."""
    if shutil.which("node") is None:
        pytest.skip("node is required to run the release plugin")

    _ = (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2025-01-01\n", encoding="utf-8"
    )
    driver = tmp_path / "driver.mjs"
    _ = driver.write_text(DRIVER, encoding="utf-8")
    proc = subprocess.run(
        ["node", str(driver), str(PLUGIN), str(tmp_path), json.dumps({}), "1.1.0"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "No user-facing changes."
    assert "## [1.1.0]" in (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")


def test_a_ledger_without_the_heading_fails_loudly(tmp_path: Path):
    if shutil.which("node") is None:
        pytest.skip("node is required to run the release plugin")

    _ = (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    driver = tmp_path / "driver.mjs"
    _ = driver.write_text(DRIVER, encoding="utf-8")
    proc = subprocess.run(
        ["node", str(driver), str(PLUGIN), str(tmp_path), json.dumps({}), "1.1.0"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "no '## [Unreleased]' heading" in proc.stderr
