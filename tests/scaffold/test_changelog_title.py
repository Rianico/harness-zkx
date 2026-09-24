"""Contract tests for the `# Changelog` title, proved against the real release plugin.

`@semantic-release/changelog` builds the next file as `notes + '\n' + currentContent`, and it
strips the existing title from `currentContent` *only* while the file starts with the
configured `changelogTitle`. So the title stays at the top only when two things hold at once:
`.releaserc.json` names the title, and `CHANGELOG.md` opens with exactly that line. Ship
either half alone and every release prepends its notes above the heading — with the config
alone it also strands a second, plugin-written title further down.

Both halves look locally reasonable and no byte-pin can see the pair, so the check runs the
plugin itself, twice. Node plus the installed plugin are required; without them this file
reports the contract as unproven instead of passing quietly.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"
REPO_ROOT = SKILL_DIR.parent.parent
CHANGELOG_PLUGIN = (
    REPO_ROOT / "node_modules" / "@semantic-release" / "changelog" / "lib" / "prepare.js"
)
TITLE = "# Changelog"

# The plugin is ESM, so the driver is a module too; `pathToFileURL` keeps the `@` in the
# package path from being read as a URL host.
DRIVER = """\
import {pathToFileURL} from "node:url";
const [pluginPath, cwd, configJson, notes] = process.argv.slice(2);
const {default: prepare} = await import(pathToFileURL(pluginPath).href);
await prepare(JSON.parse(configJson), {cwd, nextRelease: {notes}, logger: {log() {}}});
"""


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_changelog_title", SCRIPT)


def _title_lines(changelog: str) -> list[int]:
    """0-based line numbers that are exactly the title — a mention inside prose is not one."""
    return [n for n, line in enumerate(changelog.splitlines()) if line.strip() == TITLE]


def _plugin_config(cwd: Path) -> dict[str, str]:
    releaserc = json.loads((cwd / ".releaserc.json").read_text(encoding="utf-8"))
    for plugin in releaserc["plugins"]:
        if isinstance(plugin, list) and plugin[0] == "@semantic-release/changelog":
            return plugin[1]
    raise AssertionError("the shipped .releaserc.json no longer configures the changelog plugin")


# --- the shipped pair ---------------------------------------------------------


def test_template_opens_with_the_title():
    """The plugin trims before comparing, so only leading *blank* space and comments matter."""
    assert scaffold.CHANGELOG_MD.splitlines()[0] == TITLE
    assert scaffold.CHANGELOG_MD.endswith("\n")


def test_releaserc_names_the_title_the_plugin_must_rewrite():
    """`changelogTitle` has no default: unset, the plugin writes no title at all."""
    releaserc = json.loads(scaffold.RELEASERC_JSON)
    plugins = [p for p in releaserc["plugins"] if isinstance(p, list)]
    changelog = next(p for p in plugins if p[0] == "@semantic-release/changelog")
    assert changelog[1]["changelogTitle"] == TITLE


# --- the plugin, run twice on a freshly generated repo ------------------------


@pytest.mark.skipif(
    shutil.which("node") is None or not CHANGELOG_PLUGIN.is_file(),
    reason="needs node + node_modules/@semantic-release/changelog (npm ci)",
)
def test_release_keeps_the_title_at_the_top_and_the_notes_below_it(tmp_path: Path):
    scaffold.do_git(tmp_path, "demo", dry_run=False)
    driver = tmp_path / "run-changelog-plugin.mjs"
    driver.write_text(DRIVER, encoding="utf-8")
    config = json.dumps(_plugin_config(tmp_path))

    def release(notes: str) -> str:
        subprocess.run(  # noqa: S603 — argv is built here, node is a checked dependency
            ["node", str(driver), str(CHANGELOG_PLUGIN), str(tmp_path), config, notes],
            check=True,
            capture_output=True,
            text=True,
        )
        return (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")

    first = release("### Features\n\n* first feature (#1)")
    second = release("### Bug Fixes\n\n* second fix (#2)")

    for label, changelog in (("first", first), ("second", second)):
        assert _title_lines(changelog) == [0], (
            f"{label} release moved the title: {_title_lines(changelog)}"
        )
    assert "* second fix (#2)" in second and "* first feature (#1)" in second
    assert second.index("* second fix (#2)") < second.index("* first feature (#1)"), (
        "the newest release must sit directly under the title"
    )
    # the ledger block now follows the intro, so the footer is no longer the last line — the
    # invariant is that the release preserves it, not that it stays terminal.
    assert "documented in this file." in second, "release dropped the footer"
