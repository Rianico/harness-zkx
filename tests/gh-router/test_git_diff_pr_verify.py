"""Unit tests for the git-diff-digest pr and verify surface (scripts/brief.py).

Synthetic repos only: no network, no gh auth. The pr view resolves through
``skills/gh-router/lib/range_authority.py`` and adds the landing block on top
of the range payload; verify recomputes the range fingerprint and compares it
field by field.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = (
    REPO_ROOT / "skills" / "gh-router" / "subskills" / "git-diff-digest" / "scripts" / "brief.py"
)

_BANNED_RE = re.compile(r"\b(title|squash|risk)\b", re.IGNORECASE)
_FP_RE = re.compile(r"[0-9a-f]{64}")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _seed_repo(repo: Path) -> dict[str, str]:
    """Build a diverged feature branch with conventional commits."""
    _ = _git(repo, "init")
    _ = _git(repo, "config", "user.name", "Tester Author")
    _ = _git(repo, "config", "user.email", "tester@example.com")
    _ = _git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "src").mkdir()
    _ = (repo / "src" / "app.py").write_text("print('v1')\n", encoding="utf-8")
    _ = (repo / "src" / "parser.py").write_text("def parse(x):\n    return x\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "chore: base commit")
    base = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _ = _git(repo, "checkout", "-b", "feature")
    _ = (repo / "src" / "app.py").write_text("print('v1')\nprint('v2')\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "feat: add parser")
    first = _git(repo, "rev-parse", "HEAD")
    _ = (repo / "tests").mkdir()
    _ = (repo / "tests" / "test_app.py").write_text(
        "def test_v2():\n    assert True\n", encoding="utf-8"
    )
    _ = _git(repo, "add", ".")
    _ = _git(
        repo,
        "commit",
        "-m",
        f"fix: handle empty input\n\nCovers the empty case.\n\nRefs #12, follow-up to {first[:7]}.",
    )
    _ = (repo / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
    _ = (repo / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "feat(api)!: drop legacy field\n\nBREAKING CHANGE: legacy gone.")
    _ = _git(repo, "mv", "src/parser.py", "src/scanner.py")
    _ = _git(repo, "commit", "-m", "refactor: rename parser module")
    _ = _git(repo, "checkout", base)
    _ = (repo / "docs").mkdir()
    _ = (repo / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "docs: tweak guide")
    return {"base": base, "first": first}


def _run_brief(repo: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd if cwd is not None else repo,
    )


def _payload(repo: Path, *args: str) -> Any:
    result = _run_brief(repo, *args)
    assert result.returncode == 0, f"brief failed: {result.stderr}"
    return json.loads(result.stdout)


def test_pr_landing_block_values(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    payload = _payload(tmp_path, "--pr", spec, "--json")
    assert set(payload) >= {"schema", "range", "commits", "landing"}
    landing = payload["landing"]
    assert set(landing) == {"commits", "conventional", "multi_entry"}
    assert landing["commits"] == 4
    assert landing["conventional"] == 4
    assert landing["multi_entry"] is True
    assert (
        payload["range"]["fingerprint"]
        == _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    )
    assert payload["range"]["resolved_from"] == "explicit"
    text = _run_brief(tmp_path, "--pr", spec)
    assert text.returncode == 0, text.stderr
    assert "landing: commits 4 conventional 4 multi-entry yes" in text.stdout
    assert "fingerprint" in text.stdout
    assert "only-in-base 1" in text.stdout
    assert _BANNED_RE.search(text.stdout) is None


def test_pr_single_commit_is_not_multi_entry(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    base_tip = _git(tmp_path, "rev-parse", seeds["base"])
    head_tip = _git(tmp_path, "rev-parse", "feature~3")
    _ = _git(tmp_path, "branch", "single", head_tip)
    _ = _git(tmp_path, "update-ref", "refs/remotes/origin/main", base_tip)
    _ = _git(tmp_path, "checkout", "-q", "single")
    payload = _payload(tmp_path, "--pr", f"{seeds['base']}...single", "--json")
    assert payload["landing"] == {"commits": 1, "conventional": 1, "multi_entry": False}
    text = _run_brief(tmp_path, "--pr", f"{seeds['base']}...single")
    assert text.returncode == 0, text.stderr
    assert "multi-entry no" in text.stdout


def _seed_mixed_repo(repo: Path) -> str:
    _ = _git(repo, "init")
    _ = _git(repo, "config", "user.name", "Tester Author")
    _ = _git(repo, "config", "user.email", "tester@example.com")
    _ = _git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "chore: base")
    base = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _ = _git(repo, "checkout", "-b", "mixed")
    for name, message in (
        ("real.txt", "feat: real change"),
        ("wip.txt", "wip wip"),
        ("stuff.txt", "Update stuff"),
    ):
        _ = (repo / name).write_text(f"{name}\n", encoding="utf-8")
        _ = _git(repo, "add", ".")
        _ = _git(repo, "commit", "-m", message)
    return base


def test_pr_mixed_range_is_not_multi_entry(tmp_path: Path) -> None:
    base = _seed_mixed_repo(tmp_path)
    payload = _payload(tmp_path, "--pr", f"{base}...mixed", "--json")
    assert payload["landing"] == {"commits": 3, "conventional": 1, "multi_entry": False}
    text = _run_brief(tmp_path, "--pr", f"{base}...mixed")
    assert text.returncode == 0, text.stderr
    assert "landing: commits 3 conventional 1 multi-entry no" in text.stdout
    conv_sha = _git(tmp_path, "rev-parse", "mixed~2")
    narrowed = _payload(tmp_path, "--pr", f"{base}...mixed", "--commit", conv_sha, "--json")
    assert len(narrowed["commits"]) == 1
    assert narrowed["landing"]["commits"] == narrowed["range"]["counts"]["commits"] == 3
    assert narrowed["landing"]["multi_entry"] is False


def test_pr_two_conventional_commits_are_multi_entry(tmp_path: Path) -> None:
    base = _seed_mixed_repo(tmp_path)
    _ = _git(tmp_path, "checkout", "-q", "mixed")
    _ = (tmp_path / "second.txt").write_text("second\n", encoding="utf-8")
    _ = _git(tmp_path, "add", ".")
    _ = _git(tmp_path, "commit", "-m", "fix: second change")
    payload = _payload(tmp_path, "--pr", f"{base}...mixed", "--json")
    assert payload["landing"] == {"commits": 4, "conventional": 2, "multi_entry": True}


def test_pr_level_with_base_refuses_at_or_behind(tmp_path: Path) -> None:
    _ = _git(tmp_path, "init")
    _ = _git(tmp_path, "config", "user.name", "Tester Author")
    _ = _git(tmp_path, "config", "user.email", "tester@example.com")
    _ = _git(tmp_path, "config", "commit.gpgsign", "false")
    _ = (tmp_path / "f.txt").write_text("v1\n", encoding="utf-8")
    _ = _git(tmp_path, "add", ".")
    _ = _git(tmp_path, "commit", "-m", "chore: base")
    base = _git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD")
    _ = _git(tmp_path, "checkout", "-b", "level")
    result = _run_brief(tmp_path, "--pr", f"{base}...level")
    assert result.returncode == 3
    assert "head is at or behind its base; nothing to land" in result.stderr
    assert "only-in-base 0" in result.stderr


def test_pr_behind_base_refuses_with_fix(tmp_path: Path) -> None:
    _ = _git(tmp_path, "init")
    _ = _git(tmp_path, "config", "user.name", "Tester Author")
    _ = _git(tmp_path, "config", "user.email", "tester@example.com")
    _ = _git(tmp_path, "config", "commit.gpgsign", "false")
    _ = (tmp_path / "f.txt").write_text("v1\n", encoding="utf-8")
    _ = _git(tmp_path, "add", ".")
    _ = _git(tmp_path, "commit", "-m", "chore: base")
    base = _git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD")
    _ = _git(tmp_path, "checkout", "-b", "stale")
    _ = _git(tmp_path, "checkout", base)
    _ = (tmp_path / "g.txt").write_text("ahead\n", encoding="utf-8")
    _ = _git(tmp_path, "add", ".")
    _ = _git(tmp_path, "commit", "-m", "fix: base work")
    result = _run_brief(tmp_path, "--pr", f"{base}...stale")
    assert result.returncode == 3
    assert "head is behind its base; nothing to land" in result.stderr
    assert "rebase or check the base" in result.stderr


def test_pr_default_head_resolves_single_ref(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    base_tip = _git(tmp_path, "rev-parse", seeds["base"])
    _ = _git(tmp_path, "update-ref", "refs/remotes/origin/main", base_tip)
    _ = _git(tmp_path, "checkout", "-q", "feature")
    payload = _payload(tmp_path, "--pr", "--json")
    assert payload["range"]["spec_in"] == "HEAD"
    assert payload["range"]["resolved_from"] == "origin/main"
    assert payload["landing"]["commits"] == 4
    assert payload["landing"]["multi_entry"] is True


def test_verify_hit_confirms(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    result = _run_brief(tmp_path, spec, "--verify", expected)
    assert result.returncode == 0
    assert "verified fingerprint" in result.stdout
    assert expected in result.stdout
    assert "explicit" in result.stdout
    assert "only-in-base" in result.stdout
    structured = _payload(tmp_path, spec, "--verify", expected, "--json")
    assert structured["range"]["fingerprint"] == expected
    assert structured["verification"] == {
        "expected": expected,
        "actual": expected,
        "ok": True,
    }


def test_verify_miss_commit_set_names_field(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    _ = _git(tmp_path, "checkout", "-q", "feature")
    _ = (tmp_path / "later.txt").write_text("later\n", encoding="utf-8")
    _ = _git(tmp_path, "add", ".")
    _ = _git(tmp_path, "commit", "-m", "docs: later line")
    result = _run_brief(tmp_path, spec, "--verify", expected)
    assert result.returncode == 3
    assert "fingerprint mismatch" in result.stderr
    assert "commit count" in result.stderr
    assert "the range moved since this fingerprint was taken" in result.stderr
    assert "merge_base" in result.stderr
    assert "spec" in result.stderr


def test_verify_miss_mode_names_spec(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    other = f"{seeds['base']}..feature"
    result = _run_brief(tmp_path, other, "--verify", expected)
    assert result.returncode == 3
    assert "fingerprint mismatch" in result.stderr
    assert "spec" in result.stderr


def test_verify_miss_base_names_merge_base(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    narrow = "feature~1...feature"
    result = _run_brief(tmp_path, narrow, "--verify", expected)
    assert result.returncode == 3
    assert "fingerprint mismatch" in result.stderr
    assert "merge_base" in result.stderr


def test_only_in_base_in_text(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    text = _run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    assert "only-in-base 1" in text.stdout
    pr_text = _run_brief(tmp_path, "--pr", spec)
    assert pr_text.returncode == 0, pr_text.stderr
    assert "only-in-base 1" in pr_text.stdout


def test_fingerprint_and_resolved_from_in_every_digest(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    assert _FP_RE.fullmatch(expected) is not None
    range_text = _run_brief(tmp_path, spec)
    assert range_text.returncode == 0, range_text.stderr
    assert expected[:12] in range_text.stdout
    assert "explicit" in range_text.stdout
    range_payload = _payload(tmp_path, spec, "--json")
    assert range_payload["range"]["fingerprint"] == expected
    assert range_payload["range"]["resolved_from"] == "explicit"
    pr_text = _run_brief(tmp_path, "--pr", spec)
    assert pr_text.returncode == 0, pr_text.stderr
    assert expected[:12] in pr_text.stdout
    assert "explicit" in pr_text.stdout
    pr_payload = _payload(tmp_path, "--pr", spec, "--json")
    assert pr_payload["range"]["fingerprint"] == expected
    assert pr_payload["range"]["resolved_from"] == "explicit"
    hit = _run_brief(tmp_path, spec, "--verify", expected)
    assert hit.returncode == 0, hit.stderr
    assert expected in hit.stdout
    assert "explicit" in hit.stdout
    miss = _run_brief(tmp_path, spec, "--verify", "0" * 64)
    assert miss.returncode == 3
    assert "merge_base" in miss.stderr
    assert "explicit" in miss.stderr


def test_exit_two_malformed(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    assert _run_brief(tmp_path, "...").returncode == 2
    assert _run_brief(tmp_path, spec, "--verify", "short").returncode == 2
    assert _run_brief(tmp_path, "--pr", spec, "--verify", "0" * 64).returncode == 2
    assert _run_brief(tmp_path, spec, "--yaml", "--json").returncode == 2


def test_exit_three_refusals(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    assert _run_brief(tmp_path, f"{seeds['base']}...no-such-branch-xyz").returncode == 3
    assert _run_brief(tmp_path, spec, "--verify", "0" * 64).returncode == 3
    _ = _git(tmp_path, "checkout", "-b", "empty-tip", seeds["base"])
    _ = _git(tmp_path, "checkout", seeds["base"])
    _ = (tmp_path / "ahead.txt").write_text("ahead\n", encoding="utf-8")
    _ = _git(tmp_path, "add", ".")
    _ = _git(tmp_path, "commit", "-m", "fix: ahead")
    assert _run_brief(tmp_path, "--pr", f"{seeds['base']}...empty-tip").returncode == 3


def test_exit_one_outside_repo(tmp_path: Path) -> None:
    result = _run_brief(tmp_path, "main...feature", cwd=Path("/tmp"))
    assert result.returncode == 1
    assert "unexpected failure" in result.stderr


def test_no_network_surface(tmp_path: Path) -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert '"gh"' not in text
    assert "'gh'" not in text
    assert "fetch" not in text
    assert "ls-remote" not in text
    assert "urllib" not in text
    assert "socket" not in text
    assert "requests" not in text
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    for args in ((spec,), ("--pr", spec), (spec, "--verify", "0" * 64)):
        result = _run_brief(tmp_path, *args)
        assert result.returncode in (0, 3), result.stderr
