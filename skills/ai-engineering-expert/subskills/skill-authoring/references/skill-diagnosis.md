# Skill Diagnosis Guide

Actionable troubleshooting methodology for skill discovery failures, false-positive collisions, execution loops, and dead skills in the LSZ harness.

## Which part of this guide you need

- **Skill failed to trigger on a task?** → [Discovery Failure](#1-discovery-failure-trigger-miss)
- **Skill fired on an unrelated task?** → [Collision & Context Pollution](#2-collision--context-pollution)
- **Skill crashed, looped, or dumped oversized output?** → [Execution Failure](#3-execution-failure)
- **Skill has 0 invocations in audit?** → [Dead Skill Triage](#4-dead-skill-triage)
- **Standard end-to-end diagnosis protocol?** → [The 4-Step Diagnosis Protocol](#the-4-step-diagnosis-protocol)
- **Diagnosing a skill failure mid-session?** → [Mid-Session Execution](#mid-session-execution-forked-context-subagent-isolation)
- **Classify root cause into the 4 tiers?** → [4-Tier Failure Triage](#step-3-4-tier-failure-triage)

---

## Common Failure Symptoms

| Symptom | Manifestation | Root Failure Mode | Primary Lever |
|---|---|---|---|
| **Discovery Failure** | User prompt or tool error clearly matches skill domain, but model attempts manual shell/sed edits or ignores skill. | Semantic Ambiguity / Missing Symptoms | Inject concrete symptom keywords into `Use when...` |
| **Collision / Pollution** | Skill loads unexpectedly on an unrelated or adjacent task, wasting context tokens and attention. | Unbounded Semantic Trigger | Add explicit Negative Boundary (`Do not use for X; defer to Y`) |
| **Execution Failure** | Skill loads successfully but loops on tool calls, dumps oversized terminal output, or errors out mechanically. | Mechanical Violation / Route Friction | Pack shell steps into `scripts/` or add deterministic check |
| **Dead Skill** | `audit_skills.py` reports 0 invocations across past 30 days. | Discovery Failure or Redundant Skill | Recalibrate triggers or prune skill |

---

## Mid-Session Execution: Forked-Context Subagent Isolation

When diagnosing a skill failure mid-session (e.g. user says *"why didn't skill X trigger here?"*), **the parent agent must never execute the diagnosis in-process**.

Reading raw skill files, running `validate-deps.py`, inspecting ledgers, and drafting diffs consumes 3,000–8,000 tokens of diagnostic chatter, bloating the parent agent's context and derailing the user's primary task.

### The Forked-Context Dispatch Pattern

1. **Dispatch Subagent**: Parent agent invokes a specialized subagent (`Skill Diagnostician`) with forked context or passes turn pointers:
   - Target skill name.
   - Current turn observation / error output.
   - Expected trigger behavior (`should_trigger: true`).
2. **Isolated Execution**: The subagent executes the 4-step protocol in isolation:
   - Runs static gates (`validate-deps.py`).
   - Checks/captures the trigger ledger (`~/.pi/agent/evals/<skill_name>.yaml`).
   - Diagnoses the root cause via the 4-tier triage.
   - Writes the proposed frontmatter diff to scratch/tmp.
3. **Distilled Return**: Subagent returns strictly via structured response contract:
   - `## Summary`: 1–2 sentence root cause (e.g. "Trigger miss: prompt used 'rebase' but description only listened for 'merge'").
   - `## Artifacts`: Absolute path to proposed diff (`/tmp/.../patch.diff`).
   - `## Route`: `COMPLETED`.
4. **Zero Bloat on Parent**: The parent thread receives only the distilled summary and diff pointer, keeping its context window completely focused on the user's primary feature or bug.

---

## The 4-Step Diagnosis Protocol

When a skill malfunctions or fails to trigger, execute these 4 steps in order:

```
[Step 1: Deterministic Static Floor]
          │
          ▼
[Step 2: Trigger Ledger Evaluation]
          │
          ▼
[Step 3: 4-Tier Failure Triage]
          │
          ▼
[Step 4: Offline Probe Validation]
```

### Step 1: Deterministic Static Floor

Always verify structural conformance before semantic diagnosis. A syntactic flaw or budget overrun breaks discovery automatically.

Run the deterministic linters from project root:

```bash
# Frontmatter syntax, fields, and name collisions
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py lint

# Context-load budget (≤300 chars) and tripartite formula conformance
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py context-check
```

**Audit against the Static Gate Checklist:**
1. **Budget gate:** `description` is strictly ≤ 300 characters (hard gate).
2. **YAML block scalar:** Written using `>-` or `|` to avoid unquoted colon/quote parsing truncation.
3. **Tripartite formula present:**
   - Anchor noun (first 50 chars): What it is (e.g., *Methodology spine...*, *Verification gate...*).
   - Active capability: What it does (e.g., *audits test refutability...*).
   - Activation condition: Explicit `Use when...` clause.
4. **Third-person perspective:** No first-person ("I can help") or second-person ("Use this if you want") phrasing.
5. **Zero pseudo-syntax:** No deprecated `TRIGGER:` annotations. Keywords must reside naturally inside the `Use when...` clause.
6. **Invocation class:** If the skill is missing from `<available_skills>` XML on Pi, verify whether `disable-model-invocation: true` was set unintentionally.

### Step 2: Trigger Ledger Evaluation

Do not guess whether a prompt should have triggered a skill. Measure against the skill's evidential test ledger:

Ledger path: `~/.pi/agent/evals/<skill_name>.yaml`

Compute empirical rates across recorded cases:
- **Trigger Recall:** $\frac{\text{Triggered in\_domain}}{\text{Total in\_domain}}$ (target: ≥ 0.90)
- **Collision Resistance:** $\frac{\text{Suppressed hard\_negative}}{\text{Total hard\_negative}}$ (target: ≥ 0.95)

#### Capturing Failed Sessions into the Ledger
If the symptom occurred in a recent interactive session, harvest the exact turn into the ledger:

```bash
uv run skills/harness-audit/scripts/audit_skills.py capture <session-id-or-path> \
  --skill <skill_name> \
  --expect trigger \
  --intent in_domain
```

For false-positive collisions, capture with `--expect no-trigger --intent hard_negative`.

#### Dual-Layer Skill Snapshot & Regression Blame

Each case records a dual snapshot to preserve provenance:
- `git_commit` + `dirty` for the skill directory (`Macro`).
- `captured_description` for the active routing text (`Micro`).

**Regression Blame Rule:**
- If a test regresses and `captured_description == current_description` → **Model weight drift**.
- If `captured_description != current_description` → **Description regression**.

### Step 3: 4-Tier Failure Triage

Map the failure to the appropriate architectural tier. Never apply a prose patch to a mechanical defect.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        4-TIER FAILURE TRIAGE                           │
├───────────────────────┬────────────────────────────────────────────────┤
│ Failure Tier          │ Remediation Action                             │
├───────────────────────┼────────────────────────────────────────────────┤
│ 1. Mechanical         │ Pack shell steps into scripts/ or enforce tool │
│    Violation          │ gate. Never patch via prose.                   │
├───────────────────────┼────────────────────────────────────────────────┤
│ 2. Semantic Ambiguity │ Extract user symptom keywords from captured    │
│    (Trigger Miss)     │ session; inject into 'Use when...' clause.     │
├───────────────────────┼────────────────────────────────────────────────┤
│ 3. Semantic Over-     │ Add explicit Negative Boundary:                │
│    trigger (Collision)│ 'Do not use for X; defer to Y for Z'.          │
├───────────────────────┼────────────────────────────────────────────────┤
│ 4. Semantic Disregard │ Enforce via Context Pressure Asymmetry         │
│    (No-Op)            │ (Skeptic reviewer) or hard pre-commit hook.    │
└───────────────────────┴────────────────────────────────────────────────┘
```

#### Tier 1: Mechanical Violation
- **Indicators:** Skill loaded, but execution crashed on bash syntax, missing flags, unhandled exit codes, or oversized dumps (>20 lines).
- **Rule:** Never add explanatory prose to `SKILL.md` telling the agent "remember to pass flag -q".
- **Remediation:**
  - Pack the multi-step command into `$SKILL_DIR/scripts/<cmd>.py` or `.sh`.
  - Handle exit codes, piping, and output truncation natively inside the script.
  - Expose a single deterministic CLI command in `SKILL.md`.

#### Tier 2: Semantic Ambiguity / Trigger Miss
- **Indicators:** Task was clearly within skill domain, but model bypassed skill and improvised manual commands.
- **Root cause:** Description used academic abstractions (*"architectural hygiene"*, *"dependency reconciliation"*) rather than symptom vocabulary.
- **Remediation:**
  - Inspect the failed turn's `trigger_observation` (e.g., error string, user query, tool exit code).
  - Extract the exact pain terms (e.g., `merge conflict`, `drift`, `flaky test`, `syntax error`).
  - Update the `Use when...` clause to embed those exact symptom keywords within the 300-char budget.

#### Tier 3: Semantic Over-trigger / Collision
- **Indicators:** Skill fired on an unrelated task or collided with an adjacent skill (e.g., `tdd-cycle` vs `eval-gate`).
- **Remediation:**
  - Add an explicit **Negative Boundary** clause to the description:
    `Do not use for <adjacent_domain>; defer to <other-skill> for <other_task>.`
  - In benchmarks, negative boundaries improve collision resistance by +20–35% without hurting recall.

#### Tier 4: Semantic Disregard / No-Op
- **Indicators:** The instruction is already clearly written in `SKILL.md`, but the model ignored it during complex execution.
- **Root cause:** Context Pressure. An implementer agent juggling many files and errors suffers attention decay.
- **Remediation:**
  - Do not bold, capitalize, or re-emphasize the instruction in the implementer prompt.
  - Move the verification to the **Reviewer** (Context Pressure Asymmetry) or create an automated eval gate.
  - Prune the ignored prose from `SKILL.md` if it produces no behavioral difference.

### Step 4: Offline Probe Validation

Before pushing description changes, evaluate the candidate description against the trigger ledger cases.

1. **Verify candidate length:**
   ```bash
   python3 -c "desc = '''<candidate_description>'''; print(f'Length: {len(desc.strip())} chars (limit 300)')"
   ```
2. **Re-run harness lint & context checks:**
   ```bash
   uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py lint
   uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py context-check
   ```
3. **Verify Recall and Precision:** Ensure the updated description triggers on all `in_domain` test cases in `~/.pi/agent/evals/<skill_name>.yaml` without firing on `hard_negative` cases.

---

## Actionable Remediation Recipes

### Recipe A: Fixing a Trigger Miss (Discovery Failure)

**Problem:** `resolve-merge-conflicts` was not loaded when `git merge` returned exit code 1 with conflict markers.
- *Old Description (210 chars):*
  ```yaml
  Git conflict reconciliation utility. Reconciles dual author intent across git branches. Use when merging git branches, dealing with branch divergence, or inspecting git state.
  ```
- *Diagnosis:* Lacks symptom keywords. The user said "the rebase blew up with CONFLICT markers", not "reconcile dual author intent".
- *Fixed Description (282 chars):*
  ```yaml
  Git conflict reconciliation utility. Reconciles dual author intent across conflicting branches. Use when a merge, rebase, cherry-pick, or stash pop stops on conflicts, when git status shows unmerged paths, or when files contain conflict markers; not for clean branch merges.
  ```

### Recipe B: Fixing a False-Positive Collision

**Problem:** `eval-gate` fired when the user requested a qualitative code review of architecture boundaries.
- *Diagnosis:* Overlapping trigger terms (`reviewing code`, `quality decisions`).
- *Remediation:* Add negative boundary to `eval-gate`:
  `...Use when defining acceptance criteria, validating implementations, or running gates; not for code reviews.`
- And anchor `code-review` with negative boundary:
  `...Use when reviewing code changes, auditing PRs, or verifying invariants; not for styling or lint checks.`

### Recipe C: Fixing an Execution Loop or Oversized Dump

**Problem:** Agent ran a test runner inside the skill that dumped 300 lines of terminal output, causing the agent to lose context and repeat the command.
- *Diagnosis:* Tier 1 (Mechanical Violation).
- *Remediation:*
  1. Add `--keep-head-tail` or `-q` flag in the script wrapper under `$SKILL_DIR/scripts/run-gate.sh`.
  2. Direct the agent to run the script instead of raw CLI commands.
  3. Keep output bounded to ≤ 20 lines.

### Recipe D: Retiring or Pruning a Dead Skill

**Problem:** `audit_skills.py` flags a skill with 0 invocations over 30+ days.
1. Run `validate-deps.py related <skill-name>` to check for downstream dependencies.
2. Check if the skill's domain was absorbed into another tool or skill.
3. If valid but hidden: add missing symptom keywords and test against ledger.
4. If obsolete: remove skill folder and update `metadata.manage` in parent skills.
