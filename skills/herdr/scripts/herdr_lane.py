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
tab-create response carries both the tab and its root pane, and the split response carries the
new pane, so no id is ever recovered from a re-list.
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
    create_tab,
    current_workspace_id,
    entrypoint,
    find_herdr,
    require_herdr_env,
    split_pane,
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
    workspace: str | None = None
    orch_kind: str = "agy"
    tm_kind: str = "pi"
    impl_kind: str = "pi"
    cwd_orch: str | None = None
    cwd_tm: str = ""
    cwd_impl: str = ""
    tm_model: str | None = None
    impl_model: str | None = None
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
        "--workspace",
        default=None,
        metavar="ID",
        help="Herdr workspace for the lane tabs (default: the calling workspace)",
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
    _ = up.add_argument(
        "--tm-model",
        default=None,
        metavar="MODEL",
        help="model for the Task Manager's agent (default: the agent kind's own)",
    )
    _ = up.add_argument(
        "--impl-model",
        default=None,
        metavar="MODEL",
        help="model for the Implementer's agent (default: the agent kind's own)",
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


def resolve_workspace(requested: str | None, herdr: str, env: Mapping[str, str]) -> str:
    """The workspace id for the lane's tabs: explicit flag first, then the caller's workspace."""
    if requested and requested.strip():
        return requested.strip()
    return current_workspace_id(herdr, env)


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
    workspace = resolve_workspace(options.workspace, herdr, env)
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
    return [
        (
            "orch-tab",
            [
                herdr,
                "tab",
                "create",
                "--workspace",
                workspace,
                "--cwd",
                orch_cwd,
                "--label",
                prefix,
                "--no-focus",
            ],
        ),
        (
            "orch-agent",
            _bootstrap_argv(prefix, "<orch-pane>", options.orch_kind, "orch", orch_cwd, None),
        ),
        (
            "crew-tab",
            [
                herdr,
                "tab",
                "create",
                "--workspace",
                workspace,
                "--cwd",
                tm_cwd,
                "--label",
                crew_label(prefix, revision),
                "--no-focus",
            ],
        ),
        ("impl-split", split),
        (
            "tm-agent",
            _bootstrap_argv(prefix, "<tm-pane>", options.tm_kind, "tm", tm_cwd, options.tm_model),
        ),
        (
            "impl-agent",
            _bootstrap_argv(
                prefix, "<impl-pane>", options.impl_kind, "impl", impl_cwd, options.impl_model
            ),
        ),
    ]


def _bootstrap_argv(
    prefix: str,
    pane_id: str,
    kind: str,
    role: str,
    cwd: str,
    model: str | None,
) -> list[str]:
    """The `herdr_bootstrap.py` argv for one role; `--model` rides only for a role that set one."""
    argv = [
        sys.executable,
        str(BOOTSTRAP_SCRIPT),
        "--pane",
        pane_id,
        "--kind",
        kind,
        "--role",
        role,
        "--task-group",
        prefix,
        "--cwd",
        cwd,
    ]
    if model is not None:
        argv += ["--model", model]
    return argv


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


def _tab(lane: Lane, label: str, cwd: str, workspace: str) -> tuple[str, str]:
    created = create_tab(
        lane.herdr, lane.env, workspace_id=workspace, label=label, cwd=cwd, focus=False
    )
    tab_id = created.tab.tab_id
    pane_id = created.root_pane.pane_id
    lane.created.append(f"tab {tab_id} ({label}) pane {pane_id}")
    return tab_id, pane_id


def _split(lane: Lane, pane_id: str, cwd: str) -> str:
    pane = split_pane(
        lane.herdr,
        lane.env,
        pane_id=pane_id,
        direction="right",
        cwd=cwd,
        env_vars=lane_anchor_env_args(lane.env, ()),
        focus=False,
    )
    lane.created.append(f"pane {pane.pane_id} (split of {pane_id})")
    return pane.pane_id


def _agent(lane: Lane, pane_id: str, kind: str, role: str, cwd: str, model: str | None) -> None:
    run_sibling(_bootstrap_argv(lane.options.prefix, pane_id, kind, role, cwd, model), lane.env)
    lane.created.append(f"agent {role} ({kind}) in pane {pane_id}")


def _up(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    steps = plan(options, env)
    if options.dry_run:
        for _, argv in steps:
            print(shlex.join(argv))
        return EXIT_OK

    lane = Lane(options=options, env=env, herdr=find_herdr(env))
    orch_cwd = resolve_cwd(options.cwd_orch, env)
    tm_cwd = resolve_cwd(options.cwd_tm, env)
    impl_cwd = resolve_cwd(options.cwd_impl, env)
    workspace = resolve_workspace(options.workspace, lane.herdr, env)
    try:
        _, orch_pane = _tab(lane, options.prefix, orch_cwd, workspace)
        _agent(lane, orch_pane, options.orch_kind, "orch", orch_cwd, None)
        _, tm_pane = _tab(lane, crew_label(options.prefix, options.revision), tm_cwd, workspace)
        impl_pane = _split(lane, tm_pane, impl_cwd)
        _agent(lane, tm_pane, options.tm_kind, "tm", tm_cwd, options.tm_model)
        _agent(lane, impl_pane, options.impl_kind, "impl", impl_cwd, options.impl_model)
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
