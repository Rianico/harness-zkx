"""The GitHub boundary: the process runner, repo/PR resolution, mergeability, and the watch.

Everything that shells out to `git`/`gh` for pr-land's own modules lives here, including the
`run_command` seam the tests patch. A patch of `_github.run_command` is the single
interception point: every sibling module and `pr.py` call it through the qualified
`_github.run_command(...)` lookup, so an early-bound `from _github import run_command`
binding cannot silently bypass the fake. That seam covers every subprocess call **in
pr-land's own modules**; the one exception it cannot intercept is the range/repo-root
authority helper in `lib/range_authority.py`, which spawns its own `subprocess.run` coverage,
reached from here through `_authority_resolve` / `_local_base_from_authority` (and via them
from `_draft` and `_check`). The merge gate's budgets and pointers (`LOG_TIMEOUT`, the
poll/unknown/dirty retries, `CONFLICT_HELPER`) live here with the call sites that read them;
leaving them in `pr.py` would close an import cycle.

A leaf below `_options`: this module imports nothing from `pr`, `_check`, `_draft`, or
`_changelog`.
"""

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from _errors import PrError, RefusalError, UsageError
from _options import PrOptions

_LIB_DIR = str(Path(__file__).resolve().parents[3] / "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)
from range_authority import RangeRefusal, RangeResolution, resolve_range

__all__ = [
    "CONFLICT_FILES_MAX",
    "CONFLICT_HELPER",
    "DEFAULT_TIMEOUT",
    "DIRTY_INTERVAL",
    "DIRTY_STRIKES",
    "LOG_TIMEOUT",
    "MERGE_STATE_INTERVAL",
    "MERGE_STATE_TRIES",
    "POLL_INTERVAL",
    "POLL_TRIES",
    "SLUG_PATTERN",
    "UNKNOWN_INTERVAL",
    "UNKNOWN_TRIES",
    "_authority_resolve",
    "_digest_range_spec",
    "_local_base_from_authority",
    "_remote_branch_exists",
    "check_conflicts",
    "checks_verdict",
    "conflicting_files",
    "default_branch",
    "dump_failure_logs",
    "failing_run_ids",
    "fetch_merge_state",
    "fetch_mergeability",
    "MergeFetch",
    "MergeObservation",
    "merge_state_verdict",
    "pr_conflict_verdict",
    "pr_url",
    "ready_pr",
    "repo_remote_for_ref",
    "repo_slug_from_url",
    "report_merge_refusal",
    "resolve_base",
    "resolve_head",
    "resolve_merge_state",
    "resolve_repo",
    "resolve_title_and_body",
    "run_command",
    "watch_checks",
]


SLUG_PATTERN = re.compile(r"^[^/: \t\r\n]+/[^/: \t\r\n]+$")

POLL_TRIES = 60
POLL_INTERVAL = 10.0
# Mergeability is computed lazily, so a `null`/`unknown` reading is retried UNKNOWN_TRIES times
# UNKNOWN_INTERVAL apart before the gate refuses; the merge-wait shares that budget.
UNKNOWN_TRIES = 5
UNKNOWN_INTERVAL = 2.0
MERGE_STATE_TRIES = UNKNOWN_TRIES
MERGE_STATE_INTERVAL = UNKNOWN_INTERVAL
# A `dirty` reading is confirmed DIRTY_STRIKES times, DIRTY_INTERVAL apart, before it fails the gate.
DIRTY_STRIKES = 2
DIRTY_INTERVAL = 3.0
CONFLICT_FILES_MAX = 10
CONFLICT_HELPER = (
    "uv run skills/gh-router/subskills/pr-conflict/scripts/extract_conflict_context.py"
)
DEFAULT_TIMEOUT = 30.0
LOG_TIMEOUT = 60.0


def run_command(
    cmd: list[str],
    *,
    timeout: float = DEFAULT_TIMEOUT,
    cwd: Path | None = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            cwd=cwd,
            check=check,
            env=env,
        )
    except subprocess.TimeoutExpired as e:
        cmd_str = " ".join(cmd)
        raise PrError(f"command timed out after {timeout}s: {cmd_str}") from e


def resolve_head(head_ref: str | None = None, cwd: Path | None = None) -> str:
    if not head_ref:
        res = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
        )
        if res.returncode != 0:
            raise UsageError("cannot resolve HEAD ref")
        head_ref = res.stdout.strip()
    if head_ref in ("HEAD", "main"):
        raise UsageError(f"refusing to open PR from {head_ref}")
    return head_ref


def repo_remote_for_ref(ref: str | None = None, cwd: Path | None = None) -> str:
    if not ref:
        res = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
        )
        ref = res.stdout.strip() if res.returncode == 0 else ""
    if ref:
        push_remote_res = run_command(
            ["git", "config", "--get", f"branch.{ref}.pushRemote"],
            cwd=cwd,
        )
        val = push_remote_res.stdout.strip()
        if push_remote_res.returncode == 0 and val:
            return val
        remote_res = run_command(
            ["git", "config", "--get", f"branch.{ref}.remote"],
            cwd=cwd,
        )
        val = remote_res.stdout.strip()
        if remote_res.returncode == 0 and val:
            return val
    return "origin"


def repo_slug_from_url(url: str) -> str | None:
    if not url:
        return None
    s = url.strip()
    s = re.sub(r"^[A-Za-z][A-Za-z0-9+.-]*://", "", s)
    s = re.sub(r"^[^/@]*@", "", s)
    s = re.sub(r"^[^/:]+[:/]", "", s)
    s = re.sub(r"/+$", "", s)
    s = re.sub(r"\.git$", "", s)
    s = re.sub(r"/+$", "", s)
    if SLUG_PATTERN.match(s):
        return s
    return None


def resolve_repo(head_ref: str | None = None, cwd: Path | None = None) -> str:
    remote = repo_remote_for_ref(head_ref, cwd=cwd)
    url_res = run_command(
        ["git", "remote", "get-url", "--push", remote],
        cwd=cwd,
    )
    url = url_res.stdout.strip() if url_res.returncode == 0 else ""
    if not url:
        origin_res = run_command(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd,
        )
        url = origin_res.stdout.strip() if origin_res.returncode == 0 else ""
    slug = repo_slug_from_url(url)
    if not slug:
        gh_res = run_command(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            cwd=cwd,
        )
        gh_slug = gh_res.stdout.strip() if gh_res.returncode == 0 else ""
        if gh_slug and SLUG_PATTERN.match(gh_slug):
            slug = gh_slug
    if not slug:
        raise UsageError("cannot resolve repo slug (no GitHub remote for branch/origin)")
    return slug


def default_branch(repo: str, cwd: Path | None = None) -> str | None:
    res = run_command(
        ["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
        cwd=cwd,
    )
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return None


def _authority_resolve(spec: str, mode: str, cwd: Path | None = None) -> RangeResolution:
    """Resolve *spec* through the shared range authority inside the target repo.

    resolve_range discovers its repo from the process cwd, so temporarily
    chdir when the caller targets another checkout. Restores cwd on return.
    """
    if cwd is None:
        return resolve_range(spec, mode)
    previous = Path.cwd()
    target = cwd if cwd.is_absolute() else previous / cwd
    os.chdir(target)
    try:
        return resolve_range(spec, mode)
    finally:
        os.chdir(previous)


def _remote_branch_exists(name: str, cwd: Path | None = None) -> bool:
    """True when refs/remotes/origin/<name> resolves locally (no network)."""
    res = run_command(
        ["git", "rev-parse", "--verify", "-q", f"refs/remotes/origin/{name}"],
        cwd=cwd,
    )
    return res.returncode == 0


def _local_base_from_authority(cwd: Path | None = None) -> str:
    """Resolve the local base through the shared range authority (bare branch name).

    Single-ref resolution walks the authority's ordered local candidates
    (origin/HEAD, then origin/main, then origin/master) without touching the
    network. The result is stripped to the bare branch name GitHub's
    `-f base=` expects.
    """
    resolution = _authority_resolve("HEAD", "..", cwd)
    base_ref = resolution.base_ref
    if base_ref == "origin/HEAD":
        sym = run_command(
            ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            cwd=cwd,
        )
        if sym.returncode == 0 and sym.stdout.strip():
            out = sym.stdout.strip()
            if out.startswith("origin/"):
                out = out.removeprefix("origin/")
            if out and _remote_branch_exists(out, cwd=cwd):
                return out
            for fallback in ("main", "master"):
                if _remote_branch_exists(fallback, cwd=cwd):
                    return fallback
        raise RefusalError(
            "cannot resolve PR base: the git-diff-digest range authority "
            "resolved origin/HEAD but it names no branch"
        )
    if base_ref.startswith("origin/"):
        return base_ref.removeprefix("origin/")
    return base_ref


def _digest_range_spec(base: str, head_ref: str, cwd: Path | None = None) -> str:
    """Build the `git log` range so trailer authors equal the digest's commit set.

    The resolved base goes first as a two-dot range; when it cannot resolve
    locally the digest's own single-ref derivation is used instead. Raises
    RangeRefusal when neither resolves.
    """
    try:
        resolution = _authority_resolve(f"{base}..{head_ref}", "..", cwd)
    except RangeRefusal:
        resolution = _authority_resolve(head_ref, "..", cwd)
    return f"{resolution.base_ref}..{head_ref}"


def resolve_base(base: str | None, repo: str, cwd: Path | None = None) -> str:
    if base:
        return base
    b = default_branch(repo, cwd=cwd)
    if b:
        return b
    sym_res = run_command(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        cwd=cwd,
    )
    if sym_res.returncode == 0 and sym_res.stdout.strip():
        out = sym_res.stdout.strip()
        if out.startswith("origin/"):
            out = out.removeprefix("origin/")
        if out and _remote_branch_exists(out, cwd=cwd):
            return out
    try:
        return _local_base_from_authority(cwd=cwd)
    except RangeRefusal as exc:
        raise RefusalError(
            "cannot resolve PR base: no explicit --base, no GitHub default_branch, "
            "and the git-diff-digest range authority found no local base "
            f"({exc})"
        ) from exc


def resolve_title_and_body(
    options: PrOptions, cwd: Path | None = None
) -> tuple[str, str, bool, bool]:
    title = options.title
    title_supplied = options.title_supplied
    if not title:
        if options.head:
            res = run_command(
                ["git", "log", "-1", "--pretty=%s", options.head],
                cwd=cwd,
            )
            if res.returncode == 0 and res.stdout.strip():
                title = res.stdout.strip()
        if not title:
            res = run_command(
                ["git", "log", "-1", "--pretty=%s"],
                cwd=cwd,
            )
            title = res.stdout.strip() if res.returncode == 0 else ""

    body = options.body or ""
    body_supplied = options.body_supplied
    if options.body_file:
        bf = (
            options.body_file
            if options.body_file.is_absolute()
            else ((cwd or Path.cwd()) / options.body_file)
        )
        if not bf.is_file():
            raise UsageError(f"body file not found or not readable: {options.body_file}")
        try:
            body = bf.read_text(encoding="utf-8")
        except OSError:
            raise UsageError(f"body file not found or not readable: {options.body_file}") from None
        body_supplied = True

    return title, body, title_supplied, body_supplied


def checks_verdict(payload: str) -> str:
    """Evaluate checks payload (name<TAB>bucket lines) returning 'success', 'failure', or 'pending'."""
    total = 0
    failed = 0
    pending = 0
    passed = 0
    skipping = 0
    for line in payload.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            bucket = parts[1].strip()
        else:
            tokens = line.split()
            bucket = tokens[-1] if len(tokens) >= 2 else line
        total += 1
        if bucket in ("fail", "cancel"):
            failed += 1
        elif bucket == "pass":
            passed += 1
        elif bucket == "skipping":
            skipping += 1
        else:
            pending += 1

    if failed > 0:
        return "failure"
    if total == 0 or pending > 0:
        return "pending"
    if passed == 0 and skipping > 0:
        # All reported checks skipped (draft PRs get all-skipped runs): zero CI is not green.
        return "pending"
    return "success"


def pr_conflict_verdict(mergeable: str | None, state: str | None) -> str:
    m = (mergeable or "").strip()
    s = (state or "").strip()
    if m in ("false", "CONFLICTING"):
        return "conflicting"
    if s in ("dirty", "DIRTY"):
        return "conflicting"
    if s in ("behind", "BEHIND"):
        return "behind"
    if s in ("unknown", "UNKNOWN", ""):
        return "unknown"
    if m in ("null", ""):
        return "unknown"
    return "clean"


@dataclass(frozen=True, slots=True)
class MergeObservation:
    """One mergeability reading of a PR: the verdict word plus the raw fields behind it.

    ``verdict`` is ``pr_conflict_verdict``'s word (``conflicting``/``behind``/``clean``/
    ``unknown``); ``dirty`` singles out GitHub's ``dirty`` state, the conflict candidate
    that must be confirmed before it fails the gate.
    """

    verdict: str
    mergeable: str = ""
    state: str = ""
    url: str = ""

    @property
    def dirty(self) -> bool:
        """True for GitHub's `dirty` state — a conflict candidate needing a second strike."""
        return self.verdict == "conflicting" and self.state.strip().lower() == "dirty"


type MergeFetch = Callable[[str, str, Path | None], MergeObservation]


def fetch_mergeability(repo: str, num: str, cwd: Path | None = None) -> MergeObservation:
    """Read mergeable / mergeable_state / html_url in one `gh api` call."""
    res = run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls/{num}",
            "--jq",
            '[(if .mergeable == null then "null" else (.mergeable|tostring) end), (.mergeable_state // "unknown"), (.html_url // "")] | @tsv',
        ],
        cwd=cwd,
    )
    if res.returncode != 0:
        raise PrError(
            f"failed to check PR #{num} mergeable state: {res.stderr.strip() or 'gh api failed'}"
        )
    line = res.stdout.strip()
    if not line:
        raise PrError(f"failed to check PR #{num} mergeable state: empty response from gh api")
    parts = line.split("\t")
    mergeable = parts[0] if len(parts) > 0 else ""
    state = parts[1] if len(parts) > 1 else ""
    url = parts[2] if len(parts) > 2 else ""
    return MergeObservation(
        verdict=pr_conflict_verdict(mergeable, state), mergeable=mergeable, state=state, url=url
    )


def merge_state_verdict(state: str) -> str:
    """Verdict word for a bare `mergeable_state` reading: only `clean` may merge.

    ``pr_conflict_verdict`` needs `mergeable` too; the pre-merge probe reads the state
    alone, so every state that is not clean/behind/dirty reads as `unknown` and refuses.
    `behind` is its own verdict: the `--watch` loop accepts it with a warning folded into
    the poll line, while `--merge` refuses it (this function never returns `clean` for it).
    """
    normalized = state.strip().lower()
    if normalized == "clean":
        return "clean"
    if normalized in ("dirty", "conflicting"):
        return "conflicting"
    if normalized == "behind":
        return "behind"
    return "unknown"


def fetch_merge_state(repo: str, num: str, cwd: Path | None = None) -> MergeObservation:
    """Read `mergeable_state` alone — the pre-merge probe, which needs no `mergeable`/url."""
    res = run_command(
        ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".mergeable_state"], cwd=cwd
    )
    state = res.stdout.strip() if res.returncode == 0 and res.stdout.strip() else "unknown"
    return MergeObservation(verdict=merge_state_verdict(state), state=state)


def resolve_merge_state(
    repo: str,
    num: str,
    *,
    fetch: MergeFetch = fetch_mergeability,
    unknown_tries: int = UNKNOWN_TRIES,
    unknown_interval: float = UNKNOWN_INTERVAL,
    dirty_strikes: int = DIRTY_STRIKES,
    dirty_interval: float = DIRTY_INTERVAL,
    cwd: Path | None = None,
) -> MergeObservation:
    """Poll mergeability until a confident verdict, then return that observation.

    An `unknown` reading (and a transient `gh api` failure) is retried up to
    `unknown_tries` times, `unknown_interval` apart. The default budget is intentionally
    short — about 8s (5 tries x 2s) — after which the caller refuses with the verdict word
    `unknown`. That word is distinct from `conflicting`: `unknown` means GitHub never
    computed mergeability, `conflicting` means a real conflict. A `dirty` reading is
    confirmed `dirty_strikes` times, `dirty_interval` apart, before it counts as
    conflicting; any non-dirty reading resets that streak. An unresolved `unknown` comes
    back as-is: the caller refuses on it, so a PR whose mergeability GitHub never computes
    fails fast instead of stalling the watch.
    """
    unknown_left = max(1, unknown_tries)
    strikes = 0
    while True:
        try:
            obs = fetch(repo, num, cwd)
        except PrError:
            unknown_left -= 1
            if unknown_left <= 0:
                raise
            time.sleep(unknown_interval)
            continue
        if obs.dirty:
            strikes += 1
            if strikes >= max(1, dirty_strikes):
                return obs
            time.sleep(dirty_interval)
            continue
        strikes = 0
        if obs.verdict == "unknown":
            unknown_left -= 1
            if unknown_left <= 0:
                return obs
            time.sleep(unknown_interval)
            continue
        return obs


def conflicting_files(repo: str, num: str, cwd: Path | None = None) -> list[str]:
    """Every path the PR touches, best-effort — NOT the conflicting subset.

    ``gh pr view --json files`` lists all changed files and has no conflict filter, so the
    report must not call them the conflicting set. Empty when the `gh pr view` read fails.
    """
    res = run_command(
        [
            "gh",
            "pr",
            "view",
            num,
            "--repo",
            repo,
            "--json",
            "files",
            "--jq",
            '[.files[].path] | join(" ")',
        ],
        cwd=cwd,
    )
    if res.returncode != 0:
        return []
    return res.stdout.strip().strip('"').split()


def report_merge_refusal(
    obs: MergeObservation, repo: str, num: str, cwd: Path | None = None
) -> None:
    """Print the one refusal report shared by the watch fast-fail, the gate, and the merge.

    Verdict word, PR url, up to ``CONFLICT_FILES_MAX`` touched files (every path the PR
    changes — not a conflicting subset, which ``gh pr view --json files`` cannot supply;
    ``(+N more)`` past the cap), and the pr-conflict helper pointer. An empty or failed
    file read prints ``touched files: (none resolved)`` instead of dropping the line.
    """
    url = obs.url or pr_url(repo, num, cwd=cwd)
    print(f"PR {url}", file=sys.stderr)
    mergeable = f"mergeable={obs.mergeable} " if obs.mergeable else ""
    print(f"{obs.verdict}: {mergeable}merge_state_status={obs.state}", file=sys.stderr)
    files = conflicting_files(repo, num, cwd=cwd)
    if files:
        shown = files[:CONFLICT_FILES_MAX]
        extra = len(files) - len(shown)
        more = f" (+{extra} more)" if extra > 0 else ""
        print(f"touched files: {' '.join(shown)}{more}", file=sys.stderr)
    else:
        print("touched files: (none resolved)", file=sys.stderr)
    lead = "conflict detected" if obs.verdict == "conflicting" else "mergeability unresolved"
    print(
        f"{lead}: run '{CONFLICT_HELPER}' to inspect hunks and commit intent, "
        "then delegate resolution to a worker subagent.",
        file=sys.stderr,
    )


def check_conflicts(repo: str, num: str, base: str, cwd: Path | None = None) -> bool:
    """Refuse when the PR cannot merge: conflicting, or mergeability that stays unresolved.

    Compatibility wrapper kept for the tests; the live paths (``--watch``, ``--merge``)
    call ``resolve_merge_state`` + ``report_merge_refusal`` directly. Returns False on a
    conflict and on an `unknown` state that survives UNKNOWN_TRIES retries, True
    otherwise; raises PrError when the `gh api` read fails outright. A refusal names the
    touched files and the pr-conflict resolution pointer on stderr. A `behind` head is
    accepted here with a warning, the same as the watch loop (``--merge`` refuses it).
    """
    obs = resolve_merge_state(repo, num, cwd=cwd)
    if obs.verdict in ("conflicting", "unknown"):
        report_merge_refusal(obs, repo, num, cwd=cwd)
        return False
    if obs.verdict == "behind":
        print(f"warning: head branch is behind {base}", file=sys.stderr)
    return True


def failing_run_ids(repo: str, num: str, cwd: Path | None = None) -> list[str]:
    """Run IDs behind the failing/cancelled checks on this PR, best-effort, deduped."""
    run_ids: list[str] = []
    checks_json_res = run_command(
        [
            "gh",
            "pr",
            "checks",
            num,
            "--repo",
            repo,
            "--json",
            "name,bucket,link,state",
        ],
        cwd=cwd,
    )
    if checks_json_res.returncode == 0 and checks_json_res.stdout.strip():
        try:
            checks_data = json.loads(checks_json_res.stdout)
            if isinstance(checks_data, list):
                for check in checks_data:
                    if isinstance(check, dict):
                        bucket = str(check.get("bucket", "")).lower()
                        state = str(check.get("state", "")).upper()
                        if bucket in ("fail", "cancel") or state in (
                            "FAILURE",
                            "CANCELLED",
                            "TIMED_OUT",
                        ):
                            link = str(check.get("link", ""))
                            m = re.search(r"/actions/runs/(\d+)", link)
                            if m:
                                rid = m.group(1)
                                if rid not in run_ids:
                                    run_ids.append(rid)
        except ValueError, TypeError, KeyError:
            pass

    if not run_ids:
        sha_res = run_command(
            ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".head.sha"],
            cwd=cwd,
        )
        sha = sha_res.stdout.strip() if sha_res.returncode == 0 else ""
        if sha:
            runs_res = run_command(
                [
                    "gh",
                    "api",
                    f"repos/{repo}/actions/runs?head_sha={sha}&status=completed&per_page=10",
                    "--jq",
                    '[.workflow_runs[] | select(.conclusion == "failure" or .conclusion == "cancelled") | .id] | .[0] // empty',
                ],
                cwd=cwd,
            )
            rid = runs_res.stdout.strip() if runs_res.returncode == 0 else ""
            if rid:
                run_ids.append(rid)
            else:
                any_run_res = run_command(
                    [
                        "gh",
                        "api",
                        f"repos/{repo}/actions/runs?head_sha={sha}&per_page=1",
                        "--jq",
                        ".workflow_runs[0].id // empty",
                    ],
                    cwd=cwd,
                )
                rid = any_run_res.stdout.strip() if any_run_res.returncode == 0 else ""
                if rid:
                    run_ids.append(rid)

    return run_ids


def dump_failure_logs(repo: str, num: str, cwd: Path | None = None, verbose: bool = True) -> None:
    """Print the evidence behind a red watch.

    ``verbose`` (the default) keeps the full dump: the `gh run view` log tails plus a
    `gh pr checks` dump. ``verbose=False`` is the slim `--watch` default — the failing run
    ID(s) and the one-line pointer, no log bodies.
    """
    run_ids = failing_run_ids(repo, num, cwd=cwd)
    if not verbose:
        ids = " ".join(run_ids) if run_ids else "(none resolved)"
        print(f"checks failed: failing run id(s): {ids}", file=sys.stderr)
        print(
            "run 'gh run view --run-id <id> --log-failed' (or 'ci.sh why') for the failing step log",
            file=sys.stderr,
        )
        return

    for run_id in run_ids[:2]:
        try:
            view_res = run_command(
                ["gh", "run", "view", run_id, "--repo", repo, "--log-failed"],
                timeout=LOG_TIMEOUT,
                cwd=cwd,
            )
            combined = (view_res.stdout + view_res.stderr).strip()
            if not combined or view_res.returncode != 0:
                view_res = run_command(
                    ["gh", "run", "view", run_id, "--repo", repo, "--log"],
                    timeout=LOG_TIMEOUT,
                    cwd=cwd,
                )
                combined = (view_res.stdout + view_res.stderr).strip()

            tail_lines = combined.splitlines()[-200:]
            if tail_lines:
                print("\n".join(tail_lines), file=sys.stderr)
        except PrError as e:
            print(f"warning: could not fetch run logs: {e}", file=sys.stderr)

    checks_res = run_command(
        ["gh", "pr", "checks", num, "--repo", repo],
        cwd=cwd,
    )
    combined_checks = (checks_res.stdout + checks_res.stderr).splitlines()
    tail_checks = combined_checks[-50:]
    if tail_checks:
        print("\n".join(tail_checks), file=sys.stderr)


def watch_checks(
    repo: str,
    num: str,
    base: str,
    poll_tries: int = POLL_TRIES,
    poll_interval: float = POLL_INTERVAL,
    cwd: Path | None = None,
    verbose: bool = False,
) -> bool:
    """Poll mergeability and every check until a verdict, one stderr line per poll.

    A conflict — or a mergeability GitHub never computes — fails fast through the shared
    refusal report. A `behind` head is accepted here: the fact rides the poll line, so a
    behind PR still prints exactly one line per poll. The `--merge` path refuses `behind`
    instead (see ``merge_state_verdict``). Output is slim by default: a failing check
    prints its run ID(s) and a `gh run view` pointer, and only `verbose` adds the log
    bodies.
    """
    for i in range(1, poll_tries + 1):
        obs = resolve_merge_state(repo, num, cwd=cwd)
        if obs.verdict in ("conflicting", "unknown"):
            report_merge_refusal(obs, repo, num, cwd=cwd)
            return False
        checks_res = run_command(
            [
                "gh",
                "pr",
                "checks",
                num,
                "--repo",
                repo,
                "--json",
                "name,bucket",
                "--jq",
                ".[] | [.name,.bucket] | @tsv",
            ],
            cwd=cwd,
        )
        payload = checks_res.stdout if checks_res.returncode == 0 else ""
        verdict = checks_verdict(payload)
        behind = f", head behind {base}" if obs.verdict == "behind" else ""
        print(
            f"checks {verdict} (mergeable_state={obs.state}, {i}/{poll_tries}{behind})",
            file=sys.stderr,
        )
        if verdict == "success":
            return True
        if verdict == "failure":
            dump_failure_logs(repo, num, cwd=cwd, verbose=verbose)
            return False
        time.sleep(poll_interval)

    print(
        f"checks timeout after {int(poll_tries * poll_interval)}s — no green verdict",
        file=sys.stderr,
    )
    if verbose:
        last_checks = run_command(
            ["gh", "pr", "checks", num, "--repo", repo],
            cwd=cwd,
        )
        tail_lines = (last_checks.stdout + last_checks.stderr).splitlines()[-30:]
        if tail_lines:
            print("\n".join(tail_lines), file=sys.stderr)
    return False


def pr_url(repo: str, num: str, cwd: Path | None = None) -> str:
    res = run_command(
        ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".html_url"],
        cwd=cwd,
    )
    if res.returncode != 0 or not res.stdout.strip():
        return f"https://github.com/{repo}/pull/{num}"
    return res.stdout.strip()


def ready_pr(repo: str, num: str, cwd: Path | None = None) -> bool:
    """Flip a draft PR to ready so CI's ready_for_review event fires.

    Prints the command to stderr before running it. A non-zero gh pr ready is not
    silent: the exact manual fix is printed verbatim and the caller must exit 1 —
    a draft that never went ready is not success.
    """
    cmd = ["gh", "pr", "ready", num, "--repo", repo]
    print(" ".join(cmd), file=sys.stderr)
    res = run_command(cmd, cwd=cwd)
    if res.returncode != 0:
        detail = res.stderr.strip() or "gh pr ready failed"
        print(f"gh pr ready failed for PR #{num}: {detail}", file=sys.stderr)
        print(
            f"remediation: PR #{num} is still a draft; run manually: gh pr ready {num} --repo {repo}",
            file=sys.stderr,
        )
        return False
    return True
