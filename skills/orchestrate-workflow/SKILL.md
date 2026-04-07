---
name: orchestrate-workflow
description: Defines the standard multi-agent execution pipelines (Feature, Bugfix, Docs, Comprehensive). Use this skill to orchestrate multiple native sub-agents in a sequence. Includes `--heavy` variants using Opus agents.
argument-hint: "[feature|bugfix|docs]"
---

# Orchestration Workflow Skill

You have invoked the Orchestration Workflow Skill. This skill defines the strict sequence of native sub-agents you must execute to complete complex software engineering tasks.

## Orchestration Rules
1. **Sequential Execution:** You must execute the agents in the exact order specified by the pipeline.
2. **State Passing:** You must read the output of the previous agent and pass it into the `prompt` of the next agent.
3. **Strict Delegation:** You are the Orchestrator. You MUST NOT write or edit code yourself. You must only invoke the `Agent` tool.

## Standard Pipelines

### 1. Feature Pipeline (`args="feature"`)
- Step 1: `planner`
- Step 2: `tdd-guide`
- Step 3: `code-reviewer`

### 2. Bugfix Pipeline (`args="bugfix"`)
- Step 1: `tdd-guide` (Repro)
- Step 2: `build-resolver` (Fix)
- Step 3: `code-reviewer`

### 3. Documentation Pipeline (`args="docs"`)
- Step 1: `doc-updater`
- Step 2: `code-reviewer`
