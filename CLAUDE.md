## 1. The Skills-First Architecture Philosophy
The core of LSZ architecture is a skills-first design that keeps reusable workflow logic in one place, preserves context efficiency, and avoids duplicating methodology across commands, agents, and rules.

*   **Skills are the primary product surface.** Skills may define the workflow contract, user interaction model, and methodology. A skill can own both the WHAT and the HOW when that produces a cleaner, more reusable abstraction.
*   **Commands are classic convenience entrypoints.** Commands are optional, thin wrappers around skills, best suited for simple or high-frequency tasks (for example, `/plan`). Commands should stay lightweight unless there is a strong ergonomic reason to do otherwise.
*   **Agents define the WHO and the TOOLS.** Agents are lean execution engines. They define persona, tool boundaries, and focused execution roles. *Agents should generally NOT contain long workflow instructions unless the workflow is atomic, universal, and short.*

## 2. Skill Taxonomy
All skills should be designed as one of four primary types:

### 2.1 Orchestration Skills
Use orchestration skills for multi-phase, multi-party, or fan-out/fan-in workflows.
- They may invoke multiple skills and agents.
- They may define branching, checkpoints, and approval points.
- They own workflow sequencing and complex state transitions.
- They must not do implementation work directly.

### 2.2 Complex Workflow Skills
Use complex workflow skills for a substantial single-purpose workflow with multiple phases.
- They may invoke agents.
- They may generate artifacts and enforce phase transitions.
- They should prefer structured, schema-like execution instructions when dispatching agents.

### 2.3 Domain Knowledge Skills
Use domain knowledge skills for guides, patterns, expert methodology, and reusable domain constraints.
- They provide retrieval-time expertise.
- They do not generally own orchestration.
- They are designed to be loaded Just-In-Time by agents or higher-level skills.

### 2.4 Action Skills
Use action skills for narrow, simple workflows and direct task execution.
- They are the best fit for small, low-ambiguity tasks.
- They can be exposed via commands for convenience.
- They should remain simple and compact.

**When to embed logic directly in an Agent:**
Only embed workflow logic directly into an Agent's system prompt if the workflow is **Atomic** (does one specific thing without loops), **Universal** (does not change based on language/framework), and **Short** (< 300 words). Example: The `planner` agent.

## 3. The Hybrid JIT Architecture (Routing)
The harness is designed to achieve maximum context efficiency and DRY (Don't Repeat Yourself) principles.

* **Anti-Pattern:** Creating specialized commands or agents with massive, bloated system prompts containing an entire language's or workflow's methodology.
* **LSZ Pattern:** Keep agents generic and bounded. Load deep methodology from skills only when needed.
* **The Rule Router:** Claude Code's native `paths` matcher automatically injects a lightweight rule (e.g., `rules/rust.md`) into the active context based on the files it touches.
* **The Expert Skill:** The injected rule acts as a traffic cop. It provides the "80% baseline" (formatting, linting, conventions) and instructs the agent or higher-level skill to invoke the relevant expert skill (e.g., `rust-expert`) to dynamically fetch the "20% deep methodology" only when needed.

## 4. State-Passing & The Orchestrator Pattern
Generic agents executing workflows should not waste tokens doing their own domain discovery where they are invoked before any files are read, meaning no Domain Rules are injected. To protect the orchestrator's context window and prevent it from trying to write code itself ("Hero Mode"), you MUST follow these critical patterns for complex orchestration:

* **The API Schema Pattern (Job Requisitions):** When authoring orchestration skills or complex workflow skills that dispatch agents, DO NOT rely only on prose instructions like "Step 1: Write a failing test". Prefer a strict State Machine providing exact Agent tool dispatch templates alongside transition rules. A YAML-like text block is the default format because it is more stable under iterative editing than embedded JSON while still fencing the LLM into a pure routing/dispatch persona.

  **Default Agent Dispatch Template**
  ```text
  Agent tool (<subagent_type>):
    description: "<short task summary>"
    prompt: |
      <full prompt body>
  ```

  Use JSON only when a command or skill truly benefits from machine-shaped structure beyond what this template provides.

  **Example: Coercing LLM via Agent Dispatch Template**
  ```text
  ## PHASE 1: RED (Write Failing Tests)
  **Action:** Call `Agent` tool
  **Payload Template:**
  Agent tool (code-reviewer):
    description: "Write failing tests for [Feature]"
    prompt: |
      You are the RED phase agent. Read the specifications at [spec_pointer]. Write FAILING unit tests for the feature. Return a summary right before the absolute file path to your summary report. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow.
  ```

* **Pointer-Based State Passing:** This pattern is mainly for complex orchestration. When multiple phases or agents must exchange rich outputs, the orchestrator should pass absolute file paths or equivalent pointers between phases instead of re-reading large artifacts into its own context.
* **Skill-Oriented Orchestration:** When orchestrating complex, multi-step DAGs, prefer orchestrating skills rather than stringing bare agents together. Invoke agents directly only when a skill's execution contract explicitly calls for it.

## 5. Standard Artifact Storage Convention
Workflows that generate files, reports, plans, or tracking states must not clutter the project root.

* **Anti-Pattern:** Dumping `.plan.md` or `.tdd-state.json` into the root directory. Hardcoding output paths directly into agents. Minting a fresh timestamped root for each downstream phase in the same topic.
* **LSZ Pattern:** All high-level workflows MUST adhere to the centralized Artifact Storage Convention defined in the Domain Rules (`rules/common/environment-behavior.md`).
  * **Base Topic Pattern:** `.lsz/{date}/{topic_creation_time}_{short_topic}/`
  * **Workflow Artifact Pattern:** `.lsz/{date}/{topic_creation_time}_{short_topic}/{workflow_kind}/` (e.g., `.lsz/20260409/120123_auth_migration/plan/plan_v1.md`).
  * **Execution:** The topic root is created once at workflow initialization. Downstream skills, commands, and agents MUST reuse that same topic root and create only their workflow-specific subdirectory instead of generating a new timestamp.

## 6. Parallel Agent Execution
To maximize context efficiency and reduce latency, you MUST leverage parallel execution when orchestrating multiple independent or read-only tasks.

* **Anti-Pattern:** Running a security review agent, waiting for it to finish, and then running a performance review agent.
* **LSZ Pattern:** Launching multiple sub-agents concurrently in a single tool call payload when their tasks do not depend on each other's outputs.

## 7. Native Agent Orchestration Constraints
Shell-wrapper scripts executing sub-processes for multi-model collaboration are brittle, but Native Agents have strict constraints that must be respected.

* **Anti-Pattern:** Using bash to run python scripts to pipe outputs between multiple models.
* **CRITICAL ARCHITECTURE CONSTRAINT (No Agent-ception):** Sub-agents DO NOT have access to the `Agent` tool. A sub-agent cannot launch a new sub-agent. All orchestration MUST be done by the primary orchestrator in the main conversation context.
* **CRITICAL ARCHITECTURE CONSTRAINT (No Sub-Agent UI):** Sub-agents do not own the interaction flow with the user. If a sub-agent needs approval or a branch decision, it must return a structured response to the primary agent, which then handles the next step.
* **CRITICAL ARCHITECTURE CONSTRAINT (Stateless Iteration):** When iterating on a sub-agent's artifact (e.g., a user rejects a plan and provides feedback), DO NOT use the `to:` routing / `SendMessage` to resume the old sub-agent. Resumed agents accumulate context bloat and act statefully. Instead, spawn a **NEW** agent and explicitly pass the file path of the previous artifact alongside the user's feedback in the prompt.

## 8. Interaction Patterns
Destructive or highly divergent workflows should not guess the user's intent.

* **Anti-Pattern:** Generating 5 files or writing a massive plan to disk, then asking "Is this okay?" via an unstructured follow-up.
* **LSZ Pattern:** Heavy orchestration skills and complex workflow skills should define explicit checkpoints and structured branching points when approval or divergence is required.
* **Preferred Structure:** When encoding interactive branches, prefer explicit JSON-shaped interaction contracts, such as `{ "questions": [...] }`, so the control flow is unambiguous and easy to reuse across command and skill surfaces.

## 9. Required Frontmatter (Argument Hints & Allowed Tools)
To ensure a seamless user experience and strict system bounds, skills, commands, and agents have explicit YAML frontmatter requirements.

* **Anti-Pattern:** Creating skills, commands, or agents without explicit argument hints, forcing the user or the LLM to guess what arguments are accepted, or omitting tool scoping for commands and agents.
* **LSZ Pattern (Agents):**
  * ALWAYS include `tools:`. Agents MUST explicitly define their tool scope as a YAML array. If omitted, they default to full tool access, which is a security and alignment risk.
  * If an agent has deterministic skill invocation, define a `skills:` header as a YAML array so those skills can be preloaded up front. Prefer this over runtime `Skill` calls when the required skills are known in advance, because it reduces round-trip overhead and keeps execution more predictable.
* **LSZ Pattern (Commands):**
  * ALWAYS include `argument-hint:`. Use clear syntax matching the underlying routing. This provides immediate visual autocomplete for the human user in the CLI.
  * ALWAYS include `allowed-tools:`. Restrict the tools the command's context has access to as a YAML array. This prevents commands from going rogue outside their intended workflow.
  * Commands should usually be thin wrappers or aliases for skills, especially for simple action-style tasks.
* **LSZ Pattern (Skills):**
  * ALWAYS include `argument-hint:` when the skill accepts arguments.
  * Skills are the canonical place for reusable workflow contracts and methodology.

## Trade-Offs to Consider
* **Latency vs Context Bloat:** The Hybrid JIT Architecture adds a small runtime penalty to complex tasks because the agent must call the `Skill` tool to retrieve deep knowledge. This is an intentional trade-off to keep the base context window pristine and focused on the user's immediate request.
* **Agent Hero-Mode:** Generic agents are heavily prone to ignoring delegation instructions. Orchestration skills and complex workflow skills that dispatch agents SHOULD use explicit execution schemas with stable Agent dispatch templates to force the LLM into orchestration mode.
* **Command vs Skill Ergonomics:** Commands improve discoverability and user ergonomics for simple tasks, but duplicating workflow logic in both commands and skills creates drift. Prefer skills as the source of truth.
* **Tooling Preference:** When using shell-based search, prefer `rg` for content search and `fd` for file discovery over `grep`, `find`, and agent built-in search tools. Reserve `ls` and `tree` for structural inspection.
