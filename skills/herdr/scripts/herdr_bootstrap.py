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

- Inline kinds (`pi`, `claude`) take the snippet through ``agent start
  --append-system-prompt``; nothing is written to disk.
- File-reading kinds (`cline`, `codex`, `copilot`, `qodercli`, `agy`) and any unknown kind get
  the marker-wrapped block appended to ``AGENTS.md`` in the target directory. `cline` prefers
  an existing ``.clinerules`` over ``AGENTS.md``.
The append is idempotent: the marker pair (``<!-- herdr-bootstrap:role-invariant -->``) is
written once, so re-bootstrapping the same directory never duplicates the snippet and never
rewrites an untouched file.

Deliberate quirks (implemented minimally, documented here): trust flags come only from
``kinds.yaml`` and ride after ``--`` as native agent args — bootstrap never invents flags, and an
unverified kind carries none; an unknown kind falls back to the universal ``AGENTS.md`` append
rather than failing, so a new kind is bootstrapped by default. When ``--cwd`` names a worktree,
bootstrap cds the pane there and refuses to start when the pane does not converge.
Exit status: 0 ok, 1 herdr failure, 2 usage or missing precondition.

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
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
    entries,
    entry_optional_text,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr_checked,
    scoped_agent_name,
    validate_agent_name,
)

AGENTS_MD = "AGENTS.md"
CLINE_RULES = ".clinerules"
START_MARKER = "<!-- herdr-bootstrap:role-invariant -->"
END_MARKER = "<!-- /herdr-bootstrap:role-invariant -->"

# Startup contract per kind, loaded from skills/herdr/references/kinds.yaml.
# Unknown kinds fall back to the file append with no trust flags (forward-compatible).
KINDS_CONFIG = Path(__file__).resolve().parent.parent / "references" / "kinds.yaml"

_CWD_POLL_S = 0.25


@dataclass(frozen=True)
class KindEntry:
    """One kind's startup contract: native trust flags plus the invariant surface."""

    trust_flags: tuple[str, ...]
    inline_invariant: bool


FALLBACK_ENTRY = KindEntry(trust_flags=(), inline_invariant=False)


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
    """Parse the strict kinds.yaml subset: kind tables with trust_flags and invariant only.

    Values may not contain `#`; block sequences are rejected — use the flow list.
    Raises ValueError with a line number on anything outside the subset.
    """
    raw: dict[str, dict[str, str | tuple[str, ...]]] = {}
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
            else:
                raise ValueError(f"line {lineno}: unknown key {key!r}")
    entries: dict[str, KindEntry] = {}
    for kind, item in raw.items():
        flags = item.get("trust_flags")
        invariant = item.get("invariant")
        if not isinstance(flags, tuple) or invariant not in ("inline", "file"):
            raise ValueError(f"kind {kind!r}: needs trust_flags [...] and invariant inline|file")
        entries[kind] = KindEntry(trust_flags=flags, inline_invariant=invariant == "inline")
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


INVARIANT_TEMPLATE = (
    "ROLE INVARIANT: You are an {role} in a Herdr lane.\n"
    "1. Subagent-First: MUST delegate deep search, multi-file edits, and test triage to "
    "internal subagents.\n"
    "2. Reply Contract: MUST reply to caller via `uv run "
    "~/.agents/skills/herdr/scripts/herdr_reply.py <caller> --file <reply.md>` upon completion "
    "or blocker. Never exit silently."
)


def render_invariant(role: str) -> str:
    """Render the role invariant snippet for one role; stays within the 45-word budget."""
    return INVARIANT_TEMPLATE.format(role=role)


def append_invariant(path: Path, snippet: str) -> bool:
    """Append the marker-wrapped snippet unless the start marker is already present.

    Returns True when the block was written, False when the file already carried it. Existing
    content and its trailing newline are preserved; an already-marked file is never rewritten.
    """
    existing = path.read_text() if path.exists() else ""
    if START_MARKER in existing:
        return False
    if existing and not existing.endswith("\n"):
        existing += "\n"
    block = f"{START_MARKER}\n{snippet}\n{END_MARKER}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(existing + block)
    return True


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
    _ = parser.add_argument(
        "--pane", required=True, metavar="ID", help="pane to start the agent in"
    )
    _ = parser.add_argument(
        "--role",
        default="",
        metavar="ROLE",
        help="role named in the invariant (e.g. tm, impl-1); defaults to NAME",
    )
    _ = parser.add_argument(
        "--task-group",
        default=None,
        metavar="SLUG",
        help="scope NAME with this task-group slug before naming the pane and agent",
    )
    _ = parser.add_argument("--model", default=None, metavar="MODEL", help="model for agent start")
    _ = parser.add_argument(
        "--cwd",
        default=None,
        metavar="DIR",
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
        "--dry-run",
        action="store_true",
        help="print the planned file path and start argv, mutate nothing",
    )
    _ = parser.add_argument("--json", action="store_true", help="print herdr's raw start response")
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


def build_start_argv(
    herdr: str, options: Options, name: str, snippet: str, *, entry: KindEntry
) -> list[str]:
    """Assemble `agent start`; config trust flags ride after `--` as native agent args."""
    argv = [herdr, "agent", "start", name, "--kind", options.kind, "--pane", options.pane]
    if options.model:
        argv += ["--model", options.model]
    if entry.inline_invariant:
        argv += ["--append-system-prompt", snippet]
    if entry.trust_flags:
        argv += ["--", *entry.trust_flags]
    return argv


def bootstrap(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    herdr = find_herdr(env)
    name = resolve_name(options)
    role = options.role or options.name
    snippet = render_invariant(role)
    entry = load_kind_entry(options.kind)

    agents_file: Path | None = None
    if not entry.inline_invariant:
        target_dir = resolve_target_dir(herdr, options, env, dry_run=options.dry_run)
        agents_file = target_path(target_dir, options.kind)

    rename_argv = [herdr, "pane", "rename", options.pane, name]
    start_argv = build_start_argv(herdr, options, name, snippet, entry=entry)
    if options.dry_run:
        print(
            json.dumps(
                {
                    "agents_md": str(agents_file) if agents_file else None,
                    "pane_rename": rename_argv,
                    "agent_start": start_argv,
                    "cwd_ensure": options.cwd,
                }
            )
        )
        return EXIT_OK

    if options.cwd:
        ensure_pane_cwd(herdr, options.pane, options.cwd, env, timeout_s=options.cwd_timeout)
    _ = run_herdr_checked(rename_argv, env)
    if agents_file is not None:
        try:
            _ = append_invariant(agents_file, snippet)
        except OSError as exc:
            raise UsageError(f"cannot write {agents_file}: {exc}") from exc
    raw = run_herdr_checked(start_argv, env)

    if options.json:
        print(raw, end="" if raw.endswith("\n") else "\n")
        return EXIT_OK
    written = str(agents_file) if agents_file else "-"
    print(f"bootstrapped {name} ({options.kind}) pane={options.pane} agents-md={written}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-bootstrap", lambda: bootstrap(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
