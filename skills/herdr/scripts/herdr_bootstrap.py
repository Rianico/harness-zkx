#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-bootstrap — give a freshly started agent its role invariant before compaction can drop it.

A compacted agent forgets its lane. It stops delegating heavy work to subagents, and it exits
without replying to its caller. Both obligations are lane identity, not task detail, so they
must be re-asserted on every start, not trusted to survive in context. This helper stamps the
ROLE INVARIANT snippet (role, subagent-first mandate, reply contract) into the one surface the
target agent reads at launch, then starts it with the scoped name as both pane label and agent
name.

    herdr-bootstrap msg-impl-1 --kind codex  --pane w1:p3 --role impl-1 --task-group msg
    herdr-bootstrap --kind pi    --pane w1:p3 --role tm   --task-group msg --model claude-3-7-sonnet
    herdr-bootstrap msg-tm --kind claude --pane w1:p2 --role tm --dry-run

Two delivery mechanisms, chosen by `--kind` via skills/herdr/references/kinds.yaml:

- Inline kinds take the snippet through the kind's own `invariant_flag` (see
  skills/herdr/references/kinds.yaml), whose value is the absolute path of a per-agent
  lane-local file (``<target_dir>/.lane/invariants/<agent-name>.md``) holding the snippet,
  keyed by the resolved agent name so one lane's agents never overwrite each other. The
  flag is per-kind because the flags differ: `pi` reads file contents through
  ``--append-system-prompt`` while `claude` reads a path only through
  ``--append-system-prompt-file``. Herdr refuses any agent arg that cannot be encoded
  safely for the target shell — a newline is enough — and the rendered snippet is
  multi-line, so the text itself can never ride inline.
- File-reading kinds (`cline`, `codex`, `copilot`, `qodercli`, `agy`) and any unknown kind get
  the marker-wrapped block appended to ``AGENTS.md`` in the target directory. `cline` prefers
  an existing ``.clinerules`` over ``AGENTS.md``.
The append is idempotent: the marker pair (``<!-- herdr-bootstrap:role-invariant -->``) is
written once, so re-bootstrapping the same directory never duplicates the snippet and never
rewrites an untouched file.

The append also refuses to modify a version-controlled target. The target file *is* the
delivery mechanism for the file kinds — they have no ``--append-system-prompt`` and bootstrap
has no message channel — so the invariant cannot move to a lane-local file the agent never
reads. Instead: an already-present marker block is left alone and the launch proceeds, and a
tracked target that the append would change is refused (exit 2) naming
``--allow-tracked-invariant``, which appends anyway and leaves the file modified on the
record. An untracked file, or a file outside any repository, is appended as before — that
dirties nothing tracked, though a new lane-local file still shows as ``??`` in ``git status``.
Targets whose version-control state cannot be determined are handled by kind: a repository
that exists on disk — git confirms it, or a `.git` entry stands at or above the target while
git refused to read it — whose tracked state git cannot read (an unreadable index, dubious
ownership, an unreadable ``.git``, or a ``GIT_DIR``/``GIT_INDEX_FILE``/``GIT_WORK_TREE``
override) is refused, and, like the tracked refusal, overridable; only a git that cannot run at
all still gets the append — the invariant must reach the agent — with one warning line saying
the tracked state could not be determined, so a missing git never silently withholds the
invariant.

Deliberate quirks (implemented minimally, documented here): trust flags come only from
``kinds.yaml`` and ride after ``--`` as native agent args — bootstrap never invents flags, and an
unverified kind carries none; an unknown kind falls back to the universal ``AGENTS.md`` append
rather than failing, so a new kind is bootstrapped by default. When ``--cwd`` names a worktree,
bootstrap refuses a missing directory, a path that is not a registered linked worktree, and the
main checkout once the repository already has linked worktrees; the pane cwd must already agree
with the requested path before that check runs.
bootstrap cds the pane there and refuses to start when the pane does not converge.
Exit status: 0 ok, 1 herdr failure, 2 usage or missing precondition.

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_OK,
    METHOD_CONSTRAINT_EPILOG,
    HerdrError,
    UsageError,
    add_shared_argument,
    entries,
    entry_optional_text,
    entrypoint,
    find_herdr,
    reply_helper,
    require_herdr_env,
    run_herdr_checked,
    scoped_agent_name,
    validate_agent_name,
)

# The one place a pane rename is spelled, shared with `herdr-label` and the reconciliation pass
# (#182 t5 2.4); same flat-sibling import as `herdr-pane`.
from herdr_label import pane_rename_argv
from herdr_worktree import (
    expected_worktree_name,
    parse_git_worktree_entries,
    worktree_key,
)

AGENTS_MD = "AGENTS.md"
CLINE_RULES = ".clinerules"
# Lane-local delivery surface for the inline kinds: bootstrap writes one file per agent here
# and passes only the path, because herdr rejects an agent arg containing a newline. One file
# per resolved agent name, so bootstrapping a second agent never overwrites the first.
LANE_DIR = ".lane"
INVARIANTS_DIR = "invariants"
INVARIANT_SUFFIX = ".md"
# Characters allowed inside the derived file name; everything else becomes `_`.
INVARIANT_NAME_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")
# A bare script name is one path segment, so it takes the same `[A-Za-z0-9._-]` charset this
# module already uses for the derived invariant file name (and `herdr_worktree.BRANCH_UNSAFE_RE`
# for branch slugs). No path separator, quote character, shell metacharacter, or whitespace can
# match it. A dot stays legal, because a bridge script may carry a `.sh` suffix; `.` and `..` are
# path segments rather than names, so they are refused next to the charset.
BARE_SCRIPT_NAME_PATTERN = r"[A-Za-z0-9._-]+"
NON_NAME_SEGMENTS = (".", "..")
# Roles the docs spell `impl-<n>`; only they carry the implementer cooperation contract.
IMPLEMENTER_PREFIX = "impl"
# Roles spelling a coordination authority — bare or scoped (`tm`, `msg-tm`, `lane-orch`,
# `task-manager`). A term is itself split on the role separators, so `task-manager` matches as
# one consecutive segment run and `orchid` never matches `orch`.
TM_ROLE_TERMS = (
    "tm",
    "task-manager",
    "task_manager",
    "orch",
    "orchestrator",
    "coord",
    "coordinator",
)
# The scoped naming convention `<task-group-slug>-<role>[-<subrole|index>]` puts the role in a
# segment of its own, so the discriminator splits before it matches a prefix.
IMPLEMENTER_SEGMENT_SPLIT = re.compile(r"[-_]")
VOWELS = frozenset("aeiou")
START_MARKER = "<!-- herdr-bootstrap:role-invariant -->"
END_MARKER = "<!-- /herdr-bootstrap:role-invariant -->"

# Startup contract per kind, loaded from skills/herdr/references/kinds.yaml.
# Unknown kinds fall back to the file append with no trust flags (forward-compatible).
KINDS_CONFIG = Path(__file__).resolve().parent.parent / "references" / "kinds.yaml"

_CWD_POLL_S = 0.25
# The flag the tracked-target refusal names: the caller opts in to a deliberately dirty tree.
TRACKED_OVERRIDE_FLAG = "--allow-tracked-invariant"

# Environment variables that point git at a worktree, index, or object store other than the one
# the target file lives in. Each outranks `-C`, so a probe run with one set answers about that
# override, not about the file's real repository; the tracked state is then undetermined.
GIT_LOCATION_OVERRIDE_VARS: tuple[str, ...] = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")


@dataclass(frozen=True)
class KindEntry:
    """One kind's startup contract: trust flags, the invariant surface, revision behaviour.

    `lifecycle_bridge` names the bridge script that carries this kind's lifecycle signals,
    used by advice that must point at a trustworthy status surface; a kind that declares
    none is advised in bridge-neutral terms rather than another kind's bridge (#238). It is
    a bare script name, so the advice names one path segment, never a path or a command.
    """

    trust_flags: tuple[str, ...]
    inline_invariant: bool
    invariant_flag: str | None = None
    revision_moves: bool = True
    lifecycle_bridge: str | None = None


FALLBACK_ENTRY = KindEntry(trust_flags=(), inline_invariant=False)


# Bounded wait after a fresh `agent start`, before the pane is treated as acceptant (#238).
# A freshly spawned pane can report `interactive_ready: true` and `agent_status: idle` while
# still initialising, so the first prompt is swallowed. One fixed sleep, never a poll until
# steady state, and only ever on a just-spawned pane: an existing idle pane pays nothing.
DEFAULT_SETTLE_SECONDS = 5.0


def _sleep(seconds: float) -> None:
    """Sleep seam: tests monkeypatch this module attribute to skip real delays."""
    time.sleep(seconds)


def settle_fresh_pane(seconds: float) -> None:
    """Wait `seconds` after a fresh `agent start`, so a starting pane is not treated as acceptant.

    Shared by both spawn paths (`bootstrap` and the reply helper's `--auto-start` revive).
    `--settle 0` is exact: no sleep at all, not a token sleep.
    """
    if seconds <= 0:
        return
    _sleep(seconds)


def _parse_flow_flags(value: str, lineno: int) -> tuple[str, ...]:
    """Parse `["--approve", ...]`; only the quoted bracket flow list is accepted."""
    body = value.strip()
    if not (body.startswith("[") and body.endswith("]")):
        raise ValueError(f"line {lineno}: trust_flags must be a [...] flow list")
    inner = body[1:-1].strip()
    if not inner:
        return ()
    flags: list[str] = []
    for item in inner.split(","):
        flag = item.strip()
        if len(flag) < 2 or flag[0] not in "'\"" or not flag.endswith(flag[0]):
            raise ValueError(f"line {lineno}: trust_flags items must be quoted")
        text = flag[1:-1]
        if not text.startswith("-"):
            raise ValueError(f"line {lineno}: trust flag {text!r} must start with '-'")
        flags.append(text)
    return tuple(flags)


def parse_kinds_config(text: str) -> dict[str, KindEntry]:
    """Parse the strict kinds.yaml subset: kind tables with trust_flags, invariant,
    invariant_flag, revision_moves, and lifecycle_bridge.

    Values may not contain `#`; block sequences are rejected — use the flow list.
    Raises ValueError with a line number on anything outside the subset.
    """
    raw: dict[str, dict[str, str | tuple[str, ...] | bool]] = {}
    current: str | None = None
    for lineno, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            name, sep, rest = line.partition(":")
            if not sep or rest.strip() or not name.strip():
                raise ValueError(f"line {lineno}: expected `kind:`")
            current = name.strip()
            if current in raw:
                raise ValueError(f"line {lineno}: duplicate kind {current!r}")
            raw[current] = {}
        elif current is None or indent != 2:
            raise ValueError(f"line {lineno}: expected two-space `key: value`")
        else:
            key, sep, value = line.strip().partition(":")
            key = key.strip()
            if not sep or not key or key in raw[current]:
                raise ValueError(f"line {lineno}: bad or duplicate key")
            cleaned = value.strip()
            if key == "trust_flags":
                raw[current][key] = _parse_flow_flags(cleaned, lineno)
            elif key == "invariant":
                if cleaned not in ("inline", "file"):
                    raise ValueError(f"line {lineno}: invariant must be inline or file")
                raw[current][key] = cleaned
            elif key == "invariant_flag":
                if not cleaned.startswith("--") or any(ch.isspace() for ch in cleaned):
                    raise ValueError(
                        f"line {lineno}: invariant_flag must be one --flag without spaces"
                    )
                raw[current][key] = cleaned
            elif key == "revision_moves":
                if cleaned not in ("true", "false"):
                    raise ValueError(f"line {lineno}: revision_moves must be true or false")
                raw[current][key] = cleaned == "true"
            elif key == "lifecycle_bridge":
                is_bare = re.fullmatch(BARE_SCRIPT_NAME_PATTERN, cleaned) is not None
                if not is_bare or cleaned in NON_NAME_SEGMENTS:
                    raise ValueError(
                        f"line {lineno}: lifecycle_bridge must be a bare script name (one path "
                        f"segment, want {BARE_SCRIPT_NAME_PATTERN}; `.` and `..` are not names)"
                    )
                raw[current][key] = cleaned
            else:
                raise ValueError(f"line {lineno}: unknown key {key!r}")
    entries: dict[str, KindEntry] = {}
    for kind, item in raw.items():
        flags = item.get("trust_flags")
        invariant = item.get("invariant")
        flag = item.get("invariant_flag")
        moves = item.get("revision_moves", True)
        bridge = item.get("lifecycle_bridge")
        if not isinstance(flags, tuple) or invariant not in ("inline", "file"):
            raise ValueError(f"kind {kind!r}: needs trust_flags [...] and invariant inline|file")
        if invariant == "inline" and not isinstance(flag, str):
            raise ValueError(
                f"kind {kind!r}: an inline kind needs invariant_flag naming the flag "
                "that takes the snippet file (a text-only flag would receive the path "
                "as literal prompt text)"
            )
        if invariant == "file" and flag is not None:
            raise ValueError(f"kind {kind!r}: a file kind takes no invariant_flag")
        entries[kind] = KindEntry(
            trust_flags=flags,
            inline_invariant=invariant == "inline",
            invariant_flag=flag if isinstance(flag, str) else None,
            revision_moves=bool(moves),
            lifecycle_bridge=bridge if isinstance(bridge, str) else None,
        )
    return entries


def load_kind_entry(kind: str, config_path: Path | None = None) -> KindEntry:
    """Read one kind's contract from kinds.yaml; unknown kinds take the file fallback."""
    path = KINDS_CONFIG if config_path is None else config_path
    try:
        text = path.read_text()
    except OSError as exc:
        raise UsageError(f"cannot read kind config {path}: {exc}") from exc
    try:
        table = parse_kinds_config(text)
    except ValueError as exc:
        raise UsageError(f"bad kind config {path}: {exc}") from exc
    return table.get(kind, FALLBACK_ENTRY)


# The snippet is the only coordination channel that survives compaction, so it states the lane
# coordination pattern plainly, then the two standing obligations. The reply helper is this
# lane's own `herdr_reply.py` and is rendered as an absolute path resolved from this tree: the
# contract is exactly what an agent with no context left runs, so the command must spawn from
# any cwd. The derivation is single-sourced in `herdr_cli.reply_helper()` — the
# `~/.agents/skills/herdr` symlink is deliberately not used, since it resolves into another
# worktree whose `herdr_*` code may be older.
REPLY_HELPER = reply_helper()
INVARIANT_HEADER = (
    "ROLE INVARIANT: You are {article} {role} in a Herdr lane. "
    "Follow the lane coordination pattern."
)
INVARIANT_RULES = (
    "Subagent-First: MUST delegate exploration, drafting, research, and triage to subagents as "
    "drafts; main session synthesizes, verifies, and evaluates.\n"
    "Reply Contract: MUST reply via `uv run {helper} <caller> --file <reply.md>` on completion "
    "or blocker; never exit silently."
)
# Role-conditional: a coordination-only role does not pay for the implementer block. The shared
# Reply Contract above already owes the reply, so this block adds only what is implementer-only.
IMPLEMENTER_CONTRACT = (
    "Implementer: single writer for your task; never edit outside your worktree.\n"
    "Evidence: red-then-green test results, artifacts reported by path.\n"
    "Blockers: report immediately, never idle."
)
# Role-conditional mirror of the implementer block: a TM that drifted into editing source or
# test code after compaction gets its authority boundary restated in its own invariant.
TM_CONTRACT = (
    "Task Manager: coordination, design, and review authority only; NEVER edit source or test "
    "code directly.\n"
    "Dispatch: explore problem space; decompose briefs into atomic tickets; dispatch via "
    "`herdr-dispatch`.\n"
    "Eval & Review: run verification gates in pane; audit callee diffs with review subagents "
    "before accepting.\n"
    "Synthesize: track lane progress; synthesize results and report completion to caller via "
    "`herdr-reply`."
)


def role_article(role: str) -> str:
    """`a`/`an` picked from the role's first letter, so the snippet reads as prose."""
    return "an" if role[:1].lower() in VOWELS else "a"


def is_implementer_role(role: str) -> bool:
    """True for the docs' implementer vocabulary, bare or scoped (`impl-<n>`, `msg-impl-1`).

    Segment-aware, because the lane convention is `<task-group-slug>-<role>[-<subrole|index>]`
    and the role falls back to the scoped agent name; matching the whole string would miss
    every real implementer. Accepted over-match: a lane *slug* segment that itself begins with
    `impl` (an `impl-hardening` lane, say) drags its coordination roles into the block too.
    """
    return any(
        segment.startswith(IMPLEMENTER_PREFIX)
        for segment in IMPLEMENTER_SEGMENT_SPLIT.split(role.lower())
    )


def is_tm_role(role: str) -> bool:
    """True for a coordination-authority vocabulary term occupying whole role segments.

    Segment-aware like `is_implementer_role`, but a term must match as a consecutive run of
    segments rather than a prefix: `msg-tm` and `lane-orch` qualify, `tmux` and `orchid` do
    not, and `task-manager`/`task_manager` match despite carrying a separator in the term.
    """
    tokens = IMPLEMENTER_SEGMENT_SPLIT.split(role.lower())
    for term in TM_ROLE_TERMS:
        run = term.replace("_", "-").split("-")
        for start in range(len(tokens) - len(run) + 1):
            if tokens[start : start + len(run)] == run:
                return True
    return False


def render_invariant(role: str) -> str:
    """Render the role invariant snippet for one role.

    Every role carries the coordination pattern and the two standing rules; `impl`-named
    roles additionally carry the cooperation contract that role needs after compaction, and
    coordination-authority roles (`tm`, `orch`, `coordinator`, scoped forms) carry the Task
    Manager contract instead.
    """
    lines = [
        INVARIANT_HEADER.format(article=role_article(role), role=role),
        INVARIANT_RULES.format(helper=REPLY_HELPER),
    ]
    if is_implementer_role(role):
        lines.append(IMPLEMENTER_CONTRACT)
    if is_tm_role(role):
        lines.append(TM_CONTRACT)
    return "\n".join(lines)


def invariant_block(snippet: str) -> str:
    """The exact marker-wrapped block `append_invariant` writes."""
    return f"{START_MARKER}\n{snippet}\n{END_MARKER}\n"


def read_if_exists(path: Path) -> str:
    """The file's current text; a missing file reads as empty."""
    return path.read_text() if path.exists() else ""


def planned_invariant_content(existing: str, snippet: str) -> str:
    """The content `append_invariant` would leave behind, computed without writing.

    Equal to `existing` exactly when the append is a no-op: the marker block is already
    present — whatever role it names — and the file is left untouched.
    """
    if START_MARKER in existing:
        return existing
    if existing and not existing.endswith("\n"):
        existing += "\n"
    return existing + invariant_block(snippet)


def append_invariant(path: Path, snippet: str) -> bool:
    """Append the marker-wrapped snippet unless the start marker is already present.

    Returns True when the block was written, False when the file already carried it. Existing
    content and its trailing newline are preserved; an already-marked file is never rewritten.
    """
    existing = read_if_exists(path)
    planned = planned_invariant_content(existing, snippet)
    if planned == existing:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(planned)
    return True


def _run_git(
    argv: Sequence[str], env: Mapping[str, str]
) -> subprocess.CompletedProcess[str] | None:
    """Run git, or None when git cannot run at all (no binary, no exec permission).

    Same subprocess style as `run_herdr`: captured output, the caller's environment, no shell.
    A git that cannot run is not an error here — the caller reads the None as *undetermined*,
    never as "not version-controlled".
    """
    try:
        done = subprocess.run(list(argv), capture_output=True, check=False, env=dict(env))
    except OSError:
        return None
    # Decode here, not via `text=True`: universal-newline translation would turn a carriage
    # return inside a worktree root's name into a newline, so the path git printed could no
    # longer be matched against the real directory. `os.fsdecode` keeps git's bytes as written.
    return subprocess.CompletedProcess(
        done.args, done.returncode, os.fsdecode(done.stdout), os.fsdecode(done.stderr)
    )


def _git_location_is_redirected(env: Mapping[str, str]) -> bool:
    """True when the environment points git at another worktree, index, or object store.

    `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` outrank `-C`, so a probe run with any of them set
    answers about that override, never about the repository the target file really lives in. The
    answer cannot be trusted either way, so the tracked state reads as undetermined; the caller
    warns, refuses a confirmed repository, and still appends when the override flag is passed.
    """
    return any(env.get(name) for name in GIT_LOCATION_OVERRIDE_VARS)


def _repository_marker_present(path: Path) -> bool:
    """True when `path` or an ancestor carries a `.git` entry, readable by git or not.

    A genuinely absent repository and an unreadable one print the same "not a git repository"
    line, so that message alone cannot tell them apart. A `.git` entry git could not use means
    the tracked state is undetermined, not that the file is outside version control.
    """
    current = Path(os.path.realpath(path))
    while True:
        if os.path.lexists(current / ".git"):
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def on_disk_entry_name(path: Path) -> str | None:
    """The name `path` carries in its parent directory listing, or None when it is absent.

    Exact spelling first, then a case-insensitive match that is *the same file*. `git ls-files`
    matches a pathspec case-sensitively against the index's stored name, so a target computed as
    ``AGENTS.md`` must be asked about as the ``agents.md`` the filesystem actually lists on a
    case-insensitive volume — otherwise a tracked file looks untracked and the append dirties the
    tree. A case-variant name that is a *different* file (a case-sensitive volume where
    ``agents.md`` exists and ``AGENTS.md`` does not) is not the target, so it is not accepted:
    `samefile` is True only when both spellings resolve to one inode.
    """
    try:
        names = os.listdir(path.parent)
    except OSError:
        return None
    if path.name in names:
        return path.name
    folded = path.name.casefold()
    for name in names:
        if name.casefold() != folded:
            continue
        try:
            if os.path.samefile(path, path.parent / name):
                return name
        except OSError:
            continue
    return None


def target_is_tracked(path: Path, env: Mapping[str, str]) -> bool | None:
    """Whether git tracks `path` in the worktree enclosing it: True, False, or None.

    `rev-parse --is-inside-work-tree` answers "is this in a worktree at all"; the follow-up
    `ls-files --error-unmatch` answers "does the index know this file", which is the question
    the append must respect. Detection runs against the file's real location and asks about the
    on-disk entry name, not the computed one. Only an answer about the file's own repository and
    index is trusted: a `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` override, or a git that
    refuses to answer (dubious ownership, an unreadable `.git`), is *undetermined* — never a
    definitive "not tracked".

    None means *undetermined*: git could not run, could not answer, or answered about another
    repository or index. The caller must not read None as "not tracked": a confirmed repository
    with a broken index may well track the file.
    """
    real = Path(os.path.realpath(path))
    if _git_location_is_redirected(env):
        return None  # git would answer about another worktree/index, not this file's repository
    inside = _run_git(["git", "-C", str(real.parent), "rev-parse", "--is-inside-work-tree"], env)
    if inside is None:
        return None  # git could not run at all: the tracked state is unknown
    if inside.returncode != 0:
        if "not a git repository" in inside.stderr and not _repository_marker_present(real.parent):
            return False  # git ran and found no `.git` anywhere: genuinely outside a worktree
        return None  # git refused to answer (dubious ownership, an unreadable `.git`)
    if inside.stdout.removesuffix("\n") != "true":
        return False
    top = _run_git(["git", "-C", str(real.parent), "rev-parse", "--show-toplevel"], env)
    if top is None or top.returncode != 0:
        return None  # repository confirmed, but the worktree root is unknown
    root = top.stdout.removesuffix("\n")
    if not root:
        return None
    try:
        relative = real.relative_to(Path(os.path.realpath(root)))
    except ValueError:
        return None
    if str(relative) == ".":
        return False
    entry = on_disk_entry_name(real)
    if entry is not None:
        relative = relative.with_name(entry)
    # Run from the worktree root, so the pathspec stays the repo-root-relative path: ls-files
    # resolves a pathspec against its own cwd, and only the root makes that the root path.
    listed = _run_git(["git", "-C", root, "ls-files", "--error-unmatch", "--", str(relative)], env)
    if listed is None:
        return None
    if listed.returncode == 0:
        return True
    if listed.returncode == 1:
        return False  # git ran and answered: the index does not know this file
    return None  # a fatal read of the index: git could not answer


def repository_is_confirmed(path: Path, env: Mapping[str, str]) -> bool | None:
    """Why the tracked-state probe came back undetermined: git confirmed, git refused, or no git.

    Splits the undetermined state by *reason*, because the two reasons call for different
    answers. A git that ran and refused to answer about this directory (dubious ownership, an
    unreadable `.git`, a redirecting `GIT_DIR`) still leaves a repository on disk that may track
    the file, so the caller refuses; a git that could not run at all testifies to nothing, so the
    launch must keep delivering the invariant. `None` means git never ran.
    """
    real = Path(os.path.realpath(path))
    inside = _run_git(["git", "-C", str(real.parent), "rev-parse", "--is-inside-work-tree"], env)
    if inside is None:
        return None  # git could not run at all: it cannot testify about the file either way
    if inside.returncode != 0:
        return False  # git ran and refused to answer about this directory
    return inside.stdout.removesuffix("\n") == "true"


def tracked_refusal(path: Path) -> str:
    """The refusal for a version-controlled target: the file, the reason, and the override."""
    return (
        f"{path} is version-controlled; refusing to append the role invariant "
        f"(a launch must not modify a tracked file). Pass {TRACKED_OVERRIDE_FLAG} to append "
        f"anyway and leave the file modified."
    )


def undetermined_refusal(path: Path) -> str:
    """Refusal for a repository on disk whose tracked state git could not read.

    Same message family as `tracked_refusal`: names the file, the reason, and the override. The
    reason covers both halves of the evidence — a repository git confirmed, and a `.git` entry
    git refused to use — so it must not claim the index was read, only that git could not
    answer about it.
    """
    return (
        f"{path} may be version-controlled; refusing to append the role invariant "
        f"(a repository is present but git could not answer about this file's index, so the "
        f"file may be tracked). Pass {TRACKED_OVERRIDE_FLAG} to append anyway and leave the "
        f"file modified."
    )


def undetermined_warning(path: Path) -> str:
    """One stderr line: the tracked state could not be determined, so the append may dirty it."""
    return (
        f"herdr-bootstrap: could not determine whether {path} is version-controlled "
        f"(git is unavailable or did not answer); it may be tracked, so this append may leave "
        f"the tree modified."
    )


def absolute_target(path: Path) -> Path:
    """The target as an absolute path for messages; an already-absolute path passes through.

    `abspath`, not `realpath`: the message must name the file the operator passed (its `--cwd`
    plus `AGENTS.md`), the same string as the `agents_md` plan value, not a symlink-resolved
    twin of it.
    """
    return Path(os.path.abspath(path))


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    name: str = ""
    kind: str = ""
    pane: str = ""
    role: str = ""
    task_group: str | None = None
    model: str | None = None
    cwd: str | None = None
    cwd_timeout: float = 10.0
    allow_tracked_invariant: bool = False
    settle: float = DEFAULT_SETTLE_SECONDS
    dry_run: bool = False
    json: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-bootstrap",
        description=(
            "Stamp the ROLE INVARIANT into a starting agent's launch surface, then start it "
            "under its scoped name."
        ),
        epilog=(
            "exit status: 0 ok, 1 herdr failure, 2 usage or precondition\n\n"
            + METHOD_CONSTRAINT_EPILOG
        ),
    )
    _ = parser.add_argument(
        "name",
        nargs="?",
        metavar="NAME",
        default="",
        help="agent name; defaults to --role, then is scoped with --task-group",
    )
    _ = parser.add_argument("--kind", required=True, metavar="KIND", help="agent kind for start")
    add_shared_argument(parser, "pane", required=True, help="pane to start the agent in")
    add_shared_argument(
        parser,
        "role",
        default="",
        help="role named in the invariant (e.g. tm, impl-1); defaults to NAME",
    )
    add_shared_argument(
        parser,
        "task_group",
        help="scope NAME with this task-group slug before naming the pane and agent",
    )
    add_shared_argument(parser, "model", help="model for agent start")
    add_shared_argument(
        parser,
        "cwd",
        help=(
            "worktree dir the agent must start in; bootstrap cds the pane there "
            "and refuses on mismatch"
        ),
    )
    _ = parser.add_argument(
        "--cwd-timeout",
        type=float,
        default=10.0,
        metavar="SEC",
        help="seconds to wait for the pane to reach --cwd (default: 10)",
    )
    _ = parser.add_argument(
        TRACKED_OVERRIDE_FLAG,
        action="store_true",
        help=(
            "append the role invariant even when the target file is version-controlled or "
            "its version-control state could not be determined, leaving that file modified"
        ),
    )
    add_shared_argument(
        parser,
        "settle",
        default=DEFAULT_SETTLE_SECONDS,
        help=(
            "seconds to wait after a fresh `agent start` before reporting the pane "
            "bootstrapped, so a still-initialising pane is not treated as acceptant; "
            f"0 waits not at all (default: {DEFAULT_SETTLE_SECONDS:g})"
        ),
    )
    add_shared_argument(
        parser,
        "dry_run",
        help="print the planned file path and start argv, mutate nothing",
    )
    add_shared_argument(parser, "json", help="print herdr's raw start response")
    return parser


def resolve_name(options: Options) -> str:
    """Scope and validate the agent name before any mutation, so a bad name is refused early."""
    role = options.role or options.name
    if not role:
        raise UsageError("pass NAME or --role")
    name = scoped_agent_name(options.name or role, options.task_group)
    validate_agent_name(name)
    return name


def pane_cwd(herdr: str, pane_id: str, env: Mapping[str, str]) -> str | None:
    """The pane's cwd from `herdr pane list`, or None when the pane is not listed."""
    panes = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
    for entry in panes:
        if entry_optional_text(entry, "pane_id") == pane_id:
            return entry_optional_text(entry, "cwd")
    return None


def _norm_path(path: str) -> str:
    """Absolute path with symlinks resolved, so /tmp and /private/tmp compare equal."""
    return os.path.normcase(os.path.realpath(os.path.expanduser(path)))


def pane_cwd_matches(current: str | None, target: str) -> bool:
    """True when the pane already works where the caller asked it to."""
    return current is not None and _norm_path(current) == _norm_path(target)


def ensure_linked_worktree(
    target: str,
    pane_id: str,
    env: Mapping[str, str],
    *,
    role: str | None = None,
    task_group: str | None = None,
) -> None:
    """Refuse a ``--cwd`` that is missing or not a registered linked worktree.

    A directory outside git is left to the existing pane-cwd guarantee: synthetic lanes and
    non-repository workspaces have no worktree registry to answer against. Inside a repository
    the target must appear in ``git worktree list --porcelain``; the primary checkout is refused
    once the repository has linked worktrees, because that means the per-role topology is in use.
    """
    path = Path(os.path.abspath(os.path.expanduser(target)))
    if not path.is_dir():
        raise UsageError(
            f"pane {pane_id} cwd {target} is missing; expected a linked worktree directory"
        )
    if _git_location_is_redirected(env):
        return
    listed = _run_git(["git", "-C", str(path), "worktree", "list", "--porcelain"], env)
    if listed is None or listed.returncode != 0:
        return
    entries = parse_git_worktree_entries(listed.stdout)
    if not entries:
        return
    target_key = worktree_key(str(path))
    primary = worktree_key(entries[0].path)
    linked = [entry for entry in entries if worktree_key(entry.path) != primary]
    if target_key == primary:
        if not linked:
            return
        expected = linked[0].path
        if task_group and role:
            name = expected_worktree_name(Path(primary), {"task_group": task_group, "role": role})
            expected = str(Path(primary).parent / name)
        raise UsageError(
            f"pane {pane_id} cwd {target} is the main checkout; expected linked worktree {expected}"
        )
    if all(worktree_key(entry.path) != target_key for entry in linked):
        expected = ", ".join(entry.path for entry in linked) or "a registered linked worktree"
        raise UsageError(
            f"pane {pane_id} cwd {target} is not a registered linked worktree; "
            f"expected one of {expected}"
        )


def ensure_pane_cwd(
    herdr: str, pane_id: str, target: str, env: Mapping[str, str], *, timeout_s: float
) -> None:
    """cd the pane into target and verify it converged; raise HerdrError otherwise.

    The agent inherits the pane's cwd at start, so skipping this silently runs a worktree
    orchestration in the wrong tree. `pane run` types the cd plus Enter in one call; the
    follow-up `pane list` reads prove the shell actually landed before `agent start`.
    """
    if pane_cwd_matches(pane_cwd(herdr, pane_id, env), target):
        return
    _ = run_herdr_checked([herdr, "pane", "run", pane_id, f"cd {shlex.quote(target)}"], env)
    deadline = time.monotonic() + timeout_s
    while True:
        current = pane_cwd(herdr, pane_id, env)
        if pane_cwd_matches(current, target):
            return
        if time.monotonic() >= deadline:
            raise HerdrError(f"pane {pane_id} did not reach cwd {target} (still {current})")
        time.sleep(_CWD_POLL_S)


def resolve_target_dir(
    herdr: str, options: Options, env: Mapping[str, str], *, dry_run: bool
) -> str:
    """Pick the dir the file-reading kinds write into: --cwd, else the pane cwd, else $PWD."""
    if options.cwd:
        return options.cwd
    if not dry_run:
        found = pane_cwd(herdr, options.pane, env)
        if found:
            return found
    return env.get("PWD") or os.getcwd()


def target_path(target_dir: str, kind: str) -> Path:
    """The file to append to: .clinerules for cline when present, else AGENTS.md."""
    directory = Path(target_dir)
    if kind == "cline" and (directory / CLINE_RULES).exists():
        return directory / CLINE_RULES
    return directory / AGENTS_MD


def sanitise_agent_name(name: str) -> str:
    """The file-name stem for one agent: `[A-Za-z0-9._-]` kept, every other character `_`.

    Refuses an empty result and the `.`/`..` names that would escape the directory, so a
    hostile or garbled agent name can never name a file outside the lane's invariant dir.
    """
    cleaned = INVARIANT_NAME_UNSAFE.sub("_", name)
    if not cleaned or cleaned in {".", ".."}:
        raise UsageError(f"cannot derive an invariant file name from {name!r}")
    return cleaned


def lane_invariant_path(target_dir: str, agent_name: str) -> Path:
    """The per-agent lane-local file an inline kind reads its role invariant from.

    Absolute, so the target binary resolves it from any cwd. Keyed by the resolved agent
    name, so two agents in one lane each keep their own text and the second bootstrap never
    overwrites the first. Only this path is passed to ``--append-system-prompt``; the snippet
    text never reaches herdr's argv.
    """
    stem = sanitise_agent_name(agent_name)
    return (Path(target_dir) / LANE_DIR / INVARIANTS_DIR / f"{stem}{INVARIANT_SUFFIX}").resolve()


def write_role_invariant(path: Path, snippet: str) -> None:
    """Write the rendered snippet for the target binary to read back at launch.

    Idempotent for the one agent that owns `path`: the file is replaced wholesale, so
    re-bootstrapping that agent never duplicates the snippet and never leaves a previous
    role's text behind, while every other agent's file is untouched. Contents equal the
    snippet.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(snippet)


def build_start_argv(
    herdr: str,
    options: Options,
    name: str,
    *,
    entry: KindEntry,
    invariant_path: str | None = None,
) -> list[str]:
    """Assemble `agent start`; all agent-level flags ride after `--` as native agent args.

    `herdr agent start` owns only `--kind`/`--pane`/`--timeout`; the model, the
    role-invariant system prompt reference, and the per-kind trust flags are the agent
    binary's own options, so they must sit past the `--` separator. The separator is emitted
    only when there is at least one such arg.

    `invariant_path` is the absolute path of the already-written snippet file, required by
    inline kinds and ignored otherwise: the snippet must never ride inline, since herdr
    refuses any agent arg it cannot encode safely for the target shell — a newline is
    enough. The flag is the kind's own `invariant_flag` from kinds.yaml, never a hardcoded
    name: `pi` reads file contents through `--append-system-prompt`, but `claude` takes a
    path only through `--append-system-prompt-file` and would read the path string as
    literal prompt text otherwise (#240). No I/O happens here.
    """
    argv = [herdr, "agent", "start", name, "--kind", options.kind, "--pane", options.pane]
    agent_args: list[str] = []
    if entry.inline_invariant:
        if not invariant_path:
            raise ValueError("inline kinds need the role-invariant file path")
        if not entry.invariant_flag:
            raise ValueError(
                f"kind {options.kind!r}: an inline kind needs invariant_flag naming the "
                "flag that takes the snippet file"
            )
        agent_args += [entry.invariant_flag, invariant_path]
    if options.model:
        agent_args += ["--model", options.model]
    agent_args += entry.trust_flags
    for arg in agent_args:
        if "\n" in arg or "\r" in arg:
            raise ValueError(f"agent args must be single-line: {arg!r}")
    if agent_args:
        argv += ["--", *agent_args]
    return argv


def bootstrap(options: Options, env: Mapping[str, str]) -> int:
    if options.settle < 0:
        raise UsageError(f"--settle {options.settle} must not be negative")
    require_herdr_env(env)
    herdr = find_herdr(env)
    name = resolve_name(options)
    role = options.role or options.name
    snippet = render_invariant(role)
    entry = load_kind_entry(options.kind)

    target_dir = resolve_target_dir(herdr, options, env, dry_run=options.dry_run)
    agents_file: Path | None = None
    invariant_file: Path | None = None
    if entry.inline_invariant:
        invariant_file = lane_invariant_path(target_dir, name)
    else:
        agents_file = target_path(target_dir, options.kind)

    # The shared builder, so the label bootstrap writes is spelled by the same function the
    # reconciliation pass and `herdr-label` use — anchored on the physical `pane_id`, never on a
    # visible label (#182 t5 2.4). Byte-identical to the argv this call used to hand-build.
    rename_argv = pane_rename_argv(herdr, options.pane, name)
    start_argv = build_start_argv(
        herdr,
        options,
        name,
        entry=entry,
        invariant_path=None if invariant_file is None else str(invariant_file),
    )
    # The file kinds deliver the invariant through the target file itself: that file *is* the
    # surface the agent reads, so a launch must decide once, before any mutation, whether the
    # write is allowed. An append that would change nothing is skipped (no mtime churn, no
    # dirt); a tracked target that would change is refused unless the caller overrides. A
    # repository on disk whose tracked state is undetermined is refused too, and, like the
    # tracked refusal, overridable; only a git that cannot run at all appends, and it warns on
    # stderr.
    agents_tracked: bool | None = False
    refusal: str | None = None
    note: str | None = None
    if agents_file is not None:
        try:
            current = read_if_exists(agents_file)
        except OSError as exc:
            raise UsageError(f"cannot read {agents_file}: {exc}") from exc
        agents_tracked = target_is_tracked(agents_file, env)
        would_change = planned_invariant_content(current, snippet) != current
        if agents_tracked is None:
            note = undetermined_warning(absolute_target(agents_file))
            confirmed = repository_is_confirmed(agents_file, env)
            marker = _repository_marker_present(absolute_target(agents_file).parent)
            # Two independent signs say the file may be tracked: git's own worktree answer, and
            # a `.git` entry at or above the target that a refusing git could not use. Either
            # one refuses, unless the caller overrides; only a git that never ran appends.
            refusable = bool(confirmed) or (confirmed is not None and not confirmed and marker)
            if refusable and not options.allow_tracked_invariant:
                refusal = undetermined_refusal(absolute_target(agents_file))
        elif agents_tracked and would_change and not options.allow_tracked_invariant:
            refusal = tracked_refusal(absolute_target(agents_file))

    if options.dry_run:
        plan: dict[str, object] = {
            "agents_md": str(agents_file) if agents_file else None,
            "role_invariant": str(invariant_file) if invariant_file else None,
            "pane_rename": rename_argv,
            "agent_start": start_argv,
            "cwd_ensure": options.cwd,
            "settle": options.settle,
        }
        if agents_file is not None:
            plan["agents_md_tracked"] = agents_tracked
            if refusal is not None:
                plan["would_refuse"] = refusal
            if note is not None:
                plan["note"] = note
        print(json.dumps(plan))
        return EXIT_OK

    if refusal is not None:
        raise UsageError(refusal)
    if note is not None:
        print(note, file=sys.stderr)

    if options.cwd:
        ensure_pane_cwd(herdr, options.pane, options.cwd, env, timeout_s=options.cwd_timeout)
        ensure_linked_worktree(
            options.cwd,
            options.pane,
            env,
            role=options.role,
            task_group=options.task_group,
        )
    _ = run_herdr_checked(rename_argv, env)
    if agents_file is not None:
        try:
            _ = append_invariant(agents_file, snippet)
        except OSError as exc:
            raise UsageError(f"cannot write {agents_file}: {exc}") from exc
    if invariant_file is not None:
        try:
            write_role_invariant(invariant_file, snippet)
        except OSError as exc:
            raise UsageError(f"cannot write {invariant_file}: {exc}") from exc
    raw = run_herdr_checked(start_argv, env)
    # The pane is only now reported bootstrapped, and only now is it acceptant: the fresh
    # spawn may still be initialising behind a truthful `interactive_ready: true` (#238).
    settle_fresh_pane(options.settle)

    if options.json:
        print(raw, end="" if raw.endswith("\n") else "\n")
        return EXIT_OK
    surface = f"agents-md={agents_file}" if agents_file else f"role-invariant={invariant_file}"
    print(f"bootstrapped {name} ({options.kind}) pane={options.pane} {surface}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    return entrypoint(
        "herdr-bootstrap", build_parser, bootstrap, namespace=Options(), argv=argv, env=env
    )


if __name__ == "__main__":
    raise SystemExit(main())
