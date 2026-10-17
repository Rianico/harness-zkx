"""Tests for skills/herdr/scripts/herdr_label.py (herdr-label helper)."""

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

import herdr_cli
import herdr_label
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_label.py"

PANE_ENV = {
    "HERDR_PANE_ID": "w9:p1",
    "HERDR_TAB_ID": "w9:t1",
    "HERDR_WORKSPACE_ID": "w9",
}

# w9:p1 hosts the agent `reviewer`; w9:p2 is a plain shell pane.
SECOND_AGENT = {"pane_id": "w9:p9", "name": "buildbot", "agent": "pi", "agent_status": "idle"}

# A state where w9:p2 hosts a live agent, so --task-group can prove both names move.
P2_AGENT_STATE = {
    **DEFAULT_STATE,
    "agents": [{"pane_id": "w9:p2", "name": "reviewer", "agent": "pi", "agent_status": "idle"}],
}


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def renames(stub: StubHarness) -> list[list[str]]:
    return [call[1:] for call in stub.calls() if call[2] == "rename"]


def shell_pane_state(**overrides: object) -> dict[str, object]:
    return {**DEFAULT_STATE, "current": "w9:p2", "agents": [], **overrides}


# ── unit ────────────────────────────────────────────────────────────────────────────


def test_conflict_with_finds_the_other_pane() -> None:
    agents = [
        {"pane_id": "w9:p1", "name": "reviewer"},
        {"pane_id": "w9:p9", "name": "buildbot"},
    ]
    assert herdr_label.conflict_with(agents, "buildbot", "w9:p1") == "w9:p9"


@pytest.mark.parametrize("name", ["reviewer", "unused"])
def test_conflict_with_ignores_self_and_free_names(name: str) -> None:
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.conflict_with(agents, name, "w9:p1") is None


# ── integration: the happy path ─────────────────────────────────────────────────────


def test_names_the_label_and_the_agent(stub: StubHarness) -> None:
    done = stub.run("buildbot", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p1  label=buildbot  agent=buildbot"
    assert renames(stub) == [
        ["pane", "rename", "w9:p1", "buildbot"],
        ["agent", "rename", "w9:p1", "buildbot"],
    ]


def test_json_reports_both_names(stub: StubHarness) -> None:
    done = stub.run("buildbot", "--json", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert json.loads(done.stdout) == {
        "pane_id": "w9:p1",
        "label": "buildbot",
        "agent": "buildbot",
    }


def test_label_only_leaves_the_agent_name_alone(stub: StubHarness) -> None:
    done = stub.run("review pane", "--label-only", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p1  label=review pane  agent=-"
    assert renames(stub) == [["pane", "rename", "w9:p1", "review pane"]]


def test_a_pane_without_an_agent_is_only_labelled(stub: StubHarness) -> None:
    done = stub.run("scratch-pad", env=PANE_ENV, state=shell_pane_state())
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p2  label=scratch-pad  agent=-"
    assert renames(stub) == [["pane", "rename", "w9:p2", "scratch-pad"]]


def test_a_multi_word_label_is_allowed_without_an_agent(stub: StubHarness) -> None:
    done = stub.run("review pane", env=PANE_ENV, state=shell_pane_state())
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "label=review pane" in done.stdout


def test_clear_drops_both_names(stub: StubHarness) -> None:
    done = stub.run("--clear", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "cleared w9:p1  label=-  agent=-"
    assert renames(stub) == [
        ["pane", "rename", "w9:p1", "--clear"],
        ["agent", "rename", "w9:p1", "--clear"],
    ]


# ── unit: the label/agent-name pair ────────────────────────────────────────────


def test_pairs_reports_only_panes_hosting_an_agent() -> None:
    panes = [
        {"pane_id": "w9:p1", "label": "reviewer"},
        {"pane_id": "w9:p2", "label": "scratch-pad"},
    ]
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.pairs(panes, agents) == [("w9:p1", "reviewer", "reviewer")]


def test_a_label_left_by_a_departed_agent_is_not_a_mismatch() -> None:
    panes = [{"pane_id": "w9:p2", "label": "pr-orchestrator"}]
    assert herdr_label.pair_mismatches(panes, []) == []


def test_pair_mismatches_finds_a_stale_label_on_a_recovered_pane() -> None:
    panes = [{"pane_id": "w9:p2", "label": "pr-orchestrator"}]
    agents = [{"pane_id": "w9:p2", "name": "buildbot"}]
    assert herdr_label.pair_mismatches(panes, agents) == [("w9:p2", "pr-orchestrator", "buildbot")]


def test_pair_mismatches_finds_a_missing_label() -> None:
    panes = [{"pane_id": "w9:p2"}]
    agents = [{"pane_id": "w9:p2", "name": "buildbot"}]
    assert herdr_label.pair_mismatches(panes, agents) == [("w9:p2", None, "buildbot")]


def test_a_descriptive_label_is_reported_not_reconciled() -> None:
    panes = [{"pane_id": "w9:p2", "label": "review pane"}]
    agents = [{"pane_id": "w9:p2", "name": "buildbot"}]
    assert herdr_label.pair_mismatches(panes, agents) == []
    assert herdr_label.descriptive_labels(panes, agents) == [("w9:p2", "review pane", "buildbot")]


def test_a_recovered_pane_can_take_its_name_back_from_the_label() -> None:
    panes = [{"pane_id": "w9:p2", "label": "pr-orchestrator"}]
    agents = [{"pane_id": "w9:p2", "agent": "agy"}]
    assert herdr_label.unnamed_agents(panes, agents) == [("w9:p2", "pr-orchestrator")]
    assert herdr_label.restorable_agents(panes, agents) == [("w9:p2", "pr-orchestrator")]


def test_a_label_already_used_by_another_agent_is_not_restorable() -> None:
    panes = [{"pane_id": "w9:p2", "label": "pr-orchestrator"}]
    agents = [
        {"pane_id": "w9:p2", "agent": "agy"},
        {"pane_id": "w9:p9", "name": "pr-orchestrator", "agent": "pi"},
    ]
    assert herdr_label.restorable_agents(panes, agents) == []


def test_a_descriptive_label_cannot_restore_a_name() -> None:
    panes = [{"pane_id": "w9:p2", "label": "review pane"}]
    agents = [{"pane_id": "w9:p2", "agent": "agy"}]
    assert herdr_label.restorable_agents(panes, agents) == []


# ── unit: a label that outlived its agent (#234) ───────────────────────────────


def test_stale_labels_reports_a_label_whose_agent_has_exited() -> None:
    """An agent-shaped label on a pane with no live agent is stale.

    Pin -> mutant: build the rows from the *agent* inventory (the #234 defect that
    `pairs`/`pair_mismatches` share), so the exited pane is invisible and this returns [].
    """
    panes = [
        {"pane_id": "w9:p1", "label": "reviewer"},
        {"pane_id": "w9:p2", "label": "buildbot"},
    ]
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.stale_labels(panes, agents) == [("w9:p2", "buildbot")]


def test_stale_labels_never_flags_a_live_agent_that_owns_its_label() -> None:
    """A live label matching its live agent is never stale (no false positives).

    Pin -> mutant: drop the `pane_id not in live_panes` filter, so the live `w9:p1` row
    is reported too and this returns a non-empty list.
    """
    panes = [
        {"pane_id": "w9:p1", "label": "reviewer"},
        {"pane_id": "w9:p2", "label": "scratch pad"},
    ]
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.stale_labels(panes, agents) == []


def test_stale_labels_dedupes_a_repeated_pane_row() -> None:
    """`pane list` may repeat a pane id; the same orphan is reported once, not twice.

    Pin -> mutant: drop the dedupe, so both rows append and this returns the pair twice.
    """
    panes = [
        {"pane_id": "w9:p2", "label": "buildbot"},
        {"pane_id": "w9:p2", "label": "buildbot"},
    ]
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.stale_labels(panes, agents) == [("w9:p2", "buildbot")]


def test_stale_labels_keeps_a_label_that_matches_a_live_agent_name() -> None:
    """An `agent list` row without `pane_id` still names a live agent, so its label is not stale.

    Pin -> mutant: drop the label-in-live-names check, so the pane whose label matches a live
    agent is reported stale although that agent is alive (violates required behaviour 4).
    """
    panes = [{"pane_id": "w9:p2", "label": "reviewer"}]
    agents = [{"name": "reviewer"}]
    assert herdr_label.stale_labels(panes, agents) == []


def test_stale_labels_reports_an_orphan_whose_name_is_live_on_another_pane() -> None:
    """A pane whose occupant has exited is stale even when its label names a live sibling.

    The agent inventory positively places `reviewer` on `w9:p1`, so the name-match must not
    excuse `w9:p2`, which no live agent occupies (required behaviour 1).

    Pin -> mutant: build the name-match from every agent row (`label in live_names`), so the
    live name on another pane suppresses this orphan and this returns [].
    """
    panes = [{"pane_id": "w9:p2", "label": "reviewer"}]
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.stale_labels(panes, agents) == [("w9:p2", "reviewer")]


def test_stale_labels_keeps_a_label_on_a_pane_that_hosts_a_live_agent() -> None:
    """An agent-shaped label on a pane that hosts a live agent is drift, never an orphan.

    `w9:p1` hosts the live `reviewer` but carries the label `buildbot`: a live agent owns the
    pane, so the label is a label/agent mismatch for `--verify`/`--sync`, not a stale label.

    Pin -> mutant: drop the `pane in live_panes` filter, so this occupied pane is reported
    stale and this returns a non-empty list.
    """
    panes = [{"pane_id": "w9:p1", "label": "buildbot"}]
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.stale_labels(panes, agents) == []


def test_stale_labels_ignores_a_descriptive_label_with_no_agent() -> None:
    """A multi-word `--label-only` label is decoration, never a dead agent name."""
    panes = [{"pane_id": "w9:p2", "label": "review pane"}]
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.stale_labels(panes, agents) == []


@pytest.mark.parametrize(
    ("panes", "agents"),
    [
        (None, [{"pane_id": "w9:p1", "name": "reviewer"}]),
        ([{"pane_id": "w9:p2", "label": "buildbot"}], None),
        ([], [{"pane_id": "w9:p1", "name": "reviewer"}]),
        ([{"pane_id": "w9:p2", "label": "buildbot"}], []),
    ],
)
def test_stale_labels_reports_nothing_without_evidence(
    panes: list[dict[str, str]] | None, agents: list[dict[str, str]] | None
) -> None:
    """#210 precedent: an unreadable or empty inventory answers nothing, so nothing is stale.

    Pin -> mutant: remove the `if not panes or not agents` guard, so an empty `agents`
    inventory leaves `live_panes` empty and every agent-shaped label is declared stale.
    """
    assert herdr_label.stale_labels(panes, agents) == []


# ── unit: ID-anchored self-healing reconciliation (#182 t2, ADR-0020) ────────────

# The healthy lane: tab titled by the group, orchestrator pane named by the composed slug,
# worker pane holding its own name. Every reconciliation test below drifts ONE row of this.
LANE_PANES: list[dict[str, str]] = [
    {"pane_id": "w9:p1", "tab_id": "w9:t1", "label": "harness-orch"},
    {"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"},
]
LANE_AGENTS: list[dict[str, object]] = [
    {"pane_id": "w9:p1", "name": "harness-orch", "agent": "pi"},
    {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
]
LANE_TABS = {"w9:t1": "harness"}


def plan(
    panes: list[dict[str, str]],
    agents: list[dict[str, object]],
    tabs: Mapping[str, str | None],
    *,
    task_group: str | None = "harness",
    lane_tab_id: str | None = "w9:t1",
) -> tuple[list[list[str]], list[str]]:
    return herdr_label.reconciliation_argv(
        "herdr",
        panes,
        agents,
        tabs,
        lane_tab_id=lane_tab_id,
        orchestrator_pane_id="w9:p1",
        task_group=task_group,
    )


def test_a_correct_lane_reconciles_to_the_empty_plan() -> None:
    """No-op is the central invariant: what is already right earns no rename.

    Pin -> mutant: rename unconditionally (drop the drift comparisons), so this lane —
    title, orchestrator, worker all correct — still emits argv.
    """
    assert plan(LANE_PANES, LANE_AGENTS, LANE_TABS) == ([], [])


def test_a_generic_tab_title_is_renamed_on_its_physical_id() -> None:
    """Tab `w9:t1` showing `3` gets exactly one `tab rename`, anchored on the tab id."""
    panes, agents, tabs = LANE_PANES, LANE_AGENTS, {"w9:t1": "3"}
    argv, notes = plan(panes, agents, tabs)
    assert notes == []
    assert argv == [["herdr", "tab", "rename", "w9:t1", "harness"]]


def test_a_drifted_tab_title_is_renamed_too() -> None:
    """Drift (a foreign title, not just a generic one) is the same defect: rename to the slug."""
    panes, agents, tabs = LANE_PANES, LANE_AGENTS, {"w9:t1": "other-lane"}
    argv, _ = plan(panes, agents, tabs)
    assert argv == [["herdr", "tab", "rename", "w9:t1", "harness"]]


def test_a_dropped_agent_name_takes_the_agent_rename_and_the_pane_rename() -> None:
    """ADR-0020 names BOTH commands: the surviving label re-names the agent and re-marks the pane.

    Pin -> mutant: issue only one of the pair, so the pane border and the addressable name
    disagree again the moment this runs.
    """
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "name": "harness-orch", "agent": "pi"},
        {"pane_id": "w9:p3", "agent": "pi"},
    ]
    argv, notes = plan(LANE_PANES, agents, LANE_TABS)
    assert notes == []
    assert argv == [
        ["herdr", "agent", "rename", "w9:p3", "worker-1"],
        ["herdr", "pane", "rename", "w9:p3", "worker-1"],
    ]


def test_the_dropped_orchestrator_is_named_by_its_lane_exactly_once() -> None:
    """The nameless orchestrator pane is NOT also restored from its label: one rename, to `-orch`.

    Pin -> mutant: let case 1 claim the orchestrator pane, so the pane is renamed twice and
    takes a stale label instead of the composed `<task_group>-orch`.
    """
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    argv, notes = plan(LANE_PANES, agents, LANE_TABS)
    assert notes == []
    assert argv == [["herdr", "agent", "rename", "w9:p1", "harness-orch"]]


def test_an_ungrammatical_task_group_is_skipped_with_one_note() -> None:
    """A slug that breaks the grammar never reaches herdr — as tab title nor as `-orch` name —
    and the one skipped decision prints exactly one note.

    Pin -> mutant: pass the slug through unchecked, so `herdr tab rename w9:t1 'Bad Slug'`
    is issued and herdr refuses it mid-run.
    """
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "name": "harness-orch", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    argv, notes = plan(LANE_PANES, agents, {"w9:t1": "3"}, task_group="Bad Slug")
    assert argv == []
    assert len(notes) == 1
    assert "left the tab title and the orchestrator name alone" in notes[0]


def test_the_composed_name_is_fitted_not_just_validated() -> None:
    """A legal 32-char slug oversizes at `-orch`: the plan FITS it, and says nothing (#182 h1).

    Pin -> mutant: pass `task_group` through to `composed` un-truncated, so `<32 chars>-orch`
    (37) reaches herdr and is refused there; the pinned argv carries only the fitted name, so
    assert it is `<= AGENT_NAME_MAX` and grammar-valid, and forward without truncation and this
    sees the oversized argv (or a skip note) instead.
    """
    slug = "g" * 32
    fitted = herdr_label.fit_slug(slug, herdr_label.ORCHESTRATOR_SLUG_BUDGET)
    title = herdr_label.fit_slug(slug, herdr_label.TAB_TITLE_BUDGET)
    composed = f"{fitted}{herdr_label.ORCHESTRATOR_SUFFIX}"
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    panes: list[dict[str, str]] = [{"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"}]
    argv, notes = plan(panes, agents, {"w9:t1": "3"}, task_group=slug)
    assert notes == []
    assert argv == [
        ["herdr", "tab", "rename", "w9:t1", title],
        ["herdr", "agent", "rename", "w9:p1", composed],
    ]
    assert len(composed) <= herdr_label.AGENT_NAME_MAX
    assert herdr_label.AGENT_NAME.match(composed)


@pytest.mark.parametrize("length", [33, 35])
def test_an_overlong_slug_fits_the_name_with_no_note(length: int) -> None:
    """Beyond the cap itself the shape is unchanged: fit, rename, silence — never skip (#182 h1).

    Pin -> mutant: validate BEFORE truncating, so the over-long slug trips the gate first and
    this sees a skip note and no renames.
    """
    slug = "g" * length
    fitted = herdr_label.fit_slug(slug, herdr_label.ORCHESTRATOR_SLUG_BUDGET)
    title = herdr_label.fit_slug(slug, herdr_label.TAB_TITLE_BUDGET)
    composed = f"{fitted}{herdr_label.ORCHESTRATOR_SUFFIX}"
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    panes: list[dict[str, str]] = [{"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"}]
    argv, notes = plan(panes, agents, {"w9:t1": "3"}, task_group=slug)
    assert notes == []
    assert argv == [
        ["herdr", "tab", "rename", "w9:t1", title],
        ["herdr", "agent", "rename", "w9:p1", composed],
    ]


def test_a_sixty_four_char_slug_fits_to_exactly_the_grammar_cap() -> None:
    """The fitted composed name lands on 32 chars exactly, and the 64-char slug never survives.

    Pin -> mutant: budget the ticket's illustrative 26 rather than the derived
    `AGENT_NAME_MAX - len(ORCHESTRATOR_SUFFIX)`, so the composed name is 31 and this sees a
    name that leaves the cap unspent — and any lane built to the real cap stops converging.
    """
    slug = "g" * 64
    fitted = herdr_label.fit_slug(slug, herdr_label.ORCHESTRATOR_SLUG_BUDGET)
    title = herdr_label.fit_slug(slug, herdr_label.TAB_TITLE_BUDGET)
    composed = f"{fitted}{herdr_label.ORCHESTRATOR_SUFFIX}"
    assert len(composed) == herdr_label.AGENT_NAME_MAX
    assert herdr_label.AGENT_NAME.match(composed)
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    panes: list[dict[str, str]] = [{"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"}]
    argv, notes = plan(panes, agents, {"w9:t1": "3"}, task_group=slug)
    assert notes == []
    assert argv == [
        ["herdr", "tab", "rename", "w9:t1", title],
        ["herdr", "agent", "rename", "w9:p1", composed],
    ]


def test_the_fitted_rename_never_lets_case_one_name_the_orchestrator_twice() -> None:
    """`orchestrator_regained` guards on the FITTED composed name, so one rename, never two.

    Pin -> mutant: compute `orchestrator_regained` from the unfitted `<35 chars>-orch` (40), so
    the guard reads false, case 1 claims the orchestrator from its stale label, and the pane is
    renamed twice — once by the label, once by the fitted name.
    """
    slug = "g" * 35
    fitted = herdr_label.fit_slug(slug, herdr_label.ORCHESTRATOR_SLUG_BUDGET)
    title = herdr_label.fit_slug(slug, herdr_label.TAB_TITLE_BUDGET)
    composed = f"{fitted}{herdr_label.ORCHESTRATOR_SUFFIX}"
    panes: list[dict[str, str]] = [
        {"pane_id": "w9:p1", "tab_id": "w9:t1", "label": "old-reviewer"},
        {"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"},
    ]
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    argv, notes = plan(panes, agents, {"w9:t1": title}, task_group=slug)
    assert notes == []
    assert argv == [["herdr", "agent", "rename", "w9:p1", composed]]


def test_a_fitted_name_already_used_by_another_pane_is_not_handed_to_herdr() -> None:
    """The collision gate applies to the fitted name exactly as to any other (#182 h1).

    Pin -> mutant: drop the `conflict_with` gate, so the plan renames the orchestrator to a
    name a live sibling already holds and herdr refuses the duplicate.
    """
    slug = "g" * 35
    fitted = herdr_label.fit_slug(slug, herdr_label.ORCHESTRATOR_SLUG_BUDGET)
    title = herdr_label.fit_slug(slug, herdr_label.TAB_TITLE_BUDGET)
    composed = f"{fitted}{herdr_label.ORCHESTRATOR_SUFFIX}"
    panes: list[dict[str, str]] = [{"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"}]
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
        {"pane_id": "w9:p9", "name": composed, "agent": "pi"},
    ]
    argv, notes = plan(panes, agents, {"w9:t1": title}, task_group=slug)
    assert argv == []
    assert len(notes) == 1
    assert "already used by pane w9:p9" in notes[0]


# Two real lane slugs that share their whole human-readable stem: plain truncation fit both
# to `refactor-herdr-coordination` and both orchestrators composed the SAME `-orch` name, so
# `conflict_with` refused the second lane on every pass and its note printed forever.
LANE_ONE_SLUG = "refactor-herdr-coordination-hardening-lane-one"
LANE_TWO_SLUG = "refactor-herdr-coordination-hardening-lane-two"


def test_two_co_prefixed_lanes_fit_to_distinct_orchestrator_names() -> None:
    """A ≥27-char shared prefix no longer fits two lanes onto one `-orch` name.

    Pin -> mutant: revert `fit_slug` to plain `slug[:budget]`, so both slugs truncate to the
    same 27 chars, these composed names collide, and the second lane's rename is refused
    forever. Both halves stay grammar-valid and at the cap, so the disambiguation never buys
    its distinctness by breaking the grammar.
    """
    shared = 27
    assert LANE_ONE_SLUG[:shared] == LANE_TWO_SLUG[:shared]
    one = f"{herdr_label.fit_slug(LANE_ONE_SLUG, herdr_label.ORCHESTRATOR_SLUG_BUDGET)}{herdr_label.ORCHESTRATOR_SUFFIX}"
    two = f"{herdr_label.fit_slug(LANE_TWO_SLUG, herdr_label.ORCHESTRATOR_SLUG_BUDGET)}{herdr_label.ORCHESTRATOR_SUFFIX}"
    assert one != two
    for composed in (one, two):
        assert herdr_label.AGENT_NAME.match(composed)
        assert len(composed) <= herdr_label.AGENT_NAME_MAX
    assert len(one) == herdr_label.AGENT_NAME_MAX
    assert len(two) == herdr_label.AGENT_NAME_MAX


def test_the_fitted_digest_is_stable_across_repeats_and_a_fresh_process() -> None:
    """The same slug fits to the same string, in-process twice and in a fresh interpreter.

    This is what stops a lane's name churning between dispatches: a rename the lane converged
    on stays converged.

    Pin -> mutant: seed the digest with something that varies — `id(slug)`, so the id differs
    in the subprocess and the repeat mismatches; the current time, so even the in-process pair
    mismatches. Deterministic sha256 of the full slug answers both.
    """
    budget = herdr_label.ORCHESTRATOR_SLUG_BUDGET
    first = herdr_label.fit_slug(LANE_TWO_SLUG, budget)
    second = herdr_label.fit_slug(LANE_TWO_SLUG, budget)
    assert first == second
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); import herdr_label;"
        f"print(herdr_label.fit_slug(sys.argv[2], {budget}))"
    )
    done = subprocess.run(
        [sys.executable, "-c", code, str(SCRIPTS_DIR), LANE_TWO_SLUG],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == first


def test_a_short_slug_is_untouched_and_a_fitted_slug_keeps_its_stem_and_digest_shape() -> None:
    """A slug that fits comes back byte-identical; a fitted one keeps a readable stem.

    The 22-char stem before the `-` still carries the shared human-readable prefix, so the
    name stays recognisable, and the digest is exactly 4 lowercase hex — the shape the grammar
    gate tolerates.

    Pin -> mutants: widen the digest to 8 chars (or any non-hex padding) and the shape asserts
    here fail even though the length still lands inside the cap; run any digest at all on a
    short-enough slug and `fit_slug("harness", budget)` no longer comes back byte-identical,
    renaming every existing lane.
    """
    budget = herdr_label.ORCHESTRATOR_SLUG_BUDGET
    assert herdr_label.fit_slug("harness", budget) == "harness"
    assert herdr_label.fit_slug(LANE_TWO_SLUG, budget) != LANE_TWO_SLUG
    fitted = herdr_label.fit_slug(LANE_ONE_SLUG, budget)
    stem = LANE_ONE_SLUG[: budget - 5]
    assert fitted.startswith(stem)
    assert fitted[len(stem)] == "-"
    assert re.fullmatch(r"[0-9a-f]{4}", fitted[len(stem) + 1 :])
    assert len(fitted) == budget


def test_identical_full_slugs_still_collide_and_the_refusal_names_the_holding_pane() -> None:
    """Two lanes with the SAME full slug fit to the SAME name: digest cannot separate equals.

    `conflict_with` stays the last line of defence: the second rename is refused with one note
    naming the pane that already holds the name, never issued over a sibling.

    Pin -> mutant: seed the digest per call (pane id, random, time), so the two equal slugs fit
    apart and this plan hands herdr a rename that silently overwrites the sibling's claim.
    """
    budget = herdr_label.ORCHESTRATOR_SLUG_BUDGET
    fitted = herdr_label.fit_slug(LANE_ONE_SLUG, budget)
    assert herdr_label.fit_slug(LANE_ONE_SLUG, budget) == fitted
    composed = f"{fitted}{herdr_label.ORCHESTRATOR_SUFFIX}"
    title = herdr_label.fit_slug(LANE_ONE_SLUG, herdr_label.TAB_TITLE_BUDGET)
    panes: list[dict[str, str]] = [{"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"}]
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
        {"pane_id": "w9:p9", "name": composed, "agent": "pi"},
    ]
    argv, notes = plan(panes, agents, {"w9:t1": title}, task_group=LANE_ONE_SLUG)
    assert argv == []
    assert len(notes) == 1
    assert composed in notes[0]
    assert "already used by pane w9:p9" in notes[0]


def test_truncation_fixes_length_never_the_characters() -> None:
    """An over-long slug whose prefix the grammar forbids is still skipped: one note, zero argv.

    Pin -> mutant: let fitting stand in for the character-class guard (validate length only, or
    sanitize instead of truncate), and this 40-char slug with a capital start emits renames.
    """
    slug = "Bad" + "x" * 37
    assert len(slug) > herdr_label.ORCHESTRATOR_SLUG_BUDGET
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "name": "harness-orch", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    argv, notes = plan(LANE_PANES, agents, {"w9:t1": "3"}, task_group=slug)
    assert argv == []
    assert len(notes) == 1
    assert "left the tab title and the orchestrator name alone" in notes[0]


def test_the_slug_budget_is_derived_from_the_grammar_and_the_suffix() -> None:
    """Budget = cap - suffix, computed: the ticket's illustrative 26 is pinned out (#182 h1).

    Pin -> mutant: hard-code 26 (or 27) in place of the derivation, so the budget drifts the
    moment the pattern or the suffix changes and the longest fitted name no longer lands on
    `AGENT_NAME_MAX`.
    """
    assert herdr_label.ORCHESTRATOR_SLUG_BUDGET == (
        herdr_label.AGENT_NAME_MAX - len(herdr_label.ORCHESTRATOR_SUFFIX)
    )
    assert herdr_label.AGENT_NAME.match("g" * herdr_label.AGENT_NAME_MAX)
    assert not herdr_label.AGENT_NAME.match("g" * (herdr_label.AGENT_NAME_MAX + 1))
    longest_composed = f"{herdr_label.fit_slug('g' * 64, herdr_label.ORCHESTRATOR_SLUG_BUDGET)}{herdr_label.ORCHESTRATOR_SUFFIX}"
    assert len(longest_composed) == herdr_label.AGENT_NAME_MAX
    assert herdr_label.fit_slug("harness", herdr_label.ORCHESTRATOR_SLUG_BUDGET) == "harness"


def test_the_tab_title_keeps_a_legal_slug_the_name_budget_would_cut() -> None:
    """Two budgets, not one: a 30-char slug is a legal TAB TITLE even though its name must fit.

    Pin -> mutant: share `ORCHESTRATOR_SLUG_BUDGET` across both halves, and this lane's title is
    silently truncated to 27 characters — a title no record carries, renamed away from a slug
    that needed no fitting at all.
    """
    slug = "g" * 30
    composed = (
        f"{herdr_label.fit_slug(slug, herdr_label.ORCHESTRATOR_SLUG_BUDGET)}"
        f"{herdr_label.ORCHESTRATOR_SUFFIX}"
    )
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    panes: list[dict[str, str]] = [{"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"}]
    argv, notes = plan(panes, agents, {"w9:t1": "3"}, task_group=slug)
    assert notes == []
    assert argv == [
        ["herdr", "tab", "rename", "w9:t1", slug],
        ["herdr", "agent", "rename", "w9:p1", composed],
    ]
    assert herdr_label.AGENT_NAME.match(slug)


def test_a_fitted_lane_converges_so_the_next_pass_renames_nothing() -> None:
    """The central invariant survives fitting: compare and rename carry the SAME fitted value.

    Pin -> mutant: rename the tab to `fitted` while comparing against the full slug, so this
    converged lane never compares equal and a rename is re-issued on every dispatch and reply.
    """
    slug = "g" * 35
    fitted = herdr_label.fit_slug(slug, herdr_label.ORCHESTRATOR_SLUG_BUDGET)
    title = herdr_label.fit_slug(slug, herdr_label.TAB_TITLE_BUDGET)
    composed = f"{fitted}{herdr_label.ORCHESTRATOR_SUFFIX}"
    panes: list[dict[str, str]] = [
        {"pane_id": "w9:p1", "tab_id": "w9:t1", "label": composed},
        {"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"},
    ]
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "name": composed, "agent": "pi"},
        {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi"},
    ]
    tabs = {"w9:t1": title}
    assert plan(panes, agents, tabs, task_group=slug) == ([], [])
    assert plan(panes, agents, tabs, task_group=slug) == ([], [])


def test_no_task_group_leaves_the_tab_and_orchestrator_silent_but_heals_workers() -> None:
    """The caller that derived no slug plans worker repairs only, and says nothing itself."""
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "name": "harness-orch", "agent": "pi"},
        {"pane_id": "w9:p3", "agent": "pi"},
    ]
    argv, notes = plan(LANE_PANES, agents, {"w9:t1": "3"}, task_group=None)
    assert notes == []
    assert argv == [
        ["herdr", "agent", "rename", "w9:p3", "worker-1"],
        ["herdr", "pane", "rename", "w9:p3", "worker-1"],
    ]


def test_a_name_from_another_lane_is_left_for_that_lane() -> None:
    """Reconciliation anchors on THIS lane's tab id; a nameless worker elsewhere is not touched."""
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "name": "harness-orch", "agent": "pi"},
        {"pane_id": "w9:p3", "agent": "pi"},
    ]
    panes: list[dict[str, str]] = [
        {"pane_id": "w9:p1", "tab_id": "w9:t1", "label": "harness-orch"},
        {"pane_id": "w9:p3", "tab_id": "w9:t2", "label": "worker-1"},
    ]
    argv, _ = plan(panes, agents, LANE_TABS)
    assert argv == []


def test_a_nameless_worker_with_no_tab_anchor_says_why_it_was_left_alone() -> None:
    """#182 t5 2.5d: an unknown lane tab id used to skip the worker half in total silence.

    Case 1 can only prove a nameless worker belongs to THIS lane through `tab_id`, so a snapshot
    that answers no tab id heals nothing. Before the note that was indistinguishable from the
    healthy lane's own empty plan — the pass said nothing while worker-name recovery could not
    fire at all. One note, and only when a candidate actually waits on the anchor.

    Pin -> mutants: drop the note and this sees the tab-title line alone; fire it without a
    candidate and `test_a_correct_lane_reconciles_to_the_empty_plan` gets a non-empty note list.
    """
    agents: list[dict[str, object]] = [
        {"pane_id": "w9:p1", "name": "harness-orch", "agent": "pi"},
        {"pane_id": "w9:p3", "agent": "pi"},
    ]
    anchorless: list[dict[str, str]] = [
        {"pane_id": "w9:p1", "label": "harness-orch"},
        {"pane_id": "w9:p3", "label": "worker-1"},
    ]
    argv, notes = plan(anchorless, agents, LANE_TABS, lane_tab_id=None)
    assert argv == []
    assert len(notes) == 2, notes
    worker_notes = [note for note in notes if "worker" in note]
    assert len(worker_notes) == 1, notes
    assert "tab" in worker_notes[0], "the note names the anchor that is missing"


def test_a_healthy_lane_with_no_tab_anchor_still_says_nothing_about_workers() -> None:
    """The note is evidence-led: no nameless worker means nothing was withheld from recovery.

    Pin -> mutant: append the note whenever `lane_tab_id is None`, ignoring the candidates, and
    every anchorless-but-healthy lane starts printing a worker line.
    """
    anchorless: list[dict[str, str]] = [
        {"pane_id": "w9:p1", "label": "harness-orch"},
        {"pane_id": "w9:p3", "label": "worker-1"},
    ]
    _argv, notes = plan(anchorless, LANE_AGENTS, LANE_TABS, lane_tab_id=None)
    assert [note for note in notes if "worker" in note] == []


# ── integration: reconcile_lane through the stub herdr ───────────────────────────


def test_reconcile_lane_dry_run_prints_the_plan_and_renames_nothing(
    stub: StubHarness, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--dry-run` prints the argv it WOULD issue and mutates nothing.

    Pin -> mutant: run the renames anyway under dry-run, so the stub log shows a tab rename.
    """
    drifted_tab = {
        **DEFAULT_STATE,
        "tabs": [{"tab_id": "w9:t1", "workspace_id": "w9", "label": "3"}],
    }
    stub.write_state(drifted_tab)
    issued = herdr_label.reconcile_lane(
        str(stub.herdr), stub.base_env(), task_group="harness", marker="herdr-label", dry_run=True
    )
    printed = json.loads(capsys.readouterr().out)
    assert printed == [[str(stub.herdr), "tab", "rename", "w9:t1", "harness"]]
    assert [call[1:] for call in issued] == [["tab", "rename", "w9:t1", "harness"]]
    assert renames(stub) == []


def test_reconcile_lane_fits_a_35_char_task_group_with_no_stderr_noise(
    stub: StubHarness, capsys: pytest.CaptureFixture[str]
) -> None:
    """The acceptance clause end to end: a 35-char group GETS a valid ≤32 name, silently.

    Pin -> mutant: keep the length skip, and this sees the "left the orchestrator name alone"
    line on stderr and no `agent rename` at all; fit but compare the tab against the full slug,
    and a second pass over the corrected lane renames again.
    """
    slug = "g" * 35
    fitted = herdr_label.fit_slug(slug, herdr_label.ORCHESTRATOR_SLUG_BUDGET)
    title = herdr_label.fit_slug(slug, herdr_label.TAB_TITLE_BUDGET)
    composed = f"{fitted}{herdr_label.ORCHESTRATOR_SUFFIX}"
    state = {
        **DEFAULT_STATE,
        "tabs": [{"tab_id": "w9:t1", "workspace_id": "w9", "label": "3"}],
        "agents": [{"pane_id": "w9:p1", "agent": "pi", "agent_status": "working"}],
        "panes": [
            {
                "pane_id": "w9:p1",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "working",
                "cwd": "/tmp/harness",
            }
        ],
    }
    stub.write_state(state)
    issued = herdr_label.reconcile_lane(
        str(stub.herdr), stub.base_env(), task_group=slug, marker="herdr-dispatch"
    )
    captured = capsys.readouterr()
    assert captured.err == ""
    assert [call[1:] for call in issued] == [
        ["tab", "rename", "w9:t1", title],
        ["agent", "rename", "w9:p1", composed],
    ]
    assert herdr_label.AGENT_NAME.match(composed)
    assert renames(stub) == [
        ["tab", "rename", "w9:t1", title],
        ["agent", "rename", "w9:p1", composed],
    ]


def test_reconcile_lane_keeps_going_when_one_rename_is_refused(
    stub: StubHarness, capsys: pytest.CaptureFixture[str]
) -> None:
    """A refused rename is one skipped step: one stderr line, and the later steps still run.

    Pin -> mutant: let `run_herdr_checked` raise out of the pass (or break the loop), so the
    whole caller aborts over one refused label.
    """
    state = {
        **DEFAULT_STATE,
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi"},
            {"pane_id": "w9:p3", "agent": "pi"},
        ],
        "panes": [
            {"pane_id": "w9:p1", "tab_id": "w9:t1", "label": "reviewer"},
            {"pane_id": "w9:p3", "tab_id": "w9:t1", "label": "worker-1"},
        ],
        "pane_rename_error_for": ["w9:p3"],
    }
    stub.write_state(state)
    issued = herdr_label.reconcile_lane(
        str(stub.herdr), stub.base_env(), task_group=None, marker="herdr-label"
    )
    captured = capsys.readouterr()
    assert [call[1:] for call in issued] == [["agent", "rename", "w9:p3", "worker-1"]]
    assert captured.err.count("herdr-label: rename skipped:") == 1
    assert renames(stub) == [
        ["agent", "rename", "w9:p3", "worker-1"],
        ["pane", "rename", "w9:p3", "worker-1"],
    ]


def test_reconcile_lane_says_once_when_the_caller_derived_no_slug(
    stub: StubHarness, capsys: pytest.CaptureFixture[str]
) -> None:
    """`missing_note` is the caller's sentence, printed once, and reconciles nothing else."""
    stub.write_state(DEFAULT_STATE)
    issued = herdr_label.reconcile_lane(
        str(stub.herdr),
        stub.base_env(),
        task_group=None,
        marker="herdr-reply",
        missing_note="no task group recorded for this lane",
    )
    captured = capsys.readouterr()
    assert issued == []
    assert captured.err == "herdr-reply: no task group recorded for this lane\n"
    assert renames(stub) == []


def test_reconcile_lane_skips_the_whole_pass_when_the_planner_raises(
    stub: StubHarness, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """#182 t5 2.3: the planner sits inside the guard, so its raise costs one line and nothing else.

    `reconciliation_argv` ran outside `reconcile_lane`'s `try`, so an exception escaping the
    planner — a row shape it cannot plan over — propagated straight into `herdr-dispatch` before
    `resolve_targets` and into `herdr-reply` before the delivery, aborting callers whose only
    promise for this pass is that it annotates the delivery.

    Pin -> mutant: move the planner call back outside the `try` and this raises TypeError with no
    stderr line at all; widen the guard so far that it also swallows the rename loop, and
    `test_reconcile_lane_keeps_going_when_one_rename_is_refused` loses its skipped line.
    """

    def boom(*args: object, **kwargs: object) -> None:
        raise TypeError("planner boom")

    stub.write_state(DEFAULT_STATE)
    _ = monkeypatch.setattr(herdr_label, "reconciliation_argv", boom)
    issued = herdr_label.reconcile_lane(
        str(stub.herdr), stub.base_env(), task_group="harness", marker="herdr-label"
    )
    captured = capsys.readouterr()
    assert issued == []
    assert captured.err == "herdr-label: reconciliation skipped: planner boom\n"
    assert captured.out == ""
    assert renames(stub) == []


def test_reconcile_lane_prints_the_missing_slug_note_once_when_the_planner_raises(
    stub: StubHarness, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The caller's own sentence stays behind the guard: a failed pass prints the skip line only.

    Pin -> mutant: keep printing `missing_note` before the planner call and this sees two lines,
    one of which claims a decision the pass never got to make.
    """

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("planner crashed")

    stub.write_state(DEFAULT_STATE)
    _ = monkeypatch.setattr(herdr_label, "reconciliation_argv", boom)
    issued = herdr_label.reconcile_lane(
        str(stub.herdr),
        stub.base_env(),
        task_group=None,
        marker="herdr-reply",
        missing_note="no task group recorded for this lane",
    )
    captured = capsys.readouterr()
    assert issued == []
    assert captured.err == "herdr-reply: reconciliation skipped: planner crashed\n"


# ── integration: convergence and unnamed agents ────────────────────────────────


def test_sync_names_an_agent_that_lost_its_name(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "panes": [{"pane_id": "w9:p1", "label": "reviewer"}],
        "agents": [{"pane_id": "w9:p1", "agent": "pi", "agent_status": "idle"}],
    }
    done = stub.run("--sync", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "renamed w9:p1  agent=- -> reviewer" in done.stdout
    assert renames(stub) == [["agent", "rename", "w9:p1", "reviewer"]]


def test_verify_reports_an_unnamed_agent_without_failing_the_gate(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "panes": [{"pane_id": "w9:p1", "label": "reviewer"}],
        "agents": [{"pane_id": "w9:p1", "agent": "pi", "agent_status": "idle"}],
    }
    done = stub.run("--verify", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "unnamed live agents (1): w9:p1" in done.stdout
    assert "run herdr-label --sync" in done.stdout

    as_json = stub.run("--verify", "--json", env=PANE_ENV, state=state)
    payload = json.loads(as_json.stdout)
    assert payload["in_sync"] is True
    assert payload["unnamed"] == [{"pane_id": "w9:p1", "label": "reviewer"}]
    assert payload["restorable"] == ["w9:p1"]


# ── integration: --verify ─────────────────────────────────────────────────────


def test_verify_passes_when_every_live_agent_owns_its_label(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "panes": [{"pane_id": "w9:p1", "label": "reviewer"}]}
    done = stub.run("--verify", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "labels in sync with agent names" in done.stdout
    assert renames(stub) == []


def test_verify_flags_a_live_agent_whose_pane_was_never_labelled(stub: StubHarness) -> None:
    done = stub.run("--verify", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_BLOCKED
    assert "w9:p1  label=-  agent=reviewer" in done.stdout


def test_verify_reports_a_stale_label_and_exits_blocked(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "panes": [{"pane_id": "w9:p1", "label": "buildbot"}]}
    done = stub.run("--verify", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_BLOCKED
    assert "w9:p1" in done.stdout
    assert "label=buildbot" in done.stdout
    assert "--sync" in done.stdout
    assert renames(stub) == []


def test_verify_json_reports_the_pair(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "panes": [{"pane_id": "w9:p1", "label": "buildbot"}]}
    done = stub.run("--verify", "--json", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_BLOCKED
    payload = json.loads(done.stdout)
    assert payload["in_sync"] is False
    assert payload["mismatches"] == [{"pane_id": "w9:p1", "label": "buildbot", "agent": "reviewer"}]


def test_verify_scopes_to_one_pane(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "panes": [
            {"pane_id": "w9:p1", "label": "stale-name"},
            {"pane_id": "w9:p9", "label": "buildbot"},
        ],
        "agents": [*DEFAULT_STATE["agents"], SECOND_AGENT],
    }
    scoped = stub.run("--verify", "--pane", "w9:p9", env=PANE_ENV, state=state)
    assert scoped.returncode == herdr_cli.EXIT_OK, scoped.stderr
    unscoped = stub.run("--verify", env=PANE_ENV, state=state)
    assert unscoped.returncode == herdr_cli.EXIT_BLOCKED
    assert "w9:p1" in unscoped.stdout


# ── integration: --sync ───────────────────────────────────────────────────────


def test_sync_renames_only_the_drifting_pane(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "panes": [{"pane_id": "w9:p1", "label": "buildbot"}]}
    done = stub.run("--sync", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "labelled w9:p1  label=buildbot -> reviewer" in done.stdout
    assert renames(stub) == [["pane", "rename", "w9:p1", "reviewer"]]


def test_sync_leaves_a_descriptive_label_alone(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "panes": [{"pane_id": "w9:p1", "label": "review pane"}]}
    done = stub.run("--sync", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "already in sync" in done.stdout
    assert renames(stub) == []


def test_sync_dry_run_renames_nothing(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "panes": [{"pane_id": "w9:p1", "label": "buildbot"}]}
    done = stub.run("--sync", "--dry-run", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "pane" in done.stdout and "reviewer" in done.stdout
    assert renames(stub) == []


def test_verify_rejects_a_name_argument(stub: StubHarness) -> None:
    done = stub.run("reviewer", "--verify", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "pass --verify or --sync alone" in done.stderr


def test_verify_and_sync_together_are_rejected(stub: StubHarness) -> None:
    done = stub.run("--verify", "--sync", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not both" in done.stderr


def test_pane_flag_targets_another_pane(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "agents": [SECOND_AGENT]}
    done = stub.run("buildbot", "--pane", "w9:p9", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p9  label=buildbot  agent=buildbot"
    assert [call[1:3] for call in stub.calls()] == [
        ["agent", "list"],
        ["pane", "rename"],
        ["agent", "rename"],
    ]


def test_dry_run_prints_the_calls_and_renames_nothing(stub: StubHarness) -> None:
    done = stub.run("buildbot", "--dry-run", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert renames(stub) == []
    calls = json.loads(done.stdout)
    assert calls[0][1:5] == ["pane", "rename", "w9:p1", "buildbot"]
    assert calls[1][1:5] == ["agent", "rename", "w9:p1", "buildbot"]


def test_dry_run_still_rejects_a_bad_name(stub: StubHarness) -> None:
    done = stub.run("Reviewer", "--dry-run", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert renames(stub) == []


# ── integration: guards, validated before any mutation ──────────────────────────────


def test_an_invalid_agent_name_is_rejected_without_mutating(stub: StubHarness) -> None:
    done = stub.run("Reviewer", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not a valid agent name" in done.stderr
    assert renames(stub) == []


def test_a_multi_word_name_needs_label_only_when_an_agent_is_present(stub: StubHarness) -> None:
    done = stub.run("review pane", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "--label-only" in done.stderr
    assert renames(stub) == []


def test_a_name_already_in_use_is_rejected_without_mutating(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "agents": [*DEFAULT_STATE["agents"], SECOND_AGENT]}
    done = stub.run("buildbot", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "already used by pane w9:p9" in done.stderr
    assert renames(stub) == []


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (("--clear", "buildbot"), "either NAME or --clear"),
        ((), "pass NAME"),
    ],
)
def test_name_and_clear_are_mutually_required(
    stub: StubHarness, argv: tuple[str, ...], expected: str
) -> None:
    done = stub.run(*argv, env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert expected in done.stderr


def test_refuses_without_herdr_env(stub: StubHarness) -> None:
    done = stub.run("buildbot", env={"HERDR_ENV": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_a_pane_rename_failure_is_reported(stub: StubHarness) -> None:
    error = {"code": "pane_not_found", "message": "pane w9:p1 not found"}
    done = stub.run("buildbot", env=PANE_ENV, state={**DEFAULT_STATE, "pane_rename_error": error})
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "pane_not_found" in done.stderr
    assert "Traceback" not in done.stderr


def test_an_agent_rename_failure_is_reported(stub: StubHarness) -> None:
    error = {"code": "agent_not_found", "message": "no agent in w9:p1"}
    done = stub.run("buildbot", env=PANE_ENV, state={**DEFAULT_STATE, "agent_rename_error": error})
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "agent_not_found" in done.stderr
    assert "Traceback" not in done.stderr


# ── integration: --tab (rename the calling Task Group) ─────────────────────────────


def test_tab_renames_the_calling_tab(stub: StubHarness) -> None:
    done = stub.run("--tab", "harness", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert [call[1:] for call in stub.tab_renames()] == [["tab", "rename", "w9:t1", "harness"]]


def test_tab_resolves_through_pane_when_no_tab_env(stub: StubHarness) -> None:
    done = stub.run("--tab", "harness", "--pane", "w9:p2", env={**PANE_ENV, "HERDR_TAB_ID": None})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert [call[1:] for call in stub.tab_renames()] == [["tab", "rename", "w9:t1", "harness"]]


def test_tab_dry_run_prints_the_argv_and_renames_nothing(stub: StubHarness) -> None:
    done = stub.run("--tab", "harness", "--dry-run", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.tab_renames() == []
    (argv,) = json.loads(done.stdout)
    assert argv[1:] == ["tab", "rename", "w9:t1", "harness"]


@pytest.mark.parametrize(
    "argv",
    [
        ("reviewer", "--tab", "harness"),
        ("--tab", "harness", "--verify"),
        ("--tab", "harness", "--task-group", "msg"),
        ("--tab", "harness", "--clear"),
        ("--tab", "harness", "--label-only"),
    ],
)
def test_tab_conflicts_are_rejected(stub: StubHarness, argv: tuple[str, ...]) -> None:
    done = stub.run(*argv, env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "--tab cannot be combined with" in done.stderr
    assert stub.tab_renames() == []


# ── integration: --task-group scoping ──────────────────────────────────────────────


def test_task_group_scopes_the_label_and_the_agent(stub: StubHarness) -> None:
    done = stub.run(
        "tm", "--task-group", "msg", "--pane", "w9:p2", env=PANE_ENV, state=P2_AGENT_STATE
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p2  label=msg-tm  agent=msg-tm"
    assert renames(stub) == [
        ["pane", "rename", "w9:p2", "msg-tm"],
        ["agent", "rename", "w9:p2", "msg-tm"],
    ]


def test_task_group_keeps_an_already_scoped_name(stub: StubHarness) -> None:
    done = stub.run("msg-tm", "--task-group", "msg", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert renames(stub) == [
        ["pane", "rename", "w9:p1", "msg-tm"],
        ["agent", "rename", "w9:p1", "msg-tm"],
    ]


def test_task_group_rejects_an_overlong_scoped_name(stub: StubHarness) -> None:
    done = stub.run("x" * 40, "--task-group", "msg", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not a valid agent name" in done.stderr
    assert renames(stub) == []


def test_naming_is_unchanged_without_task_group(stub: StubHarness) -> None:
    done = stub.run("buildbot", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert renames(stub) == [
        ["pane", "rename", "w9:p1", "buildbot"],
        ["agent", "rename", "w9:p1", "buildbot"],
    ]


# ── metadata: PEP 723 conformance ───────────────────────────────────────────────────


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.14"' in header
    assert "dependencies = []" in header
    assert header.rstrip().endswith("# ///")


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is required for the PEP 723 runner")
def test_uv_run_help_executes_without_path_configuration(tmp_path: Path) -> None:
    done = subprocess.run(
        ["uv", "run", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env={"HOME": os.environ.get("HOME", ""), "PATH": os.environ.get("PATH", "")},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "usage: herdr-label" in done.stdout
