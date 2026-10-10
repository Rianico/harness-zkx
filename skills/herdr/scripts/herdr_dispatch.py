#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""herdr-dispatch — manager-side task dispatch helper for Herdr multi-agent lanes.

Dispatches a ticket file to one or more callees with the Sender/Receiver envelope and reply contract,
validates addressable agent names (refusing kinds), and verifies post-dispatch delivery
in one command.

    herdr-dispatch callee --file ticket.md --no-wait
    herdr-dispatch callee --file ticket.md --wait --timeout 15000
    herdr-dispatch callee1 callee2 --file ticket.md --no-wait

Draft flow: `herdr-dispatch --draft callee [--file ticket.md]` prints (or writes)
a ticket skeleton whose routing is prefilled from live state. The model fills the
Task/Context/Acceptance sections and deletes the `herdr-draft: unfilled` marker,
then dispatches that file with `--file`. Dispatch refuses a ticket that still
carries the marker, or one whose three sections are all empty. Free-form tickets
pass untouched: `{{...}}` text is reported inside a refusal message, never a
rejection reason on its own.

Exit status: 0 accepted, 1 herdr failure, 2 usage or missing precondition,
3 a target needs human input (blocked), 4 prompt delivered but wait timed out.

Local addition to the absorbed upstream Herdr skill; not part of `herdrdev/herdr`.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_OK,
    KNOWN_AGENT_KINDS,
    METHOD_CONSTRAINT_EPILOG,
    UsageError,
    entries,
    entry_optional_text,
    find_herdr,
    guard,
    inspect_target_shell_pane,
    require_herdr_env,
    run_herdr_checked,
)
from herdr_lease import acquire_lease, get_lease, release_lease
from herdr_prompt import (
    EXIT_WAIT_TIMEOUT,
    PROMPT_STATES,
    WaitTimeout,
    prompt_agents,
    resolve_caller,
    resolve_targets,
)
from herdr_prompt import Options as PromptOptions


@dataclass
class Options(PromptOptions):
    """CLI options; `argparse` writes into this typed namespace."""

    force: bool = False
    draft: bool = False
    auto_start: str | None = None
    role: str | None = None
    cwd: str | None = None
    model: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-dispatch",
        description="Dispatch a ticket file to a Herdr callee with the Sender/Receiver envelope and reply contract.",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 a target needs human input, 4 prompt delivered but wait timed out\n\n"
            "ticket-id derivation: '-' (stdin) yields none; a filename stem starting with '#' is "
            "used as-is; a stem matching ^\\d+([-_].+)?$ is prefixed with '#' (182-foo -> #182-foo); "
            "any other stem is used verbatim (PROJ-182-foo -> PROJ-182-foo)\n\n"
            + METHOD_CONSTRAINT_EPILOG
        ),
    )
    _ = parser.add_argument(
        "targets",
        nargs="*",
        metavar="TARGET",
        help="callee agent names or pane ids (one or more)",
    )
    _ = parser.add_argument(
        "--file",
        metavar="PATH",
        help="ticket payload file (required unless --draft); '-' reads stdin verbatim",
    )
    _ = parser.add_argument(
        "--draft",
        action="store_true",
        help="print a ticket skeleton with routing prefilled (or write it to --file); send nothing",
    )
    _ = parser.add_argument(
        "--label",
        metavar="LABEL",
        help="exact pane label to resolve to a pane id, instead of TARGET",
    )
    _ = parser.add_argument(
        "--wait",
        action="store_true",
        help="wait for callee to settle after receiving ticket",
    )
    _ = parser.add_argument(
        "--no-wait",
        action="store_true",
        help="dispatch without waiting; fails when combined with --wait",
    )
    _ = parser.add_argument(
        "--until",
        action="append",
        metavar="STATUS",
        help=f"exact state to match after --wait, repeatable ({PROMPT_STATES})",
    )
    _ = parser.add_argument(
        "--timeout",
        type=int,
        metavar="MS",
        help="fail after this many milliseconds",
    )
    _ = parser.add_argument("--json", action="store_true", help="print herdr's raw JSON response")
    _ = parser.add_argument("--dry-run", action="store_true", help="print the argv, submit nothing")
    _ = parser.add_argument(
        "--no-caller-context",
        action="store_true",
        help="send payload verbatim without the Sender/Receiver envelope and reply contract (warns loudly)",
    )
    _ = parser.add_argument(
        "--force",
        action="store_true",
        help="bypass active ticket lease checks and dispatch anyway",
    )
    _ = parser.add_argument(
        "--auto-start",
        metavar="KIND",
        default=None,
        help=(
            "bootstrap a missing callee through the herdr-bootstrap contract "
            "(ROLE INVARIANT, kind trust flags, pane cwd) before dispatching; "
            "live agents dispatch with no extra calls"
        ),
    )
    _ = parser.add_argument(
        "--role",
        metavar="ROLE",
        default=None,
        help="role named in the ROLE INVARIANT when --auto-start boots a missing callee",
    )
    _ = parser.add_argument(
        "--cwd",
        metavar="DIR",
        default=None,
        help="worktree dir the auto-started callee must start in (pane converges first)",
    )
    _ = parser.add_argument(
        "--model",
        metavar="MODEL",
        default=None,
        help="model for the auto-started callee's agent start",
    )
    _ = parser.add_argument(
        "--ticket-id",
        metavar="ID",
        default=None,
        help=(
            "Ticket-ID for correlation (e.g. '#182-herdr-msg-enhance'); derived from the ticket "
            "filename when omitted (see epilog for the derivation rule)"
        ),
    )
    _ = parser.add_argument(
        "--task-id",
        metavar="ID",
        default=None,
        help=(
            "Task-ID for correlation (e.g. '#182-herdr-msg-enhance#full-stack'); defaults to the "
            "Ticket-ID when omitted"
        ),
    )
    _ = parser.add_argument(
        "--task-group",
        metavar="NAME",
        default=None,
        help="Task Group (Herdr Tab) label for the Hierarchy block; omitted when not given",
    )
    _ = parser.add_argument(
        "--verbose",
        action="store_true",
        help="restore the Runtime: Cwd/Resume block in the rendered envelope (default trimmed)",
    )
    return parser


def resolve_target_identity(
    herdr: str, target: str, env: Mapping[str, str]
) -> tuple[str, str | None]:
    """Resolve target to (canonical_agent_name_or_target, pane_id)."""
    try:
        agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
        for a in agents:
            name = entry_optional_text(a, "name")
            pane = entry_optional_text(a, "pane_id")
            if target == name:
                return target, pane
            if target == pane:
                canonical = name if name is not None else target
                return canonical, pane
    except Exception:
        # An unreadable inventory is no answer: fall back to the raw target, and let the CLI
        # report `agent_not_found` for a genuinely unknown one.
        return target, None
    return target, None


def live_pane_ids(herdr: str, env: Mapping[str, str]) -> set[str] | None:
    """Pane ids Herdr reports right now, or None when that inventory cannot answer.

    An unreadable or empty inventory is no evidence, so callers must keep the conservative
    behaviour: a lease is only stale when a live inventory positively lacks its pane.
    """
    try:
        panes = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
    except Exception:
        return None
    ids = {entry_optional_text(pane, "pane_id") for pane in panes}
    live = {pane_id for pane_id in ids if pane_id}
    return live or None


def lease_pane_is_gone(lease: Mapping[str, object], herdr: str, env: Mapping[str, str]) -> bool:
    """Whether the lease records a pane that no longer exists (#210).

    A callee that replied and was then resumed runs on a new pane, so its old pane id cannot
    answer for the ticket any more. A lease with no pane id is not judged here.
    """
    pane_id = lease.get("pane_id")
    if not isinstance(pane_id, str) or not pane_id:
        return False
    live = live_pane_ids(herdr, env)
    return live is not None and pane_id not in live


PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}")
DRAFT_MARKER = "herdr-draft: unfilled"
DRAFT_SECTIONS = ("## Task", "## Context", "## Acceptance criteria")
DERIVE_TICKET_ID_RE = re.compile(r"^\d+([-_].+)?$")


def derive_ticket_id(ticket_path: str) -> str | None:
    """Derive the Ticket-ID from the ticket filename; '-' (stdin) has no stable identity."""
    if ticket_path == "-":
        return None
    stem = Path(ticket_path).stem
    if stem.startswith("#"):
        return stem
    if DERIVE_TICKET_ID_RE.match(stem):
        return f"#{stem}"
    return stem


def find_unfilled_placeholders(ticket: str) -> list[str]:
    """Return sorted `{{...}}` tokens for the refusal diagnostic; never a rejection reason alone."""
    return sorted(set(PLACEHOLDER_RE.findall(ticket)))


def ticket_is_untouched_skeleton(ticket: str) -> bool:
    """Check whether every `--draft` semantic section is present and empty."""
    bodies: list[str] = []
    for section in DRAFT_SECTIONS:
        start = ticket.find(section)
        if start < 0:
            return False
        rest = ticket[start + len(section) :]
        end = len(rest)
        for marker in ("\n## ", "\n# "):
            at = rest.find(marker)
            if at >= 0:
                end = min(end, at)
        bodies.append(rest[:end].strip())
    return all(body == "" for body in bodies)


def validate_ticket(ticket: str) -> None:
    """Refuse tickets the model must still fill in; free-form tickets pass untouched."""
    if DRAFT_MARKER in ticket:
        placeholders = find_unfilled_placeholders(ticket)
        detail = f"; unfilled placeholders: {', '.join(placeholders[:5])}" if placeholders else ""
        raise UsageError(
            f"ticket still carries the draft marker ({DRAFT_MARKER}){detail}; "
            "fill the sections and delete the marker before dispatch"
        )
    if ticket_is_untouched_skeleton(ticket):
        raise UsageError(
            "ticket has empty Task/Context/Acceptance sections; fill it before dispatch"
        )


def render_draft_skeleton(herdr: str, targets: Sequence[str], env: Mapping[str, str]) -> str:
    """Render a ticket skeleton; routing comes from live state, sections stay empty for the model."""
    from herdr_prompt import resolve_caller, sender_ref, utc_stamp

    sender = resolve_caller(herdr, env)
    lines = [
        "# Ticket draft",
        "<!-- herdr-draft: unfilled — fill Task/Context/Acceptance, then delete this line. -->",
        "",
        "## Routing (prefilled by the script; the dispatch envelope stays authoritative)",
        "",
        f"- Sender: {sender_ref(sender)}",
        f"- Drafted: {utc_stamp()}",
    ]
    for target in targets:
        canonical, pane = resolve_target_identity(herdr, target, env)
        if pane and canonical != pane:
            ref = f"{canonical}@{pane}"
        elif pane:
            ref = pane
        else:
            ref = target
        lines.append(f"- Receiver: {ref}")
    lines.extend(
        [
            "",
            "## Task",
            "",
            "## Context",
            "",
            "## Acceptance criteria",
        ]
    )
    return "\n".join(lines)


def normalize_auto_start_kind(raw: str | None) -> str | None:
    """Lowercase and validate an --auto-start KIND against the known agent kinds."""
    if raw is None:
        return None
    kind = raw.strip().lower()
    if not kind or kind not in KNOWN_AGENT_KINDS:
        raise UsageError(
            f"--auto-start kind {raw!r} is not a recognized agent kind "
            f"(known: {', '.join(sorted(KNOWN_AGENT_KINDS))})"
        )
    return kind


def derive_bootstrap_role(target: str, options: Options) -> str:
    """Pick the ROLE INVARIANT role: explicit --role, else the unscoped target."""
    if options.role:
        return options.role
    role = target
    if options.task_group:
        prefix = f"{options.task_group}-"
        if role.startswith(prefix):
            role = role[len(prefix) :]
    return role


def validate_agent_name_or_raise(name: str) -> None:
    """Reject a bootstrap name Herdr would refuse, before any rename happens."""
    from herdr_cli import validate_agent_name

    validate_agent_name(name)


def run_bootstrap_contract(
    pane_id: str,
    name: str,
    *,
    kind: str,
    role: str,
    task_group: str | None,
    cwd: str | None,
    model: str | None,
    dry_run: bool,
    env: Mapping[str, str],
) -> str | None:
    """Start one missing callee through the herdr_bootstrap contract in-process.

    Returns the dry-run plan text when `dry_run` is set, else None. Runs the
    shared `bootstrap()` entrypoint (not a raw `agent start`) so trust flags,
    the ROLE INVARIANT surface, and the pane-cwd guarantee all apply.
    """
    import herdr_bootstrap

    validate_agent_name_or_raise(name)
    bootstrap_options = herdr_bootstrap.Options(
        name=name,
        kind=kind,
        pane=pane_id,
        role=role,
        task_group=task_group,
        model=model,
        cwd=cwd,
        dry_run=dry_run,
    )
    if dry_run:
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = herdr_bootstrap.bootstrap(bootstrap_options, env)
        if code != 0:
            raise UsageError(f"herdr-dispatch: bootstrap plan for {name!r} failed")
        return buffer.getvalue()
    code = herdr_bootstrap.bootstrap(bootstrap_options, env)
    if code != 0:
        raise UsageError(f"herdr-dispatch: bootstrap for {name!r} failed")
    return None


def bootstrap_one_shell_target(
    options: Options, info: object, *, kind: str, env: Mapping[str, str]
) -> tuple[str, str | None]:
    """Bootstrap one inspected shell pane; returns (start_name, dry_run_plan)."""
    from herdr_cli import ShellPaneInfo

    assert isinstance(info, ShellPaneInfo)
    start_name = (
        info.suggested_name
        if info.suggested_name != "<name>"
        else f"agent-{info.pane_id.replace(':', '-')}"
    )
    role = derive_bootstrap_role(start_name, options)
    plan = run_bootstrap_contract(
        info.pane_id,
        start_name,
        kind=kind,
        role=role,
        task_group=options.task_group,
        cwd=options.cwd,
        model=options.model,
        dry_run=options.dry_run,
        env=env,
    )
    return start_name, plan


def candidate_targets(options: Options) -> list[str]:
    """Raw dispatch candidates before resolution: the --label or the TARGETs."""
    if options.label:
        return [options.label]
    return list(options.targets)


def is_bare_shell_failure(exc: UsageError) -> bool:
    """True when resolve_targets refused a bare shell pane (the bootstrap hook).

    The exception TYPE is the contract (herdr_cli.BareShellRefusal). The
    substring test is a documented migration fallback only: it covers
    BareShellRefusal subclasses or older call sites that still raise a plain
    UsageError with the diagnostic prose. Do not add another string-match.
    """
    from herdr_cli import BareShellRefusal

    if isinstance(exc, BareShellRefusal):
        return True
    message = str(exc)
    return "no live agent is running" in message or "has no live agent" in message


def rewrite_targets_for_bootstrap(options: Options, names: list[str]) -> None:
    """Point dispatch at the bootstrapped names; a label becomes its agent name."""
    if options.label:
        options.label = None
    options.targets = names


def try_bootstrap_on_resolve_failure(
    options: Options, herdr: str, env: Mapping[str, str], kind: str, exc: UsageError
) -> tuple[list[str], list[str]] | None:
    """Bootstrap the bare-shell callees behind a resolve_targets UsageError.

    Returns (targets, plans) after one retry, or None when the failure is not
    a bare shell (caller keeps the original error). Bootstraps each candidate
    the inventory still reports as a shell pane, rewrites the targets to the
    started names, and resolves once more.
    """
    from herdr_prompt import resolve_targets

    if not is_bare_shell_failure(exc):
        return None
    # Two-phase inspect (zero mutation): every candidate must still read as a
    # bare shell before any pane is touched. A non-shell candidate returns None
    # here, before a single rename or start.
    infos = [
        inspect_target_shell_pane(herdr, candidate, env) for candidate in candidate_targets(options)
    ]
    if any(info is None for info in infos):
        return None
    # Mutate phase with compensation: a later bootstrap (or the re-resolve)
    # can still fail (cwd convergence, agent start, bad derived name). Track
    # every started name; on any failure re-raise an error that NAMES the
    # started-but-undispatched agents so the caller can clean up. A silent
    # orphan is the defect; a loud one is the fallback.
    names: list[str] = []
    plans: list[str] = []
    try:
        for info in infos:
            assert info is not None
            start_name, plan = bootstrap_one_shell_target(options, info, kind=kind, env=env)
            names.append(start_name)
            if plan is not None:
                plans.append(plan)
        rewrite_targets_for_bootstrap(options, names)
        targets = resolve_targets(options, herdr, env)
    except Exception as failed:
        if names and not isinstance(failed, _NamedOrphansError):
            raise _NamedOrphansError(names, failed) from failed
        raise
    return targets, plans


class _NamedOrphansError(UsageError):
    """A mid-bootstrap failure that names the started-but-undispatched agents."""

    started: list[str]

    def __init__(self, started: list[str], cause: Exception) -> None:
        self.started = list(started)
        super().__init__(
            "herdr-dispatch: auto-start bootstrapped "
            f"{', '.join(self.started)} but dispatch did not complete ({cause}); "
            f"these agents hold no ticket — release or reuse them explicitly: "
            + ", ".join(f"herdr agent prompt {name}" for name in self.started)
        )


def dry_run_bootstrap_plans(
    options: Options, herdr: str, targets: list[str], kind: str | None, env: Mapping[str, str]
) -> list[str]:
    """Collect would-bootstrap plans under --dry-run without mutating anything."""
    if kind is None or not options.dry_run or options.draft:
        return []
    plans: list[str] = []
    for target in targets:
        info = inspect_target_shell_pane(herdr, target, env)
        if info is None:
            continue
        _, plan = bootstrap_one_shell_target(options, info, kind=kind, env=env)
        if plan is not None:
            plans.append(plan)
    return plans


def dispatch_agents(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    herdr = find_herdr(env)
    kind = normalize_auto_start_kind(options.auto_start)
    try:
        targets = resolve_targets(options, herdr, env)
    except UsageError as exc:
        if kind is None or options.draft:
            raise
        bootstrapped = try_bootstrap_on_resolve_failure(options, herdr, env, kind, exc)
        if bootstrapped is None:
            raise
        targets, bootstrap_plans = bootstrapped
    else:
        bootstrap_plans = dry_run_bootstrap_plans(options, herdr, targets, kind, env)

    if options.dry_run and bootstrap_plans:
        for plan in bootstrap_plans:
            print(plan)

    if options.draft:
        skeleton = render_draft_skeleton(herdr, targets, env)
        if options.file and options.file != "-":
            _ = Path(options.file).write_text(skeleton + "\n", encoding="utf-8")
            print(f"herdr-dispatch: draft written to {options.file}", file=sys.stderr)
        else:
            print(skeleton)
        return EXIT_OK
    ticket_path = options.file
    if ticket_path is None:
        raise UsageError("pass --file PATH to dispatch a ticket")
    if ticket_path != "-":
        try:
            ticket = Path(ticket_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise UsageError(
                f"cannot read ticket file {ticket_path}: {exc.strerror or exc}"
            ) from exc
        validate_ticket(ticket)

    ticket_id = options.ticket_id or derive_ticket_id(ticket_path)
    task_id = options.task_id or ticket_id
    options.ticket_id = ticket_id
    options.task_id = task_id

    if not options.force and not options.dry_run:
        for target in targets:
            canonical, pane = resolve_target_identity(herdr, target, env)
            lease = get_lease(canonical, env=env) or (get_lease(pane, env=env) if pane else None)
            if lease:
                if lease_pane_is_gone(lease, herdr, env):
                    print(
                        f"herdr-dispatch: releasing the stale lease for {target} "
                        f"(pane {lease.get('pane_id')} no longer exists)",
                        file=sys.stderr,
                    )
                    _ = release_lease(canonical, env=env)
                    continue
                raise UsageError(
                    f"target {target} has an active ticket lease ({lease['ticket']}) issued by {lease['caller']}. Await reply or pass --force"
                )

    caller_name = "caller"
    caller_recovery: dict[str, str] | None = None
    if not options.dry_run:
        try:
            caller_ctx = resolve_caller(herdr, env)
            caller_name = caller_ctx.agent or caller_ctx.label or caller_ctx.pane_id
            subset = {
                "pane_id": caller_ctx.pane_id,
                "kind": caller_ctx.kind,
                "session_path": caller_ctx.session_id,
                "resume_cmd": caller_ctx.resume_cmd,
                "cwd": caller_ctx.cwd,
            }
            filtered = {key: value for key, value in subset.items() if value}
            caller_recovery = filtered or None
        except Exception:
            caller_recovery = None

    acquired_targets: list[str] = []
    if not options.dry_run:
        for target in targets:
            canonical, pane = resolve_target_identity(herdr, target, env)
            _ = acquire_lease(
                canonical,
                ticket_path,
                caller_name,
                pane_id=pane,
                env=env,
                ticket_id=ticket_id,
                task_id=task_id,
                caller_recovery=caller_recovery,
            )
            acquired_targets.append(canonical)

    try:
        code = prompt_agents(options, env)
    except BaseException as exc:
        # A WaitTimeout means the prompt was accepted and only the wait expired, so the lease
        # stays until the reply callback resolves it. Any other exit releases this call's claims.
        if not options.dry_run and not isinstance(exc, WaitTimeout):
            for acq in acquired_targets:
                _ = release_lease(acq, env=env)
        raise

    if code != EXIT_OK and not options.dry_run:
        for acq in acquired_targets:
            _ = release_lease(acq, env=env)

    return code


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    try:
        return guard("herdr-dispatch", lambda: dispatch_agents(options, env_map))
    except WaitTimeout as exc:
        print(f"herdr-dispatch: {exc}", file=sys.stderr)
        return EXIT_WAIT_TIMEOUT


if __name__ == "__main__":
    raise SystemExit(main())
