---
name: orchestrate-workflow
description: Defines the standard multi-agent execution pipelines (Feature, Bugfix, Docs). Use this skill to orchestrate multiple native sub-agents in a sequence.
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
- Step 1: `architect`
- Step 2: `planner`
- Step 3: `tdd-guide`
- Step 4: `code-reviewer` (If issues are found, follow its delegation request to run a fixing agent)
- Step 5: `general-purpose` agent to run the `/simplify` skill on the changed files

### 2. Bugfix Pipeline (`args="bugfix"`)
- Step 1: `tdd-guide` (Repro)
- Step 2: `build-resolver` (Fix)
- Step 3: `code-reviewer`

### 3. Documentation Pipeline (`args="docs"`)
- Step 1: `doc-updater`
- Step 2: `code-reviewer`
