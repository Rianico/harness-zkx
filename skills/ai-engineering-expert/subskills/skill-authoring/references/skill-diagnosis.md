# Skill Diagnosis Guide

Actionable troubleshooting methodology for skill discovery failures, false-positive collisions, execution loops, and dead skills in the LSZ harness.

## Evidential Diagnosis & Failure Philosophy

### The Evidential Diagnosis Principle

Environmental truth is supreme authority. Never guess why a skill failed or patch frontmatter blindly. Rely strictly on fresh environmental signals, static linters, and the empirical trigger ledger.

### Context Pressure Asymmetry in Diagnosis

When diagnosing a skill failure mid-session (e.g. user asks *"why didn't skill X trigger here?"*), **the parent agent must never execute the diagnosis in-process**.

Reading raw skill files, running `validate-deps.py`, inspecting ledgers, and drafting diffs consumes 3,000–8,000 tokens of diagnostic chatter. This bloat degrades the parent agent's reasoning on the user's primary task.

#### The Forked-Context Dispatch Pattern

1. **Dispatch Subagent**: Parent agent invokes a specialized subagent (`Skill Diagnostician`) with forked context or passes turn pointers:
   - Target skill name
   - Current turn observation or tool error output
   - Expected trigger behavior (`should_trigger: true`)
2. **Isolated Execution**: The subagent executes the diagnosis protocol in isolation:
   - Runs static gates (`validate-deps.py`)
   - Evaluates the trigger ledger at `$EVALS_DIR/<skill_name>.yaml` (defaults to `~/.pi/agent/evals/<skill_name>.yaml` on Pi)
   - Classifies root cause via the 4-archetype model
   - Writes the proposed frontmatter diff to scratch or temp storage
3. **Distilled Return**: Subagent returns strictly via structured response contract:
   - `## Summary`: 1–2 sentence root cause (e.g. "Trigger miss: prompt used 'rebase' but description only listened for 'merge'")
   - `## Artifacts`: Absolute path to proposed diff
   - `## Route`: `COMPLETED`
4. **Zero Bloat on Parent**: The parent thread receives only the distilled summary and diff pointer. Its context stays focused.

### The 4-Archetype Failure Model

Map every failure to one of the four root-cause archetypes from the spine. Never apply a prose patch to a mechanical defect.

| Tier | Archetype | Evidence | Remediation |
| --- | --- | --- | --- |
| 1 | Mechanical Violation | Command exits nonzero, bad flag, missing file, or oversized dump | Pack the step into `scripts/` and handle exit codes |
| 2 | Semantic Ambiguity | Model reads the boundary too narrowly or too broadly | 2a inject symptom keywords. 2b add a negative boundary |
| 3 | Semantic Disregard | Rule is clear, but the model ignores it under context pressure | Move the check to a reviewer or a hard gate |
| 4 | Route Friction | Command works, but agents repeatedly bypass it for cost or friction | Pack the steps and make the governed path cheapest |

**Discriminator:** Mechanical means the command fails. Route Friction means the command works but gets bypassed. Semantic Disregard means a clear rule is ignored. Semantic Ambiguity means the model reads the boundary differently.

#### Tier 1: Mechanical Violation
- **Indicators:** Skill loaded, but execution crashed on bash syntax, missing flags, unhandled exit codes, or oversized dumps (>20 lines).
- **Rule:** Never add explanatory prose to `SKILL.md` telling the agent "remember to pass flag -q".
- **Remediation:**
  - Pack multi-step commands into `$SKILL_DIR/scripts/<cmd>.py` or `.sh`.
  - Handle exit codes, piping, and output truncation natively inside the script.
  - Expose a single deterministic CLI command in `SKILL.md`.

#### Tier 2: Semantic Ambiguity

##### Tier 2a: Trigger Miss
- **Indicators:** Task was clearly within skill domain, but model bypassed skill and improvised manual commands.
- **Root cause:** Description used academic abstractions (*"architectural hygiene"*, *"dependency reconciliation"*) rather than symptom vocabulary.
- **Remediation:**
  - Inspect the failed turn's `trigger_observation` (error string, user query, tool exit code).
  - Extract the exact pain terms (e.g., `merge conflict`, `drift`, `flaky test`, `syntax error`).
  - Update the `Use when...` clause to embed those exact symptom keywords within the 300-char budget.

##### Tier 2b: Semantic Collision / Over-trigger
- **Indicators:** Skill fired on an unrelated task or collided with an adjacent skill (e.g., `tdd-cycle` vs `eval-gate`).
- **Remediation:**
  - Add an explicit **Negative Boundary** clause to the description:
    `Do not use for <adjacent_domain>. Defer to <other-skill> for <other_task>.`
  - In benchmarks, negative boundaries improve collision resistance by +20–35% without hurting recall.

#### Tier 3: Semantic Disregard / No-Op
- **Indicators:** The instruction is already clearly written in `SKILL.md`, but the model ignored it during complex execution.
- **Root cause:** Context Pressure. An implementer agent juggling many files and errors suffers attention decay.
- **Remediation:**
  - Do not bold, capitalize, or re-emphasize the instruction in the implementer prompt.
  - Move the verification to the **Reviewer** (Context Pressure Asymmetry) or create an automated eval gate.
  - Prune the ignored prose from `SKILL.md` if it produces no behavioral difference.

#### Tier 4: Route Friction
- **Indicators:** The governed command works, but the agent repeatedly bypasses it. Agents improvise shell steps, skip the script, or take a manual shortcut.
- **Root cause:** The governed path costs more attention than the shortcut.
- **Remediation:**
  - Pack repeated shell steps into `$SKILL_DIR/scripts/<cmd>`.
  - Expose one deterministic command in `SKILL.md`.
  - Remove the inline lines that the script replaced.
  - Make the governed path the cheapest path.

### Common Failure Symptoms & Primary Levers

| Symptom | Manifestation | Archetype | Primary Lever |
|---|---|---|---|
| **Discovery Failure** | User prompt or tool error clearly matches skill domain, but model attempts manual shell/sed edits or ignores skill. | Semantic Ambiguity (trigger miss) | Inject concrete symptom keywords into `Use when...` |
| **Collision / Pollution** | Skill loads unexpectedly on an unrelated or adjacent task, wasting context tokens and attention. | Semantic Ambiguity (over-trigger) | Add explicit Negative Boundary (`Do not use for X. Defer to Y`) |
| **Execution Failure** | Skill loads successfully but crashes, loops on tool calls, or dumps oversized terminal output. | Mechanical Violation | Pack shell steps into `scripts/` or add deterministic check |
| **Repeated Bypass / Manual Workaround** | Governed script exists, but the agent keeps improvising shell steps or skipping it. | Route Friction | Pack steps into `scripts/` and make the governed path cheapest |
| **No-Op / Ignored Rule** | A clear instruction is ignored under context pressure. | Semantic Disregard | Move the check to a Reviewer or automated gate |
| **Dead Skill** | `audit_skills.py` reports 0 invocations across past 30 days. | Semantic Ambiguity (trigger miss) | Recalibrate triggers or prune a redundant skill |

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
[Step 3: Archetype Remediation Action]
          │
          ▼
[Step 4: Offline Probe Validation]
```

### Step 1: Deterministic Static Floor

Always verify structural conformance before semantic diagnosis. A syntactic flaw or budget overrun breaks discovery automatically.

Run deterministic linters from project root:

```bash
# Frontmatter syntax, fields, and name collisions
uv run $SKILL_DIR/scripts/validate-deps.py lint

# Description budget (≤300 chars). Trigger checks are warnings.
uv run $SKILL_DIR/scripts/validate-deps.py context-check
```

**Audit against the Static Gate Checklist:**
1. **Budget gate:** `description` is strictly ≤ 300 characters (hard gate).
2. **YAML block scalar:** Written using `>-` or `|-` to avoid unquoted colon or quote parsing truncation.
3. **Tripartite formula present:**
   - Anchor noun (first 50 chars): What it is (e.g., *Methodology spine...*, *Verification gate...*).
   - Active capability: What it does (e.g., *audits test refutability...*).
   - Activation condition: Explicit `Use when...` clause.
4. **Third-person perspective:** No first-person ("I can help") or second-person ("Use this if you want") phrasing.
5. **Zero pseudo-syntax:** No deprecated `TRIGGER:` annotations. Keywords must reside naturally inside the `Use when...` clause.
6. **Invocation class:** If the skill is missing from `<available_skills>` XML on Pi, verify whether `disable-model-invocation: true` was set unintentionally.

### Step 2: Trigger Ledger Evaluation

Do not guess whether a prompt should have triggered a skill. Measure against the skill's evidential test ledger:

Ledger path: `$EVALS_DIR/<skill_name>.yaml` (defaults to `~/.pi/agent/evals/<skill_name>.yaml` on Pi)

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

### Step 3: Archetype Remediation Action

Apply the remediation matching the diagnosed archetype from the table above:
- **Tier 1 (Mechanical):** Pack shell commands into `scripts/` with native exit code handling.
- **Tier 2a (Trigger Miss):** Extract symptom terms from the failed turn and add them to `Use when...`.
- **Tier 2b (Collision):** Add an explicit negative boundary referencing the colliding skill.
- **Tier 3 (No-Op):** Shift checks to a Reviewer subagent or automated git hook.
- **Tier 4 (Route Friction):** Pack repeated steps into `scripts/<cmd>` and make the governed path cheapest.

### Step 4: Offline Probe Validation

Before pushing description changes, evaluate the candidate description against the trigger ledger cases.

1. **Verify candidate length:**
   ```bash
   uv run python -c "desc = '''<candidate_description>'''; print(f'Length: {len(desc.strip())} chars (limit 300)')"
   ```
2. **Re-run harness lint and context checks:**
   ```bash
   uv run $SKILL_DIR/scripts/validate-deps.py lint
   uv run $SKILL_DIR/scripts/validate-deps.py context-check
   ```
3. **Verify Recall and Precision:** Ensure the updated description triggers on all in_domain test cases in `$EVALS_DIR/<skill_name>.yaml` without firing on hard_negatives.

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

**Problem:** An agent ran a test runner that dumped 300 lines of output. The terminal dump broke context and caused looping.
- *Diagnosis:* Tier 1 (Mechanical Violation).
- *Remediation:*
  1. Add `--keep-head-tail` or `-q` flag in the script wrapper under `<skill-dir>/scripts/run-gate.sh`.
  2. Direct the agent to run the script instead of raw CLI commands.
  3. Keep output bounded to ≤ 20 lines.

### Recipe D: Retiring or Pruning a Dead Skill

**Problem:** `audit_skills.py` flags a skill with 0 invocations over 30+ days.
1. Run `validate-deps.py related <skill-name>` to check for downstream dependencies.
2. Check if the skill's domain was absorbed into another tool or skill.
3. If valid but hidden: add missing symptom keywords and test against ledger.
4. If obsolete: remove skill folder and update `metadata.manage` in parent skills.
