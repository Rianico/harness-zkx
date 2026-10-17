r"""Bind the evidence module's own character class: hrg-t1 gave it a private copy (#264).

`_normalize` rewrites `_` to a space as markdown decoration BEFORE splitting on
`_NON_ALNUM_RE`, so no input can distinguish `[^a-z0-9]+` from `[^a-z0-9_]+` — that
mutant is equivalent and unkillable at any surface, and `test_underscore_is_masked_as_
decoration` documents the masking instead of pretending to bind the class. The killable
variants each need the character that survives the decoration pass: `.` for
`[^a-z0-9.]+`, `-` for `[^a-z0-9_-]+`, and a non-ASCII letter for `\W+` (word-class
Unicode stays, the current class splits it). Together with
`test_reply_record_id_slugs_underscore_and_dot_senders` in `test_herdr_reply.py` (where
`_slug` has no decoration pass and every variant is killable) both regex copies are
bound; neither is pinned to the other — the two uses are separate concerns.
"""

from __future__ import annotations

import herdr_evidence

_HEADING_BODY = "gates green\n"


def _label_of(title: str) -> str:
    heading = herdr_evidence.evidence_section(f"COMPLETED\n\n## {title}\n{_HEADING_BODY}")
    assert heading == title
    label = herdr_evidence.evidence_label(heading)
    assert label is not None
    return label


def test_evidence_label_splits_dot_heading_words() -> None:
    """`## Log.results` splits on the dot, so the label is `logs results`.

    Killed by: `[^a-z0-9.]+` (keeps `.` in a word → single stem label `logs`).
    """
    assert _label_of("Log.results") == "logs results"


def test_evidence_label_splits_hyphen_heading_words() -> None:
    """`## Log-gate` splits on the hyphen, so the label is `logs gate`.

    Killed by: `[^a-z0-9_-]+` (keeps `-` in a word → single stem label `logs`).
    """
    assert _label_of("Log-gate") == "logs gate"


def test_evidence_label_splits_non_ascii_heading_words() -> None:
    r"""`## Log验证results` splits around the CJK letter, so the label is `logs results`.

    Killed by: `\W+` (CJK counts as a word character, the word stays glued → single
    stem label `logs`).
    """
    assert _label_of("Log验证results") == "logs results"


def test_underscore_is_masked_as_decoration() -> None:
    """`## Log_results` labels `logs results` because `_` is stripped as decoration first.

    This documents why the `[^a-z0-9_]+` mutant of `_NON_ALNUM_RE` is equivalent and
    unkillable: `_` never reaches the split. It does NOT bind the class.
    """
    assert _label_of("Log_results") == "logs results"
