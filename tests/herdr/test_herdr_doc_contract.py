"""Doc-contract tests for the herdr skill: documented values vs the code, and pointer resolution.

Two contracts live here, and both read the *documentation* as the input under test:

1. **Documented values.** Every window and exit code asserted in these docs is parsed *out of the
   doc text* and compared against the code constant (imported, never re-stated as a literal), so
   the code stays the single implementation and the prose cannot drift from behaviour.
2. **Documented pointers.** Every inline-code token in `skills/herdr/**/*.md` that looks like a
   file pointer must resolve to a file that exists. `EXCLUDED_TOKENS` is an **exact** allow-list
   (no globs) naming the prose illustrations that are deliberately not pointers here, so a new
   dead pointer fails loudly instead of hiding behind a pattern.
"""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import herdr_cli
import herdr_pane
import herdr_prompt
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

REPO_ROOT = SCRIPTS_DIR.parents[2]
SKILL_DIR = SCRIPTS_DIR.parent
BOOTSTRAP_DOC = SKILL_DIR / "references" / "agent-bootstrap.md"
COORDINATION_DOC = SKILL_DIR / "references" / "lane-coordination.md"
OVERVIEW_DOC = SKILL_DIR / "SKILL.md"

# A pointer is an inline-code token that names one of the file kinds these docs cite.
POINTER_EXTENSIONS = (".md", ".py", ".yaml", ".sh", ".json")

# A pane whose agent record is `idle` at revision 0 and carries no session path: the
# weak-recognition case cli-reference.md describes, where the state feed proves nothing.
FRESH_PANE_STATE: Mapping[str, object] = {
    **DEFAULT_STATE,
    "agent_get": {"reviewer": {"agent_status": "idle", "revision": "0"}},
    "agent_read_text": "pi 0.9.0 ready\n> ",
}

# Exact allow-list: tokens that name something other than a file in *this* repository. Each entry
# is a single token (never a pattern) so any new unresolved token fails the test below.
EXCLUDED_TOKENS: Mapping[str, str] = {
    # Prose illustrations: a specimen ticket's cited file tree, not this repository's.
    "src/cli/args.py": "illustration: a specimen ticket's CLI path",
    "src/config/loader.py": "illustration: a specimen ticket's config-loader path",
    "tests/test_loader.py": "illustration: a specimen ticket's test path",
    # Prose illustrations: payload and ticket filenames a caller supplies at run time.
    "182-foo.md": "illustration: a ticket basename, used to show Ticket-ID derivation",
    "rework.md": "illustration: the filename a rework ticket is written to",
    "brief.md": "illustration: a payload filename passed to --file",
    # Agent-kind configuration paths that live in the *target* project or the user's home.
    ".agents/hooks.json": "target-project hook config the agy bridge installs, not a repo file",
    "settings.json": "a qodercli config-root file outside this repository",
    ".aider.chat.history.md": "aider's session-history file in the user's working directory",
    "hooks/herdr-agy-bridge.sh": "file the agy bridge deploys into a target project's hooks dir",
}

# ── pointer policy ────────────────────────────────────────────────────────────────────────────


def _pointer_tokens(doc: Path) -> list[tuple[str, int]]:
    """Return (token, line_number) for every inline-code token in `doc` that names a file."""
    found: list[tuple[str, int]] = []
    for line_no, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
        for span in re.findall(r"`([^`\n]+)`", line):
            for word in re.findall(r"[^\s`(),;]+", span):
                token = word.strip(":'\"")
                if token.endswith(POINTER_EXTENSIONS):
                    found.append((token, line_no))
    return found


def _exclusion_rule(token: str) -> str | None:
    """Return the rule that excludes `token` by shape, or None when it must resolve."""
    # A URL points outside the repository by construction.
    if token.startswith(("http://", "https://")):
        return "url"
    # `.lane/tasks.yaml`, `.lane/replies.yaml`, and `.lane/replies/...` are created at run time.
    if token.startswith(".lane/"):
        return "store"
    # `agents/<agent>.md` and `<reply.md` name a shape filled in at run time, not a file.
    if "<" in token or ">" in token:
        return "placeholder"
    # `~/.gemini/config/hooks.json` lives in the user's home, not in this repository.
    if token.startswith("~"):
        return "home"
    return None


def _resolution_roots(doc: Path) -> tuple[Path, ...]:
    """Where a relative token may resolve, in the order the docs' own conventions imply.

    The citing file's directory covers sibling references; the skill directory covers
    `references/...`; the repository root covers repo-relative paths; `skills/` covers the
    cross-skill form the coordination reference uses (e.g.
    `dynamic-workflow-wrapper/references/resp-format.md`).
    """
    return (doc.parent, SKILL_DIR, REPO_ROOT, REPO_ROOT / "skills")


def _resolve(doc: Path, token: str) -> Path | None:
    """Resolve one pointer token against the policy; None when nothing exists at any candidate."""
    env_prefix = "$SKILL_DIR/"
    if token.startswith(env_prefix):
        candidate = SKILL_DIR / token[len(env_prefix) :]
        return candidate if candidate.exists() else None
    if "/" in token:
        for root in _resolution_roots(doc):
            candidate = root / token
            if candidate.exists():
                return candidate
        return None
    # Bare basenames are the docs' convention for helper scripts (`herdr_reply.py`); the citing
    # directory, the skill directory, and the repository root cover any other bare citation.
    for root in (SCRIPTS_DIR, doc.parent, SKILL_DIR, REPO_ROOT):
        candidate = root / token
        if candidate.exists():
            return candidate
    return None


@dataclass(frozen=True)
class PointerReport:
    """One full scan of the skill docs: what resolved and where each skip came from."""

    resolved: tuple[tuple[Path, str, int], ...]
    unresolved: Mapping[str, tuple[str, ...]]
    excluded: Mapping[str, int]

    @property
    def resolved_tokens(self) -> frozenset[str]:
        return frozenset(token for _, token, _ in self.resolved)


def scan_pointers(docs: Sequence[Path]) -> PointerReport:
    """Scan every doc: resolve each pointer, or record the exclusion rule / unresolved target."""
    resolved: list[tuple[Path, str, int]] = []
    unresolved: dict[str, list[str]] = {}
    excluded: dict[str, int] = {}
    for doc in docs:
        for token, line_no in _pointer_tokens(doc):
            rule = _exclusion_rule(token)
            if rule is not None:
                excluded[rule] = excluded.get(rule, 0) + 1
                continue
            if token in EXCLUDED_TOKENS:
                excluded["illustration"] = excluded.get("illustration", 0) + 1
                continue
            if _resolve(doc, token) is not None:
                resolved.append((doc, token, line_no))
                continue
            unresolved.setdefault(token, []).append(f"{doc.relative_to(REPO_ROOT)}:{line_no}")
    return PointerReport(
        resolved=tuple(resolved),
        unresolved={token: tuple(where) for token, where in unresolved.items()},
        excluded=dict(excluded),
    )


@pytest.fixture(scope="module")
def report() -> PointerReport:
    """Pointer scan over the skill's docs (read-only, so one scan serves the whole module)."""
    return scan_pointers(sorted(SKILL_DIR.glob("**/*.md")))


# ── pointer contract ──────────────────────────────────────────────────────────────────────────


def test_every_documented_pointer_resolves(report: PointerReport) -> None:
    """A pointer outside the exact allow-list must name a file that exists in this repository."""
    dead = {
        token: where for token, where in report.unresolved.items() if token not in EXCLUDED_TOKENS
    }
    assert dead == {}, "unresolved documentation pointers: " + "; ".join(
        f"{token} ({', '.join(where)})" for token, where in dead.items()
    )


def test_resolved_pointer_count_stays_above_the_floor(report: PointerReport) -> None:
    """Guard against a vacuous pass: the docs cite 136 pointers over 34 distinct targets."""
    assert len(report.resolved) >= 130, "resolved pointers dropped below the observed floor"
    assert len(report.resolved_tokens) >= 30, "distinct resolved pointers dropped below the floor"


def test_allow_list_holds_only_exact_file_tokens() -> None:
    """No globs and no bare directories in the allow-list: a pattern would hide dead pointers."""
    for token in EXCLUDED_TOKENS:
        assert token.endswith(POINTER_EXTENSIONS), token
        assert not set(token) & set("*?[]"), token
        assert Path(token).suffix, token


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("https://example.com/doc.md", "url"),
        ("http://example.com/doc.md", "url"),
        ("agents/<agent>.md", "placeholder"),
        ("<reply.md", "placeholder"),
        ("~/.qoder/hooks/herdr-agent-state.sh", "home"),
        (".lane/replies/<id>.yaml", "store"),
        (".lane/lease.yaml", "store"),
        (".lane/tasks.yaml", "store"),
        ("herdr_reply.py", None),
    ],
)
def test_pointer_policy_classifies_tokens(token: str, expected: str | None) -> None:
    """The exclusion rules stay narrow: each shape is classified, everything else must resolve."""
    assert _exclusion_rule(token) == expected


def test_skill_overview_qualifies_the_reply_template_pointer() -> None:
    """The overview cites the final-reply template by path, not as a bare basename."""
    template = "resp-format.md"
    guarded = [
        line
        for line in OVERVIEW_DOC.read_text(encoding="utf-8").splitlines()
        if "Final Reply Template" in line
    ]
    assert guarded, "the overview names no Final Reply Template"
    for line in guarded:
        pointers = [span for span in re.findall(r"`([^`\n]+)`", line) if span.endswith(template)]
        assert pointers, f"no reply-template pointer on: {line.strip()}"
        for pointer in pointers:
            assert "/" in pointer, f"the template pointer is unqualified: {pointer}"
            assert pointer.endswith("dynamic-workflow-wrapper/references/" + template), pointer
            assert _resolve(OVERVIEW_DOC, pointer) is not None, f"{pointer} does not exist"


# ── divergence 1: the handshake window and the unconfirmed-acceptance exit code ───────────────


def _handshake_bullet() -> str:
    """The Pre-Flight Readiness Gate bullet, located by content (line numbers drift)."""
    return next(
        line
        for line in COORDINATION_DOC.read_text(encoding="utf-8").splitlines()
        if "Pre-Flight Readiness Gate" in line
    )


def test_documented_handshake_window_matches_the_code() -> None:
    """The coordination reference renders the code's own handshake window and interval."""
    bullet = _handshake_bullet()
    match = re.search(r"handshake up to ([0-9.]+)s \(([0-9.]+)ms intervals\)", bullet)
    assert match is not None, f"no handshake window stated in: {bullet}"
    window, interval_ms = match.group(1), match.group(2)
    assert float(window) == herdr_prompt.HANDSHAKE_TIMEOUT_SECONDS
    # The code renders the window through `_format_seconds`; the doc must render it the same way.
    assert window == herdr_prompt._format_seconds(herdr_prompt.HANDSHAKE_TIMEOUT_SECONDS)
    assert float(interval_ms) == herdr_prompt.HANDSHAKE_INTERVAL_SECONDS * 1000


def test_documented_unconfirmed_acceptance_exit_code_matches_the_code(
    stub_factory: Callable[[Path], StubHarness],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unconfirmed `--no-wait` handshake warns and still exits 0, as the doc states."""
    bullet = _handshake_bullet()
    match = re.search(r"still exits (\d+)", bullet)
    assert match is not None, f"no unconfirmed-acceptance exit code stated in: {bullet}"
    documented = int(match.group(1))
    assert documented == herdr_prompt.EXIT_OK

    # Observe the failure path itself: the agent stays idle and its revision never moves, so the
    # handshake cannot confirm acceptance.
    slept: list[float] = []
    monkeypatch.setattr(herdr_prompt, "_sleep", slept.append)
    payload = tmp_path / "brief.md"
    _ = payload.write_text("hi")
    stub = stub_factory(SCRIPTS_DIR / "herdr_prompt.py")
    stub.write_state(
        {
            **DEFAULT_STATE,
            "agent_get_seq": {"reviewer": ["idle"]},
            "agent_get_rev_seq": {"reviewer": ["r1"] * 40},
        }
    )
    code = herdr_prompt.main(["reviewer", "--file", str(payload), "--no-wait"], env=stub.base_env())
    assert code == documented, capsys.readouterr().err
    assert "acceptance was not confirmed" in capsys.readouterr().err
    assert len(stub.prompts()) == 1


# ── divergence 2 / 3: the bootstrap reference's own commands ──────────────────────────────────


def _numbered_step(text: str, title: str) -> str:
    """Return the body of the numbered step whose bold title is `title`, located by content."""
    pattern = re.compile(
        rf"^\d+\. \*\*{re.escape(title)}\*\*:(.*?)(?=^\d+\. \*\*|^---|\Z)", re.M | re.S
    )
    match = pattern.search(text)
    assert match is not None, f"no numbered step titled {title!r}"
    return match.group(1)


def _fenced_command(block: str) -> str:
    """Return the one shell command inside the step's fenced example (comments dropped)."""
    fences = re.findall(r"```(?:bash|sh)\n(.*?)```", block, re.S)
    assert len(fences) == 1, f"expected exactly one shell sample, found {len(fences)}"
    commands = [
        line.strip()
        for line in fences[0].splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert len(commands) == 1, f"expected exactly one command, found {len(commands)}: {commands}"
    return commands[0]


def _step_command(title: str) -> list[str]:
    """Split the step's documented command into argv, substituting its shell placeholders."""
    step = _numbered_step(BOOTSTRAP_DOC.read_text(encoding="utf-8"), title)
    tokens = shlex.split(_fenced_command(step))
    if tokens[:2] == ["uv", "run"]:
        tokens = tokens[2:]
    # Values for the step's own shell placeholders (`$WORKTREE_PATH` is Step 0's variable).
    substitutions = {
        "<name>": "reviewer",
        "<role>": "reviewer",
        "$WORKTREE_PATH": "/tmp/herdr-lane-worktree",
    }
    resolved: list[str] = []
    for token in tokens:
        if token in substitutions:
            resolved.append(substitutions[token])
            continue
        if token.startswith("$SKILL_DIR/"):
            token = str(SKILL_DIR / token[len("$SKILL_DIR/") :])
        resolved.append(token)
    return resolved


def _documented_exit_code(step: str, subject: str) -> int | None:
    """Parse `<subject> exits N` out of the step text; None when the step states no such code."""
    match = re.search(rf"{re.escape(subject)} exits (\d+)", step)
    return int(match.group(1)) if match is not None else None


def _run_documented(
    argv: Sequence[str],
    *,
    harness: StubHarness,
    make_harness: Callable[[Path], StubHarness],
    state: Mapping[str, object],
) -> tuple[subprocess.CompletedProcess[str], StubHarness]:
    """Run one documented argv through the stub harness against `state`.

    A documented helper script runs in-process bound to that script; a documented bare `herdr`
    command runs against the harness's stub binary, resolved on the harness PATH.
    """
    program = Path(argv[0])
    helper = SCRIPTS_DIR / program.name
    if program.name.endswith(".py") and helper.exists():
        bound = make_harness(helper)
        return bound.run(*argv[1:], state=state), bound
    harness.write_state(state)
    stub_herdr = shutil.which(argv[0], path=harness.base_env()["PATH"])
    assert stub_herdr is not None, f"the stub harness does not provide {argv[0]!r}"
    completed = subprocess.run(
        [stub_herdr, *argv[1:]], env=harness.base_env(), capture_output=True, text=True, check=False
    )
    return completed, harness


@pytest.fixture
def harness(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    """Harness bound to the wait helper; its PATH, log, and state file serve every run here."""
    return stub_factory(SCRIPTS_DIR / "herdr_wait.py")


def test_documented_settle_command_succeeds_on_a_fresh_pane(
    harness: StubHarness, stub_factory: Callable[[Path], StubHarness]
) -> None:
    """The documented startup settle path must exit with the success code, not the refusal."""
    argv = _step_command("State Settling")
    completed, bound = _run_documented(
        argv, harness=harness, make_harness=stub_factory, state=FRESH_PANE_STATE
    )
    step = _numbered_step(BOOTSTRAP_DOC.read_text(encoding="utf-8"), "State Settling")
    documented = _documented_exit_code(step, "pane read")
    assert documented == completed.returncode, (
        f"documented success code {documented!r} != observed exit {completed.returncode} "
        f"for {argv}: {completed.stderr}"
    )
    assert documented == herdr_cli.EXIT_OK
    # The documented command itself reached the stub: argv[0] is the documented program name,
    # and the stub logs the path it was resolved to on the harness PATH.
    assert any(call[1:] == list(argv[1:]) for call in bound.calls()), bound.calls()


def test_documented_wait_refusal_code_matches_the_helper(harness: StubHarness) -> None:
    """A wanted state at revision 0 is unsatisfiable: the wait helper exits 2, as step 5 states."""
    completed = harness.run("reviewer", state=FRESH_PANE_STATE)
    assert "unsatisfiable wait" in completed.stderr
    step = _numbered_step(BOOTSTRAP_DOC.read_text(encoding="utf-8"), "State Settling")
    documented = _documented_exit_code(step, "wait helper")
    assert documented == completed.returncode, (
        f"documented refusal code {documented!r} != observed exit {completed.returncode}: "
        f"{completed.stderr}"
    )
    assert documented == herdr_cli.EXIT_USAGE


def test_documented_pane_invocation_parses_with_the_real_parser() -> None:
    """Step 2's split command must parse: direction positional, every `--flag` accepted."""
    argv = _step_command("Pane Allocation")
    assert argv[0].endswith("herdr_pane.py"), argv
    assert Path(argv[0]).exists(), argv[0]
    parser = herdr_pane.build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    for token in argv:
        if token.startswith("-"):
            assert token in option_strings, f"the pane helper does not accept {token!r}"
    options = parser.parse_args(argv[1:], namespace=herdr_pane.Options())
    # The direction is the bare positional token, never the value of a flag.
    assert argv[1] == options.direction
    assert herdr_pane.normalize_direction(options.direction or "") == "right"
    assert options.label == "reviewer"
    assert options.cwd == "/tmp/herdr-lane-worktree"
    assert options.no_focus is True


def test_direction_flag_form_is_refused_by_the_parser() -> None:
    """The pre-fix `--direction right` form stays invalid: the flag is not an option here."""
    argv = ["--direction", "right", "--label", "reviewer", "--cwd", "/tmp/wt", "--no-focus"]
    with pytest.raises(SystemExit) as excinfo:
        _ = herdr_pane.build_parser().parse_args(argv)
    assert excinfo.value.code == herdr_cli.EXIT_USAGE
