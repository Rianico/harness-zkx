---
name: lsp-guideline
description: >-
  Essential guide for implementing LSP 3.17 diagnostic features and server lifecycle. Use when building LSP clients/servers, handling diagnostics, managing versions, working with progress tokens, or implementing daemon-style process management. Covers initialize → shutdown → exit sequence, request vs notification patterns, workspace vs textDocument diagnostics, stale resultId detection, and parent-child process lifecycle.
argument-hint: >-
  [implementation-area]
---

# LSP Guideline

Key implementation patterns and pitfalls for LSP 3.17. Use when implementing diagnostic handling, version tracking, progress streaming, or server lifecycle management.

## 0. Context Discovery Checklist

- `eza -T -L 2` at repo root to find client/server entrypoints, transport, state/cache, tests
- `rg` on protocol nouns: `textDocument/diagnostic`, `workspace/diagnostic`, `publishDiagnostics`, `resultId`, `previousResultId`, `partialResultToken`, `workDoneToken`, `initialize`, `shutdown`, `exit`
- Expand from first hit into adjacent registration, state ownership, serialization files

---

## Server Lifecycle (CRITICAL)

### Initialization Sequence

```
1. Start transport (spawn subprocess, connect stdin/stdout)
2. Send initialize request with client capabilities
3. Receive InitializeResult with server capabilities
4. Send initialized notification (fire-and-forget)
5. Server ready for requests
```

### Shutdown Sequence

```
1. Send shutdown request (WAIT for response)
2. Send exit notification (fire-and-forget)
3. Stop transport (terminate subprocess)
4. Reset state (_initialized=False, clear caches)
```

**CRITICAL**: `shutdown` → `exit` → `stop` must happen in this order. The `shutdown` request allows the server to clean up resources. The `exit` notification tells the server to terminate.

### Common Mistake: Not Sending Shutdown Before Exit

```python
# WRONG: No shutdown request
await transport.send_notification("exit")
await transport.stop()

# CORRECT: Graceful shutdown sequence
await transport.send_request("shutdown")  # Wait for response
await transport.send_notification("exit")  # Then exit
await transport.stop()  # Then stop transport
```

### Initialization Timing: Lazy vs Eager

| Strategy | When LSP Starts | Pros | Cons |
|----------|----------------|------|------|
| **Lazy** (on-demand) | First LSP request | Fast daemon startup, resource efficient | First request latency spike |
| **Eager** (at startup) | With daemon start | Server ready immediately | Slower startup, wasted resources if unused |

**Recommendation**: Lazy initialization for CLI tools; eager for IDE-like persistent clients.

---

## Process Lifecycle Management (Daemon/CLI Tools)

When a CLI daemon manages LSP servers as child processes:

### Parent-Child Lifecycle Rule

**Daemon lifecycle MUST exceed LSP server lifecycle.** When daemon stops, LSP servers MUST shutdown first.

### Anti-Pattern: Orphaned LSP Processes

```python
# WRONG: Stopping daemon without shutting down LSP servers
async def run_daemon():
    try:
        await server.start()
        await shutdown_event.wait()
    finally:
        await server.stop()  # LSP servers still running as orphans!
```

### Correct Pattern

```python
async def run_daemon():
    handler = RequestHandler(...)
    server = UNIXServer(socket_path, handler.handle)
    try:
        await server.start()
        await shutdown_event.wait()
    finally:
        # 1. Shutdown LSP servers FIRST (while socket is active)
        try:
            await handler._registry.shutdown_all()
        except Exception as e:
            logger.exception(f"Error shutting down LSP servers: {e}")
        # 2. Then stop socket
        await server.stop()
```

### State Reset on Shutdown

After shutdown, state must be reset for potential re-initialization:

```python
class WorkspaceManager:
    async def shutdown(self) -> None:
        if self._client and self._initialized:
            await self._client.shutdown()
            self._client = None
            self._initialized = False  # CRITICAL: Reset for re-initialization

class ServerRegistry:
    async def shutdown_all(self) -> None:
        for workspace in self._workspaces.values():
            await workspace.shutdown()
        self._workspaces.clear()  # CRITICAL: Clear for fresh start
```

---

## Core Concepts

### Request vs Notification vs Response

| Type | Has ID | Response | Example |
|------|--------|----------|---------|
| **Request** | Yes | Required | `textDocument/diagnostic`, `initialize`, `shutdown` |
| **Notification** | No | None (fire-and-forget) | `$/progress`, `initialized`, `exit`, `didChange` |
| **Response** | Matches request | Is the reply | Contains `result` or `error` |

### Two Token Types

| Token | Purpose | Streaming |
|-------|---------|-----------|
| `partialResultToken` | Partial results via `$/progress` | Multiple reports |
| `workDoneToken` | Progress lifecycle | begin → report → end |

---

## Diagnostic Requests: Key Distinctions

### textDocument/diagnostic vs workspace/diagnostic

| Aspect | textDocument/diagnostic | workspace/diagnostic |
|--------|------------------------|---------------------|
| **Scope** | Single document | Entire workspace |
| **Pattern** | Request/Response | Fire-and-forget |
| **Parameter** | `previousResultId` (string) | `previousResultIds` (array) |
| **Results** | Response `items` array | Via `$/progress` notifications |

### Common Mistake: Parameter Names

```python
# WRONG: Array for textDocument/diagnostic
{"previousResultIds": [{"uri": uri, "value": "6"}]}

# CORRECT: Singular string
{"previousResultId": "6"}
```

### Common Mistake: Awaiting workspace/diagnostic

```python
# WRONG: This never resolves
result = await send_request("workspace/diagnostic", params)

# CORRECT: Fire-and-forget, results come via $/progress
await send_message(LSPMessage(id=1, method="workspace/diagnostic", params=params))
# Diagnostics arrive via $/progress notifications
```

---

## Version Tracking

### Two Separate Versions

| Version | Managed By | Purpose | Lifecycle |
|---------|------------|---------|-----------|
| **Document version** | Client | Track content edits | Increments on change, never resets |
| **resultId** | Server | Track diagnostic state | Resets to 0 on file open |

**Key insight**: `resultId` is the server's internal diagnostic version as a string.

### Stale resultId Detection

```python
def _result_id_greater(new_id: str, cached_id: str) -> bool:
    if not new_id or not cached_id:
        return bool(new_id)
    try:
        return int(new_id) > int(cached_id)  # Numeric comparison
    except ValueError:
        return new_id > cached_id  # Fallback lexicographic
```

### On Document Close

- Reset `last_result_id = None` (diagnostic version invalid)
- Keep `document_version` (content history preserved)
- Set `is_open = False`

---

## Common Mistakes

### Mistake 1: Adding Non-Existent `version` Parameter

`workspace/diagnostic` does NOT accept `version`. Use `previousResultIds` array instead.

### Mistake 2: Regenerating Tokens Each Request

Tokens must remain constant within a session. Generate once in `__init__`, reuse throughout.

### Mistake 3: Not Auto-Opening Documents

Before `didChange` or `textDocument/diagnostic`, ensure document is open via `didOpen`.

### Mistake 4: workspace/diagnostic Never Resolves

Don't await it. Results arrive via `$/progress` notifications using `partialResultToken`.

---

## Implementation Checklist

**Server Lifecycle:**
- [ ] Shutdown sequence: `shutdown` request → `exit` notification → stop transport
- [ ] State reset: `_initialized = False`, `_client = None` on shutdown
- [ ] Workspace clearing: `_workspaces.clear()` in `shutdown_all()`
- [ ] Parent-child lifecycle: LSP servers shutdown before daemon stops

**Diagnostics:**
- [ ] Token handling: Constant tokens (not regenerated per request)
- [ ] Version separation: Document version vs resultId tracked separately
- [ ] Stale detection: `_result_id_greater()` before updating cache
- [ ] Fire-and-forget: `workspace/diagnostic` not registered as pending
- [ ] Auto-open: Documents opened before `didChange`/diagnostic requests
- [ ] Parameter names: `previousResultId` (singular) vs `previousResultIds` (array)

---

## Reference Files

`reference/` contains LSP 3.17 spec excerpts. Start with `reference/INDEX.md`.

---

## When to Use This Skill

- Implementing LSP diagnostic features (pull model)
- Managing server lifecycle (initialize, shutdown, exit)
- Building daemon-style CLI tools that manage LSP servers
- Debugging diagnostic versioning issues
- Handling `$/progress` notifications
- Implementing parent-child process lifecycle patterns
