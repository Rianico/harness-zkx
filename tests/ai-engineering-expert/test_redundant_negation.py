"""Fixture-integrity and classifier tests for the redundant-negation audit (#315).

The YAML fixture under `writing-for-agents/fixtures/` is the single source of truth for
the fragments. This module adds the mechanical layer: it checks the fixture's shape and
proves that the 3-tier classifier reproduces every recorded decision.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import pytest
import yaml

ROOT = Path(__file__).parents[2]
FIXTURE_PATH = (
    ROOT
    / "skills"
    / "ai-engineering-expert"
    / "subskills"
    / "writing-for-agents"
    / "fixtures"
    / "redundant-negation.yaml"
)

type Decision = Literal["keep", "delete_clause", "positive_rewrite"]

DECISIONS: frozenset[str] = frozenset({"keep", "delete_clause", "positive_rewrite"})

# The scan instrument from writing-for-agents section 5. It finds negations, it does not
# judge them: every match still needs a semantic decision.
SCANNER_RE = re.compile(r"\b(?:no|not|never|without|nothing)\b", re.IGNORECASE)

# Tier 1: the negation names a system decision, so deleting it loses a rule.
CONTRACT_BOUNDARY_PHRASES: tuple[str, ...] = (
    "writes nothing",
    "never served",
    "is not capped",
    "when you will not edit",
    "no anchors",
)

# Tier 3, delete shape: the negation hangs off a positive clause or restates a bounded state.
_APPENDED_NEGATION_RE = re.compile(r",\s+(?:never|no|not|without|nothing)\b", re.IGNORECASE)
_EXISTENTIAL_NEGATION_RE = re.compile(r"\b(?:there|it)\s+(?:is|are)\s+no\b", re.IGNORECASE)
# Tier 3, rewrite shape: the negation is the whole predicate, so nothing positive survives.
_PREDICATE_NEGATION_RE = re.compile(
    r"\b(?:is|are|was|were|does|do|did|has|have)\s+not\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Fragment:
    """One fixture fragment with its recorded audit decision."""

    id: str
    text: str
    classification: str
    decision: str
    reason: str
    positive_form: str | None = None


def contract_boundary_phrase(text: str) -> str | None:
    """Return the Tier 1 phrase carried by ``text``, or None when no phrase matches."""
    lowered = text.lower()
    for phrase in CONTRACT_BOUNDARY_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def classify_text(text: str) -> Decision:
    """Classify one fragment by the 3-tier rubric, using the fragment text alone."""
    if contract_boundary_phrase(text) is not None:
        return "keep"
    if SCANNER_RE.search(text) is None:
        raise AssertionError(f"fragment carries no negation to audit: {text!r}")
    if _APPENDED_NEGATION_RE.search(text) is not None:
        return "delete_clause"
    if _EXISTENTIAL_NEGATION_RE.search(text) is not None:
        return "delete_clause"
    if _PREDICATE_NEGATION_RE.search(text) is not None:
        return "positive_rewrite"
    raise AssertionError(f"negation matches no tier: {text!r}")


def classify_fragment(text: str, classification: str) -> Decision:
    """Classify a fragment and reject a recorded classification that contradicts the text."""
    decision = classify_text(text)
    labelled_boundary = classification == "contract_boundary"
    if labelled_boundary != (decision == "keep"):
        raise AssertionError(f"recorded classification {classification!r} contradicts {text!r}")
    return decision


def _require_string(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"fixture field {key!r} must be a non-empty string")
    return value


def _load_raw() -> dict[str, object]:
    loaded: object = yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise AssertionError(f"fixture must be a mapping: {FIXTURE_PATH}")
    return cast("dict[str, object]", loaded)


def _load_fragments() -> list[Fragment]:
    entries = _load_raw().get("fragments")
    if not isinstance(entries, list):
        raise AssertionError("fixture must carry a 'fragments' list")
    fragments: list[Fragment] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise AssertionError("every fixture fragment must be a mapping")
        mapping = cast("dict[str, object]", entry)
        positive_form = mapping.get("positive_form")
        fragments.append(
            Fragment(
                id=_require_string(mapping, "id"),
                text=_require_string(mapping, "text"),
                classification=_require_string(mapping, "classification"),
                decision=_require_string(mapping, "decision"),
                reason=_require_string(mapping, "reason"),
                positive_form=positive_form if isinstance(positive_form, str) else None,
            )
        )
    return fragments


FRAGMENTS: list[Fragment] = _load_fragments()


def test_fixture_declares_version_one_and_a_description() -> None:
    raw = _load_raw()
    assert raw.get("version") == 1
    description = raw.get("description")
    assert isinstance(description, str)
    assert description.strip()


def test_fixture_holds_five_redundant_and_six_boundary_fragments() -> None:
    redundant = [fragment for fragment in FRAGMENTS if fragment.classification == "redundant"]
    boundary = [
        fragment for fragment in FRAGMENTS if fragment.classification == "contract_boundary"
    ]
    assert len(redundant) == 5
    assert len(boundary) == 6
    assert len(FRAGMENTS) == 11


def test_every_fragment_carries_the_audit_fields() -> None:
    for fragment in FRAGMENTS:
        assert fragment.id.strip(), "id must be non-empty"
        assert fragment.text.strip(), f"{fragment.id}: text must be non-empty"
        assert fragment.classification in {"redundant", "contract_boundary"}, fragment.id
        assert fragment.decision in DECISIONS, fragment.id
        assert fragment.reason.strip(), f"{fragment.id}: reason must be non-empty"


def test_fragment_ids_are_unique() -> None:
    ids = [fragment.id for fragment in FRAGMENTS]
    assert len(ids) == len(set(ids))


def test_ids_cover_the_ticket_fragment_sets() -> None:
    ids = {fragment.id for fragment in FRAGMENTS}
    assert {f"REDUNDANT-{number}" for number in range(1, 6)} <= ids
    assert {f"BOUNDARY-{number}" for number in range(1, 7)} <= ids


@pytest.mark.parametrize("fragment", FRAGMENTS, ids=[fragment.id for fragment in FRAGMENTS])
def test_classifier_agrees_with_every_recorded_decision(fragment: Fragment) -> None:
    assert classify_fragment(fragment.text, fragment.classification) == fragment.decision


def test_boundary_fragments_all_match_a_tier_one_phrase() -> None:
    for fragment in FRAGMENTS:
        if fragment.classification != "contract_boundary":
            continue
        assert contract_boundary_phrase(fragment.text) is not None, fragment.id


def test_scanner_flags_the_header_exclusion_as_redundant() -> None:
    control = "The header states the range. There is no footer."
    assert SCANNER_RE.search(control) is not None
    assert classify_text(control) == "delete_clause"


def test_scanner_flags_the_embedded_directory_negation() -> None:
    control = "file is the text file, never a directory."
    assert SCANNER_RE.search(control) is not None
    assert classify_text(control) == "delete_clause"


def test_contract_boundary_phrases_are_preserved() -> None:
    for phrase in ("writes nothing", "never served"):
        assert contract_boundary_phrase(phrase) == phrase
        assert classify_text(phrase) == "keep"


def test_every_ticket_boundary_phrase_maps_to_keep() -> None:
    for phrase in CONTRACT_BOUNDARY_PHRASES:
        assert classify_fragment(phrase, "contract_boundary") == "keep"


def test_predicate_negation_is_rewritten_not_deleted() -> None:
    assert classify_text("The refusal is not a blind retry.") == "positive_rewrite"


def test_mislabelled_fragment_is_rejected() -> None:
    with pytest.raises(AssertionError):
        _ = classify_fragment("never served", "redundant")


def test_no_count_only_gate() -> None:
    decisions = {
        fragment.id: classify_fragment(fragment.text, fragment.classification)
        for fragment in FRAGMENTS
    }
    assert set(decisions) == {fragment.id for fragment in FRAGMENTS}
    for fragment in FRAGMENTS:
        assert fragment.decision in DECISIONS, fragment.id
        assert fragment.reason.strip(), fragment.id
        assert decisions[fragment.id] == fragment.decision, fragment.id
    assert len(decisions) == len(FRAGMENTS)
    # Per-fragment decisions, not one tally: several fragments share a decision yet each
    # keeps its own entry, so a count can never stand in for the verdict.
    assert len(decisions) > len(set(decisions.values()))
