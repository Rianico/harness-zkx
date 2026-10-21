"""Dispatch preview shows the curated release notes, never the analyzed commit body (#284).

`semantic-release --dry-run` logs each analyzed commit message with its body under
`Analyzing commit: …`, then prints the release notes after a `Release note for version`
marker. A bare heading filter therefore reprinted the commit body's own contract headings
(`## Summary`, `## Root Cause`, …) above the real notes. These cases drive the real
`dispatch.sh` against a scripted semantic-release trace, so the assertion is on what the
operator sees at the last checkpoint before an irreversible publish.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DISPATCH = REPO_ROOT / "skills/gh-router/subskills/gh-release/scripts/dispatch.sh"

FAKE_GH = """#!/usr/bin/env bash
if [[ "$1 $2" == "auth token" ]]; then echo fake-token; fi
exit 0
"""

FAKE_NPX = """#!/usr/bin/env bash
cat "$FAKE_TRACE_FILE"
exit 0
"""

# Excerpt of a real v25 dry-run: the commit body's contract headings are part of the
# `Analyzing commit:` log message; the curated notes follow the release-note marker.
TRACE_WITH_COMMIT_BODY = """\
[12:19:56 AM] [semantic-release] › ℹ  Running semantic-release version 25.0.9
[12:19:56 AM] [semantic-release] [@semantic-release/commit-analyzer] › ℹ  Analyzing commit: fix(bash-view): fail closed on compound chains (#164)

## Summary
Compound `&&` chains no longer crash the bash view.
## What Changed
- `compound-andor-operand` fails a chain closed.
## Root Cause
`AndOr.commands` holds any statement kind.
## Evidence
Session replay of 248 bash results.
[12:19:56 AM] [semantic-release] [@semantic-release/commit-analyzer] › ℹ  The commit should not trigger a release
[12:19:56 AM] [semantic-release] [@semantic-release/commit-analyzer] › ℹ  Analysis of 2 commits complete: patch release
[12:19:56 AM] [semantic-release] › ℹ  The next release version is 2.13.2
[12:19:56 AM] [semantic-release] › ✔  Published release 2.13.2 on default channel
[12:19:56 AM] [semantic-release] › ℹ  Release note for version 2.13.2:
### Features

    * **diagnostics:** internal failures are recorded in a log file (#164)

### Bug Fixes

    * **bash-view:** a `&&` chain whose operand is a compound statement no longer crashes (#164)
"""

# Older semantic-release trace with no release-note marker: the fallback must keep the
# pre-existing condensed rendering.
TRACE_WITHOUT_MARKER = """\
[12:19:56 AM] [semantic-release] › ℹ  The next release version is 1.2.3

## 1.2.3
### Features
* add thing
"""

# A trace that only carries the commit body (no notes, no marker): nothing here is a
# release note, so no heading may reach the preview.
TRACE_COMMIT_BODY_ONLY = """\
[12:19:56 AM] [semantic-release] › ℹ  The next release version is 1.2.3
[12:19:56 AM] [semantic-release] [@semantic-release/commit-analyzer] › ℹ  Analyzing commit: fix(x): thing (#1)

## Summary
No.
## Root Cause
No.
"""

CONTRACT_HEADINGS = ("## Summary", "## What Changed", "## Root Cause", "## Evidence")


def _fake_env(tmp_path: Path, trace: str) -> dict[str, str]:
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir()
    trace_file = tmp_path / "trace.log"
    _ = trace_file.write_text(trace, encoding="utf-8")
    for name, body in (("gh", FAKE_GH), ("npx", FAKE_NPX)):
        path = mock_bin / name
        _ = path.write_text(body, encoding="utf-8")
        _ = path.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
        "FAKE_TRACE_FILE": str(trace_file),
        "NO_COLOR": "1",
    }
    _ = env.pop("GH_RELEASE_QUIET", None)
    return env


def _preview(tmp_path: Path, trace: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(DISPATCH), "--dry-run"],
        cwd=tmp_path,
        env=_fake_env(tmp_path, trace),
        capture_output=True,
        text=True,
        check=False,
    )


def test_preview_shows_curated_notes_without_commit_body_headings(tmp_path: Path) -> None:
    result = _preview(tmp_path, TRACE_WITH_COMMIT_BODY)
    combined = result.stdout + result.stderr

    assert result.returncode == 0, f"preview should succeed:\n{combined}"
    assert "next version: v2.13.2" in combined, f"version line changed:\n{combined}"
    for heading in CONTRACT_HEADINGS:
        assert heading not in combined, f"commit-body heading leaked into the preview:\n{combined}"
    assert "### Features" in combined, f"curated features section missing:\n{combined}"
    assert "### Bug Fixes" in combined, f"curated fixes section missing:\n{combined}"
    assert (
        "    * **diagnostics:** internal failures are recorded in a log file (#164)" in combined
    ), f"curated bullet did not render verbatim:\n{combined}"
    assert (
        "    * **bash-view:** a `&&` chain whose operand is a compound statement no longer"
        " crashes (#164)" in combined
    ), f"curated bullet did not render verbatim:\n{combined}"
    assert "full trace: GITHUB_TOKEN=$(gh auth token) npx semantic-release --dry-run" in combined, (
        f"full trace hint missing:\n{combined}"
    )


def test_preview_keeps_condensed_notes_for_a_trace_without_the_marker(tmp_path: Path) -> None:
    """Older semantic-release output has no release-note marker; keep its prior rendering."""
    result = _preview(tmp_path, TRACE_WITHOUT_MARKER)
    combined = result.stdout + result.stderr

    assert result.returncode == 0, f"preview should succeed:\n{combined}"
    assert "next version: v1.2.3" in combined, f"version line changed:\n{combined}"
    assert "### Features" in combined, f"notes heading missing:\n{combined}"
    assert "* add thing" in combined, f"notes bullet missing:\n{combined}"


def test_preview_prints_no_heading_from_a_commit_body_without_notes(tmp_path: Path) -> None:
    result = _preview(tmp_path, TRACE_COMMIT_BODY_ONLY)
    combined = result.stdout + result.stderr

    assert result.returncode == 0, f"preview should succeed:\n{combined}"
    for heading in CONTRACT_HEADINGS:
        assert heading not in combined, f"commit-body heading leaked into the preview:\n{combined}"
