#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
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

`allocate` in its plain form prints only the absolute path, so callers substitute it
directly: `WORKTREE_PATH=$(... allocate <branch>)`. Exit status: `0` ok, `1` the worktree
engine failed, `2` usage or missing precondition. Unlike its siblings this helper needs no
`HERDR_ENV=1` session; it only shells out to `wt`/`git`. Local addition to the absorbed
upstream Herdr skill; not part of `herdrdev/herdr`.
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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from herdr_cli import EXIT_OK, HerdrError, UsageError, guard

ENGINE_WORKTRUNK = "worktrunk"
ENGINE_GIT = "git"

PORCELAIN_WORKTREE = "worktree "
PORCELAIN_BRANCH = "branch "
HEAD_REF_PREFIX = "refs/heads/"
DETACHED_MARKER = "(detached HEAD)"
# `git worktree list` compact rows some wrappers emit despite --porcelain:
#   /path/to/wt 0e57943 [feat/184-worktree]
COMPACT_WORKTREE_RE = re.compile(r"^(?P<path>\S+)\s+[0-9a-f]{7,40}\s+\[(?P<branch>.+)\]$")
BRANCH_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


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


def run(argv: Sequence[str], env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    """Run argv without a shell, capturing text; missing binaries raise WorktreeError."""
    try:
        return subprocess.run(
            list(argv), capture_output=True, text=True, check=False, env=dict(env)
        )
    except OSError as exc:
        raise WorktreeError(f"cannot run {argv[0]}: {exc}") from exc


def failure_detail(done: subprocess.CompletedProcess[str]) -> str:
    """One-line diagnostic from a failed process, preferring stderr."""
    return (done.stderr or done.stdout).strip() or f"exit status {done.returncode}"


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
    return run_checked(["git", "rev-parse", "--is-bare-repository"], env).strip() == "true"


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


def sanitize_branch(branch: str) -> str:
    """Reduce a branch name to a filesystem-safe suffix (feat/184 -> feat-184)."""
    sanitized = BRANCH_UNSAFE_RE.sub("-", branch).strip("-.")
    return sanitized or "worktree"


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


def allocate(branch: str, base: str | None, env: Mapping[str, str]) -> Allocation:
    """Allocate the branch's worktree through Worktrunk when present, else `git worktree`.

    A bare repository is always allocated by git: Worktrunk's `{{ repo_path }}` is then the
    git directory itself, so its sibling convention collapses to `<git-dir>.<slug>` (#207).
    """
    name = require_branch(branch)
    wt = wt_binary(env)
    if wt is not None and not is_bare_repository(env):
        allocation = allocate_with_wt(wt, name, base, env)
        guard_not_in_git_dir(Path(allocation.path), env)
        return allocation
    if wt is not None:
        print(
            "herdr-worktree: bare repository; allocating with git worktree instead of wt",
            file=sys.stderr,
        )
    return allocate_with_git(name, base, env)


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


def emit_allocation(allocation: Allocation, status: str, as_json: bool) -> None:
    """Print one allocation as a bare path or as JSON."""
    if as_json:
        print(
            json.dumps(
                {
                    "branch": allocation.branch,
                    "cwd": allocation.path,
                    "engine": allocation.engine,
                    "status": status,
                }
            )
        )
        return
    print(allocation.path)


def emit_list(engine: str, worktrees: Sequence[Worktree], as_json: bool) -> None:
    """Print active worktrees as `branch  path` rows or as JSON."""
    if as_json:
        print(
            json.dumps(
                {
                    "engine": engine,
                    "worktrees": [{"branch": w.branch, "path": w.path} for w in worktrees],
                }
            )
        )
        return
    for worktree in worktrees:
        print(f"{worktree.branch}  {worktree.path}")


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
    else:
        raise UsageError(f"unknown command {options.command!r}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for allocate, resolve, and list."""
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
        "--base", help="base revision to branch from (defaults to wt/git)"
    )
    _ = allocate_parser.add_argument("--json", action="store_true", help="emit a JSON object")

    resolve_parser = subparsers.add_parser(
        "resolve", help="print the existing worktree path for a branch"
    )
    _ = resolve_parser.add_argument("branch", help="branch to look up")
    _ = resolve_parser.add_argument("--json", action="store_true", help="emit a JSON object")

    list_parser = subparsers.add_parser("list", help="list every active worktree")
    _ = list_parser.add_argument("--json", action="store_true", help="emit a JSON object")
    return parser


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    """Parse arguments and run the helper; return the process exit status."""
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())

    def action() -> int:
        return run_command(options, env_map)

    return guard("herdr-worktree", action)


if __name__ == "__main__":
    raise SystemExit(main())
