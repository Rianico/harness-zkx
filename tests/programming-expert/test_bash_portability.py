"""Tests for bash portability guidance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_bash_expert_portability_documents_cat_a() -> None:
    skill_path = (
        REPO_ROOT / "skills" / "programming-expert" / "subskills" / "bash-expert" / "SKILL.md"
    )
    content = skill_path.read_text(encoding="utf-8")
    assert "cat -A" in content
    assert "cat -vet" in content
    assert "gcat -A" in content
    assert "od -c" in content
    assert "xxd" in content


def test_bash_rules_documents_cat_portability() -> None:
    rule_path = REPO_ROOT / "rules" / "bash" / "bash-rules.md"
    content = rule_path.read_text(encoding="utf-8")
    assert "cat -vet" in content
    assert "cat -A" in content


def test_tool_preferences_documents_cat_portability() -> None:
    pref_path = REPO_ROOT / "rules" / "common" / "tool-preferences.md"
    content = pref_path.read_text(encoding="utf-8")
    assert "cat -A" in content
    assert "cat -vet" in content
    assert "gcat -A" in content
    assert "#176" in content


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS BSD cat specific verification")
def test_darwin_bsd_cat_behavior() -> None:
    """Empirical verification: BSD cat rejects -A, while cat -vet works."""
    proc_bad = subprocess.run(
        ["/bin/cat", "-A"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_bad.returncode != 0
    assert "illegal option" in proc_bad.stderr

    proc_good = subprocess.run(
        ["/bin/cat", "-vet"],
        input="hello\tworld\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_good.returncode == 0
    assert proc_good.stdout == "hello^Iworld$\n"
