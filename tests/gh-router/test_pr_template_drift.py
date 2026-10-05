"""Drift guard relocated from scaffold (T3 retired its byte pin).

The repo's installed `.github/pull_request_template.md` must equal the gh-router canonical
byte-for-byte; without this guard the two drift silently now that scaffold no longer owns
either side of the pair.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INSTALLED = REPO_ROOT / ".github/pull_request_template.md"
CANONICAL = REPO_ROOT / "skills/gh-router/references/pull_request_template.md"


def test_repo_template_matches_canonical_bytes() -> None:
    fix = "skills/gh-router/scripts/install-template.sh --target . --force"
    assert INSTALLED.is_file(), (
        f"{INSTALLED} missing — refresh it with: {fix}"
    )
    assert CANONICAL.is_file(), (
        f"{CANONICAL} missing — the canonical template is the drift-guard source of truth"
    )
    assert INSTALLED.read_bytes() == CANONICAL.read_bytes(), (
        f"{INSTALLED} drifted from {CANONICAL} — refresh the installed copy with: {fix}"
    )
