"""Doc-contract tests for the herdr skill: documented values vs the code, and pointer resolution.

Two contracts live here, and both read the *documentation* as the input under test:

1. **Documented values.** Every window, exit code, and rendered notice asserted in these docs is
   parsed *out of the doc text* and compared against the code constant (imported, never re-stated
   as a literal), so the code stays the single implementation and the prose cannot drift from
   behaviour.
2. **Documented pointers.** Every inline-code token in `skills/herdr/**/*.md` that looks like a
   file pointer must resolve to a file that exists. `EXCLUDED_TOKENS` is an **exact** allow-list
   (no globs) naming the prose illustrations that are deliberately not pointers here, so a new
   dead pointer fails loudly instead of hiding behind a pattern. That allow-list is frozen as a
   literal in `doc_contract_allow_list_golden.json` and pinned from three sides: each entry states
   a non-empty reason, each token is one exact token (never a pattern), and no entry resolves to a
   file that exists in this repository, so growing the allow-list is a deliberate two-file edit.
   The two spellings of "the
   reader's own skill directory" — `$SKILL_DIR/…` and `${herdr_skill}/…` — both resolve against
   this tree's skill directory, so a dead pointer in either spelling is caught.
"""

from __future__ import annotations

import json
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
import herdr_reply
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
# is a single token (never a pattern) so any new unresolved token fails the test below. The mapping
# is frozen in `doc_contract_allow_list_golden.json`; the pins below hold it to that literal, to a
# stated reason per entry, to the single-token shape, and to resolving nowhere in this repository.
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

# The frozen copy of `EXCLUDED_TOKENS`, harvested from this module at commit 3b5e078b and pinned as
# a literal, so an exclusion is a deliberate two-file edit instead of a one-line silence. Never
# derive it from `EXCLUDED_TOKENS`: an expectation read out of the live mapping moves with it and
# passes whatever it holds.
GOLDEN_ALLOW_LIST_PATH = Path(__file__).with_name("doc_contract_allow_list_golden.json")
GOLDEN_ALLOW_LIST: Mapping[str, str] = json.loads(
    GOLDEN_ALLOW_LIST_PATH.read_text(encoding="utf-8")
)

# fnmatch's metacharacters plus bash brace expansion: any of these makes one token stand for many
# files, which is exactly what the allow-list must never hold.
GLOB_CHARACTERS = frozenset("*?[]{}")

# ── pointer policy ────────────────────────────────────────────────────────────────────────────


# The two spellings the docs use for "the reader's own skill directory": the bootstrap reference's
# `$SKILL_DIR/` shell variable and the Protocol notice's `${herdr_skill}/` placeholder. Both name
# this tree's skill directory here, so both resolve (or fail) against it — a dead token in either
# spelling is a dead pointer, never a skip.
SKILL_DIR_PREFIXES = ("$SKILL_DIR/", "${herdr_skill}/")


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
    for prefix in SKILL_DIR_PREFIXES:
        if token.startswith(prefix):
            candidate = SKILL_DIR / token[len(prefix) :]
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
    """Guard against a vacuous pass: the docs cite 146 pointers over 37 distinct targets."""
    assert len(report.resolved) >= 130, "resolved pointers dropped below the observed floor"
    assert len(report.resolved_tokens) >= 30, "distinct resolved pointers dropped below the floor"


def test_allow_list_holds_only_exact_file_tokens() -> None:
    """No globs and no bare directories in the allow-list: a pattern would hide dead pointers."""
    for token in EXCLUDED_TOKENS:
        assert token.endswith(POINTER_EXTENSIONS), token
        assert not set(token) & set("*?[]"), token
        assert Path(token).suffix, token


def test_allow_list_matches_the_frozen_golden_set() -> None:
    """The allow-list equals `doc_contract_allow_list_golden.json`, entry for entry.

    The expectation is the fixture's literal copy, harvested from this module at commit 3b5e078b,
    never `EXCLUDED_TOKENS` itself: a derived expectation is a tautology that proves nothing.

    Mutant killed: add one token to `EXCLUDED_TOKENS` — a dead pointer a reader wants silenced —
    and this pin fails on the added entry, naming it, so the silence must become a deliberate edit
    to the fixture too. Re-wording one reason fails the same way.
    """
    golden = dict(GOLDEN_ALLOW_LIST)
    added = sorted(set(EXCLUDED_TOKENS) - set(golden))
    dropped = sorted(set(golden) - set(EXCLUDED_TOKENS))
    assert not added, f"allow-list entries added without freezing them in the fixture: {added}"
    assert not dropped, f"allow-list entries dropped from the fixture: {dropped}"
    for token in sorted(golden):
        assert EXCLUDED_TOKENS[token] == golden[token], (
            f"{token}: reason {EXCLUDED_TOKENS[token]!r} != frozen {golden[token]!r}"
        )


def test_every_allow_listed_token_is_still_cited(report: PointerReport) -> None:
    """Every allow-listed token must still appear in the scan, so a stale entry cannot linger.

    `scan_pointers` counts one `illustration` exclusion per cited allow-listed token, so the count
    equals the allow-list length while every entry is cited. A doc edit that deletes an entry's only
    citation drops a token from the scan and the count falls below the length, which the count
    assertion catches. The count alone is a floor: an edit that deletes one entry's only citation
    and duplicates another entry's citation in the same change keeps the total at the length while a
    token is now uncited, so the per-token `cited` set below binds each allow-listed token to its
    own citation. Mutants killed: (a) remove one allow-listed token's citation and the count pin
    fails; (b) remove one token's citation and duplicate another's and the per-token pin still
    fails. Measured: `excluded["illustration"] == 10 == len(EXCLUDED_TOKENS)`.
    """
    assert report.excluded.get("illustration", 0) >= len(EXCLUDED_TOKENS), (
        "fewer allow-listed citations than allow-list entries: a stale entry may now be uncited"
    )
    cited = {
        token for doc in sorted(SKILL_DIR.glob("**/*.md")) for token, _ in _pointer_tokens(doc)
    }
    assert set(EXCLUDED_TOKENS) <= cited, (
        f"allow-listed tokens no longer cited anywhere: {sorted(set(EXCLUDED_TOKENS) - cited)}"
    )


@pytest.mark.parametrize("token", sorted(EXCLUDED_TOKENS))
def test_every_allow_list_entry_states_a_reason(token: str) -> None:
    """An entry must say why it is not a pointer here; a bare token is an unexplained skip.

    Mutant killed: blank one entry's reason in `EXCLUDED_TOKENS` and this case fails for that
    token, naming it. The allow-list comment's guarantee that each entry names what it is then
    holds as a check instead of a convention.
    """
    reason = EXCLUDED_TOKENS[token]
    assert reason.strip(), f"{token}: an allow-list entry must state why it is not a pointer"


@pytest.mark.parametrize("token", sorted(EXCLUDED_TOKENS))
def test_every_allow_list_token_is_one_exact_token(token: str) -> None:
    """One exact token, never a pattern or a list: a glob or whitespace would match many files.

    `test_allow_list_holds_only_exact_file_tokens` already refuses `*?[]`; this pin adds brace
    expansion and whitespace, so no entry can stand for more than the one token it names.

    Mutant killed: add `src/*.py` to `EXCLUDED_TOKENS` and this case fails, naming the token.
    """
    assert not set(token) & GLOB_CHARACTERS, f"{token}: an allow-list token may not be a pattern"
    assert token.split() == [token], f"{token}: an allow-list entry is one token, never a list"


def test_no_allow_listed_token_resolves_to_a_file_in_this_repository() -> None:
    """Every allow-listed token resolves nowhere, against any doc: that is why the list is safe.

    An entry that resolves is the dangerous case: `scan_pointers` skips an allow-listed token
    before `_resolve` runs, so a token that *does* name a file in this repository would be excused
    from resolution, and a genuinely broken pointer could later hide behind that same token.
    Measured at 3b5e078b: none of the ten entries resolves against any scanned doc.

    Mutant killed: add `README.md` — or any other existing repository path — to `EXCLUDED_TOKENS`
    and this pin fails, naming the token, the doc, and the file it resolved to.
    """
    docs = sorted(SKILL_DIR.glob("**/*.md"))
    assert docs, "no docs scanned, so this pin would pass vacuously"
    offenders = {
        token: f"{doc.relative_to(REPO_ROOT)} -> {found.relative_to(REPO_ROOT)}"
        for token in EXCLUDED_TOKENS
        for doc in docs
        if (found := _resolve(doc, token)) is not None
    }
    assert offenders == {}, "allow-listed tokens that resolve to a file here: " + "; ".join(
        f"{token} ({where})" for token, where in offenders.items()
    )


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
        ("${herdr_skill}/scripts/herdr_reply.py", None),
    ],
)
def test_pointer_policy_classifies_tokens(token: str, expected: str | None) -> None:
    """The exclusion rules stay narrow: each shape is classified, everything else must resolve.

    Mutant killed: re-add `if token.startswith("${herdr_skill}/"): return "placeholder"` to
    `_exclusion_rule` — the `${herdr_skill}/`-prefixed helper then classifies as a placeholder
    instead of None, so the two documented pointers at `lane-coordination.md:220` and `:245`
    could go back to being silently unchecked.
    """
    assert _exclusion_rule(token) == expected


def test_lane_coordination_documents_the_superset_merge_workaround() -> None:
    """#244: the skill references name the --ff-only workaround for superset integrations."""
    text = (SKILL_DIR / "references" / "lane-coordination.md").read_text(encoding="utf-8")
    assert "git merge --ff-only" in text
    assert "merge-base --is-ancestor" in text
    assert "squash" in text


def test_superset_merge_workaround_keeps_a_cited_sha_on_history(tmp_path: Path) -> None:
    """#244: the workaround text is accurate — a fast-forward keeps the cited SHA on history.

    A descendant task branch integrated with `git merge --ff-only` writes no new commit,
    so the cited per-unit commit is an ancestor of the landed HEAD; a squash landing
    leaves it off-history. Ancestry — not bare resolvability, which a lingering object
    store still answers — is what the evidence citations need.

    Mutant killed: land with `--squash` instead of `--ff-only` — the cited SHA is no
    ancestor of HEAD and the final `merge-base --is-ancestor` fails.
    """
    repo = tmp_path / "ff-only-repo"
    repo.mkdir()

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
        )

    assert git("init", "-q", "-b", "main").returncode == 0
    assert (
        git(
            "-c",
            "user.name=herdr",
            "-c",
            "user.email=herdr@example.invalid",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "base",
        ).returncode
        == 0
    )
    assert git("checkout", "-q", "-b", "task").returncode == 0
    assert (
        git(
            "-c",
            "user.name=herdr",
            "-c",
            "user.email=herdr@example.invalid",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "per-unit work",
        ).returncode
        == 0
    )
    unit_sha = git("rev-parse", "HEAD").stdout.strip()
    assert git("checkout", "-q", "main").returncode == 0
    assert git("merge-base", "--is-ancestor", "main", "task").returncode == 0
    assert git("merge", "-q", "--ff-only", "task").returncode == 0
    assert git("merge-base", "--is-ancestor", unit_sha, "HEAD").returncode == 0


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
            assert pointer.endswith("ai-engineering-expert/references/" + template), pointer
            assert _resolve(OVERVIEW_DOC, pointer) is not None, f"{pointer} does not exist"


# ── divergence 4: the Protocol notice quoted in every envelope sample ─────────────────────────


def _quoted_protocol_notices(doc: Path) -> list[str]:
    """Lines the doc quotes as the envelope's Protocol notice, located by its leading token.

    The notice rides every rendered envelope, so the docs quote it verbatim; the leading
    `Herdr:` token finds each quote without depending on line numbers. Lines are returned
    stripped, the indentation being the sample's, not the notice's.
    """
    return [
        line.strip()
        for line in doc.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("Herdr:")
    ]


@pytest.mark.parametrize("doc", (OVERVIEW_DOC, COORDINATION_DOC))
def test_documented_protocol_notice_matches_the_code(doc: Path) -> None:
    """Every quoted Protocol notice equals `herdr_prompt.SKILL_NOTICE`, so prose cannot lag it."""
    quoted = _quoted_protocol_notices(doc)
    where = doc.relative_to(REPO_ROOT)
    assert quoted, f"{where} quotes no Protocol notice"
    for line in quoted:
        assert line == herdr_prompt.SKILL_NOTICE, f"{where}: {line}"


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
        prefix = next((p for p in SKILL_DIR_PREFIXES if token.startswith(p)), None)
        if prefix is not None:
            token = str(SKILL_DIR / token[len(prefix) :])
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


# ── herdr228-p3#P4: the guard-doc drift pins ───────────────────────────────────────

# Five doc/code drifts the E2 review found (F2–F5, plus the SKILL.md paraphrase folded
# in from P1's review): each pin parses the doc text and holds it against the code
# (imported, never re-stated), so the prose cannot drift from behaviour again.


def _reply_docstring() -> str:
    """The reply helper's module docstring: the guard contract most callers read first."""
    assert herdr_reply.__doc__ is not None
    return herdr_reply.__doc__


def test_reply_docstring_states_the_backticked_review_id_refusal_and_waiver() -> None:
    """P4 item 1: a backticked review-record id IS refused; the waiver is the sanctioned route.

    The docstring once claimed review-record ids "are not read as citations" while the
    broad trigger refuses a backticked one. Mutant: restore that sentence and this pin
    fails on the revived claim and the missing refusal.
    """
    doc = _reply_docstring()
    assert "are not read as citations" not in doc
    assert "backticked review-record id" in doc
    assert "waive that token by name" in doc
    assert herdr_reply.ALLOW_UNRESOLVABLE_SHA in doc


def test_e2_do_not_rewrite_pin_cross_references_the_scope_issue() -> None:
    """P4 item 2: the E2 pin-1 docstring cites #247, not #245.

    The section header names the scope decision #247 E2 while the pin-1 line cites the
    incident #247 (the incident number was confirmed via the issue tracker, not
    retyped from memory). Mutant: re-apply #245 and this pin fails on both halves.
    """
    text = Path(__file__).with_name("test_herdr_reply.py").read_text(encoding="utf-8")
    line = next(line for line in text.splitlines() if "drifted by one hex digit" in line)
    assert "#247" in line, line
    assert "#245" not in line, line


def test_changelog_states_the_length_difference_not_exact_likeness() -> None:
    """P4 item 3: seven-hex notation merely resembles the eight-hex ids; it is not like them.

    Seven and eight hex differ in length, so "exactly like" overclaims. Mutant: restore
    the phrase and this pin fails.
    """
    bullet = next(
        line
        for line in (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        if "seven hex characters" in line
    )
    assert "exactly like" not in bullet
    assert "differing in length" in bullet


def _skill_waiver_quote() -> str:
    """The double-quoted waiver sentence in the skill overview."""
    match = re.search(
        r'"(If the reply quotes a review id.*?)"',
        OVERVIEW_DOC.read_text(encoding="utf-8"),
        re.S,
    )
    assert match is not None, "the overview quotes no waiver sentence"
    return match.group(1)


def test_skill_quotes_the_rendered_waiver_route_verbatim() -> None:
    """P4 item 5: the overview quotes the rendered waiver line verbatim, not paraphrased.

    The renderer is the single implementation: the pin compares the overview's quote
    against `render_reply_contract` itself. Mutant: reword either side and this pin fails.
    """
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="orchestrator", agent="orchestrator")
    rendered = herdr_prompt.render_reply_contract(sender, "herdr228-p3#P4")
    waiver_line = rendered.splitlines()[-1].strip()
    assert waiver_line.startswith("If the reply quotes a review id"), rendered
    assert _skill_waiver_quote() == waiver_line


# ── herdr228-closeout#C1: the SHA-guard citation referents ─────────────────────────

# Every live citation of the SHA-guard convention names its tracking referent inline
# (`#<n>` beside the D2/E2 label). The audit found the long-standing `#245` referent
# does not resolve — tracker 245 is a gh-router PR — while `#247` is the drifted-SHA
# incident the guard exists to refuse. The fixture freezes both verified titles so
# this pin runs without network; refresh it with `gh issue view <n> --json title`.
SHA_GUARD_REFERENTS_FIXTURE = Path(__file__).with_name("sha_guard_citation_referents.json")

# One stable number-free fragment per live citation line: the fragment finds the line
# before and after any re-citation, so the pin holds the referent, never the prose.
SHA_GUARD_CITATION_SITES: tuple[tuple[Path, str], ...] = (
    (REPO_ROOT / "CHANGELOG.md", "instead of paraphrasing it"),
    (OVERVIEW_DOC, "token drifted by one digit points at nothing"),
    (COORDINATION_DOC, "one that drifts by a digit points at nothing"),
    (SCRIPTS_DIR / "herdr_reply.py", "the outbound payload itself is checked"),
    (
        SCRIPTS_DIR / "herdr_reply.py",
        "an outbound payload may not cite a SHA that resolves to nothing",
    ),
    (SCRIPTS_DIR / "herdr_reply.py", "scanned 668"),
    (SCRIPTS_DIR / "herdr_reply.py", "byte-identical to a clean environment"),
    (
        SCRIPTS_DIR / "herdr_reply.py",
        "Refuse a payload whose backticked SHA-shaped token names no commit",
    ),
    (
        SCRIPTS_DIR / "herdr_reply.py",
        "is an instruction, and an instruction that names no",
    ),
    (
        SCRIPTS_DIR / "herdr_envelope.py",
        "trigger, so without guidance the reply is refused with no sanctioned next",
    ),
    (
        Path(__file__).with_name("test_herdr_reply.py"),
        "an outbound payload may not cite a SHA that resolves to nothing",
    ),
    (
        Path(__file__).with_name("test_herdr_reply.py"),
        "the guard's scope decision, pinned so the choice is visible",
    ),
    (
        Path(__file__).with_name("test_herdr_reply.py"),
        "which git overrides actually move the object store",
    ),
    (
        Path(__file__).with_name("test_herdr_reply.py"),
        "the object-store overrides skip loudly",
    ),
    (
        Path(__file__).with_name("test_herdr_reply.py"),
        "the index and work-tree overrides must not skip",
    ),
    (
        Path(__file__).with_name("test_herdr_prompt.py"),
        "so the contract itself must tell the callee the",
    ),
)


def test_sha_guard_citations_resolve_to_the_verified_referent() -> None:
    """C1: each SHA-guard citation names the referent whose title states the subject.

    The fixture records the verified tracker titles: the referent's title carries the
    drifted-SHA subject while the superseded number's title is an unrelated gh-router
    PR — the audit's mismatch evidence, frozen so the pin runs without network. Every
    citation line must carry the referent and none of the superseded number. Mutant:
    re-point one citation at the superseded (or any unrelated) number and this pin
    fails on that line.
    """
    fixture = json.loads(SHA_GUARD_REFERENTS_FIXTURE.read_text(encoding="utf-8"))
    referent = str(fixture["referent"])
    superseded = str(fixture["superseded"])
    keywords = [str(keyword) for keyword in fixture["asserted_subject_keywords"]]
    titles = {str(number): str(title) for number, title in fixture["titles"].items()}
    assert all(keyword in titles[referent] for keyword in keywords), titles[referent]
    assert not all(keyword in titles[superseded] for keyword in keywords), titles[superseded]
    assert len(SHA_GUARD_CITATION_SITES) == 16, "audit site dropped without review"
    for path, needle in SHA_GUARD_CITATION_SITES:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if needle in line]
        assert len(lines) == 1, (str(path), needle, lines)
        (line,) = lines
        assert f"#{referent}" in line, (str(path), line)
        assert f"#{superseded}" not in line, (str(path), line)
