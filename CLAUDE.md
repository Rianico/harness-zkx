## Talking Style
Sacrifice the grammar for the sake of concision.

## 1. The Skills-First Mental Model
The core of LSZ architecture is a **Subagent-First Execution** model that keeps reusable workflow logic in skills, preserves context efficiency, and avoids duplicating methodology.

### 1.1 The 7-Factor Engineering Mindset
Every mission must be evaluated against these seven factors:
1. **Action Space**: What tools and skills are available?
2. **Observation**: What does the environment tell us (LSP, tests, logs)?
3. **Recovery**: How do we backtrack from errors or unexpected states?
4. **Displacement**: Use handoffs to ignore old history and stay lean.
5. **Tool Feedback**: Automated signals (LSP/Linter) are authoritative blockers.
6. **Intent Preservation**: Handoffs bridge the "why" between agents.
7. **Artifact Hygiene**: Keep the workspace organized to prevent discovery failure.

### 1.2 Structural Rules
*   **Skills are the primary product surface.** Skills define the workflow contract and methodology.
*   **Agents define the WHO and the TOOLS.** Agents are lean execution engines. They define persona and tool boundaries.
*   **No Hero Mode**: Orchestrators are forbidden from doing implementation work directly. They MUST dispatch agents using strict **API Schema Templates** (Job Requisitions).
*   **Pointer-Based State Passing**: Pass absolute file paths between phases instead of re-reading large artifacts into the orchestrator's context.
*   **Commands are ergonomic shortcuts**: Only add a command if it provides CLI benefits beyond simple retrieval. Prefer direct skill invocation.

## 2. Skill Taxonomy

Skill taxonomy (orchestration, complex workflow, domain knowledge, action) and the authoring process (Gather-Draft-Review) are defined in `ai-engineering-expert skill-authoring`. Invoke that skill when creating, classifying, or structuring a skill.

**Naming Conventions:**
- **Domain Knowledge**: Use nouns (standardize on `[topic]-expert` for expertise skills).
- **Actions/Workflows**: Use verbs or prepositional phrases (e.g., `to-prd`, `handoff`).
- **Orchestration**: Use present participles (e.g., `orchestrating`).

## 3.1 Expert Role Placement Policy
When you want the model to "play" a specialist role (for example, architect expert, TDD expert, refactoring expert, API reviewer), place that role according to scope rather than stuffing it into one layer.

* **Agents own the stable baseline identity.** Put short, durable role framing here when it should apply in nearly every use of that agent. This is the default "who" for the agent, not a workflow-specific script.
* **Skills own deep reusable methodology.** Put expert checklists, heuristics, trade-off frameworks, and discipline-specific guidance here when they should be reusable across workflows. This is the main place for expert-role prompting.
* **Commands and orchestration skills own workflow-specific overlays.** If the same agent should behave differently in different workflows, inject that role framing in the command or workflow prompt. Use this for phase-local emphasis, suppressions, or artifact-specific instructions.
* **Rules own lightweight cross-cutting constraints.** Put conventions, tool preferences, artifact locations, and global guardrails here. Do NOT use rules as the primary home for expert personas or deep methodology.

**Default decision rule:**
- If the behavior should apply almost everywhere for that agent -> put it in the agent.
- If the behavior is deep and reusable across multiple workflows -> put it in a skill.
- If the behavior is specific to one workflow, phase, or artifact contract -> put it in the command or orchestration skill.
- If the behavior is a broad repository-wide constraint -> put it in rules.

**Examples**
- `developer` agent in TDD: keep the agent generic; load the `tdd-expert` skill for methodology; inject scope boundaries like "implementation-level verification only" in the TDD workflow prompt.
- `onboarding` agent: load the `onboarding` skill for codebase-specific context; use the agent to answer high-level structural questions.
- `code-reviewer` agent: keep the agent generally reusable; inject "do not replay TDD verification" only in the `/code-review` command.

## 3.2 Phase Transitions and Handoffs
For complex missions, transitions between major phases (e.g., Design to Implementation) must be used to preserve **intent, reasoning, and context**.

- **The Handoff as Context Aggregator**: Use the `handoff` skill to capture *why* decisions were made. The handoff acts as a **Context Aggregator** that distills Goals, Reasoning, and Intent from a sprawling session into a single source of truth, allowing subsequent agents to **displace** (ignore) the original full conversation history for better efficiency.
- **The Subagent Response Contract**: Sub-agents MUST return a structured response (using the format in `ai-engineering-expert process-arch`) that includes:
  * **Summary**: Concise bullet list of work completed.
  * **Artifact Pointers**: Absolute file paths to generated plans, code, or reviews.
  * **Route/Status**: Explicit signal for the orchestrator (e.g., `COMPLETED`, `REJECTED`, `BLOCKED`).
  * **Issues**: List of discovered risks or required follow-ups.
- **Pointer Continuity**: Use the handoff document as the index for durable artifacts (`design.md`, `lineage.md`, etc.) to keep the context window efficient. Subsequent agents start by reading the handoff to initialize state.

## 4. Hook Design Philosophy

Reusable hook capabilities MUST follow a consistent family-based design so they stay editable, installable, and understandable.

* **Family layout is the module boundary.** Each hook capability lives under `hooks/<family>/`. Canonical source files, runtime scripts, family-specific installer logic, and any family-local prompt/spec files stay inside that directory.
* **The root installer is the management surface.** `install-hooks.py` is the stable user-facing entrypoint. Family-specific install logic belongs in `hooks/<family>/install.py`, while the root installer dispatches to one family or `all`.
* **Source and runtime are intentionally separate.** Installers copy runtime hook scripts into the target `.claude/hooks/` directory and register those copied paths in the target `settings.json`. Do not point settings directly at source files in this repository.
* **Settings mutation must be surgical and idempotent.** A hook family manages only its own entries. Install adds the exact missing entry. Uninstall removes only the exact matching entry and should delete copied runtime scripts only when their corresponding entry was actually removed.
* **Runtime logic belongs in hook scripts, not installers.** Installers manage copying and settings mutation. Approve/block behavior, payload parsing, side effects, and soft-fail runtime handling belong in the installed hook scripts.
* **Personal hooks should fail soft by default.** Missing env vars, missing files, parse issues, and local command failures should degrade safely unless the hook's explicit purpose is to block the current action.
* **Docs are organized at two levels.** `hooks/README.md` is the top-level index for layout, conventions, and installer usage across families. Family-specific prompt/spec files may live inside `hooks/<family>/` when they help reproduce or extend the pattern.
* **Every hook family should document the same essentials.** Document purpose, file layout, install/uninstall commands, runtime behavior, configuration inputs, and a minimal example.

## 5. Standard Artifact Storage Convention
Workflows that generate files, reports, plans, evals, reviews, or tracking states must not clutter the project root and must remain independently invokable.

* **Anti-Pattern:** Dumping `.plan.md` or `.tdd-state.json` into the root directory. Hardcoding output paths directly into agents. Requiring a standalone workflow skill to know orchestration-specific root-selection logic. Minting a fresh timestamped root for each downstream phase in the same topic.
* **LSZ Pattern:** All artifact-generating workflows MUST use a default-plus-override storage contract.
  * **Standalone Default:** When invoked directly without an explicit artifact override, the workflow owns its default path: `.lsz/{date}/{topic_creation_time}_{short_topic}/{workflow_kind}/`.
  * **Caller Override:** A caller may override storage by passing an explicit `topic_root=<path>` or `artifact_dir=<path>` argument. `artifact_dir` is the exact output directory. `topic_root` is a shared topic directory; the callee writes under `{topic_root}/{workflow_kind}/`.
  * **Override Precedence:** `artifact_dir` wins over `topic_root`; `topic_root` wins over the standalone default.
  * **Orchestration Boundary:** Orchestration skills may create one shared `topic_root` for a multi-phase mission and pass it downstream, but downstream workflow skills must treat that as a caller override, not embed orchestration-only assumptions into their standalone path logic.
  * **Base Topic Pattern:** `.lsz/{date}/{topic_creation_time}_{short_topic}/`
  * **Workflow Artifact Pattern:** `.lsz/{date}/{topic_creation_time}_{short_topic}/{workflow_kind}/` (e.g., `.lsz/20260409/120123_auth_migration/plan/plan_v1.md`).
  * **Execution:** Create the selected artifact directory with `mkdir -p` before writing artifacts. Downstream phases in an orchestrated workflow MUST reuse the caller-provided topic root or artifact directory instead of generating unrelated roots.

## 6. Test Placement Convention
All tests MUST be placed in the project root `tests/` directory, never inside skill or feature directories.

* **Anti-Pattern:** Placing tests alongside source code in `skills/<name>/tests/` or `features/<name>/tests/`. This fragments test discovery, complicates CI configuration, and duplicates conftest.py files.
* **LSZ Pattern:** All tests live under `tests/` at project root. Test directory names MUST exactly match their corresponding skill directory names:
  ```
  tests/
  ├── conftest.py              # Shared fixtures for all tests
  ├── continuous-learning/     # Tests for skills/continuous-learning
  ├── docs-scraper/            # Tests for skills/docs-scraper
  ├── skill-comply/            # Tests for skills/skill-comply
  ├── skill-stocktake/         # Tests for skills/skill-stocktake
  └── test_hook_install_smoke.py
  ```
* **Naming rule:** `tests/<name>/` must correspond to `skills/<name>/`. No exceptions.
* **Test file naming:** Within `tests/<skill>/`, individual test files follow `test_<component>.py` (e.g., `test_render.py`, `test_validate_flavor.py`, `test_contract.py`). Shared fixtures live in `conftest.py` at the skill test directory level. This convention is NOT yet enforced — see the gap note below.
* **Known gap:** The individual test file naming convention (`test_<component>.py`) is observed but not enforced by any tooling. New test files should follow it by convention.
* **Path resolution:** Test conftest.py files must add the source directory to `sys.path` for imports. Use `Path(__file__).parent.parent.parent / "skills" / "<skill-name>" / "scripts"` pattern.
* **Known gap:** Individual test files currently duplicate the `sys.path.insert()` boilerplate from conftest.py at module level (e.g., `test_validate_flavor.py`, `test_contract.py`). This is needed because conftest.py's `sys.path` manipulation happens at fixture definition time, which is after module-level imports in test files are resolved. The correct fix is to move the source module(s) into a proper package structure under the skill directory so imports resolve naturally, eliminating the conftest dependency. Until then, the duplication is accepted but flagged — each test file independently manages its own import path.
* **Benefits:** Single `pytest` command runs all tests. Shared fixtures are discoverable. No duplicate test infrastructure.

## 7. Parallel Agent Execution
To maximize context efficiency and reduce latency, you MUST leverage parallel execution when orchestrating multiple independent or read-only tasks.

* **Anti-Pattern:** Running a security review agent, waiting for it to finish, and then running a performance review agent.
* **LSZ Pattern:** Launching multiple sub-agents concurrently in a single tool call payload when their tasks do not depend on each other's outputs.

## 8. Native Agent Orchestration Constraints
Shell-wrapper scripts executing sub-processes for multi-model collaboration are brittle, but Native Agents have strict constraints that must be respected.

* **Anti-Pattern:** Using bash to run python scripts to pipe outputs between multiple models.
* **CRITICAL ARCHITECTURE CONSTRAINT (No Agent-ception):** Sub-agents DO NOT have access to the `Agent` tool. A sub-agent cannot launch a new sub-agent. All orchestration MUST be done by the primary orchestrator in the main conversation context.
* **CRITICAL ARCHITECTURE CONSTRAINT (No Sub-Agent UI):** Sub-agents do not own the interaction flow with the user. If a sub-agent needs approval or a branch decision, it must return a structured response to the primary agent, which then handles the next step.
* **CRITICAL ARCHITECTURE CONSTRAINT (Stateless Iteration):** When iterating on a sub-agent's artifact (e.g., a user rejects a plan and provides feedback), DO NOT use the `to:` routing / `SendMessage` to resume the old sub-agent. Resumed agents accumulate context bloat and act statefully. Instead, spawn a **NEW** agent and explicitly pass the file path of the previous artifact alongside the user's feedback in the prompt.

## 9. Interaction Patterns
Destructive or highly divergent workflows should not guess the user's intent.

* **Anti-Pattern:** Generating 5 files or writing a massive plan to disk, then asking "Is this okay?" via an unstructured follow-up.
* **LSZ Pattern:** Heavy orchestration skills and complex workflow skills should define explicit checkpoints and structured branching points when approval or divergence is required.
* **Preferred Structure:** When encoding interactive branches, use the Dialog Contract pattern (YAML format that maps to `AskUserQuestion` tool calls). See `ai-engineering-expert skill-authoring` sub-skill's `dialog-contract.md` reference for the full specification.

## 10. Required Frontmatter (Argument Hints & Allowed Tools)
To ensure a seamless user experience and strict system bounds, skills, commands, and agents have explicit YAML frontmatter requirements.

* **Anti-Pattern:** Creating skills, commands, or agents without explicit argument hints, forcing the user or the LLM to guess what arguments are accepted, or omitting tool scoping for commands and agents.
* **LSZ Pattern (Agents):**
  * ALWAYS include `tools:`. Agents MUST explicitly define their tool scope as a YAML array. If omitted, they default to full tool access, which is a security and alignment risk.
  * If an agent has deterministic skill invocation, define a `skills:` header as a YAML array so those skills can be preloaded up front. Prefer this over runtime `Skill` calls when the required skills are known in advance, because it reduces round-trip overhead and keeps execution more predictable.
* **LSZ Pattern (Commands):**
  * Avoid creating commands that only forward to a skill. Prefer direct skill invocation as the default product surface.
  * Add a command only when it provides clear CLI ergonomics beyond retrieval, such as high-frequency shorthand, compatibility with existing workflows, argument autocomplete, or a genuinely command-specific interaction shell.
  * When a command is justified, ALWAYS include `argument-hint:`. Use clear syntax matching the underlying routing. This provides immediate visual autocomplete for the human user in the CLI.
  * When a command is justified, ALWAYS include `allowed-tools:`. Restrict the tools the command's context has access to as a YAML array. This prevents commands from going rogue outside their intended workflow.
* **LSZ Pattern (Skills):**
  * Invoke the `ai-engineering-expert` skill (with domain argument: `skill-authoring`, `rules-development`, `agent-harness`, `extension-dev`, `testing`, or `process-arch`) for comprehensive methodology on designing skills, agents, workflows, and orchestration patterns.
  * See `.claude/rules/skill-conventions.md` for mandatory guardrails only.
  * **Parent Skill with Sub-Skills Pattern:** When a skill manages multiple related capabilities, structure as `skills/<name>/SKILL.md` (parent) with `skills/<name>/subskills/<sub>/SKILL.md` (children). Parent has `metadata.manage: [...]`; sub-skills have `metadata.managed-by: <parent>`. Parent dispatches via `Read` (not `Skill` tool — nested paths not discoverable). Use this instead of routing commands for better discoverability and explicit relationships.

## Trade-Offs to Consider
* **Latency vs Context Efficiency:** The **On-Demand Skill Loading** pattern adds a small runtime penalty because the agent must call the `Skill` tool to retrieve deep knowledge. This is an intentional trade-off to keep the base context window pristine and focused on the user's immediate request. Load only what is needed for the current sub-task.
* **Agent Hero-Mode:** Generic agents are heavily prone to ignoring delegation instructions. Orchestration skills and complex workflow skills that dispatch agents SHOULD use explicit execution schemas with stable Agent dispatch templates to force the LLM into orchestration mode.
* **Command vs Skill Ergonomics:** Skills are the default product surface, including for simple action workflows. Commands are reserved for cases where CLI ergonomics materially improve use; thin forwarding wrappers create drift and should be avoided.
* **Tooling Preference:** When using shell-based search, prefer `rg` for content search and `fd` for file discovery over `grep`, `find`, and agent built-in search tools. Reserve `ls` and `tree` for structural inspection.

## Agent skills

### Issue tracker

Issues live as GitHub issues. Use `gh` CLI for all operations. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.
