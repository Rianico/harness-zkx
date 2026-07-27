---
name: llm-lsp-cli-guide
description: >-
  Practical guide for LLMs using llm-lsp-cli for code intelligence.
  Covers definition lookup, references, call chain tracing,
  diagnostics, rename, completion, and cache coherence.
  TRIGGER: find definition, find references, trace call chain,
  rename symbol, check diagnostics.
argument-hint: |-
  [command] <file> [line] [column]
---

# llm-lsp-cli Guide for LLMs

A practical guide for using `llm-lsp-cli` to navigate, analyze, and refactor codebases through LSP intelligence.

## Prerequisites

```bash
# Ensure daemon is running
llm-lsp-cli daemon status

# If not running, start it (auto-detects language from workspace)
llm-lsp-cli daemon start

# If stale, restart
llm-lsp-cli daemon restart
```

The daemon auto-detects the language server from workspace root markers (e.g., `pyproject.toml` triggers basedpyright).

---

## 1. Project Overview

Before diving into specifics, understand the codebase structure.

### List Symbols in a File

```bash
llm-lsp-cli lsp document-symbol src/llm_lsp_cli/daemon.py
```

Returns all top-level symbols (classes, functions, constants) with their ranges. Use `--depth 2` to see nested members (methods inside classes).

**Output:**
```json
{
  "_source": "Basedpyright",
  "file": "src/llm_lsp_cli/daemon.py",
  "command": "document-symbol",
  "items": [
    {"name": "_to_json_serializable", "kind_name": "Function", "range": "44:5-61:1"},
    {"name": "DaemonManager", "kind_name": "Class", "range": "78:1-500:1",
     "children": [
       {"name": "start", "kind_name": "Method", "range": "100:5-120:1"},
       {"name": "stop", "kind_name": "Method", "range": "122:5-140:1"}
     ]}
  ]
}
```

**Key fields:** `name` (symbol name), `kind_name` (Function/Class/Method/Variable), `range` (1-based `L:C-L:C`), `children` (nested symbols).

### Search Symbols Across the Workspace

```bash
# Search by name pattern
llm-lsp-cli lsp workspace-symbol "DaemonManager"

# Search for all classes
llm-lsp-cli lsp workspace-symbol "class:"

# Search for functions matching a pattern
llm-lsp-cli lsp workspace-symbol "handle_request"
```

Returns matching symbols grouped by file. Use this to locate symbols without knowing which file they're in.

### Get Diagnostics

```bash
# Individual file
llm-lsp-cli lsp diagnostics src/main.py

# Entire workspace
llm-lsp-cli lsp workspace-diagnostics
```

Diagnostics include severity (`Error`, `Warning`, `Information`, `Hint`), range, message, and diagnostic code (e.g., `reportUndefinedVariable`).

### Notify External File Changes (CRITICAL)

When files are edited outside the daemon (by editors, scripts, or manual fixes), notify the daemon before querying diagnostics:

```bash
# 1. Fix code externally
# 2. Notify daemon
llm-lsp-cli lsp did-change src/main.py

# 3. Query fresh diagnostics
llm-lsp-cli lsp diagnostics src/main.py
```

> NOTE: In general, use mechanisms like `hook` to send `did-change` request automatically after any edits.

---

## 2. Identify the Source

When you encounter a symbol and need to know where it comes from.

### Find Definition

Given a file, line, and column (all 1-based), find where the symbol is defined:

```bash
# Where is the function at line 44, column 5 defined?
llm-lsp-cli lsp definition src/llm_lsp_cli/daemon.py 44 5
```

**Output:**
```json
{
  "_source": "Basedpyright",
  "file": "src/llm_lsp_cli/daemon.py",
  "command": "definition",
  "items": [
    {"file": "src/llm_lsp_cli/daemon.py", "range": "44:5-44:26"}
  ]
}
```

The `range` field uses compact 1-based format: `startLine:startCol-endLine:endCol`. This matches `cat -n` and editor line numbers.

### Get Type and Documentation (Hover)

```bash
# What is the type and docstring of the symbol at line 44, column 5?
llm-lsp-cli lsp hover src/llm_lsp_cli/daemon.py 44 5
```

**Output:**
```json
{
  "_source": "Basedpyright",
  "file": "src/llm_lsp_cli/daemon.py",
  "command": "hover",
  "content": "(function) def _to_json_serializable(obj: Any) -> Any\n\nConvert Pydantic models...",
  "range": "44:5-44:26"
}
```

Use `hover` to understand types, signatures, and documentation without reading the source file.

### Find All References

```bash
# Where is the symbol at line 44, column 5 used?
llm-lsp-cli lsp references src/llm_lsp_cli/daemon.py 44 5
```

**Output (grouped by file):**
```json
{
  "_source": "Basedpyright",
  "command": "references",
  "files": [
    {
      "file": "src/llm_lsp_cli/daemon.py",
      "references": [
        {"range": "44:5-44:26"},
        {"range": "58:17-58:38"},
        {"range": "616:22-616:43"}
      ]
    }
  ]
}
```

Use `references` to assess impact before renaming or refactoring.

---

## 3. Track Calling Chains

Understand how functions call each other — essential for tracing bugs, understanding data flow, and planning refactors.

### Find Who Calls a Function (Incoming Calls)

```bash
# Who calls _to_json_serializable?
llm-lsp-cli lsp incoming-calls src/llm_lsp_cli/daemon.py 44 5
```

**Output:**
```json
{
  "_source": "Basedpyright",
  "command": "incoming-calls",
  "items": [
    {
      "file": "src/llm_lsp_cli/daemon.py",
      "name": "_handle_standard_lsp_method",
      "kind_name": "Function",
      "range": "627:15-627:42",
      "selection_range": "627:15-627:42",
      "from_ranges": ["708:22-708:43"]
    },
    {
      "file": "src/llm_lsp_cli/daemon.py",
      "name": "_send_lsp_request",
      "kind_name": "Function",
      "range": "564:15-564:32",
      "from_ranges": ["616:22-616:43"]
    }
  ]
}
```

**Key fields:**
- `name`: Caller function name
- `range`: Full body of the caller function
- `selection_range`: The function name location (where to jump)
- `from_ranges`: Exact call sites within the caller

### Find What a Function Calls (Outgoing Calls)

```bash
# What does _to_json_serializable call?
llm-lsp-cli lsp outgoing-calls src/llm_lsp_cli/daemon.py 44 5
```

**Output:**
```json
{
  "_source": "Basedpyright",
  "command": "outgoing-calls",
  "items": [
    {
      "file": ".venv/.../pydantic/main.py",
      "name": "model_dump",
      "kind_name": "Method",
      "range": "418:9-418:19",
      "from_ranges": ["56:20-56:30"]
    },
    {
      "file": "src/llm_lsp_cli/daemon.py",
      "name": "_to_json_serializable",
      "kind_name": "Function",
      "range": "44:5-44:26",
      "from_ranges": ["58:17-58:38", "60:20-60:41"]
    }
  ]
}
```

### Chaining Calls for Full Trace

To trace a call chain (e.g., "who calls A, and who calls those callers"):

```bash
# Step 1: Find callers of function A
CALLERS=$(llm-lsp-cli lsp incoming-calls src/file.py <line> <col>)

# Step 2: For each caller found, find ITS callers
# Use the selection_range from step 1 as input
llm-lsp-cli lsp incoming-calls src/file.py <caller_line> <caller_col>
```

The `from_ranges` field tells you the exact call site — use it to read the calling context with `sed` or `Read`.

---

## 4. Complete Workflows

### Workflow: Understand an Unfamiliar Function

```bash
# 1. What is it? (type + docs)
llm-lsp-cli lsp hover src/module.py 44 5

# 2. Where is it defined?
llm-lsp-cli lsp definition src/module.py 44 5

# 3. Who calls it?
llm-lsp-cli lsp incoming-calls src/module.py 44 5

# 4. What does it call?
llm-lsp-cli lsp outgoing-calls src/module.py 44 5

# 5. Where else is it referenced?
llm-lsp-cli lsp references src/module.py 44 5
```

### Workflow: Assess Refactoring Impact

```bash
# 1. Find all references to the symbol
llm-lsp-cli lsp references src/module.py 44 5

# 2. Find all callers (for functions)
llm-lsp-cli lsp incoming-calls src/module.py 44 5

# 3. Preview rename (dry-run is default)
llm-lsp-cli lsp rename src/module.py 44 5 new_name

# 4. Apply if satisfied
llm-lsp-cli lsp rename src/module.py 44 5 new_name --apply

# 5. Rollback if needed
llm-lsp-cli lsp rename --rollback <session-id>
```

### Workflow: Map a File's Structure

```bash
# 1. Get all symbols with nested children
llm-lsp-cli lsp document-symbol src/module.py --depth 2

# 2. For each interesting symbol, check its callers
llm-lsp-cli lsp incoming-calls src/module.py <line> <col>

# 3. Check diagnostics for issues
llm-lsp-cli lsp diagnostics src/module.py
```

### Workflow: Trace a Bug Through Call Chain

```bash
# 1. Find the buggy function's definition
llm-lsp-cli lsp definition src/module.py 100 10

# 2. Who calls it? (go up the chain)
llm-lsp-cli lsp incoming-calls src/module.py 100 10

# 3. For each caller, check what IT calls (go down)
llm-lsp-cli lsp outgoing-calls src/module.py 200 5

# 4. Check types at suspicious points
llm-lsp-cli lsp hover src/module.py 200 15
```

### Workflow: Fix Diagnostics Loop

Iterate on type errors until clean:

```bash
# 1. Get current diagnostics
llm-lsp-cli lsp diagnostics src/module.py

# 2. Fix the error in your editor (externally)

# 3. Notify daemon of the change
llm-lsp-cli lsp did-change src/module.py

# 4. Re-check — should show fewer errors
llm-lsp-cli lsp diagnostics src/module.py

# 5. Repeat until clean
```

The `did-change` step is required between external edits and diagnostic queries. Without it, the daemon returns cached (stale) results from before your fix.

---

## 5. Position Conventions

**All line and column numbers are 1-based** — matching `cat -n`, `sed -n`, and editor display.

```
File content (cat -n output):
     1  def hello():
     2      return "world"
     3
     4  def main():
     5      hello()

To reference `hello()` call on line 5:
  llm-lsp-cli lsp definition src/app.py 5 5
                                        ^ ^
                                        | |
                                      line column
```

The `range` in output uses the same convention: `"5:5-5:10"` means line 5, columns 5 through 10.

---

## 6. Output Formats

All commands support `--format`:

```bash
--format json    # Default, structured (best for LLM parsing)
--format text    # Human-readable, one line per result
--format yaml    # YAML format
--format csv     # Tabular, good for diffing
```

**JSON structure:**
- `_source`: Language server name (e.g., "Basedpyright")
- `command`: Which command produced this
- `file`: Source file (relative to workspace)
- `items` or `files`: Results (varies by command)

---

## 7. Common Options

| Option | Purpose | Default |
|--------|---------|---------|
| `--workspace, -w` | Override workspace path | cwd |
| `--language, -l` | Override language detection | auto |
| `--include-tests` | Include test file results | excluded |
| `--raw` | Show raw LSP response | off |
| `--depth, -d` | Symbol nesting depth | 1 |

---

## 8. Gotchas

- **Daemon must be running.** All `lsp` commands fail if the daemon is down. Check with `daemon status`.
- **File must be in workspace.** The LSP server only knows about files under the workspace root.
- **Stale after external edits.** If files are modified outside the tool, run `llm-lsp-cli lsp did-change <file>` to notify the daemon. Without this, diagnostics and other queries return cached (possibly stale) results.
- **Diagnostic cache has two layers.** Both workspace-diagnostics and diagnostics share a unified cache but track versions independently, while the previous one is updated asynchronously, the later one is synchronous.
- **Test files excluded by default.** Use `--include-tests` to include them in references, workspace-symbol, and workspace-diagnostics.
- **Ranges are 1-based.** `"44:5-44:26"` means line 44, columns 5 to 26. Do NOT subtract 1.
- **Call hierarchy needs a function name.** Point `incoming-calls`/`outgoing-calls` at a function/method name, not at a random line.
