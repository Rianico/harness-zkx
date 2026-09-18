"""Tests for dynamic workflow scripts under skills/dynamic-workflow-wrapper/workflows/."""

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "dynamic-workflow-wrapper"
WORKFLOWS_DIR = SKILL_DIR / "workflows"

# Mirrors pi-dynamic-workflows' DETERMINISM_BLOCKLIST, applied to the RAW script text:
# a literal mention inside a comment is a hard SCRIPT_VALIDATION_ERROR, not a style nit.
VM_DETERMINISM_BLOCKLIST = re.compile(
    r"\bDate\s*\.\s*now\b|\bMath\s*\.\s*random\b|\bnew\s+Date\s*\(\s*\)"
)

# The runtime body already executes inside an async function; wrap it the same way to check syntax.
NODE_SYNTAX_CHECKER = """
const fs = require('node:fs');
const full = fs.readFileSync(process.argv[1], 'utf8');
const body = full.replace(/export const meta = \\{[\\s\\S]*?\\};\\n/, '');
new Function('(async () => {' + body + '})');
"""

CANONICAL_ROLES = ["developer", "gate-runner", "code-reviewer", "ticket-planner", "merger"]


def workflow_scripts() -> list[Path]:
    """Every workflow script the skill ships; the glob keeps new scripts under the same checks."""
    return sorted(WORKFLOWS_DIR.glob("*.js"))


def read_workflow(name: str) -> str:
    script_path = WORKFLOWS_DIR / name
    assert script_path.exists(), f"Missing workflow script: {script_path}"
    return script_path.read_text(encoding="utf-8")


def strip_comments(content: str) -> str:
    return re.sub(r"/\*[\s\S]*?\*/|//.*", "", content)


def test_workflow_scripts_exist():
    """The skill must ship at least one workflow script."""
    scripts = workflow_scripts()
    assert scripts, f"No workflow scripts found in {WORKFLOWS_DIR}"


def test_workflow_scripts_are_syntactically_valid():
    """Every workflow must parse in the runtime's async-body execution model."""
    for script_path in workflow_scripts():
        proc = subprocess.run(
            ["node", "-e", NODE_SYNTAX_CHECKER, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"{script_path.name} syntax check failed:\n{proc.stderr}"


def test_workflow_scripts_avoid_vm_forbidden_globals():
    """The workflow VM provides no modules and no ambient nondeterminism."""
    for script_path in workflow_scripts():
        raw = script_path.read_text(encoding="utf-8")
        stripped = strip_comments(raw)
        assert "import " not in stripped, f"{script_path.name} must not contain imports"
        assert "require(" not in stripped, f"{script_path.name} must not use require()"
        # The runtime validates the raw script before it executes anything, so the
        # determinism guard must not strip comments first — a mention in a comment
        # still refuses the whole run.
        match = VM_DETERMINISM_BLOCKLIST.search(raw)
        assert match is None, (
            f"{script_path.name} contains {match.group(0)!r}, which the runtime's "
            "determinism blocklist rejects"
        )


def test_converge_tasks_declares_meta_and_phases():
    """converge-tasks.js must declare its meta and enter every phase it declares."""
    content = read_workflow("converge-tasks.js")

    assert "export const meta = {" in content
    assert re.search(r"name: ['\"]converge-tasks['\"]", content), "meta.name must be converge-tasks"
    assert "description:" in content

    for phase_title in ("Plan & Prepare", "Integrate & Gate", "Finalize", "Report"):
        assert phase_title in content, f"phase {phase_title!r} is not declared"
        assert f"phase('{phase_title}')" in content or f'phase("{phase_title}")' in content

    for primitive in ("agent(", "gate(", "log("):
        assert primitive in content, f"converge-tasks.js must use {primitive}()"


def test_converge_tasks_uses_the_canonical_roster():
    """Every node must be bound to a canonical role, so the roster stays load-bearing."""
    content = read_workflow("converge-tasks.js")
    for role in CANONICAL_ROLES:
        assert f"agentType: '{role}'" in content or f'agentType: "{role}"' in content, (
            f"role {role} is never dispatched"
        )


def test_converge_tasks_takes_a_task_list_with_bounded_budgets():
    """One task and many share the same code path; both budgets are explicit and bounded."""
    content = read_workflow("converge-tasks.js")

    assert "rawArgs.tasks" in content, "the task list is the interface"
    assert "dependsOn" in content, "batch ordering is declarative"
    assert "resolveOrder" in content, "dependency order must be resolved deterministically"
    assert "maxRounds" in content
    assert "maxMergeAttempts" in content
    assert "Math.min(" in content, "budgets must be clamped"


def test_converge_tasks_keeps_the_isolation_guards():
    """The two isolation phases are the falsifiable guards each round must run."""
    content = read_workflow("converge-tasks.js")
    assert "worktree-branch" in content
    assert "root-untouched" in content
    assert "status --porcelain --untracked-files=no" in content


def test_converge_tasks_derives_reverification_from_merge_exit_codes():
    """Merge authority: the merger reports exit codes; only the workflow decides re-verification."""
    content = read_workflow("converge-tasks.js")

    assert "merge_copy.py" in content
    assert "exitCode" in content
    assert "nonZero" in content, "a non-zero merge attempt must invalidate the round"
    assert "exactly ONE merge" in content, "the merger must not retry a merge inside one call"
    assert "reReview" not in content, "re-verification must never be a subagent self-report"


def test_converge_tasks_never_pushes_or_opens_a_pull_request():
    """Delivery is the operator's step: nothing external may be emitted unattended."""
    content = read_workflow("converge-tasks.js")

    for forbidden in ("git push", "gh pr create", "gh pr merge"):
        assert forbidden not in content, f"converge-tasks.js must not run {forbidden!r}"

    assert "nextActions" in content, "the operator step must be reported as nextActions"


def test_converge_tasks_supports_suggestions_and_known_gotchas():
    """converge-tasks.js must feed forward knownGotchas and collect non-blocking suggestions."""
    content = read_workflow("converge-tasks.js")

    assert "knownGotchas" in content
    assert "gotchasBlock" in content
    assert "recordSuggestions" in content
    assert "suggestions: { type: 'array' }" in content

    for source in (
        "ticket-planner",
        "prepare",
        "allocate",
        "developer",
        "gate-runner",
        "code-reviewer",
        "merger",
    ):
        assert f"recordSuggestions('{source}'" in content, (
            f"missing suggestion recording for {source}"
        )


DOCS_WITH_WORKFLOW_POINTERS = (
    SKILL_DIR / "SKILL.md",
    SKILL_DIR / "references" / "workflow-guidelines.md",
)

WORKFLOW_PATH_PATTERN = re.compile(r"workflows/([A-Za-z0-9._-]+\.js)")


def test_retired_workflow_scripts_stay_retired():
    """converge-goal was generalized into converge-tasks; the old entry surface stays closed."""
    assert not (WORKFLOWS_DIR / "converge-goal.js").exists(), (
        "converge-goal.js was retired into converge-tasks.js — re-adding it recreates the duplicate loop"
    )


def test_documented_workflow_paths_exist():
    """A documented workflow path that does not resolve is drift, not a TODO."""
    shipped = {script.name for script in workflow_scripts()}

    for doc in DOCS_WITH_WORKFLOW_POINTERS:
        referenced = set(WORKFLOW_PATH_PATTERN.findall(doc.read_text(encoding="utf-8")))
        assert referenced, f"{doc.name} must point at the workflow it routes to"
        for name in sorted(referenced):
            assert (WORKFLOWS_DIR / name).exists(), f"{doc.name} points at missing workflows/{name}"

    assert shipped <= set(
        WORKFLOW_PATH_PATTERN.findall((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    ), "every shipped workflow must be reachable from the routing table in SKILL.md"


def test_no_dangling_ship_tasks_pointers():
    """The removed ship-tasks workflow must not survive as a pointer to nothing."""
    for doc in DOCS_WITH_WORKFLOW_POINTERS:
        content = doc.read_text(encoding="utf-8")
        assert "ship-tasks" not in content, (
            f"{doc.name} still references the retired ship-tasks workflow"
        )


# --- regression guards for the convergence-loop defects (issues #38, #40, #41, #42) -------------


def _extract_functions(names: list[str]) -> str:
    """Verbatim source of the named top-level functions, to exercise them outside the VM."""
    content = read_workflow("converge-tasks.js")
    chunks: list[str] = []
    for name in names:
        match = re.search(rf"function {name}\(.*?\n\}}\n", content, re.DOTALL)
        assert match is not None, f"function {name}() not found in converge-tasks.js"
        chunks.append(match.group(0))
    return "\n".join(chunks)


def _run_node(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["node", "-e", script], capture_output=True, text=True)


def test_converge_tasks_breaks_a_stagnant_round() -> None:
    """Issue #42: an identical diff plus identical failures must stop the loop, not burn rounds."""
    content = read_workflow("converge-tasks.js")

    assert "diff-hash" in content, "the gate must report a worktree diff hash for the breaker"
    assert "lastFailedSignature" in content
    assert "BLOCKED (eval-gate stagnation)" in content
    assert "stalled: true" in content, "the ledger must record the round as stalled"
    # The signature must be cleared when the gate goes green, or a later failure re-trips it.
    assert re.search(r"lastFailedSignature = '';", content), "the signature is never reset"


def test_failure_signature_is_diff_and_error_identity() -> None:
    """Two failing rounds are stagnant only when both the diff and the failing output match."""
    source = _extract_functions(["failureSignature"])
    script = (
        source
        + """
const fails = [{ name: 'pytest', tail: '1 failed' }, { name: 'lint', tail: 'boom' }];
const same = failureSignature('abc', fails);
if (same !== failureSignature('abc', fails)) throw new Error('identical rounds differ');
if (same === failureSignature('def', fails)) throw new Error('a new diff must break stagnation');
if (same === failureSignature('abc', [{ name: 'pytest', tail: '2 failed' }])) {
  throw new Error('a different failure must break stagnation');
}
"""
    )
    proc = _run_node(script)
    assert proc.returncode == 0, proc.stderr


def test_changelog_drift_only_is_recognized() -> None:
    """Issue #38: only a changelog-only failure may trigger the auto-sync repair."""
    source = _extract_functions(["failedPhaseNames", "changelogDriftOnly"])
    script = (
        source
        + """
const drift = { ok: false, phases: [{ name: 'tests', ok: true }, { name: 'changelog-check', ok: false }] };
const alsoFailing = { ok: false, phases: [{ name: 'tests', ok: false }, { name: 'changelog-check', ok: false }] };
const green = { ok: true, phases: [{ name: 'changelog-check', ok: true }] };
if (!changelogDriftOnly(drift)) throw new Error('changelog-only drift must be recognized');
if (changelogDriftOnly(alsoFailing)) throw new Error('a real failure must not be repaired as drift');
if (changelogDriftOnly(green)) throw new Error('a green gate is not drift');
if (changelogDriftOnly(null)) throw new Error('missing output is not drift');
"""
    )
    proc = _run_node(script)
    assert proc.returncode == 0, proc.stderr


def test_converge_tasks_syncs_changelog_drift_once() -> None:
    """Issue #38: the drift repair is one idempotent hidden-type commit, re-verified once."""
    content = read_workflow("converge-tasks.js")

    assert "changelog-check" in content, "the final gate must report drift read-only"
    assert "changelog-unreleased.py check" in content
    assert "It is READ-ONLY" in content, "the gate must detect drift without mutating the tree"
    assert "finalize-changelog-sync" in content
    assert "chore: sync changelog unreleased section" in content
    assert "changelogDriftOnly" in content
    assert "final-recheck" in content, "the composite gate must be re-run after the sync"
    assert content.count("const syncResult = await accept") == 1, "exactly one sync dispatch"


def test_converge_tasks_admission_tolerates_ephemeral_caches() -> None:
    """Issue #40: ambient __pycache__ must not halt admission before round 1."""
    content = read_workflow("converge-tasks.js")

    assert "PYTHONDONTWRITEBYTECODE=1" in content
    assert content.count("__pycache__/") >= 3, (
        "prepare, allocate and workspace must all tolerate it"
    )
    assert "\\.pyc$" in content
    # The strict tracked-only guard on the session root (no untracked files at all) survives.
    assert "status --porcelain --untracked-files=no" in content


def test_converge_tasks_identifiers_use_word_boundaries() -> None:
    """Issue #41: criteria must anchor identifiers and count diffs with --numstat."""
    content = read_workflow("converge-tasks.js")
    assert "git diff --numstat" in content
    assert "\\\\b<identifier>\\\\b" in content, "the plan prompt must demand word boundaries"


def test_converge_tasks_caps_agent_calls_with_a_two_hour_default() -> None:
    """Issue #42: the VM has no clock, so the cap is a per-agent ceiling with a 2h default."""
    content = read_workflow("converge-tasks.js")

    assert "rawArgs.taskTimeoutMs" in content
    assert "rawArgs.runTimeoutMs" in content
    assert "DEFAULT_RUN_TIMEOUT_MS = 7_200_000" in content, "the run cap defaults to 2h"
    assert "rawArgs.runTimeoutMs === null" in content, "an explicit null must disable the cap"
    assert "function callOptions(" in content
    assert "timeoutMs" in content, "the resolved cap must reach agent()"
    assert "Date.now(" not in strip_comments(content), "the VM forbids a clock"
    # Every in-loop agent call must be capped through the helper, not constructed ad hoc.
    assert content.count("callOptions({") >= 7


# --- the Report phase and the failed-run exit contract -------------------------------------------


def test_converge_tasks_fails_the_run_when_a_node_fails() -> None:
    """A run whose node failed must exit with an error, not complete with a sad result."""
    content = read_workflow("converge-tasks.js")

    assert "phase('Report')" in content, "the Report phase must be entered"
    assert "function buildRunReport(" in content
    assert "if (!converged) {" in content, "the non-converged path must throw"
    # Both run-level exits fail the run: the admission gate and the final Report phase. A third
    # exit that silently returns a BLOCKED result would recreate the defect this guards.
    assert content.count("throw new Error(`[RUN FAILED] ${") == 2, (
        "every run-level exit must throw, so a blocked batch cannot read as a green run"
    )
    assert "report: runReport," in content, "a converged run still returns its report"


def test_run_report_renders_the_unified_status_table() -> None:
    """The Report phase renders from run evidence, deterministically and falsifiably."""
    source = _extract_functions(["clip", "buildRunReport"])
    script = (
        source
        + """
const rows = [
  { id: 'T-a', ref: 'do the thing', status: 'MERGED', rounds: 2, mergeAttempts: 1, reviewScore: 100, worktreePath: '/wt/a', issues: [] },
  { id: 'T-b', ref: 'do the other thing', status: 'BLOCKED', rounds: 3, mergeAttempts: 1, reviewScore: 0, worktreePath: '/wt/b', issues: ['gate-runner: 1 failed'] }
];
const input = {
  workflow: 'converge-tasks',
  status: 'BLOCKED',
  converged: false,
  failure: '',
  maxRounds: 5,
  tasks: rows,
  delivery: { mode: 'integration-branch', branch: 'dev/x', base: 'main', worktreePath: '/wt/integration' },
  planIssues: [],
  abortedTasks: ['T-b'],
  compositeOk: false,
  compositePhases: ['tests'],
  nextActions: ['Resolve the reported block, then re-run.']
};
const text = buildRunReport(input);
const checks = [
  ['table header', '| Task | Status | Rounds | Merge | Crux Review | Worktree |'],
  ['blocked task row', 'T-b'],
  ['status column', '**BLOCKED**'],
  ['delivery branch', '`dev/x`'],
  ['row evidence', 'gate-runner: 1 failed'],
  ['composite gate', 'composite gate: FAILED (tests)'],
  ['halted batch', 'halted after: T-b'],
  ['failure headline', 'did NOT converge'],
  ['next actions', 'Next actions']
];
for (const [what, needle] of checks) {
  if (!text.includes(needle)) throw new Error('report is missing ' + what + ': ' + needle);
}
if (buildRunReport(input) !== text) throw new Error('the report must be deterministic');
const converged = buildRunReport({
  ...input,
  status: 'CONVERGED',
  converged: true,
  abortedTasks: [],
  compositeOk: true,
  compositePhases: []
});
if (converged === text) throw new Error('a converged run must not render like a blocked one');
if (!converged.includes('The run converged')) throw new Error('the converged headline must say so');
if (!converged.includes('1/2 task(s)')) throw new Error('the delivered count must come from the rows');
"""
    )
    proc = _run_node(script)
    assert proc.returncode == 0, proc.stderr
