"""Contract tests for the `# Changelog` title and the release plugin that rewrites the file.

The scaffold ships `scripts/release-changelog.mjs`, which promotes the curated `## [Unreleased]`
ledger in place. The title survives only when two things hold at once: the template opens with it,
and the config names the promote plugin rather than a regenerator — `@semantic-release/changelog`
built the next file as `notes + currentContent` and rewrote the title in place only when
`changelogTitle` was configured, which is why the scaffold no longer configures it.

These run the real plugin, because a config that names the right file still mangles the file if the
plugin is wrong.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import cast

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCAFFOLD = REPO_ROOT / "skills" / "scaffold"
TITLE = "# Changelog"
TEMPLATE = SCAFFOLD / "templates" / "git" / "CHANGELOG.md"
RELEASERC = SCAFFOLD / "templates" / "git" / ".releaserc.json"
PLUGIN = SCAFFOLD / "scripts" / "release-changelog.mjs"

DRIVER = """\
import {pathToFileURL} from "node:url";
const [pluginPath, cwd, version] = process.argv.slice(2);
const plugin = await import(pathToFileURL(pluginPath).href);
const context = {cwd, nextRelease: {version}, logger: {log() {}}};
await plugin.prepare({changelogFile: "CHANGELOG.md"}, context);
"""

ENTRY = "### Features\n\n* **demo:** a curated entry (#1)\n"


def _plugins() -> list[str | list[object]]:
    return cast(
        list[str | list[object]], json.loads(RELEASERC.read_text(encoding="utf-8"))["plugins"]
    )


def test_template_opens_with_the_title() -> None:
    assert TEMPLATE.read_text(encoding="utf-8").startswith(f"{TITLE}\n")


def test_releaserc_names_the_promote_plugin_and_no_regenerator() -> None:
    """One plugin owns the changelog: naming a regenerator alongside it would discard curation."""
    names = [plugin if isinstance(plugin, str) else plugin[0] for plugin in _plugins()]
    assert "./scripts/release-changelog.mjs" in names
    assert "@semantic-release/changelog" not in names
    assert "@semantic-release/release-notes-generator" not in names


def test_release_keeps_the_title_at_the_top_and_promotes_the_ledger(tmp_path: Path) -> None:
    if shutil.which("node") is None:
        pytest.skip("node is required to run the release plugin")

    template = TEMPLATE.read_text(encoding="utf-8")
    assert "## [Unreleased]" in template
    _ = (tmp_path / "CHANGELOG.md").write_text(
        template.replace("## [Unreleased]", f"## [Unreleased]\n\n{ENTRY}"), encoding="utf-8"
    )
    driver = tmp_path / "driver.mjs"
    _ = driver.write_text(DRIVER, encoding="utf-8")
    proc = subprocess.run(
        ["node", str(driver), str(PLUGIN), str(tmp_path), "1.1.0"], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr

    released = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert released.startswith(f"{TITLE}\n"), "the title must stay the first line"
    assert released.index("## [Unreleased]") < released.index("## [1.1.0]")
    assert ENTRY in released.split("## [1.1.0]")[1]
    assert "documented in this file." in released, "the release dropped the intro"
