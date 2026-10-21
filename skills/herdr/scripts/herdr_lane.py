"""herdr-lane: build a lane's tab and pane topology in one command.

The standard lane is two tabs: the orchestrator alone in its own tab, and a crew tab with the
Task Manager and the Implementer side by side. The orchestrator tab keeps the bare prefix so it
survives every respawn; the crew tab carries the lane revision (`<prefix>-r<N>`).

Bring-up only. Teardown stays manual (`herdr pane close`) because the daemon has no agent-stop
primitive: closing a generation means letting its process exit in the pane, which is exactly the
shell prompt the next `herdr-bootstrap --pane` needs.

Every daemon call goes through the shared subprocess seam, and each agent start is delegated to
`herdr_bootstrap.py` rather than re-implemented here, so the role invariant, the scoped agent
name, and the `--cwd` worktree rule stay in one place. Ids are read back, never predicted: the
tab from the creation response (or `tab list` when it is silent), its first pane from
`pane list`, and the split pane from the split response.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from herdr_cli import (
    EXIT_OK,
    HerdrError,
    UsageError,
    add_shared_argument,
    entrypoint,
    find_herdr,
    payload_field,
    require_herdr_env,
    run_herdr_checked,
    text_field,
)
from herdr_pane import build_split_argv, lane_anchor_env_args, resolve_cwd

PROG = "herdr-lane"
SCRIPTS_DIR = Path(__file__).resolve().parent
BOOTSTRAP_SCRIPT = SCRIPTS_DIR / "herdr_bootstrap.py"
REVISION_FLOOR = 1
PLANNED_STEPS = 6


@dataclass
class Options:
    """Parsed `up` arguments."""

    verb: str = "up"
    prefix: str = ""
    revision: int = 1
    orch_kind: str = "agy"
    tm_kind: str = "pi"
    impl_kind: str = "pi"
    cwd_orch: str | None = None
    cwd_tm: str = ""
    cwd_impl: str = ""
    dry_run: bool = False


@dataclass
class Lane:
    """What a bring-up knows while it runs: the resolved plan inputs and what already exists."""

    options: Options
    env: Mapping[str, str]
    herdr: str
    created: list[str] = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    """The `up` verb and its arguments."""
    parser = argparse.ArgumentParser(prog=PROG, description=(__doc__ or "").splitlines()[0])
    verbs = parser.add_subparsers(dest="verb", required=True)
    up = verbs.add_parser("up", help="create the lane's tabs, panes, and agents")
    _ = up.add_argument(
        "--prefix", required=True, metavar="SLUG", help="lane slug, also the task group"
    )
    _ = up.add_argument(
        "--revision",
        type=int,
        default=1,
        metavar="N",
        help="crew tab revision suffix (default 1)",
    )
    _ = up.add_argument(
        "--orch-kind", default="agy", metavar="KIND", help="agent kind for the orchestrator"
    )
    _ = up.add_argument(
        "--tm-kind", default="pi", metavar="KIND", help="agent kind for the Task Manager"
    )
    _ = up.add_argument(
        "--impl-kind", default="pi", metavar="KIND", help="agent kind for the Implementer"
    )
    _ = up.add_argument(
        "--cwd-orch",
        default=None,
        metavar="DIR",
        help="orchestrator worktree (default: the current directory)",
    )
    _ = up.add_argument(
        "--cwd-tm",
        required=True,
        metavar="DIR",
        help="Task Manager worktree (required: a crew pane never defaults into the orchestrator's checkout)",
    )
    _ = up.add_argument(
        "--cwd-impl",
        required=True,
        metavar="DIR",
        help="Implementer worktree (required, same reason)",
    )
    add_shared_argument(
        up,
        "dry_run",
        help=f"print the {PLANNED_STEPS} planned commands and execute nothing",
    )
    return parser


def _validated_prefix(value: str) -> str:
    prefix = value.strip()
    if not prefix or "\n" in prefix:
        raise UsageError("--prefix must be a non-empty single-line lane slug")
    return prefix


def _validated_revision(value: int) -> int:
    if value < REVISION_FLOOR:
        raise UsageError(f"--revision {value} is out of range: want >= {REVISION_FLOOR}")
    return value


def crew_label(prefix: str, revision: int) -> str:
    """The crew tab's label: the prefix with this lane's revision."""
    return f"{prefix}-r{revision}"


def plan(options: Options, env: Mapping[str, str]) -> list[tuple[str, list[str]]]:
    """The six commands, in order, with placeholders where an id is only known at run time.

    Building the plan before executing it is what makes `--dry-run` honest: the printed lines are
    the argv this helper would run, in the same order, and a test compares the two.
    """
    prefix = _validated_prefix(options.prefix)
    revision = _validated_revision(options.revision)
    orch_cwd = resolve_cwd(options.cwd_orch, env)
    tm_cwd = resolve_cwd(options.cwd_tm, env)
    impl_cwd = resolve_cwd(options.cwd_impl, env)
    herdr = find_herdr(env)
    anchor = lane_anchor_env_args(env, ())
    split = build_split_argv(
        herdr,
        "<tm-pane>",
        "right",
        cwd=impl_cwd,
        ratio=None,
        extra_env=anchor,
        focus=False,
    )
    bootstrap = [sys.executable, str(BOOTSTRAP_SCRIPT)]
    return [
        ("orch-tab", [herdr, "tab", "create", "--label", prefix, "--cwd", orch_cwd, "--no-focus"]),
        (
            "orch-agent",
            [
                *bootstrap,
                "--pane",
                "<orch-pane>",
                "--kind",
                options.orch_kind,
                "--role",
                "orch",
                "--task-group",
                prefix,
                "--cwd",
                orch_cwd,
            ],
        ),
        (
            "crew-tab",
            [
                herdr,
                "tab",
                "create",
                "--label",
                crew_label(prefix, revision),
                "--cwd",
                tm_cwd,
                "--no-focus",
            ],
        ),
        ("impl-split", split),
        (
            "tm-agent",
            [
                *bootstrap,
                "--pane",
                "<tm-pane>",
                "--kind",
                options.tm_kind,
                "--role",
                "tm",
                "--task-group",
                prefix,
                "--cwd",
                tm_cwd,
            ],
        ),
        (
            "impl-agent",
            [
                *bootstrap,
                "--pane",
                "<impl-pane>",
                "--kind",
                options.impl_kind,
                "--role",
                "impl",
                "--task-group",
                prefix,
                "--cwd",
                impl_cwd,
            ],
        ),
    ]


def _created_tab_id(lane: Lane, raw: str, label: str) -> str:
    """The id of the tab just created: the response first, `tab list` as the fallback."""
    for path in (("result", "tab", "tab_id"), ("result", "tab")):
        try:
            return text_field(raw, *path)
        except HerdrError:
            continue
    listed = payload_field(
        run_herdr_checked([lane.herdr, "tab", "list"], lane.env), "result", "tabs"
    )
    tabs = listed if isinstance(listed, list) else []
    matches = [
        entry.get("tab_id")
        for entry in tabs
        if isinstance(entry, dict) and entry.get("label") == label
    ]
    if len(matches) == 1 and isinstance(matches[0], str):
        return matches[0]
    raise HerdrError(f"cannot identify the tab created for label {label!r}: {raw.strip()[:200]}")


def _first_pane(lane: Lane, tab_id: str) -> str:
    """The tab's first pane, read from `pane list` — the creation response names no pane."""
    listed = payload_field(
        run_herdr_checked([lane.herdr, "pane", "list"], lane.env), "result", "panes"
    )
    panes = listed if isinstance(listed, list) else []
    for entry in panes:
        if isinstance(entry, dict) and entry.get("tab_id") == tab_id:
            pane_id = entry.get("pane_id")
            if isinstance(pane_id, str) and pane_id:
                return pane_id
    raise HerdrError(f"tab {tab_id} reported no pane in `pane list`")


def run_sibling(argv: Sequence[str], env: Mapping[str, str]) -> None:
    """Run a sibling helper in-process-equivalent terms; a non-zero exit aborts the bring-up."""
    result = subprocess.run(  # noqa: S603 - fixed helper argv, no shell
        list(argv),
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        tail = detail[-1] if detail else "no output"
        raise HerdrError(f"{Path(argv[1]).name} exited {result.returncode}: {tail}")


def _tab(lane: Lane, label: str, cwd: str) -> tuple[str, str]:
    raw = run_herdr_checked(
        [lane.herdr, "tab", "create", "--label", label, "--cwd", cwd, "--no-focus"], lane.env
    )
    tab_id = _created_tab_id(lane, raw, label)
    pane_id = _first_pane(lane, tab_id)
    lane.created.append(f"tab {tab_id} ({label}) pane {pane_id}")
    return tab_id, pane_id


def _split(lane: Lane, pane_id: str, cwd: str) -> str:
    argv = build_split_argv(
        lane.herdr,
        pane_id,
        "right",
        cwd=cwd,
        ratio=None,
        extra_env=lane_anchor_env_args(lane.env, ()),
        focus=False,
    )
    new_pane = text_field(run_herdr_checked(argv, lane.env), "result", "pane", "pane_id")
    lane.created.append(f"pane {new_pane} (split of {pane_id})")
    return new_pane


def _agent(lane: Lane, pane_id: str, kind: str, role: str, cwd: str) -> None:
    run_sibling(
        [
            sys.executable,
            str(BOOTSTRAP_SCRIPT),
            "--pane",
            pane_id,
            "--kind",
            kind,
            "--role",
            role,
            "--task-group",
            lane.options.prefix,
            "--cwd",
            cwd,
        ],
        lane.env,
    )
    lane.created.append(f"agent {role} ({kind}) in pane {pane_id}")


def _up(options: Options, env: Mapping[str, str]) -> int:
    steps = plan(options, env)
    if options.dry_run:
        for _, argv in steps:
            print(shlex.join(argv))
        return EXIT_OK

    require_herdr_env(env)
    lane = Lane(options=options, env=env, herdr=find_herdr(env))
    orch_cwd = resolve_cwd(options.cwd_orch, env)
    tm_cwd = resolve_cwd(options.cwd_tm, env)
    impl_cwd = resolve_cwd(options.cwd_impl, env)
    try:
        _, orch_pane = _tab(lane, options.prefix, orch_cwd)
        _agent(lane, orch_pane, options.orch_kind, "orch", orch_cwd)
        _, tm_pane = _tab(lane, crew_label(options.prefix, options.revision), tm_cwd)
        impl_pane = _split(lane, tm_pane, impl_cwd)
        _agent(lane, tm_pane, options.tm_kind, "tm", tm_cwd)
        _agent(lane, impl_pane, options.impl_kind, "impl", impl_cwd)
    except (HerdrError, UsageError) as exc:
        done = "; ".join(lane.created) if lane.created else "nothing"
        raise HerdrError(
            f"bring-up stopped: {exc}. Created so far — {done}. Close those panes before retrying."
        ) from exc

    print(f"lane {options.prefix} r{options.revision}: " + "; ".join(lane.created))
    return EXIT_OK


def _dispatch(options: Options, env: Mapping[str, str]) -> int:
    return _up(options, env)


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    return entrypoint(PROG, build_parser, _dispatch, namespace=Options(), argv=argv, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
