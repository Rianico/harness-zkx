"""The documented A2A envelope is mechanically checkable (#182 t4).

`test_herdr_doc_contract.py` already pins the quoted skill notice and every file pointer; this
module pins the envelope *shape* itself. Docs are the input under test: every fenced envelope
sample in `skills/herdr/SKILL.md`, `skills/herdr/references/lane-coordination.md`, and
`GLOSSARY.md` must be valid A2A frontmatter — line 1 `---`, top-level keys exactly
`id`/`context_id`/`status`/`metadata`, closed by `---`, the skill notice on its own line after
the closing fence — and nothing may be presented as the format in use that `herdr_envelope.py`
does not render. Retired-format text is allowed only where it is explicitly labelled retired.

A sample is a fenced block whose first content line is exactly the paging delimiter. The floors
below (`_MIN_SAMPLES_PER_DOC`) make extraction non-vacuous: a regex that silently matched zero
samples, or an edit that converted a sample into something else, fails the count pin, not the
silent pass. Constants come from `herdr_envelope` and `herdr_lease` — never re-stated as
literals here — so a docs-vs-code drift fails here instead of both sides agreeing on a stale
shape.

Refutability (each mutation below was executed against these docs and observed to fail the named
cases; the harness applied the mutation, ran this module, and restored the doc byte-for-byte):
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

# The enumeration a doc offers as canonical: the comma-separated backticked list that follows the
# words "Canonical statuses:". The list ends at the first span that is not quoted, so prose after
# it ("— every write emits these") and the parenthesized historical tokens stay out of scope.
_CANONICAL_LIST_RE = re.compile(r"Canonical statuses:(?:\s*`[A-Za-z0-9_]+`,?)+")

# Sample floors: SKILL.md documents the canonical dispatch envelope, lane-coordination.md
# documents the dispatch and reply pair. A doc whose samples vanish fails the floor, so an
# over-narrow extractor can never void the pin by finding nothing.
_MIN_SAMPLES_PER_DOC = {OVERVIEW_DOC: 1, COORDINATION_DOC: 2}


def _fences(doc: Path) -> list[tuple[str, str]]:
    """Every top-level fenced block in `doc` as (info string, body)."""
    return [
        (match.group(1), match.group(2))
        for match in _FENCE_RE.finditer(doc.read_text(encoding="utf-8"))
    ]


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
    assert found >= minimum, (
        f"{doc.relative_to(REPO_ROOT)}: {found} envelope samples < floor {minimum}"
    )


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
        where = f"{doc.relative_to(REPO_ROOT)} sample {number}"
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
    """No fenced block shows `Routing:`/`Hierarchy:`/`Runtime:`/`Protocol:` or a bracket timestamp.

    A block is exempt when its info string or the nearest preceding non-blank line labels it
    retired — recording what was retired is allowed, presenting it as the format in use is not.

    Mutant: reintroduce a `Routing:` block into a doc sample (labelled or not) without the word
    "retired" on the info line or the line before it, and this case fails naming the marker.
    """
    text = doc.read_text(encoding="utf-8")
    fences = _fences(doc)
    if doc in _MIN_SAMPLES_PER_DOC:
        assert fences, f"{doc} has no fenced blocks to scan"
    for info, body in fences:
        preceding = _nearest_preceding_non_blank(text, body)
        if "retired" in info.lower() or "retired" in preceding.lower():
            continue
        block = _RETIRED_BLOCK_RE.search(body)
        assert block is None, (
            f"{doc.relative_to(REPO_ROOT)}: fenced block renders the retired "
            f"{block.group(1)}: block"
        )
        stamp = _BRACKET_TIMESTAMP_RE.search(body)
        assert stamp is None, (
            f"{doc.relative_to(REPO_ROOT)}: fenced block opens with the retired bracket "
            f"timestamp {stamp.group(0)!r}"
        )


def _nearest_preceding_non_blank(text: str, body: str) -> str:
    """The non-blank line directly before a fenced block's body, for the retired exemption."""
    start = text.find(body)
    assert start != -1, "fence body not found in its own doc"
    before = text[:start].rstrip("\n").splitlines()
    return before[-1] if before else ""


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
                    f"{doc.relative_to(REPO_ROOT)}:{line_no}: `{span}` presents the retired "
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
        assert lists, f"{doc.relative_to(REPO_ROOT)} states no canonical status enumeration"
        for match in lists:
            named = re.findall(r"`([A-Za-z0-9_]+)`", match.group(0))
            line_no = text[: match.start()].count("\n") + 1
            assert named == list(herdr_lease.CANONICAL_STATUSES), (
                f"{doc.relative_to(REPO_ROOT)}:{line_no}: canonical enumeration drifts — "
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
        assert "STATUS_ALIASES" in text, f"{doc.relative_to(REPO_ROOT)} never names the alias table"
        assert "never written" in text or "are never migrated" in text, (
            f"{doc.relative_to(REPO_ROOT)} does not say historical tokens are never written"
        )
    assert "shared live database" in COORDINATION_DOC.read_text(encoding="utf-8"), (
        "lane-coordination.md must state why reads accept both vocabularies"
    )
