"""Unit tests for the git-diff-digest pr and verify surface (scripts/brief.py).

Synthetic repos only: no network, no gh auth. The pr view resolves through
``skills/gh-router/lib/range_authority.py`` and adds the landing block on top
of the range payload; verify recomputes the range fingerprint and compares it
field by field.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.gh_router_repos import SCRIPT, brief_payload, git, run_brief, seed_diverged_repo

_BANNED_RE = re.compile(r"\b(title|squash|risk)\b", re.IGNORECASE)
_FP_RE = re.compile(r"[0-9a-f]{64}")


def test_pr_landing_block_values(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    payload = brief_payload(tmp_path, "--pr", spec, "--json")
    assert set(payload) >= {"schema", "range", "commits", "landing"}
    landing = payload["landing"]
    assert set(landing) == {"commits", "conventional", "multi_entry"}
    assert landing["commits"] == 4
    assert landing["conventional"] == 4
    assert landing["multi_entry"] is True
    assert (
        payload["range"]["fingerprint"]
        == brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    )
    assert payload["range"]["resolved_from"] == "explicit"
    text = run_brief(tmp_path, "--pr", spec)
    assert text.returncode == 0, text.stderr
    assert "landing: commits 4 conventional 4 multi-entry yes" in text.stdout
    assert "fingerprint" in text.stdout
    assert "only-in-base 1" in text.stdout
    assert _BANNED_RE.search(text.stdout) is None


def test_pr_single_commit_is_not_multi_entry(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    base_tip = git(tmp_path, "rev-parse", seeds["base"])
    head_tip = git(tmp_path, "rev-parse", "feature~3")
    _ = git(tmp_path, "branch", "single", head_tip)
    _ = git(tmp_path, "update-ref", "refs/remotes/origin/main", base_tip)
    _ = git(tmp_path, "checkout", "-q", "single")
    payload = brief_payload(tmp_path, "--pr", f"{seeds['base']}...single", "--json")
    assert payload["landing"] == {"commits": 1, "conventional": 1, "multi_entry": False}
    text = run_brief(tmp_path, "--pr", f"{seeds['base']}...single")
    assert text.returncode == 0, text.stderr
    assert "multi-entry no" in text.stdout


def _seed_mixed_repo(repo: Path) -> str:
    _ = git(repo, "init")
    _ = git(repo, "config", "user.name", "Tester Author")
    _ = git(repo, "config", "user.email", "tester@example.com")
    _ = git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _ = git(repo, "add", ".")
    _ = git(repo, "commit", "-m", "chore: base")
    base = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _ = git(repo, "checkout", "-b", "mixed")
    for name, message in (
        ("real.txt", "feat: real change"),
        ("wip.txt", "wip wip"),
        ("stuff.txt", "Update stuff"),
    ):
        _ = (repo / name).write_text(f"{name}\n", encoding="utf-8")
        _ = git(repo, "add", ".")
        _ = git(repo, "commit", "-m", message)
    return base


def test_pr_mixed_range_is_not_multi_entry(tmp_path: Path) -> None:
    base = _seed_mixed_repo(tmp_path)
    payload = brief_payload(tmp_path, "--pr", f"{base}...mixed", "--json")
    assert payload["landing"] == {"commits": 3, "conventional": 1, "multi_entry": False}
    text = run_brief(tmp_path, "--pr", f"{base}...mixed")
    assert text.returncode == 0, text.stderr
    assert "landing: commits 3 conventional 1 multi-entry no" in text.stdout
    conv_sha = git(tmp_path, "rev-parse", "mixed~2")
    narrowed = brief_payload(tmp_path, "--pr", f"{base}...mixed", "--commit", conv_sha, "--json")
    assert len(narrowed["commits"]) == 1
    assert narrowed["landing"]["commits"] == narrowed["range"]["counts"]["commits"] == 3
    assert narrowed["landing"]["multi_entry"] is False


def test_pr_two_conventional_commits_are_multi_entry(tmp_path: Path) -> None:
    base = _seed_mixed_repo(tmp_path)
    _ = git(tmp_path, "checkout", "-q", "mixed")
    _ = (tmp_path / "second.txt").write_text("second\n", encoding="utf-8")
    _ = git(tmp_path, "add", ".")
    _ = git(tmp_path, "commit", "-m", "fix: second change")
    payload = brief_payload(tmp_path, "--pr", f"{base}...mixed", "--json")
    assert payload["landing"] == {"commits": 4, "conventional": 2, "multi_entry": True}


def test_pr_level_with_base_refuses_at_or_behind(tmp_path: Path) -> None:
    _ = git(tmp_path, "init")
    _ = git(tmp_path, "config", "user.name", "Tester Author")
    _ = git(tmp_path, "config", "user.email", "tester@example.com")
    _ = git(tmp_path, "config", "commit.gpgsign", "false")
    _ = (tmp_path / "f.txt").write_text("v1\n", encoding="utf-8")
    _ = git(tmp_path, "add", ".")
    _ = git(tmp_path, "commit", "-m", "chore: base")
    base = git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD")
    _ = git(tmp_path, "checkout", "-b", "level")
    result = run_brief(tmp_path, "--pr", f"{base}...level")
    assert result.returncode == 3
    assert "head is at or behind its base; nothing to land" in result.stderr
    assert "only-in-base 0" in result.stderr


def test_pr_behind_base_refuses_with_fix(tmp_path: Path) -> None:
    _ = git(tmp_path, "init")
    _ = git(tmp_path, "config", "user.name", "Tester Author")
    _ = git(tmp_path, "config", "user.email", "tester@example.com")
    _ = git(tmp_path, "config", "commit.gpgsign", "false")
    _ = (tmp_path / "f.txt").write_text("v1\n", encoding="utf-8")
    _ = git(tmp_path, "add", ".")
    _ = git(tmp_path, "commit", "-m", "chore: base")
    base = git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD")
    _ = git(tmp_path, "checkout", "-b", "stale")
    _ = git(tmp_path, "checkout", base)
    _ = (tmp_path / "g.txt").write_text("ahead\n", encoding="utf-8")
    _ = git(tmp_path, "add", ".")
    _ = git(tmp_path, "commit", "-m", "fix: base work")
    result = run_brief(tmp_path, "--pr", f"{base}...stale")
    assert result.returncode == 3
    assert "head is behind its base; nothing to land" in result.stderr
    assert "rebase or check the base" in result.stderr


def test_pr_default_head_resolves_single_ref(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    base_tip = git(tmp_path, "rev-parse", seeds["base"])
    _ = git(tmp_path, "update-ref", "refs/remotes/origin/main", base_tip)
    _ = git(tmp_path, "checkout", "-q", "feature")
    payload = brief_payload(tmp_path, "--pr", "--json")
    assert payload["range"]["spec_in"] == "HEAD"
    assert payload["range"]["resolved_from"] == "origin/main"
    assert payload["landing"]["commits"] == 4
    assert payload["landing"]["multi_entry"] is True


def test_verify_hit_confirms(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    result = run_brief(tmp_path, spec, "--verify", expected)
    assert result.returncode == 0
    assert "verified fingerprint" in result.stdout
    assert expected in result.stdout
    assert "explicit" in result.stdout
    assert "only-in-base" in result.stdout
    structured = brief_payload(tmp_path, spec, "--verify", expected, "--json")
    assert structured["range"]["fingerprint"] == expected
    assert structured["verification"] == {
        "expected": expected,
        "actual": expected,
        "ok": True,
    }


def test_verify_miss_commit_set_names_field(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    _ = git(tmp_path, "checkout", "-q", "feature")
    _ = (tmp_path / "later.txt").write_text("later\n", encoding="utf-8")
    _ = git(tmp_path, "add", ".")
    _ = git(tmp_path, "commit", "-m", "docs: later line")
    result = run_brief(tmp_path, spec, "--verify", expected)
    assert result.returncode == 3
    assert "fingerprint mismatch" in result.stderr
    assert "commit count" in result.stderr
    assert "the range moved since this fingerprint was taken" in result.stderr
    assert "merge_base" in result.stderr
    assert "spec" in result.stderr


def test_verify_miss_mode_names_spec(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    other = f"{seeds['base']}..feature"
    result = run_brief(tmp_path, other, "--verify", expected)
    assert result.returncode == 3
    assert "fingerprint mismatch" in result.stderr
    assert "spec" in result.stderr


def test_verify_miss_base_names_merge_base(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    narrow = "feature~1...feature"
    result = run_brief(tmp_path, narrow, "--verify", expected)
    assert result.returncode == 3
    assert "fingerprint mismatch" in result.stderr
    assert "merge_base" in result.stderr


def test_only_in_base_in_text(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    text = run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    assert "only-in-base 1" in text.stdout
    pr_text = run_brief(tmp_path, "--pr", spec)
    assert pr_text.returncode == 0, pr_text.stderr
    assert "only-in-base 1" in pr_text.stdout


def test_fingerprint_and_resolved_from_in_every_digest(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    expected = brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    assert _FP_RE.fullmatch(expected) is not None
    range_text = run_brief(tmp_path, spec)
    assert range_text.returncode == 0, range_text.stderr
    assert expected[:12] in range_text.stdout
    assert "explicit" in range_text.stdout
    range_payload = brief_payload(tmp_path, spec, "--json")
    assert range_payload["range"]["fingerprint"] == expected
    assert range_payload["range"]["resolved_from"] == "explicit"
    pr_text = run_brief(tmp_path, "--pr", spec)
    assert pr_text.returncode == 0, pr_text.stderr
    assert expected[:12] in pr_text.stdout
    assert "explicit" in pr_text.stdout
    pr_payload = brief_payload(tmp_path, "--pr", spec, "--json")
    assert pr_payload["range"]["fingerprint"] == expected
    assert pr_payload["range"]["resolved_from"] == "explicit"
    hit = run_brief(tmp_path, spec, "--verify", expected)
    assert hit.returncode == 0, hit.stderr
    assert expected in hit.stdout
    assert "explicit" in hit.stdout
    miss = run_brief(tmp_path, spec, "--verify", "0" * 64)
    assert miss.returncode == 3
    assert "merge_base" in miss.stderr
    assert "explicit" in miss.stderr


def test_exit_two_malformed(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    assert run_brief(tmp_path, "...").returncode == 2
    assert run_brief(tmp_path, spec, "--verify", "short").returncode == 2
    assert run_brief(tmp_path, "--pr", spec, "--verify", "0" * 64).returncode == 2
    assert run_brief(tmp_path, spec, "--yaml", "--json").returncode == 2


def test_exit_three_refusals(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    assert run_brief(tmp_path, f"{seeds['base']}...no-such-branch-xyz").returncode == 3
    assert run_brief(tmp_path, spec, "--verify", "0" * 64).returncode == 3
    _ = git(tmp_path, "checkout", "-b", "empty-tip", seeds["base"])
    _ = git(tmp_path, "checkout", seeds["base"])
    _ = (tmp_path / "ahead.txt").write_text("ahead\n", encoding="utf-8")
    _ = git(tmp_path, "add", ".")
    _ = git(tmp_path, "commit", "-m", "fix: ahead")
    assert run_brief(tmp_path, "--pr", f"{seeds['base']}...empty-tip").returncode == 3


def test_exit_one_outside_repo(tmp_path: Path) -> None:
    result = run_brief(tmp_path, "main...feature", cwd=Path("/tmp"))
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
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    for args in ((spec,), ("--pr", spec), (spec, "--verify", "0" * 64)):
        result = run_brief(tmp_path, *args)
        assert result.returncode in (0, 3), result.stderr
