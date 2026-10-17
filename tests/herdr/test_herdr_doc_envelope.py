"""The documented A2A envelope is mechanically checkable (#182 t4).

`test_herdr_doc_contract.py` already pins the quoted skill notice and every file pointer; this
module pins the envelope *shape* itself. Docs are the input under test: every fenced envelope
sample in `skills/herdr/SKILL.md`, `skills/herdr/references/lane-coordination.md`, and
`GLOSSARY.md` must be valid A2A frontmatter — line 1 `---`, top-level keys exactly
`id`/`context_id`/`status`/`metadata`, closed by `---`, the skill notice on its own line after
the closing fence — and nothing may be presented as the format in use that `herdr_envelope.py`
does not render. Retired-format text is allowed only in a block whose own fence line labels it
retired.

A sample is a fenced block whose first content line is exactly the paging delimiter. The floors
below (`_MIN_SAMPLES_PER_DOC`) make extraction non-vacuous: a regex that silently matched zero
samples, or an edit that converted a sample into something else, fails the count pin, not the
silent pass. Constants come from `herdr_envelope` and `herdr_lease` — never re-stated as
literals here — so a docs-vs-code drift fails here instead of both sides agreeing on a stale
shape.

Refutability (each mutation was applied to these docs, this module run against it, and the doc
restored byte-for-byte with its sha256 checked and `git status` clean: t4 reports the first four,
t5 re-ran the green baseline at HEAD and executed the last two itself):
- Reintroduce a `Routing:` block into the `skills/herdr/SKILL.md` sample: it becomes a fifth
  top-level key, so `test_documented_envelope_samples_are_valid_a2a_frontmatter[SKILL.md]` fails,
  and the same line trips `test_no_fenced_block_renders_the_retired_envelope_shape[SKILL.md]`.
- Convert the `lane-coordination.md` reply sample's opening `---` into the retired bracket
  timestamp: that doc drops below its extraction floor
  (`test_envelope_sample_extraction_is_not_vacuous[lane-coordination.md]`), the docs-wide count
  fails (`test_envelope_samples_are_evidence_not_a_vacuum`), and the bracket stamp itself fails
  `test_no_fenced_block_renders_the_retired_envelope_shape[lane-coordination.md]`.
- Reintroduce the sentence "a message that arrives without a `Sender:` line did not come from
  these scripts": `test_no_doc_label_presents_retired_header_labels_as_envelope_syntax[SKILL.md]`
  fails on the backticked `Sender:` span.
- Restore "Canonical statuses: `dispatched`, `in_progress`, `blocked`, `completed`, `rework`":
  `test_documented_canonical_statuses_are_exactly_the_a2a_names` fails naming the doc, the line and
  the documented-vs-code enumerations.
- Append to `skills/herdr/SKILL.md` an unlabelled `text` fence holding the one bare retired label
  line `Sender: w1:p4 - label pr-orchestrator - tab w1:t1 - kind agy`: that is the shape t4 could
  not catch — before the label-line regex existed every case stayed green on it, fifteen of fifteen
  — and it now fails `test_no_fenced_block_renders_the_retired_envelope_shape[SKILL.md]`.
- Delete `metadata.ticket_id` from the `GLOSSARY.md` Ticket-ID entry:
  `test_glossary_names_the_envelope_fields_its_entries_claim` fails naming the field, and nothing
  else does, because `GLOSSARY.md` carries no fence for the shape cases to scan (measured: zero).
  The two helper-level mutations are pinned by their own cases instead of by a doc edit: a
  byte-identical pair of fence bodies, fed to `_nearest_preceding_non_blank`, must be judged by
  their own offsets
  (`test_retired_exemption_reads_the_blocks_own_offset_not_the_first_matching_body`), and a doc
  copied outside `REPO_ROOT` must still raise `AssertionError` rather than `ValueError`
  (`test_a_failing_pin_reports_a_sandbox_copy_as_an_assertion`).
"""

from __future__ import annotations

import re
from pathlib import Path

import herdr_envelope
import herdr_lease
import pytest
import yaml

from tests.herdr.stub import SCRIPTS_DIR

REPO_ROOT = SCRIPTS_DIR.parents[2]
SKILL_DIR = SCRIPTS_DIR.parent
OVERVIEW_DOC = SKILL_DIR / "SKILL.md"
COORDINATION_DOC = SKILL_DIR / "references" / "lane-coordination.md"
GLOSSARY_DOC = REPO_ROOT / "GLOSSARY.md"

DOCS = (OVERVIEW_DOC, COORDINATION_DOC, GLOSSARY_DOC)

# Envelope samples live at the top level of these docs (not inside blockquote callouts), so one
# column-0 fence regex sees all of them; the floors below catch anything this misses.
_FENCE_RE = re.compile(r"^```[ \t]*([^\s`]*)[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)

# A backticked label spelled `<Word>:` is envelope *syntax* presentation, not a concept name.
_RETIRED_LABEL_SPANS = ("Sender:", "Receiver:", "Ticket-ID:", "Task-ID:", "Group:", "In-Reply-To:")

# The retired Style 2 blocks and their leading bracket timestamp: shape markers of the format
# `herdr_envelope.parse_envelope` refuses.
_RETIRED_BLOCK_RE = re.compile(r"^\s*(Routing|Hierarchy|Runtime|Protocol):", re.M)
_BRACKET_TIMESTAMP_RE = re.compile(r"^\[\d{4}-\d{2}-\d{2}", re.M)

# The pre-cutover header also rendered bare label LINES inside the block, one
# `Sender: w1:p4 - label pr-orchestrator - tab w1:t1 - kind agy` at a time. The block-label
# regex above cannot see them (none of its four words is a header label) and neither can the
# backtick rule below (a fenced line is not a backticked span), so a fence body teaching the
# retired format slipped through both. Inside a fence a `Word:` line is presentation of the
# format, never a concept name, so the whole retired header vocabulary is refused here.
_RETIRED_LABEL_LINE_RE = re.compile(
    r"^\s*(Sender|Receiver|Ticket-ID|Task-ID|In-Reply-To|Group|Task-Group|Routing|Hierarchy|"
    r"Runtime|Protocol):",
    re.M,
)

# The enumeration a doc offers as canonical: the comma-separated backticked list that follows the
# words "Canonical statuses:". The list ends at the first span that is not quoted, so prose after
# it ("— every write emits these") and the parenthesized historical tokens stay out of scope.
_CANONICAL_LIST_RE = re.compile(r"Canonical statuses:(?:\s*`[A-Za-z0-9_]+`,?)+")

# Sample floors: SKILL.md documents the canonical dispatch envelope, lane-coordination.md
# documents the dispatch and reply pair. A doc whose samples vanish fails the floor, so an
# over-narrow extractor can never void the pin by finding nothing.
_MIN_SAMPLES_PER_DOC = {OVERVIEW_DOC: 1, COORDINATION_DOC: 2}


def _display_path(doc: Path) -> str:
    """How a failure message names `doc`: repo-relative, or the basename when it is not under.

    `relative_to` raises `ValueError` for a path outside `REPO_ROOT`, so the eager call this
    module used to make inside the message path replaced the intended `AssertionError` with a
    crash whenever the pin was driven from a sandbox copy of a doc. A missing-file message is
    the one place that keeps the full path: there the caller needs the path it could not find.
    """
    try:
        return str(doc.relative_to(REPO_ROOT))
    except ValueError:
        return doc.name


def _fence_matches(text: str) -> list[re.Match[str]]:
    """Every top-level fenced block, as matches, so a caller can read the block's own offset."""
    return list(_FENCE_RE.finditer(text))


def _fences(doc: Path) -> list[tuple[str, str]]:
    """Every top-level fenced block in `doc` as (info string, body)."""
    text = doc.read_text(encoding="utf-8")
    return [(match.group(1), match.group(2)) for match in _fence_matches(text)]


def _envelope_samples(doc: Path) -> list[list[str]]:
    """The lines of every fenced block whose first content line is the `---` paging delimiter."""
    samples: list[list[str]] = []
    for _, body in _fences(doc):
        lines = body.rstrip("\n").splitlines()
        if lines and lines[0] == herdr_envelope.PAGING_DELIMITER:
            samples.append(lines)
    return samples


def _frontmatter_lines(sample: list[str]) -> list[str]:
    """The fenced frontmatter body: between the opening `---` (line 1) and the next `---`."""
    close = sample.index(herdr_envelope.PAGING_DELIMITER, 1)
    return sample[1:close]


def _backtick_spans(line: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", line)


@pytest.mark.parametrize("doc", DOCS, ids=lambda path: path.name)
def test_envelope_sample_extraction_is_not_vacuous(doc: Path) -> None:
    """Each doc still carries the envelope samples the floor promises; extractors see them.

    Mutant: convert a sample so it no longer opens with `---` (e.g. restore a bracket-timestamp
    first line) and this pin fails on that doc's count, naming the floor.
    """
    assert doc.exists(), f"{doc} vanished"
    minimum = _MIN_SAMPLES_PER_DOC.get(doc, 0)
    found = len(_envelope_samples(doc))
    assert found >= minimum, f"{_display_path(doc)}: {found} envelope samples < floor {minimum}"


def test_envelope_samples_are_evidence_not_a_vacuum() -> None:
    """Docs-wide the pin has something to check: at least three samples across the three docs.

    Mutant: delete every documented sample and this case fails on the docs-wide count even where
    a per-doc floor stays silent.
    """
    total = sum(len(_envelope_samples(doc)) for doc in DOCS)
    assert total >= 3, f"only {total} envelope samples docs-wide; the pin would be near-vacuous"


@pytest.mark.parametrize("doc", DOCS, ids=lambda path: path.name)
def test_documented_envelope_samples_are_valid_a2a_frontmatter(doc: Path) -> None:
    """Every documented sample parses with exactly the four A2A top-level keys, fence, and notice.

    Mutant: make a sample an unquoted or `>`-folded shape that `yaml.safe_load` cannot read as
    this dict, add a fifth top-level key, or drop the closing `---`/notice line — each fails
    this case with the sample's doc and line 1 in the message.
    """
    for number, sample in enumerate(_envelope_samples(doc), 1):
        where = f"{_display_path(doc)} sample {number}"
        assert sample[0] == herdr_envelope.PAGING_DELIMITER, f"{where}: line 1 must be `---`"
        assert herdr_envelope.PAGING_DELIMITER in sample[1:], f"{where}: no closing `---`"
        close = sample.index(herdr_envelope.PAGING_DELIMITER, 1)
        raw = yaml.safe_load("\n".join(_frontmatter_lines(sample)))
        assert isinstance(raw, dict), f"{where}: frontmatter is not a mapping"
        assert set(raw) == herdr_envelope.FRONTMATTER_KEYS, (
            f"{where}: top-level keys {sorted(set(raw) - herdr_envelope.FRONTMATTER_KEYS)} "
            f"extra/missing vs the A2A set"
        )
        status = raw["status"]
        assert isinstance(status, dict) and set(status) == herdr_envelope.STATUS_KEYS, (
            f"{where}: `status` must hold exactly state/timestamp"
        )
        assert status["state"] in herdr_lease.CANONICAL_STATUSES, (
            f"{where}: `{status['state']}` is not a canonical TASK_STATE_* name"
        )
        metadata = raw["metadata"]
        assert isinstance(metadata, dict) and metadata.keys() <= herdr_envelope.METADATA_KEYS, (
            f"{where}: metadata keys outside the rendered set: "
            f"{sorted(set(metadata) - herdr_envelope.METADATA_KEYS)}"
        )
        notice = sample[close + 1] if close + 1 < len(sample) else ""
        assert notice == herdr_envelope.SKILL_NOTICE, (
            f"{where}: the line after the closing fence must be the skill notice verbatim, got {notice!r}"
        )


@pytest.mark.parametrize("doc", DOCS, ids=lambda path: path.name)
def test_no_fenced_block_renders_the_retired_envelope_shape(doc: Path) -> None:
    """No fenced block shows a retired block label, a bare retired header label line, or a stamp.

    The block labels are `Routing:`/`Hierarchy:`/`Runtime:`/`Protocol:`; the bare label lines are
    what the same pre-cutover header rendered line by line (`Sender:`, `Receiver:`, `Ticket-ID:`,
    `Task-ID:`, `In-Reply-To:`, `Group:`, `Task-Group:`), and only the label-line regex refuses a
    fence that holds nothing but one of them.

    A block is exempt when its own fence line labels it retired — recording what was retired is
    allowed, presenting it as the format in use is not. The label is read at the block's own match
    offset, so a later byte-identical block can never borrow an earlier block's label, and the
    sentence above the fence is deliberately not consulted (`_nearest_preceding_non_blank` says why).

    Mutant: reintroduce a `Routing:` block into a doc sample without the word "retired" on its own
    fence line, and this case fails naming the marker; append an unlabelled `text` fence holding the
    single line `Sender: w1:p4 - label pr-orchestrator - tab w1:t1 - kind agy` to
    `skills/herdr/SKILL.md` and this case fails naming the `Sender:` label.
    """
    text = doc.read_text(encoding="utf-8")
    matches = _fence_matches(text)
    if doc in _MIN_SAMPLES_PER_DOC:
        assert matches, f"{_display_path(doc)} has no fenced blocks to scan"
    for match in matches:
        info, body = match.group(1), match.group(2)
        preceding = _nearest_preceding_non_blank(text, match.start(2))
        if "retired" in info.lower() or "retired" in preceding.lower():
            continue
        block = _RETIRED_BLOCK_RE.search(body)
        assert block is None, (
            f"{_display_path(doc)}: fenced block renders the retired {block.group(1)}: block"
        )
        label = _RETIRED_LABEL_LINE_RE.search(body)
        assert label is None, (
            f"{_display_path(doc)}: fenced block renders the retired "
            f"{label.group(1)}: header label line"
        )
        stamp = _BRACKET_TIMESTAMP_RE.search(body)
        assert stamp is None, (
            f"{_display_path(doc)}: fenced block opens with the retired bracket "
            f"timestamp {stamp.group(0)!r}"
        )


def _nearest_preceding_non_blank(text: str, body_start: int) -> str:
    """The nearest non-blank line before a fenced body, which for a top-level fence is its own
    opening ``` line — so the retired label has to ride the fence itself, never prose above it.

    Two facts this pins by construction. The offset comes from the block's own regex match, never
    from `text.find(body)`: two byte-identical bodies would make the later block read the earlier
    block's opening line and borrow its "retired" exemption. And because a top-level body starts
    immediately after its own ``` line, what this returns is that fence line, not the prose above
    the block — the stricter reading, and deliberately so: the third block of
    `skills/herdr/references/lane-coordination.md` sits under a sentence citing
    `retired/dynamic-workflow-wrapper/references/resp-format.md`, a path rather than a label, and
    consulting prose would exempt that live reply sample from every refusal here.
    """
    before = text[:body_start].rstrip("\n").splitlines()
    return before[-1] if before else ""


def test_retired_exemption_reads_the_blocks_own_offset_not_the_first_matching_body(
    tmp_path: Path,
) -> None:
    """Two byte-identical fence bodies must be judged by their own fence line, not the first hit.

    The collision is latent in the shipped docs — no body is duplicated there — but a
    search-based offset makes it live the moment one is: labelled the first block retired, an
    identical body in a later block inherits that label and skips every refusal.
    """
    text = (
        "Recording the retired shape:\n"
        "```retired\nSender: w1:p4\n```\n\n"
        "Presenting the format in use:\n"
        "```text\nSender: w1:p4\n```\n"
    )
    matches = _fence_matches(text)
    assert len(matches) == 2, "the extractor must see both blocks before the offsets are compared"
    assert matches[0].group(2) == matches[1].group(2), "the fixture needs byte-identical bodies"
    assert text.find(matches[1].group(2)) == matches[0].start(2), (
        "a search for the second body lands on the first block: that was the bug"
    )
    borrowed = _nearest_preceding_non_blank(text, text.find(matches[1].group(2)))
    assert "retired" in borrowed.lower(), "so the search offset labels the later block retired"
    own = _nearest_preceding_non_blank(text, matches[1].start(2))
    assert own == "```text", "the block's own offset reads its own fence line"
    assert "retired" not in own.lower(), "and its own fence line says nothing about retirement"
    assert _RETIRED_LABEL_LINE_RE.search(matches[1].group(2)) is not None, (
        "the body does carry a retired label line, so the pin has something to refuse"
    )
    copied = tmp_path / "SKILL.md"
    _ = copied.write_text(text, encoding="utf-8")
    with pytest.raises(AssertionError) as failure:
        test_no_fenced_block_renders_the_retired_envelope_shape(copied)
    assert "Sender" in str(failure.value), (
        f"the later block must be refused on its own merits, got {failure.value}"
    )


def test_a_failing_pin_reports_a_sandbox_copy_as_an_assertion(tmp_path: Path) -> None:
    """Driving the pin from a copy outside `REPO_ROOT` must still raise `AssertionError`.

    The message path used to compute `doc.relative_to(REPO_ROOT)` eagerly, so the one situation
    where a reviewer can point the pin at a mutation — a sandbox copy — died with `ValueError`
    instead of naming the offender.
    """
    copied = tmp_path / "SKILL.md"
    _ = copied.write_text("```text\nSender: w1:p4 - label pr-orchestrator\n```\n", encoding="utf-8")
    assert _display_path(copied) == "SKILL.md" == copied.name
    assert _display_path(OVERVIEW_DOC) == str(OVERVIEW_DOC.relative_to(REPO_ROOT))
    with pytest.raises(AssertionError) as failure:
        test_no_fenced_block_renders_the_retired_envelope_shape(copied)
    assert "SKILL.md" in str(failure.value), "the message must name the doc it refused"
    assert "Sender" in str(failure.value), "and the retired label it refused"


@pytest.mark.parametrize("doc", DOCS, ids=lambda path: path.name)
def test_no_doc_label_presents_retired_header_labels_as_envelope_syntax(doc: Path) -> None:
    """No line backticks `Sender:`/`In-Reply-To:` (or sibling header labels) as envelope syntax.

    The retired sentence "a message that arrives without a `Sender:` line did not come from
    these scripts" is actively wrong: no producer renders a `Sender:` line any more. Field names
    now ride lowercase (`metadata.sender`, `metadata.in_reply_to`); concept names (Ticket-ID,
    Task-ID) stay without a colon.

    Mutant: restore that sentence, or write `In-Reply-To:` in backticks anywhere in the three
    docs, and this case fails naming the line.
    """
    for line_no, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
        for span in _backtick_spans(line):
            for label in _RETIRED_LABEL_SPANS:
                assert label not in span, (
                    f"{_display_path(doc)}:{line_no}: `{span}` presents the retired "
                    f"`{label}` header label as envelope syntax"
                )


def test_documented_canonical_statuses_are_exactly_the_a2a_names() -> None:
    """The docs name all five canonical states and never call a historical token canonical.

    The expectation is `herdr_lease.CANONICAL_STATUSES` imported, never re-stated: rename a state
    in the code and the docs fail this pin, not a literal here. Only the enumeration that follows
    the words "Canonical statuses:" is compared, so the store-schema keys and the parenthesized
    readable-but-never-written tokens on the same line stay out of scope.

    Mutant: restore "Canonical statuses: `dispatched`, `in_progress`, `blocked`, `completed`,
    `rework`" in either skill doc and this case fails naming that doc and the historical spans;
    delete a `TASK_STATE_*` name from the enumeration and it fails short.
    """
    assert len(herdr_lease.CANONICAL_STATUSES) == 5, "the canonical set moved; review the docs"
    assert set(herdr_lease.HISTORICAL_STATUSES).isdisjoint(herdr_lease.CANONICAL_STATUSES)
    coordination = COORDINATION_DOC.read_text(encoding="utf-8")
    missing = [name for name in herdr_lease.CANONICAL_STATUSES if name not in coordination]
    assert not missing, f"lane-coordination.md does not name: {missing}"
    for doc in (OVERVIEW_DOC, COORDINATION_DOC):
        text = doc.read_text(encoding="utf-8")
        lists = list(_CANONICAL_LIST_RE.finditer(text))
        assert lists, f"{_display_path(doc)} states no canonical status enumeration"
        for match in lists:
            named = re.findall(r"`([A-Za-z0-9_]+)`", match.group(0))
            line_no = text[: match.start()].count("\n") + 1
            assert named == list(herdr_lease.CANONICAL_STATUSES), (
                f"{_display_path(doc)}:{line_no}: canonical enumeration drifts — "
                f"documented {named}, code emits {list(herdr_lease.CANONICAL_STATUSES)}"
            )


def test_docs_explain_the_read_accepts_writes_emit_split() -> None:
    """The status drift fix is substantive: both skill docs name the alias table and its reason.

    A doc may not just list the five states; it must say reads accept the historical tokens
    through `STATUS_ALIASES` and that writes emit canonical names — the split that the shared
    live lane store requires while the per-process envelope took the zero-shim cutover.

    Mutant: delete the alias-table paragraph from lane-coordination.md and this case fails on
    the missing `STATUS_ALIASES` mention.
    """
    for doc in (OVERVIEW_DOC, COORDINATION_DOC):
        text = doc.read_text(encoding="utf-8")
        assert "STATUS_ALIASES" in text, f"{_display_path(doc)} never names the alias table"
        assert "never written" in text or "are never migrated" in text, (
            f"{_display_path(doc)} does not say historical tokens are never written"
        )
    assert "shared live database" in COORDINATION_DOC.read_text(encoding="utf-8"), (
        "lane-coordination.md must state why reads accept both vocabularies"
    )


# The envelope fields `GLOSSARY.md` claims: the Ticket-ID entry names the first, the Task-ID and
# Reply entries the second. Taken as bare key names and checked against `herdr_envelope`, so a
# code-side rename lands here for review instead of quietly stranding the prose.
_GLOSSARY_ENVELOPE_FIELDS = ("ticket_id", "in_reply_to")


def test_glossary_names_the_envelope_fields_its_entries_claim() -> None:
    """`GLOSSARY.md` holds no fenced block, so every shape case above is inert on it — this is not.

    Measured, not assumed: `_fences(GLOSSARY_DOC)` is empty, which makes
    `test_no_fenced_block_renders_the_retired_envelope_shape[GLOSSARY.md]` and
    `test_documented_envelope_samples_are_valid_a2a_frontmatter[GLOSSARY.md]` structurally
    incapable of failing no matter what the file says. The glossary is where the envelope's
    correlation fields are named as domain concepts, so that is what gets pinned here.

    Mutant: delete `metadata.ticket_id` from the Ticket-ID entry and this case fails naming the
    field, while all three shape cases stay green.
    """
    for key in _GLOSSARY_ENVELOPE_FIELDS:
        assert key in herdr_envelope.METADATA_KEYS, (
            f"the code no longer renders metadata `{key}`; review what the glossary claims"
        )
    assert not _fences(GLOSSARY_DOC), (
        f"{_display_path(GLOSSARY_DOC)} gained a fence, so the shape cases are no longer inert "
        "on it: re-judge this pin against them"
    )
    text = GLOSSARY_DOC.read_text(encoding="utf-8")
    for key in _GLOSSARY_ENVELOPE_FIELDS:
        claim = f"metadata.{key}"
        assert claim in text, (
            f"{_display_path(GLOSSARY_DOC)} never names `{claim}`, the field its Ticket-ID, "
            "Task-ID and Reply entries say the envelope carries"
        )
