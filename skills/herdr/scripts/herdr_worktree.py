#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""herdr-worktree — pre-provision isolated worktrees for Herdr lane coordination.

A root orchestrator allocates one worktree per lane so that Task Manager and Implementer
panes start inside an isolated tree from turn zero, instead of improvising ad-hoc
`.claude/worktrees/` directories in the repository root (which trips Worktrunk's
`branch_worktree_mismatch` guard). Prefers Worktrunk (`wt`) when it is on `PATH`, and
falls back to `git worktree` when it is not.

    uv run "$SKILL_DIR/scripts/herdr_worktree.py" allocate feat/184-worktree --base main
    uv run "$SKILL_DIR/scripts/herdr_worktree.py" allocate feat/184-worktree --json
    uv run "$SKILL_DIR/scripts/herdr_worktree.py" resolve feat/184-worktree
    uv run "$SKILL_DIR/scripts/herdr_worktree.py" list --json
    uv run "$SKILL_DIR/scripts/herdr_worktree.py" claim <worktree> lane/<group>/<role>/<ticket> --base main
    uv run "$SKILL_DIR/scripts/herdr_worktree.py" status --worktree <path> --json
    uv run "$SKILL_DIR/scripts/herdr_worktree.py" retire <worktree|branch>
    uv run "$SKILL_DIR/scripts/herdr_worktree.py" doctor --prune

`allocate` in its plain form prints only the absolute path, so callers substitute it
directly: `WORKTREE_PATH=$(... allocate <branch>)`. Exit status: `0` ok, `1` the worktree
engine failed, `2` usage or missing precondition. Unlike its siblings this helper needs no
`HERDR_ENV=1` session; it only shells out to `wt`/`git`. Local addition to the absorbed
upstream Herdr skill; not part of `herdrdev/herdr`.

`claim`, `status`, `retire`, and `doctor` extend the helper with agent-scoped lifecycle verbs.
`claim` records the binding in `<lane-base>/.lane/tasks.yaml` under the top-level `worktrees`
mapping, keyed by the worktree's real path (the anchor `resolve_lane_base_dir` uses, never
`PWD`). `claim` never forces a checkout: it requires a clean tree, an explicit `--base`, and a
branch inside `lane/<task-group>/<role>/<ticket>`, and it refuses `switch -C`, `switch -B`,
`switch -f`, `git stash`, and `worktree add --force`. `retire` removes only a clean worktree
and deletes its branch with `git branch -d` (never `-D`); `doctor --prune` only drops admin
entries for missing directories.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import herdr_cli
from herdr_cli import BRANCH_UNSAFE_RE as BRANCH_UNSAFE_RE
from herdr_cli import (
    EXIT_OK,
    HerdrError,
    UsageError,
    add_shared_argument,
    entrypoint,
    failure_detail,
    resolve_lane_base_dir,
    sanitize_branch,
)
from herdr_cli import LANE_DIR_ENV as LANE_DIR_ENV
from herdr_cli import LaneAnchorError as LaneAnchorError

ENGINE_WORKTRUNK = "worktrunk"
ENGINE_GIT = "git"

PORCELAIN_WORKTREE = "worktree "
PORCELAIN_BRANCH = "branch "
HEAD_REF_PREFIX = "refs/heads/"
DETACHED_MARKER = "(detached HEAD)"
# `git worktree list` compact rows some wrappers emit despite --porcelain:
#   /path/to/wt 0e57943 [feat/184-worktree]
COMPACT_WORKTREE_RE = re.compile(r"^(?P<path>\S+)\s+[0-9a-f]{7,40}\s+\[(?P<branch>.+)\]$")
BRANCH_NAMESPACE_RE = re.compile(
    r"^lane/(?P<task_group>[A-Za-z0-9._-]+)/(?P<role>[A-Za-z0-9._-]+)/"
    r"(?P<ticket>[A-Za-z0-9._-]+)$"
)
STORE_RELATIVE_PATH = ".lane/tasks.yaml"
WORKTREES_KEY = "worktrees"
FORBIDDEN_TOKENS = frozenset({"-B", "-f", "--force"})
FLAG_DETACHED = "detached"
FLAG_DIRTY = "dirty"
FLAG_UNLINKED = "unlinked"
FLAG_ORPHAN = "orphan"
FLAG_NAMESPACE = "namespace"
FLAG_LAYOUT = "layout"


class WorktreeError(HerdrError):
    """A worktree engine failed to allocate or resolve (exit status 1)."""


@dataclass(frozen=True)
class Worktree:
    """One active worktree, keyed by the branch it has checked out."""

    branch: str
    path: str


@dataclass(frozen=True)
class Allocation:
    """The worktree allocated or resolved for one branch."""

    branch: str
    path: str
    engine: str


@dataclass
class Options:
    """Parsed command line for one helper invocation."""

    command: str | None = None
    branch: str | None = None
    base: str | None = None
    json: bool = False
    worktree: str | None = None
    target: str | None = None
    prune: bool = False


def run(argv: Sequence[str], env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    """Run argv without a shell; a failure raises this module's own error type.

    Delegates to the shared subprocess seam so one place spawns a process, and translates
    its `HerdrError` so worktree callers (and their tests) keep seeing `WorktreeError`.
    """
    try:
        return herdr_cli.run_herdr(argv, env)
    except HerdrError as exc:
        raise WorktreeError(str(exc)) from exc


def run_checked(argv: Sequence[str], env: Mapping[str, str]) -> str:
    """Run argv and return stdout, raising WorktreeError on a non-zero exit."""
    done = run(argv, env)
    if done.returncode != 0:
        raise WorktreeError(f"{shlex.join(argv)} failed: {failure_detail(done)}")
    return done.stdout


def wt_binary(env: Mapping[str, str]) -> str | None:
    """Absolute path to `wt` on the given PATH, or None when Worktrunk is absent."""
    return shutil.which("wt", path=env.get("PATH", ""))


def wt_env(env: Mapping[str, str]) -> dict[str, str]:
    """Environment for `wt`: CI=1 suppresses the interactive pager."""
    return {**env, "CI": "1"}


def require_branch(branch: str) -> str:
    """Trim a branch argument and reject an empty one as a usage error."""
    cleaned = branch.strip()
    if not cleaned:
        raise UsageError("branch name is empty")
    return cleaned


def parse_wt_list(raw: str) -> list[Worktree]:
    """Parse `wt list --format=json`, accepting schema 1 (array) and schema 2 (`items`)."""
    try:
        decoded = cast(object, json.loads(raw))
    except json.JSONDecodeError as exc:
        raise WorktreeError(f"wt list returned non-JSON output: {raw.strip()[:200]!r}") from exc

    if isinstance(decoded, dict):
        items = decoded.get("items")
    elif isinstance(decoded, list):
        items = decoded
    else:
        items = None
    if not isinstance(items, list):
        raise WorktreeError(
            "wt list JSON is neither an array (schema 1) nor an object with 'items'"
        )

    worktrees: list[Worktree] = []
    for item in items:
        if not isinstance(item, dict):
            raise WorktreeError(f"wt list entry is not an object: {item!r}")
        path = item.get("path")
        branch = item.get("branch")
        if not isinstance(path, str) or not path:
            raise WorktreeError(f"wt list entry has no usable 'path': {item!r}")
        if not isinstance(branch, str) or not branch:
            continue  # detached worktree: no branch to match
        worktrees.append(Worktree(branch=branch, path=path))
    return worktrees


def parse_git_worktree_list(raw: str) -> list[Worktree]:
    """Parse `git worktree list --porcelain`, tolerating the compact wrapper format."""
    worktrees: list[Worktree] = []
    current_path: str | None = None
    current_branch: str | None = None
    saw_porcelain = False

    def flush() -> None:
        nonlocal current_path, current_branch
        if current_path is not None and current_branch is not None:
            worktrees.append(Worktree(branch=current_branch, path=current_path))
        current_path = None
        current_branch = None

    for line in raw.splitlines():
        if line.startswith(PORCELAIN_WORKTREE):
            flush()
            saw_porcelain = True
            current_path = line[len(PORCELAIN_WORKTREE) :].strip()
        elif line.startswith(PORCELAIN_BRANCH):
            ref = line[len(PORCELAIN_BRANCH) :].strip()
            current_branch = ref[len(HEAD_REF_PREFIX) :] if ref.startswith(HEAD_REF_PREFIX) else ref
    flush()

    if saw_porcelain:
        return worktrees
    for line in raw.splitlines():
        match = COMPACT_WORKTREE_RE.match(line.strip())
        if match is None or match.group("branch") == DETACHED_MARKER:
            continue
        worktrees.append(Worktree(branch=match.group("branch"), path=match.group("path")))
    return worktrees


def wt_worktree_for(wt: str, branch: str, env: Mapping[str, str]) -> str | None:
    """Return the worktree path Worktrunk reports for branch, or None."""
    raw = run_checked([wt, "list", "--format=json"], wt_env(env))
    for worktree in parse_wt_list(raw):
        if worktree.branch == branch:
            return worktree.path
    return None


def git_common_dir(env: Mapping[str, str]) -> Path:
    """Absolute path to the git directory every worktree of this repository shares.

    `--path-format=absolute` answers inside a bare repository too, where `--show-toplevel`
    fails with "this operation must be run in a work tree" and the plain flag returns `.`,
    which used to collapse a bare repo's root onto the git directory itself (#207).
    """
    done = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], env)
    if done.returncode == 0 and done.stdout.strip():
        return Path(os.path.realpath(done.stdout.strip()))
    raw = run_checked(["git", "rev-parse", "--git-common-dir"], env).strip()
    common = Path(raw)
    if not common.is_absolute():
        top = run_checked(["git", "rev-parse", "--show-toplevel"], env).strip()
        common = Path(top).resolve() / common
    return Path(os.path.realpath(common))


def git_repo_root(env: Mapping[str, str]) -> Path:
    """Absolute path to the main worktree root, even when called from a linked worktree."""
    common = git_common_dir(env)
    return common.parent if common.name == ".git" else common


def is_bare_repository(env: Mapping[str, str]) -> bool:
    """Whether this repository has no working tree of its own."""
    state = run_checked(["git", "rev-parse", "--is-bare-repository"], env).strip()
    return state == "true"


def path_is_within(path: Path, root: Path) -> bool:
    """Whether path is root itself or sits under it, comparing resolved paths."""
    resolved = Path(os.path.realpath(path))
    return resolved == root or root in resolved.parents


def guard_not_in_git_dir(path: Path, env: Mapping[str, str]) -> None:
    """Refuse a path in the git directory, or in a hidden sibling named after it (#207).

    A bare repository whose directory is named `.git` makes Worktrunk derive
    `<git-dir>.<slug>`; that path holds no checkout, so no lane can start there. A bare repo
    named `repo.git` stays unaffected: Worktrunk's `<git-dir>.<slug>` sibling is then the
    documented convention.
    """
    common = git_common_dir(env)
    resolved = Path(os.path.realpath(path))
    hidden_sibling = (
        common.name.startswith(".")
        and resolved.parent == common.parent
        and resolved.name.startswith(f"{common.name}.")
    )
    if path_is_within(resolved, common) or hidden_sibling:
        raise WorktreeError(
            f"refusing to place a lane worktree in the git directory {common} "
            f"(computed {path}); remove that worktree, fix Worktrunk's worktree-path, or run "
            "herdr-worktree from a normal checkout"
        )


def fallback_path(branch: str, env: Mapping[str, str]) -> Path:
    """Predictable sibling path used when `wt` is unavailable."""
    root = git_repo_root(env)
    return root.parent / f"{root.name}.{sanitize_branch(branch)}"


def allocate_with_wt(wt: str, branch: str, base: str | None, env: Mapping[str, str]) -> Allocation:
    """Create the branch and worktree through `wt switch --create`, then read its path back."""
    argv = [wt, "switch", "--create", branch]
    if base:
        argv += ["--base", base]
    done = run(argv, wt_env(env))
    if done.returncode != 0:
        # A re-run against an already-allocated branch is success, not failure.
        try:
            existing = wt_worktree_for(wt, branch, env)
        except WorktreeError:
            existing = None
        if existing is not None:
            return Allocation(branch=branch, path=existing, engine=ENGINE_WORKTRUNK)
        raise WorktreeError(f"{shlex.join(argv)} failed: {failure_detail(done)}")

    path = wt_worktree_for(wt, branch, env)
    if path is None:
        raise WorktreeError(
            f"{shlex.join(argv)} succeeded but wt list reports no worktree for {branch!r}"
        )
    return Allocation(branch=branch, path=path, engine=ENGINE_WORKTRUNK)


def git_worktree_for(branch: str, env: Mapping[str, str]) -> str | None:
    """Return the worktree path git reports for branch, or None."""
    raw = run_checked(["git", "worktree", "list", "--porcelain"], env)
    for worktree in parse_git_worktree_list(raw):
        if worktree.branch == branch:
            return worktree.path
    return None


def recover_git_worktree(branch: str, env: Mapping[str, str]) -> Allocation | None:
    """Best-effort reuse of a worktree git already tracks for branch."""
    try:
        existing = git_worktree_for(branch, env)
    except WorktreeError:
        return None
    if existing is not None and Path(existing).is_dir():
        return Allocation(branch=branch, path=existing, engine=ENGINE_GIT)
    return None


def allocate_with_git(branch: str, base: str | None, env: Mapping[str, str]) -> Allocation:
    """Fallback allocation with `git worktree add` under a predictable sibling path."""
    path = fallback_path(branch, env)
    guard_not_in_git_dir(path, env)
    argv = ["git", "worktree", "add", "-b", branch, str(path)]
    if base:
        argv.append(base)
    done = run(argv, env)
    if done.returncode != 0:
        # The branch may already exist: attach it instead of recreating it.
        retry = ["git", "worktree", "add", str(path), branch]
        done = run(retry, env)
        if done.returncode != 0:
            recovered = recover_git_worktree(branch, env)
            if recovered is not None:
                guard_not_in_git_dir(Path(recovered.path), env)
                return recovered
            raise WorktreeError(f"{shlex.join(retry)} failed: {failure_detail(done)}")
    if not path.is_dir():
        raise WorktreeError(f"git reported success but {path} is not a directory")
    return Allocation(branch=branch, path=str(path), engine=ENGINE_GIT)


def resolve_base_sha(base: str | None, env: Mapping[str, str]) -> str:
    """Resolve the branch base to a commit SHA, defaulting to the caller HEAD (#242)."""
    rev = base if base else "HEAD"
    return run_checked(["git", "rev-parse", "--verify", rev], env).strip()


def allocate(branch: str, base: str | None, env: Mapping[str, str]) -> Allocation:
    """Allocate the branch's worktree through Worktrunk when present, else `git worktree`.

    A bare repository is always allocated by git: Worktrunk's `{{ repo_path }}` is then the
    git directory itself, so its sibling convention collapses to `<git-dir>.<slug>` (#207).
    """
    name = require_branch(branch)
    resolved = resolve_base_sha(base, env)
    print(f"herdr-worktree: base {resolved} for {name}", file=sys.stderr)
    effective: str | None = base if base is not None else resolved
    wt = wt_binary(env)
    if wt is not None and not is_bare_repository(env):
        allocation = allocate_with_wt(wt, name, effective, env)
        guard_not_in_git_dir(Path(allocation.path), env)
        return allocation
    if wt is not None:
        print(
            "herdr-worktree: bare repository; allocating with git worktree instead of wt",
            file=sys.stderr,
        )
    return allocate_with_git(name, effective, env)


def resolve(branch: str, env: Mapping[str, str]) -> Allocation:
    """Look up the existing worktree path for branch, preferring Worktrunk's view."""
    name = require_branch(branch)
    wt = wt_binary(env)
    if wt is not None:
        path = wt_worktree_for(wt, name, env)
        if path is not None:
            return Allocation(branch=name, path=path, engine=ENGINE_WORKTRUNK)

    raw = run_checked(["git", "worktree", "list", "--porcelain"], env)
    for worktree in parse_git_worktree_list(raw):
        if worktree.branch == name:
            return Allocation(branch=name, path=worktree.path, engine=ENGINE_GIT)
    raise WorktreeError(f"no worktree found for branch {name!r}")


def list_worktrees(env: Mapping[str, str]) -> tuple[str, list[Worktree]]:
    """Return (engine, worktrees) for every active worktree."""
    wt = wt_binary(env)
    if wt is not None:
        raw = run_checked([wt, "list", "--format=json"], wt_env(env))
        return ENGINE_WORKTRUNK, parse_wt_list(raw)
    raw = run_checked(["git", "worktree", "list", "--porcelain"], env)
    return ENGINE_GIT, parse_git_worktree_list(raw)


def print_rows(rows: Iterable[str]) -> None:
    """Print one pre-formatted row per line."""
    for row in rows:
        print(row)


def emit(payload: Mapping[str, Any], as_json: bool, render: Callable[[], None]) -> None:
    """Print `payload` as JSON, or let the caller render its plain-text rows.

    Every verb answers with the same shape: a JSON object under `--json`, and a fixed
    human row otherwise. Keeping the branch here means one place decides the encoding,
    and each verb keeps only its own payload keys and row format.
    """
    if as_json:
        print(json.dumps(payload))
        return
    render()


def emit_allocation(allocation: Allocation, status: str, as_json: bool) -> None:
    """Print one allocation as a bare path or as JSON."""
    emit(
        {
            "branch": allocation.branch,
            "cwd": allocation.path,
            "engine": allocation.engine,
            "status": status,
        },
        as_json,
        lambda: print(allocation.path),
    )


def emit_list(engine: str, worktrees: Sequence[Worktree], as_json: bool) -> None:
    """Print active worktrees as `branch  path` rows or as JSON."""
    emit(
        {
            "engine": engine,
            "worktrees": [{"branch": w.branch, "path": w.path} for w in worktrees],
        },
        as_json,
        lambda: print_rows(f"{worktree.branch}  {worktree.path}" for worktree in worktrees),
    )


@dataclass(frozen=True)
class WorktreeEntry:
    """One `git worktree list --porcelain` entry, detached entries included."""

    path: str
    branch: str | None
    detached: bool


@dataclass(frozen=True)
class BindingStatus:
    """The branch binding and mismatch flags for one worktree."""

    path: str
    branch: str | None
    clean: bool
    detached: bool
    flags: tuple[str, ...]
    hint: str | None = None


@dataclass(frozen=True)
class RetireResult:
    """What `retire` removed and whether its branch was deleted."""

    path: str
    branch: str | None
    branch_deleted: bool


def parse_git_worktree_entries(raw: str) -> list[WorktreeEntry]:
    """Parse `git worktree list --porcelain`, keeping detached entries too."""
    entries: list[WorktreeEntry] = []
    path: str | None = None
    branch: str | None = None
    detached = False

    def flush() -> None:
        nonlocal path, branch, detached
        if path is not None:
            entries.append(WorktreeEntry(path=path, branch=branch, detached=detached))
        path, branch, detached = None, None, False

    for line in raw.splitlines():
        if line.startswith(PORCELAIN_WORKTREE):
            flush()
            path = line[len(PORCELAIN_WORKTREE) :].strip()
        elif line.startswith(PORCELAIN_BRANCH):
            ref = line[len(PORCELAIN_BRANCH) :].strip()
            if ref.startswith(HEAD_REF_PREFIX):
                branch = ref[len(HEAD_REF_PREFIX) :]
        elif line.strip() == "detached":
            detached = True
    flush()
    return entries


def namespace_parts(branch: str) -> dict[str, str] | None:
    """Return the lane/<task-group>/<role>/<ticket> segments, or None."""
    match = BRANCH_NAMESPACE_RE.match(branch)
    return cast(dict[str, str], match.groupdict()) if match else None


def expected_worktree_name(repo_root: Path, parts: Mapping[str, str]) -> str:
    """Return the `<repo>.<task-group>.<role>` directory name for a namespace."""
    group = sanitize_branch(parts["task_group"])
    role = sanitize_branch(parts["role"])
    return f"{repo_root.name}.{group}.{role}"


def worktree_key(path: str) -> str:
    """Normalize a worktree path into the store key used by `.lane/tasks.yaml`."""
    return os.path.realpath(path)


def git_common_dir_for(path: str, env: Mapping[str, str]) -> Path:
    """Resolve the common git directory as seen from one worktree."""
    raw = run_checked(
        ["git", "-C", path, "rev-parse", "--path-format=absolute", "--git-common-dir"], env
    ).strip()
    return Path(os.path.realpath(raw))


def repo_root_for(path: str, env: Mapping[str, str]) -> Path:
    """Resolve the repository root as seen from one worktree."""
    common = git_common_dir_for(path, env)
    return common.parent if common.name == ".git" else common


def guard_operation(argv: Sequence[str]) -> None:
    """Refuse the forbidden operation surface before anything touches git."""
    tokens = list(argv)
    unsafe = [token for token in tokens if token in FORBIDDEN_TOKENS]
    if "stash" in tokens:
        unsafe.append("stash")
    for verb in ("switch", "checkout"):
        if verb in tokens and "-C" in tokens[tokens.index(verb) + 1 :]:
            unsafe.append("-C")
    if unsafe:
        raise WorktreeError(f"refusing unsafe git operation: {shlex.join(argv)}")


def run_safe(argv: Sequence[str], env: Mapping[str, str]) -> str:
    """Guard then run argv; used for every mutating lifecycle step."""
    guard_operation(argv)
    return run_checked(argv, env)


# --- `.lane/tasks.yaml` persistence -------------------------------------


def yaml_module() -> Any:
    """Import pyyaml on demand; sibling scripts import this module without the dependency."""
    try:
        return herdr_cli.yaml_module()
    except HerdrError as exc:
        raise WorktreeError("claim/retire need pyyaml; run this script with `uv run`") from exc


def now_iso() -> str:
    """UTC timestamp with a trailing Z, matching the lease store style."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def resolve_tasks_file(env: Mapping[str, str]) -> Path:
    """Resolve the shared store from the lane anchor, never from PWD."""
    return resolve_lane_base_dir(env) / STORE_RELATIVE_PATH


def load_tasks(path: Path) -> dict[str, Any]:
    """Load the shared YAML store, treating a missing file as empty."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise WorktreeError(f"cannot read {path}: {exc}") from exc
    if not raw.strip():
        return {}
    yaml = yaml_module()
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise WorktreeError(f"{path} is not valid YAML: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise WorktreeError(f"{path} must contain a mapping at the top level")
    return cast(dict[str, Any], data)


def write_tasks(path: Path, data: Mapping[str, Any]) -> None:
    """Atomically rewrite the shared store so other lanes never see half a file."""
    try:
        herdr_cli.atomic_write_yaml(path, data)
    except OSError as exc:
        raise WorktreeError(f"cannot write {path}: {exc}") from exc


def record_claim(branch: str, path: str, base_sha: str, env: Mapping[str, str]) -> None:
    """Upsert one binding into the store's top-level `worktrees` mapping."""
    parts = namespace_parts(branch)
    if parts is None:
        raise UsageError(f"branch {branch!r} is outside the agent namespace")
    tasks_file = resolve_tasks_file(env)
    data = load_tasks(tasks_file)
    stored = data.get(WORKTREES_KEY)
    if stored is None:
        entries: dict[str, Any] = {}
    elif isinstance(stored, dict):
        entries = cast(dict[str, Any], stored)
    else:
        raise WorktreeError(f"{tasks_file} has a non-mapping {WORKTREES_KEY} section")
    key = worktree_key(path)
    entries[key] = {
        "branch": branch,
        "path": key,
        "base_sha": base_sha,
        "role": parts["role"],
        "task_group": parts["task_group"],
        "ticket": parts["ticket"],
        "claimed_at": now_iso(),
    }
    data[WORKTREES_KEY] = entries
    write_tasks(tasks_file, data)


def forget_claim(path: str, env: Mapping[str, str]) -> None:
    """Drop one binding, removing the `worktrees` key once it is empty."""
    tasks_file = resolve_tasks_file(env)
    data = load_tasks(tasks_file)
    stored = data.get(WORKTREES_KEY)
    if not isinstance(stored, dict):
        return
    entries = cast(dict[str, Any], stored)
    entries.pop(worktree_key(path), None)
    if entries:
        data[WORKTREES_KEY] = entries
    else:
        data.pop(WORKTREES_KEY, None)
    write_tasks(tasks_file, data)


# --- lifecycle verbs ----------------------------------------------------


def worktree_entries(env: Mapping[str, str]) -> list[WorktreeEntry]:
    """List worktrees straight from git (the lifecycle verbs ignore `wt`)."""
    raw = run_checked(["git", "worktree", "list", "--porcelain"], env)
    return parse_git_worktree_entries(raw)


def find_entry(entries: Sequence[WorktreeEntry], path: str) -> WorktreeEntry | None:
    """Find the registered entry whose real path matches."""
    wanted = worktree_key(path)
    for entry in entries:
        if worktree_key(entry.path) == wanted:
            return entry
    return None


def claim(worktree: str, branch: str, base: str, env: Mapping[str, str]) -> Allocation:
    """Move one clean worktree onto a new agent-scoped branch from an explicit base."""
    name = require_branch(branch)
    if namespace_parts(name) is None:
        raise UsageError(
            f"branch {name!r} is outside the agent namespace lane/<task-group>/<role>/<ticket>"
        )
    if not base.strip():
        raise UsageError("claim requires an explicit --base <ref>")
    target = Path(worktree).expanduser()
    if not target.is_dir():
        raise UsageError(f"worktree path {worktree!r} is not a directory")
    entries = worktree_entries(env)
    entry = find_entry(entries, worktree)
    if entry is None:
        raise UsageError(f"{worktree!r} is not a registered git worktree")
    if entry.branch == name:
        record_claim(name, entry.path, resolve_base_sha(base, env), env)
        return Allocation(branch=name, path=entry.path, engine=ENGINE_GIT)
    for other in entries:
        if other.branch == name and worktree_key(other.path) != worktree_key(entry.path):
            raise WorktreeError(
                f"branch {name!r} is already checked out at {other.path}; retire that "
                f"worktree or claim a fresh ticket branch"
            )
    if run_checked(["git", "-C", entry.path, "status", "--porcelain"], env).strip():
        raise UsageError(f"worktree {entry.path} has uncommitted changes; claim needs a clean tree")
    existing = run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{name}"], env)
    if existing.returncode == 0:
        raise WorktreeError(
            f"branch {name!r} already exists and is not checked out anywhere; delete it "
            f"if it is stale, or claim a fresh ticket branch"
        )
    base_sha = resolve_base_sha(base, env)
    _ = run_safe(["git", "-C", entry.path, "switch", "--create", name, base_sha], env)
    head = run_checked(["git", "-C", entry.path, "rev-parse", "--abbrev-ref", "HEAD"], env)
    if head.strip() != name:
        raise WorktreeError(f"switch succeeded but HEAD is {head.strip()!r}, not {name!r}")
    record_claim(name, entry.path, base_sha, env)
    return Allocation(branch=name, path=entry.path, engine=ENGINE_GIT)


def inspect_status(worktree: str | None, env: Mapping[str, str]) -> BindingStatus:
    """Inspect one worktree's branch binding and mismatch flags."""
    target = worktree or "."
    raw_branch = run_checked(
        ["git", "-C", target, "rev-parse", "--abbrev-ref", "HEAD"], env
    ).strip()
    detached = raw_branch == "HEAD"
    branch = None if detached else raw_branch
    clean = not run_checked(["git", "-C", target, "status", "--porcelain"], env).strip()
    resolved = worktree_key(target)
    flags: list[str] = []
    if detached:
        flags.append(FLAG_DETACHED)
    if not clean:
        flags.append(FLAG_DIRTY)
    parts = namespace_parts(branch) if branch is not None else None
    if branch is not None and parts is None:
        flags.append(FLAG_NAMESPACE)
    hint: str | None = None
    if parts is not None:
        expected = expected_worktree_name(repo_root_for(target, env), parts)
        if Path(resolved).name != expected:
            flags.append(FLAG_LAYOUT)
            hint = (
                f"legacy worktree name; migrate with `herdr_worktree.py retire {resolved}` "
                f"then `herdr_worktree.py claim {Path(resolved).parent / expected} "
                f"{branch} --base <base>`"
            )
    return BindingStatus(
        path=resolved,
        branch=branch,
        clean=clean,
        detached=detached,
        flags=tuple(flags),
        hint=hint,
    )


def retire(target: str, env: Mapping[str, str]) -> RetireResult:
    """Remove a clean worktree, delete its merged branch, and prune admin entries."""
    entries = worktree_entries(env)
    wanted = worktree_key(target)
    entry = next(
        (item for item in entries if worktree_key(item.path) == wanted or item.branch == target),
        None,
    )
    if entry is None:
        raise UsageError(f"no registered worktree matches {target!r}")
    if entries and worktree_key(entries[0].path) == worktree_key(entry.path):
        raise UsageError("refusing to retire the primary worktree")
    if entry.branch is not None:
        for other in entries:
            if other.branch == entry.branch and worktree_key(other.path) != worktree_key(
                entry.path
            ):
                raise WorktreeError(f"branch {entry.branch!r} is still checked out at {other.path}")
    if run_checked(["git", "-C", entry.path, "status", "--porcelain"], env).strip():
        raise UsageError(
            f"worktree {entry.path} has uncommitted changes; retire needs a clean tree"
        )
    _ = run_safe(["git", "worktree", "remove", entry.path], env)
    deleted = False
    if entry.branch is not None:
        done = run(["git", "branch", "-d", entry.branch], env)
        if done.returncode == 0:
            deleted = True
        else:
            print(
                f"herdr-worktree: kept branch {entry.branch} (not fully merged): "
                f"{failure_detail(done)}",
                file=sys.stderr,
            )
    _ = run_safe(["git", "worktree", "prune"], env)
    forget_claim(entry.path, env)
    return RetireResult(path=entry.path, branch=entry.branch, branch_deleted=deleted)


def doctor(prune: bool, env: Mapping[str, str]) -> tuple[list[dict[str, Any]], bool]:
    """Audit registered worktrees, optionally pruning only missing admin entries."""
    entries = worktree_entries(env)
    primary = entries[0] if entries else None
    repo_root = Path(worktree_key(primary.path)) if primary is not None else None
    rows: list[dict[str, Any]] = []
    for entry in entries:
        if primary is not None and worktree_key(entry.path) == worktree_key(primary.path):
            continue
        present = Path(entry.path).is_dir()
        flags: list[str] = []
        if not present:
            flags.append(FLAG_UNLINKED)
        if entry.branch is None:
            flags.append(FLAG_ORPHAN)
        parts = namespace_parts(entry.branch) if entry.branch is not None else None
        if entry.branch is not None and parts is None:
            flags.append(FLAG_NAMESPACE)
        if present and parts is not None and repo_root is not None:
            if Path(entry.path).name != expected_worktree_name(repo_root, parts):
                flags.append(FLAG_LAYOUT)
        rows.append({"path": entry.path, "branch": entry.branch, "flags": flags})
    if prune:
        _ = run_safe(["git", "worktree", "prune"], env)
    return rows, prune


def emit_status(status: BindingStatus, as_json: bool) -> None:
    """Print one binding as JSON or as a `branch path state flags` row."""
    branch = status.branch or DETACHED_MARKER
    state = "clean" if status.clean else "dirty"
    flags = ",".join(status.flags) if status.flags else "ok"
    emit(
        {
            "branch": status.branch,
            "path": status.path,
            "clean": status.clean,
            "dirty": not status.clean,
            "detached": status.detached,
            "flags": list(status.flags),
            "hint": status.hint,
        },
        as_json,
        lambda: print(
            f"{branch}  {status.path}  {state}  {flags}"
            + (f"\n  hint: {status.hint}" if status.hint else "")
        ),
    )


def emit_retire(result: RetireResult, as_json: bool) -> None:
    """Print the retired worktree path or a JSON summary."""
    emit(
        {
            "path": result.path,
            "branch": result.branch,
            "removed": True,
            "branch_deleted": result.branch_deleted,
            "pruned": True,
        },
        as_json,
        lambda: print(result.path),
    )


def emit_doctor(rows: Sequence[Mapping[str, Any]], pruned: bool, as_json: bool) -> None:
    """Print the audit as JSON or as `flags branch path` rows."""
    issues = sum(1 for row in rows if row["flags"])
    emit(
        {
            "engine": ENGINE_GIT,
            "pruned": pruned,
            "issues": issues,
            "worktrees": list(rows),
        },
        as_json,
        lambda: print_rows(
            f"{','.join(row['flags']) if row['flags'] else 'ok'}  "
            f"{row['branch'] or DETACHED_MARKER}  {row['path']}"
            for row in rows
        ),
    )


def run_command(options: Options, env: Mapping[str, str]) -> int:
    """Execute the selected subcommand and emit its result."""
    if options.command == "allocate":
        emit_allocation(
            allocate(options.branch or "", options.base, env), "allocated", options.json
        )
    elif options.command == "resolve":
        emit_allocation(resolve(options.branch or "", env), "resolved", options.json)
    elif options.command == "list":
        engine, worktrees = list_worktrees(env)
        emit_list(engine, worktrees, options.json)
    elif options.command == "claim":
        emit_allocation(
            claim(options.worktree or "", options.branch or "", options.base or "", env),
            "claimed",
            options.json,
        )
    elif options.command == "status":
        emit_status(inspect_status(options.worktree, env), options.json)
    elif options.command == "retire":
        emit_retire(retire(options.target or "", env), options.json)
    elif options.command == "doctor":
        rows, pruned = doctor(options.prune, env)
        emit_doctor(rows, pruned, options.json)
    else:
        raise UsageError(f"unknown command {options.command!r}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the lifecycle verbs."""
    parser = argparse.ArgumentParser(
        prog="herdr-worktree",
        description="Pre-provision isolated worktrees for Herdr lane coordination.",
        epilog='allocate prints only the path, so CWD="$(herdr-worktree allocate <branch>)" works.',
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    allocate_parser = subparsers.add_parser(
        "allocate", help="create the branch's worktree and print its path"
    )
    _ = allocate_parser.add_argument("branch", help="branch to create and check out")
    _ = allocate_parser.add_argument(
        "--base", help="base revision to branch from (defaults to the caller HEAD)"
    )
    add_shared_argument(allocate_parser, "json", help="emit a JSON object")

    resolve_parser = subparsers.add_parser(
        "resolve", help="print the existing worktree path for a branch"
    )
    _ = resolve_parser.add_argument("branch", help="branch to look up")
    add_shared_argument(resolve_parser, "json", help="emit a JSON object")

    list_parser = subparsers.add_parser("list", help="list every active worktree")
    add_shared_argument(list_parser, "json", help="emit a JSON object")

    claim_parser = subparsers.add_parser(
        "claim", help="move one worktree onto a new agent-scoped branch"
    )
    _ = claim_parser.add_argument("worktree", help="path of the registered worktree to move")
    _ = claim_parser.add_argument("branch", help="agent branch lane/<task-group>/<role>/<ticket>")
    _ = claim_parser.add_argument(
        "--base", required=True, help="base revision the new branch starts from"
    )
    add_shared_argument(claim_parser, "json", help="emit a JSON object")

    status_parser = subparsers.add_parser("status", help="inspect one worktree's branch binding")
    _ = status_parser.add_argument(
        "--worktree", help="worktree path (defaults to the current directory)"
    )
    add_shared_argument(status_parser, "json", help="emit a JSON object")

    retire_parser = subparsers.add_parser(
        "retire", help="remove a clean worktree and its merged branch"
    )
    _ = retire_parser.add_argument("target", help="worktree path or branch to retire")
    add_shared_argument(retire_parser, "json", help="emit a JSON object")

    doctor_parser = subparsers.add_parser("doctor", help="audit every registered worktree")
    _ = doctor_parser.add_argument(
        "--prune", action="store_true", help="prune admin entries for missing directories"
    )
    add_shared_argument(doctor_parser, "json", help="emit a JSON object")
    return parser


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    """Parse arguments and run the helper; return the process exit status."""
    return entrypoint(
        "herdr-worktree", build_parser, run_command, namespace=Options(), argv=argv, env=env
    )


if __name__ == "__main__":
    raise SystemExit(main())
