## 1. The Separation of Concerns Philosophy
The core of ECC architecture is the separation of orchestration, capabilities, and methodologies to maintain context window efficiency and high reusability. When designing new features, strictly adhere to this separation boundary:

*   **Commands define the WHAT and the UI.** The Orchestrator lives here. It handles human interaction (`AskUserQuestion`), launches sub-agents (`Agent`), passes state between them, and manages the overall Directed Acyclic Graph (DAG) of the workflow.
*   **Agents define the WHO and the TOOLS.** Agents are lean execution engines (e.g., Code Reviewer, TDD Orchestrator). They define system prompts, persona, and strict tool boundaries. *Agents should generally NOT contain long workflow instructions.*
*   **Skills define the HOW.** Skills hold the deep, domain-specific methodology (e.g., how to do Red-Green-Refactor, how to write a secure Next.js API route). They are loaded Just-In-Time (JIT) only when needed, keeping the Agent's baseline context pristine.

**When to embed logic directly in an Agent:**
Only embed workflow logic directly into an Agent's system prompt if the workflow is **Atomic** (does one specific thing without loops), **Universal** (does not change based on language/framework), and **Short** (< 300 words). Example: The `planner` agent.

## 2. The Hybrid JIT Architecture (Routing)
The harness is designed to achieve maximum context efficiency and DRY (Don't Repeat Yourself) principles.

* **Anti-Pattern:** Creating specialized commands (`/rust-build`) that spawn specialized agents (`rust-build-resolver`) with massive, bloated system prompts containing an entire language's methodology.
* **ECC Pattern:** A universal command (`/build-fix`) invokes a universal agent (`build-resolver`). 
* **The Rule Router:** Claude Code's native `paths` matcher automatically injects a lightweight rule (e.g., `rules/rust.md`) into the generic agent's context based on the files it touches.
* **The Expert Skill:** The injected rule acts as a traffic cop. It provides the "80% baseline" (formatting, linting) and instructs the agent to invoke the `Skill` tool (e.g., `rust-expert`) to dynamically fetch the "20% deep methodology" only when needed.

## 3. State-Passing & The Orchestrator Pattern
Generic agents executing workflows should not waste tokens doing their own domain discovery where they are invoked before any files are read, meaning no Domain Rules are injected. To protect the Orchestrator's context window and prevent it from trying to write code itself ("Hero Mode"), you MUST follow these critical patterns:

* **The API Schema Pattern (Job Requisitions):** When authoring complex workflow skills (like `/tdd`), DO NOT write prose instructions like "Step 1: Write a failing test". This triggers the main agent to attempt the work itself. Instead, format the skill as a strict State Machine providing exact JSON payload templates for the `Agent` tool alongside transition rules. Coercing the instructions into an API schema fences the LLM into a pure routing/dispatch persona.

  **Example: Coercing LLM via API Schema**
  ```json
  ## PHASE 1: RED (Write Failing Tests)
  **Action:** Call `Agent` tool
  **Payload Template:**
  {
    "subagent_type": "code-reviewer",
    "description": "Write failing tests for [Feature]",
    "prompt": "You are the RED phase agent. Read the specifications at [spec_pointer]. Write FAILING unit tests for the feature. Return a brief summary (up to 100 words) right before the absolute file path to your summary report."
  }
  ```

* **Pointer-Based State Passing:** The Orchestrator must NEVER read the code, diffs, or implementation files between execution phases. When Sub-Agent A finishes, it must return an absolute file path (a pointer). The Orchestrator extracts this pointer and injects it directly into the prompt payload for Sub-Agent B. This keeps the Orchestrator's context perfectly flat and focused on the "big picture".
* **Command Orchestration (Meta-Commands):** When orchestrating complex, multi-step DAGs, DO NOT string bare agents together. Instead, orchestrate the **Commands** themselves (via `Skill` tool loading) and pass state sequentially. This ensures that the workflow inherits all the interactive UI guardrails defined in each Command.

## 4. Standard Artifact Storage Convention
Workflows that generate files, reports, plans, or tracking states must not clutter the project root.

* **Anti-Pattern:** Dumping `.plan.md` or `.tdd-state.json` into the root directory. Hardcoding output paths directly into agents.
* **ECC Pattern:** All high-level workflows MUST adhere to the centralized Artifact Storage Convention defined in the Domain Rules (`rules/common/environment-behavior.md`).
  * **Pattern:** `.claude/ecc/{date}/{time}_{short_topic}/{workflow_kind}/` (e.g., `.claude/ecc/20260409/120123_auth_migration/plan/plan_v1.md`).
  * **Execution:** Agents or Skills should be instructed to read the Domain Rules for this path structure, construct the dynamic `base_dir`, and use `mkdir -p` via the Bash tool before writing files.

## 5. Parallel Agent Execution
To maximize context efficiency and reduce latency, you MUST leverage parallel execution when orchestrating multiple independent or read-only tasks.

* **Anti-Pattern:** Running a security review agent, waiting for it to finish, and then running a performance review agent.
* **ECC Pattern:** Launching multiple sub-agents concurrently in a single tool call payload when their tasks do not depend on each other's outputs.

## 6. Native Agent Orchestration Constraints
Shell-wrapper scripts executing sub-processes for multi-model collaboration are brittle, but Native Agents have strict constraints that must be respected.

* **Anti-Pattern:** Using bash to run python scripts to pipe outputs between Codex and Gemini.
* **CRITICAL ARCHITECTURE CONSTRAINT (No Agent-ception):** Sub-agents DO NOT have access to the `Agent` tool. A sub-agent cannot launch a new sub-agent. All orchestration MUST be done by the primary orchestrator (the main conversation context).
* **CRITICAL ARCHITECTURE CONSTRAINT (No Sub-Agent UI):** Sub-agents DO NOT have access to the `AskUserQuestion` tool. All interactive prompts must be handled in the main conversation agent. If a sub-agent needs human approval, it must return a structured response to the primary agent, which then invokes `AskUserQuestion`.
* **CRITICAL ARCHITECTURE CONSTRAINT (Stateless Iteration):** When iterating on a sub-agent's artifact (e.g., a user rejects a plan and provides feedback), DO NOT use the `to:` routing / `SendMessage` to resume the old sub-agent. Resumed agents accumulate context bloat and act statefully. Instead, spawn a **NEW** agent and explicitly pass the file path of the previous artifact alongside the user's feedback in the prompt.

## 6. Interactive Workflows (AskUserQuestion)
Destructive or highly divergent commands should not guess the user's intent.

* **Anti-Pattern:** Generating 5 files or writing a massive plan to disk, then asking "Is this okay?" via standard chat. Or using invalid JSON schemas for the tool.
* **ECC Pattern:** Heavy workflows (`/plan`, `/architect`, `/code-review`) MUST use the `AskUserQuestion` tool. The agent executes the read-only analysis phase, builds a structured menu, and blocks execution until the user clicks a button. (Remember: This must be done by the main agent, as sub-agents lack this tool).
* **Tool Schema Requirement:** You MUST use the correct JSON schema. The tool accepts an object with a `questions` array. Each question object contains `question`, `header`, `multiSelect`, and an `options` array (which contains `label` and `description` objects). Do NOT pass the question fields straight to the root of the tool parameters.
  ```json
  {
    "questions": [{
      "question": "Clear question text?",
      "header": "Short Label",
      "multiSelect": false,
      "options": [
        { "label": "Option 1", "description": "What happens if selected" },
        { "label": "Option 2", "description": "What happens if selected" }
      ]
    }]
  }
  ```

## 7. Required Frontmatter (Argument Hints & Allowed Tools)
To ensure a seamless user experience and strict system bounds, underlying skills, commands, and agents have explicit YAML frontmatter requirements.

* **Anti-Pattern:** Creating commands or skills without explicit argument hints, forcing the user (or the LLM) to guess what arguments are accepted, or omitting tool scoping for commands/agents, risking unauthorized execution.
* **ECC Pattern (Agents):**
  * ALWAYS include `tools:`. Agents MUST explicitly define their tool scope as a YAML array. If omitted, they default to full tool access, which is a security and alignment risk. Remember: Agents NEVER have access to `AskUserQuestion` or `Agent`.
* **ECC Pattern (Commands):** 
  * ALWAYS include `argument-hint:`. Use clear syntax matching the underlying routing. This provides immediate visual autocomplete for the human user in the CLI.
  * ALWAYS include `allowed-tools:`. Restrict the tools the command's context has access to as a YAML array. This prevents commands from "going rogue" outside their intended workflow.
* **ECC Pattern (Skills):**
  * ALWAYS include `argument-hint:`. Use array syntax to denote accepted arguments. This explicitly informs the agent exactly how to invoke the skill for targeted retrieval.

## Trade-Offs to Consider
* **Latency vs Context Bloat:** The Hybrid JIT Architecture adds a ~3 second penalty to complex tasks because the agent must call the `Skill` tool to retrieve deep knowledge. This is an intentional trade-off to keep the base context window pristine and focused on the user's immediate request.
* **Agent Hero-Mode:** Generic agents are heavily prone to ignoring delegation instructions. Commands that wrap generic agents MUST use an explicit "Execution Instruction" schema that provides the exact JSON mapping for the `Agent` tool parameters to force the LLM into orchestration mode.
