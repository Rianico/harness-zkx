"""Derived landing state for pr-land: the `--status` report and its fact builders.

State is derived from git and `gh` on every run and never stored (ADR-0021).
`collect_status` is read-only: it pushes nothing, creates nothing, and deletes
nothing — every subprocess read goes through the qualified
`_github.run_command(...)` lookup so the tests' single patch point still
intercepts. `gh` or git failures become advisory `refusals[]` entries, never a
traceback, and `--status` always exits 0.
"""

import contextlib
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import _github
from _changelog import _read_unreleased_block as _read_unreleased_block
from _changelog import unreleased_attributes_pr as unreleased_attributes_pr
from _errors import PrError as PrError
from _errors import RefusalError as RefusalError
from _errors import UsageError as UsageError
from _github import checks_verdict as checks_verdict
from _github import fetch_mergeability as fetch_mergeability
from _options import PrOptions as PrOptions
from _options import resolve_squash_override as resolve_squash_override
from _squash import CONVENTIONAL_TYPES as CONVENTIONAL_TYPES
from _squash import DEFAULT_TEMPLATE_PATH as DEFAULT_TEMPLATE_PATH
from _squash import FILL_SENTINEL_RE as FILL_SENTINEL_RE
from _squash import SQUASH_TITLE_MAX as SQUASH_TITLE_MAX
from _squash import SQUASH_TITLE_RE as SQUASH_TITLE_RE
from _squash import has_unfilled_sentinels as has_unfilled_sentinels
from _squash import is_unfilled_body as is_unfilled_body
from _squash import resolve_squash_message as resolve_squash_message

_LIB_DIR = str(Path(__file__).resolve().parents[3] / "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)
from range_authority import find_repo_root as find_repo_root

__all__ = [
    "ARTIFACT_PREFIX",
    "BODY_STATES",
    "CHECK_SCHEMA",
    "CHECK_STATES",
    "FAILURE_STATES",
    "MERGEABLE_STATES",
    "MUTATIONS",
    "PR_STATES",
    "SCAFFOLD_MARKER_PREFIX",
    "STATUS_SCHEMA",
    "TITLE_BUDGET",
    "artifact_stale",
    "body_site_with_line",
    "build_transitions",
    "classify_body",
    "collect_status",
    "degraded_report",
    "failing_tool",
    "first_sentinel_line",
    "head_slug",
    "make_refusal",
    "make_transition",
    "parse_checks",
    "pr_error_to_refusal",
    "preflight_title",
    "render_text",
    "resolve_artifact_path",
    "run_status",
    "title_gate",
]


STATUS_SCHEMA = "gh-router/pr-land/status@1"
CHECK_SCHEMA = "gh-router/pr-land/check@1"
TITLE_BUDGET = SQUASH_TITLE_MAX

PR_STATES = ("none", "open", "merged", "closed")
BODY_STATES = ("none", "scaffold", "unfilled", "ready")
CHECK_STATES = ("none", "pending", "green", "red")
MERGEABLE_STATES = ("unknown", "mergeable", "conflicting")
FAILURE_STATES = ("diverged", "head_stale", "stamp_failed")
MUTATIONS = ("none", "local", "remote")

ARTIFACT_PREFIX = Path(".lsz") / "gh-router"
SCAFFOLD_MARKER_PREFIX = "<!-- pr-land scaffold: head="


def first_sentinel_line(text: str) -> int | None:
    """1-based line number of the first `<FILL:>` sentinel, or None."""
    for lineno, line in enumerate(text.splitlines(), start=1):
        if FILL_SENTINEL_RE.search(line):
            return lineno
    return None


def body_site_with_line(site: str, text: str) -> str:
    """Append the first sentinel line (`pr_body.md:12`) when the text carries one."""
    lineno = first_sentinel_line(text)
    return f"{site}:{lineno}" if lineno is not None else site


def degraded_report(head: str, repo: str, refusals: list[dict[str, str]]) -> dict[str, object]:
    """Minimal pinned-schema report when derivation itself is impossible.

    Used when the head ref or repo slug cannot be resolved: `--status` still
    exits 0 and reports what it knows plus the advisory `refusals[]`.
    """
    return {
        "schema": STATUS_SCHEMA,
        "repo": repo,
        "head": head,
        "base": "main",
        "predicates": {
            "branch_pushed": False,
            "remote": "origin",
            "ahead": 0,
            "behind": 0,
            "pr_state": "none",
            "pr_number": None,
            "pr_draft": False,
            "body_state": "none",
            "worktree_clean": True,
            "changelog_stamped": False,
            "head_pushed": False,
            "checks": {"state": "none", "ok": 0, "total": 0},
            "mergeable": "unknown",
        },
        "failure_states": [],
        "artifact": {"path": "", "stale": False},
        "title": {"text": "", "chars": 0, "budget": TITLE_BUDGET, "derived": True},
        "squash_body_preview": "",
        "refusals": refusals,
        "transitions": [],
    }


def make_refusal(code: str, reason: str, remedy: str, site: str) -> dict[str, str]:
    """One `refusals[]` entry. `site` names the caller's input or artifact.

    `site` is a flag (`--title`), a caller file (`pr_body.md:12`), a caller ref
    (`origin/feat-x`), or the `gh` dependency — never a pr-land source location,
    which stays behind `--verbose`.
    """
    return {"code": code, "reason": reason, "remedy": remedy, "site": site}


def make_transition(command: str, preconditions: list[str], mutation: str) -> dict[str, object]:
    """One legal `transitions[]` entry: the command, what it needs, what it mutates."""
    if mutation not in MUTATIONS:
        raise ValueError(f"unknown mutation {mutation!r}")
    return {"command": command, "preconditions": list(preconditions), "mutation": mutation}


_SLUG_MAX_BYTES = 200


def head_slug(head_ref: str) -> str:
    """Branch-scoped scaffold leaf stem, injective over head refs.

    ASCII alphanumerics plus `._-` stay literal; every other character (including
    `/` and a literal `%`) becomes `%XX` uppercase hex over its UTF-8 bytes, so
    distinct branches never share a leaf and the stem stays filename-safe and
    directory-safe (a single path component). Stems longer than 200 bytes are
    capped to a readable prefix plus a 16-hex digest of the full ref, which keeps
    the mapping injective and every leaf within `NAME_MAX`.
    """
    parts: list[str] = []
    for char in head_ref:
        if char.isascii() and (char.isalnum() or char in "._-"):
            parts.append(char)
        else:
            parts.extend(f"%{byte:02X}" for byte in char.encode("utf-8"))
    slug = "".join(parts) or "head"
    if len(slug.encode("utf-8")) > _SLUG_MAX_BYTES:
        digest = hashlib.sha256(head_ref.encode("utf-8")).hexdigest()[:16]
        slug = f"{slug[:120]}-{digest}"
    return slug


def resolve_artifact_path(
    out_leaf: str | Path | None, head_ref: str, cwd: Path | None = None
) -> Path:
    """Resolve the scaffold artifact: `<repo-root>/.lsz/gh-router/<leaf>`.

    The leaf defaults to the head-ref slug so two branches never collide; `--out`
    names another leaf under the same tool-owned prefix. An absolute `--out`
    escapes the prefix deliberately (caller-owned path).
    """
    if out_leaf is not None and Path(out_leaf).is_absolute():
        return Path(out_leaf)
    try:
        root = find_repo_root(cwd or Path.cwd())
    except RuntimeError:
        root = (cwd or Path.cwd()).resolve()
    leaf = str(out_leaf) if out_leaf else f"{head_slug(head_ref)}.md"
    return (root / ARTIFACT_PREFIX / leaf).resolve()


def _marker_sha(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(SCAFFOLD_MARKER_PREFIX) and stripped.endswith("-->"):
            return stripped[len(SCAFFOLD_MARKER_PREFIX) : -len("-->")].strip()
    return None


def artifact_stale(path: Path, head_sha: str) -> bool:
    """Deterministic staleness of an existing artifact against the head commit.

    True when the file is missing its scaffold marker, unreadable, or marked for
    another commit. An absent leaf reports False — there is nothing stale.
    This only reports; nothing is ever decided from an artifact's bytes.
    """
    if not path.is_file():
        return False
    try:
        marked = _marker_sha(path.read_text(encoding="utf-8"))
    except OSError:
        return True
    if not marked:
        return True
    return marked != head_sha if head_sha else True


def classify_body(text: str, template_path: Path | None = None) -> str:
    """`body_state` for a description: scaffold, unfilled, or ready."""
    if SCAFFOLD_MARKER_PREFIX in text:
        return "scaffold"
    if not text.strip() or is_unfilled_body(text, template_path=template_path):
        return "unfilled"
    if has_unfilled_sentinels(text):
        return "unfilled"
    return "ready"


def parse_checks(payload: str) -> dict[str, object]:
    """`gh pr checks` TSV payload to the `checks` predicate: state plus ok/total."""
    lines = [line for line in payload.splitlines() if line.strip()]
    total = len(lines)
    ok = 0
    for line in lines:
        parts = line.split("\t")
        bucket = parts[1].strip() if len(parts) >= 2 else line.split()[-1]
        if bucket == "pass":
            ok += 1
    if total == 0:
        return {"state": "none", "ok": 0, "total": 0}
    verdict = checks_verdict(payload)
    state = {"success": "green", "failure": "red", "pending": "pending"}.get(verdict, "pending")
    return {"state": state, "ok": ok, "total": total}


def failing_tool(message: str) -> str:
    """Tool name from a `run_command` failure message, or empty when unknown."""
    marker = "command not found or not executable: "
    if marker in message:
        return message.split(marker, 1)[1].split(":")[0].strip().split(" ")[0]
    marker = "command timed out after "
    if marker in message:
        _span, sep, cmd = message.split(marker, 1)[1].partition(":")
        if sep:
            argv = cmd.strip().split(" ")
            return argv[0] if argv else ""
    return ""


def _infer_tool(message: str) -> str:
    """Guess the failing layer from message fingerprints, or empty when unknown.

    `gh`-side fingerprints win over `git`-side ones: a `gh api` failure quoting a
    `github.com` URL is still a `gh` failure, while a bare push/fetch-shaped
    message is `git`. Anything unrecognized stays empty and generic.
    """
    lowered = message.lower()
    if re.search(r"\bgh\b|gh api|pulls|mergeable|\bprs?\b|checks", lowered):
        return "gh"
    if any(
        marker in lowered
        for marker in (
            "github.com",
            "git ",
            "git:",
            "push",
            "fetch",
            "rev-list",
            "merge-base",
            "rebase",
            "origin/",
        )
    ):
        return "git"
    return ""


def pr_error_to_refusal(exc: BaseException, *, tool: str = "") -> dict[str, str] | None:
    """Map a `gh`/git failure to a structured refusal entry, or None when generic.

    `gh` missing, unauthenticated, or offline becomes data with a remedy instead
    of a traceback; anything else stays a plain error. `gh`-only markers apply
    solely when the failing layer resolved to `gh` — anything else (including
    an unrecognized layer) returns the generic `command_failed` entry, never a
    `gh_*` label for a `git` failure.
    """
    message = str(exc)
    lowered = message.lower()
    resolved = tool or failing_tool(message) or _infer_tool(message)
    if resolved == "gh":
        if "command not found or not executable: gh" in message:
            return make_refusal(
                "gh_unavailable",
                f"gh CLI is not installed or not executable: {message}",
                "install gh (https://cli.github.com) and authenticate with `gh auth login`, then re-run",
                "gh",
            )
        if "timed out" in lowered:
            return make_refusal(
                "gh_offline",
                f"gh did not answer in time: {message}",
                "check the network / GH_TOKEN scopes and re-run",
                "gh",
            )
    auth_markers = (
        "authenticate",
        "authenticated",
        "authentication",
        "401",
        "403",
        "bad credentials",
    )
    if resolved == "gh" and any(marker in lowered for marker in auth_markers):
        return make_refusal(
            "gh_unauthenticated",
            f"gh cannot authenticate: {message}",
            "run `gh auth login` (or export a fresh GH_TOKEN) and re-run",
            "gh",
        )
    offline_markers = (
        "could not resolve",
        "failed to connect",
        "network",
        "offline",
        "connection refused",
        "timed out",
    )
    if resolved == "gh" and any(marker in lowered for marker in offline_markers):
        return make_refusal(
            "gh_offline",
            f"github is unreachable: {message}",
            "check the network connection and re-run",
            "gh",
        )
    if resolved and resolved != "gh":
        return make_refusal(
            "command_failed",
            message,
            f"re-run once {resolved} answers; if it persists, run the failing command by hand",
            resolved,
        )
    if not resolved:
        return make_refusal(
            "command_failed",
            message,
            "re-run; if the failure persists, run the failing command by hand to see the tool involved",
            "unknown",
        )
    return None


def title_gate(title: str, num: str | None, *, derived: bool) -> dict[str, str] | None:
    """Advisory title check: None when the title holds, else the refusal entry.

    Without a PR number the length check runs against the bare title (an
    approximation the reason says out loud) — never a placeholder number, so the
    `--check`, create, and merge evaluations share one information state. The
    refusal names the derivation: `--title` when supplied, `HEAD` when derived.
    """
    site = "--title" if not derived else "HEAD"
    provenance = (
        "title from --title" if not derived else "title derived from the HEAD commit subject"
    )
    if not title.strip():
        return make_refusal(
            "title_missing",
            f"{provenance} is empty; a squash merge needs one Conventional Commit line",
            "pass --title 'type(scope): subject' explicitly, then re-run",
            site,
        )
    if num is not None:
        header = f"{title} (#{num})"
        if len(header) > TITLE_BUDGET:
            return make_refusal(
                "title_budget",
                f"{provenance} exceeds the {TITLE_BUDGET}-char budget "
                f"({len(header)} chars as {header!r})",
                "shorten the PR title, then re-run",
                site,
            )
    elif len(title) > TITLE_BUDGET:
        return make_refusal(
            "title_budget",
            f"{provenance} already exceeds the {TITLE_BUDGET}-char budget "
            f"({len(title)} chars, before the ` (#N)` suffix a PR number adds)",
            "shorten the PR title, then re-run",
            site,
        )
    match = SQUASH_TITLE_RE.match(title.strip())
    if match is None or match.group("type").casefold() not in CONVENTIONAL_TYPES:
        return make_refusal(
            "title_shape",
            f"{provenance} is not a Conventional Commit `type(scope): subject` line: {title!r}",
            "rename the PR title to `type(scope): subject` "
            "(feat, fix, docs, refactor, test, ...), then re-run",
            site,
        )
    return None


def preflight_title(title: str, *, derived: bool) -> None:
    """Fail-fast title gate for mutating commands: runs before any `gh` mutation.

    Raises RefusalError carrying the `refusals[]` entry (exit 1 with the facts
    attached). The merge path keeps its authoritative check against the final
    body and the real PR number.
    """
    entry = title_gate(title, None, derived=derived)
    if entry is not None:
        raise RefusalError(entry["reason"], refusals=[entry])


def _head_sha(cwd: Path | None = None) -> str:
    try:
        res = _github.run_command(["git", "rev-parse", "HEAD"], cwd=cwd)
    except PrError, OSError:
        return ""
    return res.stdout.strip() if res.returncode == 0 else ""


def _worktree_clean(cwd: Path | None = None) -> bool:
    try:
        res = _github.run_command(["git", "--no-optional-locks", "status", "--porcelain"], cwd=cwd)
    except PrError, OSError:
        return True
    if res.returncode != 0:
        return True
    return not any(line.strip() for line in res.stdout.splitlines())


def _query_pr(repo: str, head_ref: str, cwd: Path | None = None) -> tuple[str, str | None, bool]:
    """(pr_state, pr_number, pr_draft) for the head branch; raises PrError on failure."""
    owner = repo.split("/")[0]
    res = _github.run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls?head={owner}:{head_ref}&state=all",
            "--jq",
            r'.[0] | "\(.number)\t\(.state)\t\(.isDraft)\t\(.merged)"',
        ],
        cwd=cwd,
    )
    if res.returncode != 0:
        raise PrError(
            f"failed to query PRs for head {head_ref}: {res.stderr.strip() or 'gh api failed'}"
        )
    line = res.stdout.strip()
    if not line or line == "null":
        return ("none", None, False)
    fields = line.split("\t")
    num = fields[0].strip() or None
    if num is None:
        return ("none", None, False)
    state = fields[1].strip() if len(fields) > 1 else "open"
    is_draft = len(fields) > 2 and fields[2].strip().lower() == "true"
    merged = len(fields) > 3 and fields[3].strip().lower() == "true"
    if state == "open":
        return ("open", num, is_draft)
    if merged:
        return ("merged", num, False)
    return ("closed", num, False)


def _pr_body(repo: str, num: str, cwd: Path | None = None) -> str:
    res = _github.run_command(
        ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", '.body // ""'], cwd=cwd
    )
    if res.returncode != 0:
        raise PrError(
            f"failed to fetch body for PR #{num}: {res.stderr.strip() or 'gh api failed'}"
        )
    return res.stdout


def build_transitions(
    *,
    head_ref: str,
    remote: str,
    repo: str,
    pr_number: str | None,
    pr_state: str,
    pr_draft: bool,
    body_state: str,
    body_path: str,
    branch_pushed: bool,
    failure_states: list[str],
    worktree_clean: bool,
) -> list[dict[str, object]]:
    """Legal transitions for the current derived state, each with its mutation."""
    transitions: list[dict[str, object]] = []
    if "diverged" in failure_states:
        transitions.append(
            make_transition(
                f"git pull --rebase {remote} {head_ref}",
                ["worktree_clean"] if worktree_clean else ["stash or commit local work first"],
                "local",
            )
        )
    if body_state != "ready":
        transitions.append(
            make_transition(
                f"pr.py --check --body-file {body_path}",
                ["authored body: fill or delete every <FILL:> slot"],
                "local",
            )
        )
    if pr_state == "none":
        if not branch_pushed:
            transitions.append(
                make_transition(
                    f"git push {remote} {head_ref}",
                    ["diverged resolved"] if "diverged" in failure_states else [],
                    "remote",
                )
            )
        transitions.append(
            make_transition(
                f"pr.py --body-file {body_path}",
                ["branch_pushed", "body_state == ready", "title within budget"],
                "remote",
            )
        )
    if pr_state == "open" and pr_draft:
        transitions.append(
            make_transition(
                f"gh pr ready {pr_number} --repo {repo}",
                ["changelog_stamped"],
                "remote",
            )
        )
    if pr_state == "open":
        transitions.append(make_transition("pr.py --watch", ["pr_state == open"], "none"))
        transitions.append(
            make_transition(
                "pr.py --merge --squash-message-file <path>",
                [
                    "checks green",
                    "mergeable",
                    "title gate",
                    "squash message supplied",
                ],
                "remote",
            )
        )
    return transitions


def collect_status(
    *,
    head_ref: str,
    repo: str,
    title: str,
    body: str,
    title_supplied: bool,
    body_supplied: bool,
    body_site: str,
    squash_override: str | None,
    squash_supplied: bool,
    out_leaf: str | Path | None,
    template_path: Path | None = None,
    cwd: Path | None = None,
) -> tuple[dict[str, object], list[str]]:
    """Derive the pinned `--status --json` report plus stderr commentary notes.

    Read-only: pushes nothing, creates nothing, deletes nothing. Every refusal a
    mutating command would raise from this state is listed advisory in
    `refusals[]`; the exit code stays 0 for the caller (`pr.py`) to keep.
    """
    refusals: list[dict[str, str]] = []
    notes: list[str] = []
    gh_broken = False

    def note_gh(exc: BaseException, what: str) -> None:
        nonlocal gh_broken
        entry = pr_error_to_refusal(exc, tool="gh")
        if entry is None:
            entry = make_refusal(
                "gh_query_failed",
                f"could not {what}: {exc}",
                "check the network / GH_TOKEN scopes and re-run",
                "gh",
            )
        if not gh_broken:
            refusals.append(entry)
            gh_broken = True

    try:
        remote = _github.repo_remote_for_ref(head_ref, cwd=cwd)
    except PrError, OSError:
        remote = "origin"
    try:
        branch_exists = _github._remote_branch_exists(head_ref, cwd=cwd, remote=remote)
    except PrError, OSError:
        branch_exists = False
    ahead = behind = 0
    compare_failed = False
    if branch_exists:
        try:
            ahead, behind = _github._ahead_behind(head_ref, remote, cwd=cwd)
        except (PrError, OSError) as exc:
            # Never assert a push fact from a failed read: a failed compare must
            # not report branch_pushed/head_pushed, so record the failure here and
            # force both flags False below.
            compare_failed = True
            ahead, behind = 0, 0
            base_entry = pr_error_to_refusal(exc, tool="git") or make_refusal(
                "compare_failed",
                f"could not compare {head_ref} against {remote}/{head_ref}: {exc}",
                f"fetch {remote} and re-run",
                f"{remote}/{head_ref}",
            )
            refusals.append(
                {
                    **base_entry,
                    "reason": f"could not compare {head_ref} against {remote}/{head_ref}: {base_entry['reason']}",
                }
            )
    branch_pushed = branch_exists and behind == 0 and not compare_failed

    sha = _head_sha(cwd)
    clean = _worktree_clean(cwd)

    try:
        base: str | None = _github.resolve_base(None, repo, cwd=cwd)
    except PrError, OSError:
        base = None
    try:
        default_base = _github.default_branch(repo, cwd=cwd)
    except PrError, OSError:
        default_base = None
    base_name = base or default_base or "main"

    pr_state = "none"
    pr_number: str | None = None
    pr_draft = False
    try:
        pr_state, pr_number, pr_draft = _query_pr(repo, head_ref, cwd)
    except (PrError, OSError) as exc:
        note_gh(exc, f"query PRs for head {head_ref}")

    artifact_path = resolve_artifact_path(out_leaf, head_ref, cwd)
    try:
        display_path = str(artifact_path.relative_to(find_repo_root(cwd or Path.cwd())))
    except RuntimeError, ValueError, OSError:
        display_path = str(artifact_path)
    stale = artifact_stale(artifact_path, sha)
    if not body_site:
        body_site = display_path

    pr_text = ""
    if pr_state == "open" and pr_number is not None and not body_supplied:
        try:
            pr_text = _pr_body(repo, pr_number, cwd)
        except (PrError, OSError) as exc:
            note_gh(exc, f"fetch body for PR #{pr_number}")
    artifact_text = ""
    if not body_supplied and not pr_text and artifact_path.is_file():
        try:
            artifact_text = artifact_path.read_text(encoding="utf-8")
        except OSError:
            artifact_text = ""
    active_body = body if (body_supplied or body) else (pr_text or artifact_text)
    if template_path is None:
        template_path = DEFAULT_TEMPLATE_PATH
    if cwd is not None and not template_path.is_absolute():
        template_for_classify = cwd / template_path
    else:
        template_for_classify = template_path
    if body_supplied or pr_text or artifact_text:
        body_state = classify_body(active_body, template_path=template_for_classify)
    else:
        body_state = "none"

    changelog_stamped = pr_number is not None and unreleased_attributes_pr(pr_number, cwd=cwd)
    head_pushed = branch_exists and ahead == 0 and behind == 0 and not compare_failed

    checks: dict[str, object] = {"state": "none", "ok": 0, "total": 0}
    if pr_state == "open" and pr_number is not None:
        try:
            checks_res = _github.run_command(
                [
                    "gh",
                    "pr",
                    "checks",
                    pr_number,
                    "--repo",
                    repo,
                    "--json",
                    "name,bucket",
                    "--jq",
                    ".[] | [.name,.bucket] | @tsv",
                ],
                cwd=cwd,
            )
        except (PrError, OSError) as exc:
            note_gh(exc, f"read checks for PR #{pr_number}")
            checks_res = None
        if checks_res is not None and checks_res.returncode == 0:
            checks = parse_checks(checks_res.stdout)
        elif checks_res is not None:
            note_gh(
                PrError(
                    "failed to read checks for PR #{}: {}".format(
                        pr_number,
                        checks_res.stderr.strip() or "gh pr checks failed",
                    )
                ),
                f"read checks for PR #{pr_number}",
            )

    mergeable = "unknown"
    merge_verdict = "unknown"
    if pr_state == "open" and pr_number is not None:
        try:
            obs = fetch_mergeability(repo, pr_number, cwd=cwd)
            merge_verdict = obs.verdict
            if obs.verdict in ("clean", "behind"):
                mergeable = "mergeable"
            elif obs.verdict == "conflicting":
                mergeable = "conflicting"
        except (PrError, OSError) as exc:
            note_gh(exc, f"read mergeability for PR #{pr_number}")

    failure_states: list[str] = []
    if behind > 0:
        failure_states.append("diverged")
        refusals.append(
            make_refusal(
                "diverged",
                f"remote {remote}/{head_ref} is ahead ({behind} remote-only commit(s)); "
                "a push would be refused",
                f"reconcile first (e.g. git pull --rebase {remote} {head_ref}), then re-run; "
                "pr-land never force-pushes",
                f"{remote}/{head_ref}",
            )
        )
    if merge_verdict == "behind":
        failure_states.append("head_stale")
    if (
        pr_state == "open"
        and pr_number is not None
        and _read_unreleased_block(cwd) is not None
        and not changelog_stamped
    ):
        failure_states.append("stamp_failed")

    if not body_supplied and body_state == "none":
        refusals.append(
            make_refusal(
                "body_missing",
                "no description supplied and no PR body or scaffold leaf found; "
                "opening a PR requires a description",
                f"author the description, then re-run with --body-file {display_path} "
                "(or run body-less --check to write the scaffold leaf)",
                body_site,
            )
        )
    elif body_state == "unfilled":
        refusals.append(
            make_refusal(
                "body_unfilled",
                "the description is empty, the unfilled repo template, or still "
                "carries <FILL:> placeholders",
                "fill every placeholder (or delete the Closes slot), then re-run",
                body_site_with_line(body_site, active_body),
            )
        )

    title_entry = title_gate(title, pr_number, derived=not title_supplied)
    if title_entry is not None:
        refusals.append(title_entry)

    if pr_state == "open" and pr_draft and pr_number is not None:
        refusals.append(
            make_refusal(
                "pr_draft",
                f"PR #{pr_number} is still a draft; reuse never flips draft state, "
                "so --watch/--merge would refuse",
                f"run manually: gh pr ready {pr_number} --repo {repo}",
                f"PR #{pr_number}",
            )
        )
    if checks.get("state") == "red" and pr_number is not None:
        refusals.append(
            make_refusal(
                "checks_failing",
                f"checks are red on PR #{pr_number} "
                f"({checks.get('ok')}/{checks.get('total')} passing)",
                "fix the failing checks, then re-run",
                f"PR #{pr_number}",
            )
        )
    if pr_state == "open" and mergeable == "conflicting" and pr_number is not None:
        refusals.append(
            make_refusal(
                "merge_conflict",
                f"PR #{pr_number} is conflicting (mergeable_state={merge_verdict})",
                "run the pr-conflict surface to inspect hunks and commit intent, "
                "then reconcile and re-run",
                f"PR #{pr_number}",
            )
        )
    if pr_state == "open" and mergeable == "unknown" and pr_number is not None:
        refusals.append(
            make_refusal(
                "mergeability_unknown",
                f"github has not computed mergeability for PR #{pr_number} "
                f"(mergeable_state={merge_verdict})",
                "wait for github to compute mergeability, then re-run",
                f"PR #{pr_number}",
            )
        )

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            preview = resolve_squash_message(
                active_body,
                explicit=squash_override,
                supplied=squash_supplied,
                template_path=template_for_classify,
            )
        except RefusalError:
            preview = ""
        except Exception:  # noqa: BLE001 — advisory preview must never break --status
            preview = ""
    title_text = title
    transitions = build_transitions(
        head_ref=head_ref,
        remote=remote,
        repo=repo,
        pr_number=pr_number,
        pr_state=pr_state,
        pr_draft=pr_draft,
        body_state=body_state,
        body_path=display_path,
        branch_pushed=branch_pushed,
        failure_states=failure_states,
        worktree_clean=clean,
    )

    report: dict[str, object] = {
        "schema": STATUS_SCHEMA,
        "repo": repo,
        "head": head_ref,
        "base": base_name,
        "predicates": {
            "branch_pushed": branch_pushed,
            "remote": remote,
            "ahead": ahead,
            "behind": behind,
            "pr_state": pr_state,
            "pr_number": pr_number,
            "pr_draft": pr_draft,
            "body_state": body_state,
            "worktree_clean": clean,
            "changelog_stamped": changelog_stamped,
            "head_pushed": head_pushed,
            "checks": checks,
            "mergeable": mergeable,
        },
        "failure_states": failure_states,
        "artifact": {"path": display_path, "stale": stale},
        "title": {
            "text": title_text,
            "chars": len(title_text),
            "budget": TITLE_BUDGET,
            "derived": not title_supplied,
        },
        "squash_body_preview": preview,
        "refusals": refusals,
        "transitions": transitions,
    }
    return report, notes


def render_text(report: dict[str, object]) -> str:
    """Human-readable `--status` facts for stdout (commentary stays on stderr)."""
    predicates = report["predicates"]
    assert isinstance(predicates, dict)
    checks = predicates["checks"]
    assert isinstance(checks, dict)
    artifact = report["artifact"]
    assert isinstance(artifact, dict)
    title = report["title"]
    assert isinstance(title, dict)
    failures = report["failure_states"]
    assert isinstance(failures, list)
    refusals = report["refusals"]
    assert isinstance(refusals, list)
    transitions = report["transitions"]
    assert isinstance(transitions, list)
    lines = [
        f"repo: {report['repo']} head: {report['head']} base: {report['base']}",
        "predicates: "
        f"branch_pushed={str(predicates['branch_pushed']).lower()} "
        f"remote={predicates['remote']} "
        f"ahead={predicates['ahead']} behind={predicates['behind']} "
        f"pr={predicates['pr_state']}"
        + (f" #{predicates['pr_number']}" if predicates["pr_number"] is not None else "")
        + f" draft={str(predicates['pr_draft']).lower()} "
        f"body={predicates['body_state']} "
        f"clean={str(predicates['worktree_clean']).lower()} "
        f"stamped={str(predicates['changelog_stamped']).lower()} "
        f"head_pushed={str(predicates['head_pushed']).lower()} "
        f"checks={checks['state']} {checks['ok']}/{checks['total']} "
        f"mergeable={predicates['mergeable']}",
        f"failure_states: {', '.join(str(f) for f in failures) if failures else 'none'}",
        f"artifact: {artifact['path']} stale={str(artifact['stale']).lower()}",
        f"title ({'derived' if title['derived'] else 'from --title'}): "
        f"{title['text']!r} {title['chars']}/{title['budget']} chars",
    ]
    preview = str(report["squash_body_preview"])
    if preview.strip():
        lines.append("squash_body_preview:")
        lines.extend(preview.splitlines())
    else:
        lines.append("squash_body_preview: (none — no usable body)")
    if refusals:
        lines.append("refusals:")
        for entry in refusals:
            assert isinstance(entry, dict)
            lines.append(
                f"  - {entry['code']}: {entry['reason']} "
                f"[remedy: {entry['remedy']}] [site: {entry['site']}]"
            )
    else:
        lines.append("refusals: none")
    if transitions:
        lines.append("transitions:")
        for entry in transitions:
            assert isinstance(entry, dict)
            preconditions = ", ".join(str(p) for p in entry["preconditions"]) or "—"
            lines.append(
                f"  - {entry['command']} (needs: {preconditions}; mutates: {entry['mutation']})"
            )
    else:
        lines.append("transitions: none")
    return "\n".join(lines) + "\n"


def _status_body_site(options: PrOptions) -> str:
    """Where `--status` looked for the description: flag, or empty for the leaf."""
    if options.body_file is not None:
        return f"--body-file {options.body_file}"
    if options.body is not None:
        return "--body"
    return ""


def _emit_status(report: dict[str, object], options: PrOptions) -> int:
    if options.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report), end="")
    return 0


def run_status(options: PrOptions, cwd: Path | None = None) -> int:
    """Read-only landing state: derive, emit, exit 0 — never refuse.

    Head/repo resolution failures degrade to the minimal report with the
    advisory refusals attached; body/squash file failures degrade the same way
    while the rest of the state still derives.
    """
    head_ref = ""
    head_entry: dict[str, str] | None = None
    try:
        head_ref = _github.resolve_head(options.head)
    except UsageError as exc:
        head_entry = make_refusal(
            "unusable_head",
            str(exc),
            "pass --head <branch> for a real head ref, then re-run",
            "--head",
        )
    except (PrError, OSError) as exc:
        head_entry = pr_error_to_refusal(exc, tool="git") or make_refusal(
            "command_failed",
            str(exc),
            "re-run once git answers; if it persists, run the failing command by hand",
            "git",
        )
    if head_entry is not None:
        return _emit_status(
            degraded_report(
                options.head or "",
                "",
                [head_entry],
            ),
            options,
        )
    extra: list[dict[str, str]] = []
    title, body, title_supplied, body_supplied = "", "", False, False
    try:
        title, body, title_supplied, body_supplied = _github.resolve_title_and_body(options)
    except UsageError as exc:
        extra.append(
            make_refusal(
                "body_file_unreadable",
                str(exc),
                "pass a readable --body-file, then re-run",
                f"--body-file {options.body_file}",
            )
        )
    except (PrError, OSError) as exc:
        extra.append(
            pr_error_to_refusal(exc, tool="git")
            or make_refusal(
                "command_failed",
                str(exc),
                "re-run once git answers; if it persists, run the failing command by hand",
                "git",
            )
        )
    squash_override, squash_supplied = None, False
    try:
        squash_override, squash_supplied = resolve_squash_override(options)
    except UsageError as exc:
        extra.append(
            make_refusal(
                "squash_message_unreadable",
                str(exc),
                "pass a readable --squash-message-file, then re-run",
                "--squash-message-file",
            )
        )
    repo = ""
    repo_error: BaseException | None = None
    repo_usage = False
    try:
        repo = _github.resolve_repo(head_ref)
    except UsageError as exc:
        repo_error = exc
        repo_usage = True
    except (PrError, OSError) as exc:
        repo_error = exc
    if repo_error is not None:
        try:
            remote = _github.repo_remote_for_ref(head_ref)
        except PrError, OSError:
            remote = "origin"
        if repo_usage:
            repo_entry = make_refusal(
                "repo_unresolvable",
                str(repo_error),
                "configure a GitHub remote for the branch, then re-run",
                remote,
            )
        else:
            repo_entry = pr_error_to_refusal(repo_error, tool="git") or make_refusal(
                "command_failed",
                str(repo_error),
                "re-run once git answers; if it persists, run the failing command by hand",
                "git",
            )
        return _emit_status(
            degraded_report(
                head_ref,
                "",
                [
                    repo_entry,
                    *extra,
                ],
            ),
            options,
        )
    report, notes = collect_status(
        head_ref=head_ref,
        repo=repo,
        title=title,
        body=body,
        title_supplied=title_supplied,
        body_supplied=body_supplied,
        body_site=_status_body_site(options),
        squash_override=squash_override,
        squash_supplied=squash_supplied,
        out_leaf=options.out,
        cwd=cwd,
    )
    existing = report["refusals"]
    assert isinstance(existing, list)
    report["refusals"] = [*extra, *existing]
    for note in notes:
        print(note, file=sys.stderr)
    return _emit_status(report, options)
