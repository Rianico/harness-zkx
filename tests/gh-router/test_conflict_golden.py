"""Byte-for-byte guard for the conflict extractor golden fixture.

The golden file stores the pre-refactor summary stdout, both exact and with
the volatile ``repo:`` line normalised to ``<REPO_ROOT>``. The guard rebuilds
an identical conflicted repo (summary output carries no SHAs or dates, so it
is deterministic) and compares normalised bytes exactly.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SCRIPT_PATH = (
    REPO_ROOT / "skills" / "gh-router" / "subskills" / "pr-conflict" / "scripts"
) / "extract_conflict_context.py"
GOLDEN_PATH = FIXTURES_DIR / "conflict_extractor_golden.json"


def _git(repo: Path, *args: str) -> None:
    _ = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _build_conflict_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.name", "Tester Author")
    _git(repo, "config", "user.email", "tester@example.com")
    _git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "common.txt").write_text("base line\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: base commit")
    base = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _git(repo, "checkout", "-b", "feat/calc")
    _ = (repo / "app.py").write_text("def calc(): return 'feature'\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feat(calc): implement feature calc")
    _git(repo, "checkout", base)
    _ = (repo / "app.py").write_text("def calc(): return 'main'\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fix(calc): hotfix main calc")
    merged = subprocess.run(
        ["git", "-C", str(repo), "merge", "feat/calc"],
        capture_output=True,
        text=True,
    )
    assert merged.returncode != 0


def _normalise(stdout: str) -> bytes:
    lines = stdout.splitlines(keepends=True)
    assert lines[0].startswith("repo: ")
    return ("repo: <REPO_ROOT>\n" + "".join(lines[1:])).encode("utf-8")


def test_conflict_extractor_golden_bytes(tmp_path: Path) -> None:
    _build_conflict_repo(tmp_path)
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

    assert completed.returncode == golden["returncode"]
    assert golden["stdout_exact"].splitlines()[1:] == completed.stdout.splitlines()[1:]
    assert _normalise(completed.stdout) == golden["stdout_normalized"].encode("utf-8")


FULL_GOLDEN_PATH = FIXTURES_DIR / "conflict_extractor_golden_full.json"


# SHAs normalize to value-anchored tokens: each output's own intent blocks say
# which sha is ours and which is theirs, so swapping the two slots changes the
# normalized text and the guard fails. A global hex substitution would mask
# exactly that inversion. The fixture declares this same list per case; the
# guard asserts the declaration matches, so neither can drift silently.
_NORMALIZATION_RULES: list[str] = [
    "repo line value -> <REPO_ROOT> (whole-line match)",
    "intent SHAs value-anchored -> <OURS_SHA> / <THEIRS_SHA>",
    "relative durations ('N unit(s) ago') -> <DURATION>",
]


def _intent_shas(stdout: str, is_json: bool) -> tuple[str, str] | None:
    """Return (ours_sha, theirs_sha) straight from the output's intent blocks."""
    if is_json:
        intent = json.loads(stdout)["conflicted_files"][0]["author_intent"]
        assert intent["ours"]["ref"] == "HEAD"
        assert intent["theirs"]["ref"] == "MERGE_HEAD"
        return intent["ours"]["sha"], intent["theirs"]["sha"]
    ours = re.search(r"ours \(HEAD\): \[([0-9a-f]{7,40})\]", stdout)
    theirs = re.search(r"theirs \(MERGE_HEAD\): \[([0-9a-f]{7,40})\]", stdout)
    if ours is None or theirs is None:
        assert ours is None and theirs is None
        assert not re.search(r"\b[0-9a-f]{7,40}\b", stdout), "unexpected volatile sha"
        return None
    return ours.group(1), theirs.group(1)


def _normalise_full(stdout: str, is_json: bool) -> bytes:
    """Normalise only volatile fields; everything else compares byte-for-byte."""
    text = re.sub(r"^repo: .*$", "repo: <REPO_ROOT>", stdout, flags=re.M)
    text = re.sub(
        r'^(\s*)"repo_root": "[^"]*"(,?)$',
        r'\1"repo_root": "<REPO_ROOT>"\2',
        text,
        flags=re.M,
    )
    anchored = _intent_shas(text, is_json)
    if anchored is not None:
        ours_sha, theirs_sha = anchored
        assert ours_sha != theirs_sha
        slots = re.compile(f"\\b({re.escape(theirs_sha)}|{re.escape(ours_sha)})\\b")
        text = slots.sub(
            lambda match: "<THEIRS_SHA>" if match.group(1) == theirs_sha else "<OURS_SHA>",
            text,
        )
    text = re.sub(r"\b\d+ (second|minute|hour|day|week|month|year)s? ago\b", "<DURATION>", text)
    return text.encode("utf-8")


def test_conflict_extractor_full_goldens(tmp_path: Path) -> None:
    golden = json.loads(FULL_GOLDEN_PATH.read_text(encoding="utf-8"))
    assert [case["name"] for case in golden["cases"]] == [
        "summary",
        "json",
        "json_all",
        "all_capped",
    ]
    for case in golden["cases"]:
        repo = tmp_path / case["name"]
        repo.mkdir()
        _build_conflict_repo(repo)
        # Every recorded argv starts with the repo placeholder, so the command
        # below replays exactly the argv the fixture records.
        assert case["normalization"] == _NORMALIZATION_RULES
        assert case["argv"][:2] == ["--repo", "<REPO>"]
        argv = [part if part != "<REPO>" else str(repo) for part in case["argv"]]
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *argv],
            capture_output=True,
            text=True,
        )
        assert completed.returncode == case["returncode"]
        is_json = "--json" in case["argv"]
        assert _normalise_full(completed.stdout, is_json) == case["stdout_normalized"].encode(
            "utf-8"
        )


_SAMPLE_TEXT = (
    "repo: /tmp/somewhere/repo\n"
    "conflicted files: 1\n"
    "  merge (merging bbbbbbb into aaaaaaa)\n"
    "  ours (HEAD): [aaaaaaa]\n"
    "  theirs (MERGE_HEAD): [bbbbbbb]\n"
    "  author date 3 hours ago\n"
)

_SAMPLE_JSON = json.dumps(
    {
        "repo_root": "/tmp/somewhere/repo",
        "conflicted_files": [
            {
                "operation": "merge (merging bbbbbbb into aaaaaaa)",
                "author_intent": {
                    "ours": {"ref": "HEAD", "sha": "aaaaaaa"},
                    "theirs": {"ref": "MERGE_HEAD", "sha": "bbbbbbb"},
                },
            }
        ],
    }
)

# Each declared rule maps to (sample_input, is_json, expected_substring).
# An unknown declaration raises KeyError; an edited transformation drops the
# expected token. Either way the guard fails.
_RULE_SAMPLES: dict[str, tuple[str, bool, str]] = {
    "repo line value -> <REPO_ROOT> (whole-line match)": (
        _SAMPLE_TEXT,
        False,
        "repo: <REPO_ROOT>",
    ),
    "intent SHAs value-anchored -> <OURS_SHA> / <THEIRS_SHA>": (
        _SAMPLE_JSON,
        True,
        '"operation": "merge (merging <THEIRS_SHA> into <OURS_SHA>)"',
    ),
    "relative durations ('N unit(s) ago') -> <DURATION>": (
        _SAMPLE_TEXT,
        False,
        "<DURATION>",
    ),
}


def test_normaliser_implements_each_declared_rule() -> None:
    """Scope: the normaliser only. Extractor-side changes are pinned by the golden."""
    golden = json.loads(FULL_GOLDEN_PATH.read_text(encoding="utf-8"))
    declared = golden["cases"][0]["normalization"]
    for rule in declared:
        sample, is_json, expected = _RULE_SAMPLES[rule]
        assert expected in _normalise_full(sample, is_json).decode("utf-8"), rule
