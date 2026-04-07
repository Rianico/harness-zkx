---
name: harness-architecture
description: Deep knowledge of the ECC Hybrid JIT Architecture, including Native Sub-Agent Pipelines, Universal Discovery, Rule Routing, and AskUserQuestion patterns. Use this when modifying or extending the Claude Code harness.
argument-hint: "[routing|agents|discovery|interactive]"
---

# Harness Architecture Skill

You have invoked the Harness Architecture Skill. This document codifies the design principles, patterns, and trade-offs of the Everything-Claude-Code (ECC) architecture.

## 1. The Hybrid JIT Architecture (Routing)
The harness is designed to achieve maximum context efficiency and DRY (Don't Repeat Yourself) principles.

* **Anti-Pattern:** Creating specialized commands (`/rust-build`) that spawn specialized agents (`rust-build-resolver`) with massive, bloated system prompts containing an entire language's methodology.
* **ECC Pattern:** A universal command (`/build-fix`) invokes a universal agent (`build-resolver`). 
* **The Rule Router:** Claude Code's native `paths` matcher automatically injects a lightweight rule (e.g., `rules/rust.md`) into the generic agent's context based on the files it touches.
* **The Expert Skill:** The injected rule acts as a traffic cop. It provides the "80% baseline" (formatting, linting) and instructs the agent to invoke the `Skill` tool (e.g., `rust-expert`) to dynamically fetch the "20% deep methodology" only when needed.

## 2. State-Passing Orchestration
Generic agents executing workflows should not waste tokens doing their own domain discovery where they are invoked before any files are read, meaning no Domain Rules are injected.

* **ECC Pattern:** The Primary LLM acts as the "Orchestrator". It determines the domain context once, and passes it to the sub-agent in the `prompt` parameter (e.g., "This is a Rust project. Read Cargo.toml").
The sub-agent wakes up, immediately reads the root file specified by the Orchestrator, triggering Rule Injection, and starts work. No redundant exploration loops. to find root configuration files (`Cargo.toml`, `pyproject.toml`, `docker-compose.yml`, `README.md`). It uses the `Read` tool on those files. This physically forces the Claude Code engine to inject the corresponding Domain Rules into the agent's context.

## 3. Native Agent Orchestration
Shell-wrapper scripts executing sub-processes for multi-model collaboration are brittle.

* **Anti-Pattern:** Using bash to run python scripts to pipe outputs between Codex and Gemini.
* **ECC Pattern:** The `/orchestrate` command uses Claude Code's native `Agent` tool to form Directed Acyclic Graphs (DAGs). The primary LLM orchestrates by passing state: `Planner Output -> prompt -> TDD Guide -> prompt -> Code Reviewer`. 

## 4. Interactive Workflows (AskUserQuestion)
Destructive or highly divergent commands should not guess the user's intent.

* **Anti-Pattern:** Generating 5 files or writing a massive plan to disk, then asking "Is this okay?" via standard chat.
* **ECC Pattern:** Heavy workflows (`/plan`, `/mine-conventions`, `/update-docs`) MUST use the `AskUserQuestion` tool. The agent executes the read-only analysis phase, builds a structured multi-select or strict choice menu (Approve/Modify/Reject), and blocks execution until the user clicks a button.

## Trade-Offs to Consider
* **Latency vs Context Bloat:** The Hybrid JIT Architecture adds a ~3 second penalty to complex tasks because the agent must call the `Skill` tool to retrieve deep knowledge. This is an intentional trade-off to keep the base context window pristine and focused on the user's immediate request.
* **Agent Hero-Mode:** Generic agents are heavily prone to ignoring delegation instructions. Commands that wrap generic agents MUST use an explicit "Execution Instruction" schema that provides the exact JSON mapping for the `Agent` tool parameters to force the LLM into orchestration mode.

## 5. UI Alignment (Argument Hints)
To ensure a seamless user experience, both the underlying skills and the top-level commands must provide clear autocomplete guidance.

* **Anti-Pattern:** Creating commands or skills without explicit argument hints, forcing the user (or the LLM) to guess what arguments are accepted.
* **ECC Pattern:** Always include the `argument-hint:` field in the YAML frontmatter of both Commands and Skills.
  * **For Skills:** Use the array syntax to denote accepted arguments (e.g., `argument-hint: "[frameworks|coroutines|testing|build]"`). This explicitly informs the agent exactly how to invoke the skill for targeted retrieval.
  * **For Commands:** Use clear syntax matching the skill routing (e.g., `argument-hint: "[feature|bugfix|docs] <task_description>"`). This provides immediate visual autocomplete for the human user in the CLI, keeping the UX perfectly aligned with the underlying skill architecture.
