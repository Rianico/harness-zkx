"""Mechanical pin for the `uv run` invariant on documented harness-script commands (#182 h4).

The lane rule: every documented **harness-script** invocation is written `uv run …`; every
documented **herdr CLI** invocation is NOT. This module scans the surfaces and asserts that
distinction. The matcher is keyed on the script file name (`herdr_[a-z_]+\\.py`), never on the
word `herdr`, so the CLI family (`herdr pane read …`, `herdr agent send-keys …`) is never swept
into the script rule and vice versa — an "everything starts with `uv run`" rule would fire on
every documented CLI call and get disabled inside a week.

What counts as an invocation (the pinned distinction):

1. **Argument-shaped use.** A `herdr_[a-z_]+\\.py` occurrence is an invocation only when the next
   token after it (modulo spaces) opens a `<placeholder>`, a `--flag`, a quote, an expansion `$`,
   or a word — i.e. the name is *used as a command*, not merely named. `herdr_reply.py` followed
   by a closing backtick or by `─` (a diagram arrow) names the script; it does not invoke it.
2. **Command statement only.** A candidate is examined when it sits in a command statement:
   (a) a line inside a fenced code block — except that a ```` ```mermaid ```` fence is a diagram,
   its `A->>B: herdr_reply.py …` messages are labels no agent copy-pastes, so they are excluded
   by fence language, by rule and not by a filename list; (b) a backtick span that is the whole
   trimmed line or the whole markdown table cell (the helper table's house form); or (c) a
   rendered agent-facing string, whose every line is what a callee actually reads.
   Prose that merely names a script — an inline backtick span inside a sentence, even with
   placeholders like `herdr_dispatch.py <callee> --file <ticket>` — is a mention, not a command
   statement, and is excluded by rule (b): the span is not the whole statement.
3. **`uv run` placement.** An examined invocation must have `uv run` somewhere before the script
   token on the same line (this tolerates `printf … | uv run …` and `$(uv run …)`). A documented
   CLI occurrence must NOT have `uv run` glued directly in front of it (`uv run herdr agent …`).

Surfaces: the five markdown docs (`skills/herdr/SKILL.md`, `references/lane-coordination.md`,
`references/agent-bootstrap.md`, every `references/agents/*.md`, `GLOSSARY.md`) plus the RENDERED
Python text — `herdr_envelope.SKILL_NOTICE`, `herdr_envelope.render_reply_contract` called with a
real `CallerContext` and ticket id, `herdr_bootstrap.INVARIANT_RULES` formatted with the real
helper path, `herdr_reply.format_reply_recovery_diagnostic` (the JIT recovery block), and each
script's argparse `epilog` taken from `build_parser()` — never grepped from the source literal.

Measured at authoring (after the single omission fix): 106 harness-script invocations across the
docs (95 in fenced blocks, 11 in whole-cell spans of the SKILL.md helper table) and 3 more in the
rendered strings — 109 examined total, every one `uv run`-prefixed. 80 herdr CLI occurrences;
every skill doc contains at least one. GLOSSARY.md contains zero commands of either family (its
`herdr` hits are ticket-id prose), so the per-doc CLI floor binds the twelve skill docs and
GLOSSARY.md is pinned to contribute nothing but is still scanned. A scanner that matched nothing
would pass the per-invocation loop vacuously, hence the floors below.
"""

from __future__ import annotations

import importlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import herdr_bootstrap
import herdr_envelope
import herdr_reply
import pytest

from tests.herdr.stub import SCRIPTS_DIR

REPO_ROOT = SCRIPTS_DIR.parents[2]
SKILL_DIR = SCRIPTS_DIR.parent
GLOSSARY_DOC = REPO_ROOT / "GLOSSARY.md"

# Every scanned markdown surface, in the order the ticket names them.
DOC_SURFACES: tuple[Path, ...] = (
    SKILL_DIR / "SKILL.md",
    SKILL_DIR / "references" / "lane-coordination.md",
    SKILL_DIR / "references" / "agent-bootstrap.md",
    *sorted((SKILL_DIR / "references" / "agents").glob("*.md")),
    GLOSSARY_DOC,
)

# The script family, keyed on the file name, never on the bare word `herdr`.
SCRIPT_NAME = re.compile(r"herdr_[a-z_]+\.py")
# The CLI family: `herdr <group> <subcommand>` with a real subcommand word.
CLI_INVOCATION = re.compile(r"\bherdr\s+(?:pane|agent|workspace|tab|worktree)\s+[a-z][a-z_-]+\b")
# The forbidden shape for the CLI family: `uv run` glued directly in front of a CLI call.
UV_RUN_ON_CLI = re.compile(r"\buv\s+run\s+herdr\s+(?:pane|agent|workspace|tab|worktree)\b")

# Floors chosen from the measured counts above with room to spare; a scanner that matches
# nothing fails here even though its per-invocation loop would pass vacuously.
INVOCATION_FLOOR = 99
RENDERED_INVOCATION_FLOOR = 3
CLI_OCCURRENCE_FLOOR = 60

# Scripts whose agent-facing `--help` epilog is scanned (every module exposing build_parser()).
EPILOG_MODULES: tuple[str, ...] = (
    "herdr_agy_bridge",
    "herdr_bootstrap",
    "herdr_dispatch",
    "herdr_label",
    "herdr_lease",
    "herdr_overview",
    "herdr_pane",
    "herdr_prompt",
    "herdr_reply",
    "herdr_transcript",
    "herdr_wait",
    "herdr_worktree",
)

_WHOLE_LINE_SPAN = re.compile(r"[-*>+\s]*`[^`]+`")
_FENCE_LINE = re.compile(r"```(\S*)")


def _is_argument_shaped(text: str, at: int) -> bool:
    """Whether the token starting at `at` (after an optional space run) opens an argument.

    `<placeholder>`, `--flag`, a quote, an expansion `$`, or a word: the shapes a copy-paste
    command shows after the script name. A closing backtick, punctuation, or end of text does not.
    """
    j = at
    while j < len(text) and text[j] == " ":
        j += 1
    if j >= len(text):
        return False
    c = text[j]
    return c in "<-\"'$" or c.isalnum()


@dataclass(frozen=True)
class Found:
    """One harness-script invocation the scanner examined, and whether it was `uv run`-prefixed."""

    where: str
    line_no: int
    text: str
    uv_run_before: bool


@dataclass(frozen=True)
class InvariantReport:
    """One full scan: examined invocations, CLI occurrences, and the two kinds of violations."""

    invocations: tuple[Found, ...]
    rendered_invocations: int
    cli_by_surface: dict[str, int]
    script_violations: tuple[str, ...]
    cli_violations: tuple[str, ...]

    @property
    def total_cli(self) -> int:
        return sum(self.cli_by_surface.values())


def _scan_text(
    where: str, lines: list[str], *, statement_of: Callable[[int], bool]
) -> tuple[list[Found], int, list[str]]:
    """Shared core: examine one surface's lines; return invocations, CLI count, violations.

    `statement_of(idx)` decides command-statement membership for the script family; the
    CLI family is counted and prefix-checked on every line (a `uv run herdr …` prefix is wrong
    in prose too), so the distinction pin is never vacuous.
    """
    found: list[Found] = []
    cli_count = 0
    cli_bad: list[str] = []
    for idx, line in enumerate(lines):
        cli_count += len(CLI_INVOCATION.findall(line))
        if UV_RUN_ON_CLI.search(line):
            cli_bad.append(f"{where}:{idx + 1}: herdr CLI glued to 'uv run': {line.strip()[:120]}")
        if not statement_of(idx):
            continue
        for m in SCRIPT_NAME.finditer(line):
            if not _is_argument_shaped(line, m.end()):
                continue
            found.append(
                Found(
                    where=where,
                    line_no=idx + 1,
                    text=line.strip(),
                    uv_run_before="uv run" in line[: m.start()],
                )
            )
    return found, cli_count, cli_bad


def _scan_doc(path: Path) -> tuple[list[Found], int, list[str]]:
    """Scan one markdown surface with fence tracking; ```mermaid fences are diagram labels."""
    lines = path.read_text(encoding="utf-8").splitlines()
    in_fence = False
    fence_lang = ""
    statement: list[bool] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                match = _FENCE_LINE.match(stripped)
                fence_lang = match.group(1) if match else ""
            else:
                in_fence = False
                fence_lang = ""
            statement.append(False)
            continue
        in_command_fence = in_fence and fence_lang != "mermaid"
        whole_span = bool(_WHOLE_LINE_SPAN.fullmatch(stripped))
        in_cell = "|" in line and any(
            _WHOLE_LINE_SPAN.fullmatch(cell.strip()) for cell in line.split("|") if cell.strip()
        )
        statement.append(in_command_fence or whole_span or in_cell)
    where = str(path.relative_to(REPO_ROOT))
    return _scan_text(where, lines, statement_of=lambda idx: statement[idx])


def rendered_surfaces() -> tuple[tuple[str, str], ...]:
    """The agent-facing Python text, RENDERED by calling the real code — never grepped source."""
    sender = herdr_envelope.CallerContext(pane_id="w1:p1", label="impl-1", agent="impl-1")
    surfaces: list[tuple[str, str]] = [
        ("rendered:herdr_envelope.SKILL_NOTICE", herdr_envelope.SKILL_NOTICE),
        (
            "rendered:herdr_envelope.render_reply_contract",
            herdr_envelope.render_reply_contract(sender, "#182-a2a-hardening#h4"),
        ),
        (
            "rendered:herdr_bootstrap.INVARIANT_RULES",
            herdr_bootstrap.INVARIANT_RULES.format(helper=herdr_bootstrap.REPLY_HELPER),
        ),
        (
            "rendered:herdr_reply.recovery_block",
            herdr_reply.format_reply_recovery_diagnostic(
                "orchestrator",
                {"pane_id": "w1:p9", "kind": "pi", "resume_cmd": "pi --resume /tmp/s.jsonl"},
                "reply.md",
            ),
        ),
    ]
    for name in EPILOG_MODULES:
        parser = importlib.import_module(name).build_parser()
        epilog = parser.epilog
        if callable(epilog):
            epilog = epilog(parser.formatter)
        if isinstance(epilog, str):
            surfaces.append((f"rendered:{name}.epilog", epilog))
    return tuple(surfaces)


def _scan_rendered(name: str, text: str) -> tuple[list[Found], int, list[str]]:
    """A rendered string is what the callee reads verbatim: every line is a command statement."""
    return _scan_text(name, text.splitlines(), statement_of=lambda idx: True)


def scan_invariant() -> InvariantReport:
    """One full scan of every surface: docs first, then the rendered agent-facing text."""
    invocations: list[Found] = []
    rendered_count = 0
    cli_by_surface: dict[str, int] = {}
    violations: list[str] = []
    cli_bad: list[str] = []
    for path in DOC_SURFACES:
        found, cli, bad = _scan_doc(path)
        invocations.extend(found)
        cli_by_surface[str(path.relative_to(REPO_ROOT))] = cli
        for f in found:
            if not f.uv_run_before:
                violations.append(f"{f.where}:{f.line_no}: {f.text[:120]}")
        cli_bad.extend(bad)
    for name, text in rendered_surfaces():
        found, cli, bad = _scan_rendered(name, text)
        invocations.extend(found)
        rendered_count += len(found)
        cli_by_surface[name] = cli
        for f in found:
            if not f.uv_run_before:
                violations.append(f"{f.where}:{f.line_no}: {f.text[:120]}")
        cli_bad.extend(bad)
    return InvariantReport(
        invocations=tuple(invocations),
        rendered_invocations=rendered_count,
        cli_by_surface=cli_by_surface,
        script_violations=tuple(violations),
        cli_violations=tuple(cli_bad),
    )


@pytest.fixture(scope="module")
def report() -> InvariantReport:
    """Scan once per module: the surfaces are read-only files and pure renders."""
    return scan_invariant()


# ── the script pin ─────────────────────────────────────────────────────────────────────────────


def test_every_harness_script_invocation_is_uv_run_prefixed(report: InvariantReport) -> None:
    """Every examined harness-script invocation carries `uv run`; a miss names file:line.

    Refutability: delete `uv run` from one documented invocation and this fails, naming it.
    """
    n = len(report.invocations)
    print(f"herdr uv-run invariant: examined {n} harness-script invocations")
    assert not report.script_violations, (
        "harness-script invocations documented without 'uv run':\n"
        + ("\n".join(report.script_violations))
    )


def test_scanner_is_not_vacuous(report: InvariantReport) -> None:
    """A scan that examined almost nothing proves nothing: pin the floors from the measurement."""
    assert len(report.invocations) >= INVOCATION_FLOOR, (
        f"scanner examined only {len(report.invocations)} invocations, floor is {INVOCATION_FLOOR}; "
        "a matcher that matches nothing must not pass this invariant"
    )
    assert report.rendered_invocations >= RENDERED_INVOCATION_FLOOR, (
        f"rendered agent-facing surfaces contributed only {report.rendered_invocations} "
        f"invocations (reply contract, role invariant, and recovery block each contribute one)"
    )
    assert report.total_cli >= CLI_OCCURRENCE_FLOOR, (
        f"scanner found only {report.total_cli} herdr CLI occurrences, floor is {CLI_OCCURRENCE_FLOOR}"
    )


def test_each_required_rendered_surface_carries_its_uv_run_command(report: InvariantReport) -> None:
    """The rendered branch is exercised: the three command-bearing surfaces each match one."""
    for where, expected in (
        ("rendered:herdr_envelope.render_reply_contract", 1),
        ("rendered:herdr_bootstrap.INVARIANT_RULES", 1),
        ("rendered:herdr_reply.recovery_block", 1),
    ):
        hits = [f for f in report.invocations if f.where == where and f.uv_run_before]
        assert len(hits) >= expected, f"{where}: expected the reply command rendered with 'uv run'"
    notice = [f for f in report.invocations if f.where == "rendered:herdr_envelope.SKILL_NOTICE"]
    assert not notice, "SKILL_NOTICE names no script, so it must contribute no invocation"


# ── the distinction pin: the CLI family must stay bare ────────────────────────────────────────


def test_documented_herdr_cli_invocations_are_never_uv_run_prefixed(
    report: InvariantReport,
) -> None:
    """`uv run herdr agent …` is wrong wherever documented: prose, fences, and renders alike."""
    assert not report.cli_violations, "herdr CLI documented behind 'uv run':\n" + "\n".join(
        report.cli_violations
    )


def test_every_skill_doc_documents_at_least_one_bare_cli_invocation(
    report: InvariantReport,
) -> None:
    """Per-skill-doc CLI floor, so the distinction pin cannot pass on an empty CLI branch.

    GLOSSARY.md documents no commands of either family (measured: zero occurrences of both), so
    the per-doc floor binds the twelve skill docs; GLOSSARY.md is still scanned for violations
    and pinned here to stay command-free — a command added to it must be classified, not missed.
    """
    skill_docs = [str(p.relative_to(REPO_ROOT)) for p in DOC_SURFACES if p != GLOSSARY_DOC]
    missing = [where for where in skill_docs if report.cli_by_surface.get(where, 0) < 1]
    assert not missing, "skill docs documenting no herdr CLI invocation: " + ", ".join(missing)
    glossary = str(GLOSSARY_DOC.relative_to(REPO_ROOT))
    assert report.cli_by_surface.get(glossary, 0) == 0, (
        "GLOSSARY.md gained CLI occurrences: re-measure"
    )
    assert not [f for f in report.invocations if f.where == glossary], (
        "GLOSSARY.md gained harness-script invocations: re-measure"
    )
