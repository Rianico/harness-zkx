---
name: LSP 3.17 Implementation Guide
description: Essential guide for implementing LSP 3.17 diagnostic features. Use when building LSP clients/servers, handling diagnostics, managing versions, or working with progress tokens. Covers request vs notification patterns, workspace vs textDocument diagnostics, stale resultId detection, and fire-and-forget streaming.
argument-hint: [implementation-area]
user-invocable: false
---

# LSP 3.17 Implementation Guide

This skill captures key implementation patterns and common pitfalls for LSP 3.17 diagnostic features. Use it when implementing diagnostic handling, version tracking, or progress streaming.

## Core Concepts

### Request vs Notification vs Response

| Type | Has ID | Sends Reply | Purpose | Example |
|------|--------|-------------|---------|---------|
| **Request** | Yes | Receives response | Invoke method, get result | `textDocument/diagnostic` |
| **Notification** | No | No response | Fire event | `$/progress`, `textDocument/didChange` |
| **Response** | Yes (matches request) | Is the reply | Return result/error | Response to `textDocument/diagnostic` |

**Critical distinction:**
- **Request**: Must have `id` field, receiver MUST send response back
- **Notification**: MUST NOT have `id` field, no response expected (fire-and-forget)
- **Response**: Has `id` matching the request, contains `result` or `error`

### Two Token Types for Progress

| Token | Purpose | Used For |
|-------|---------|----------|
| `partialResultToken` | Streaming partial results via `$/progress` | `workspace/diagnostic`, `textDocument/diagnostic` |
| `workDoneToken` | Progress lifecycle tracking (begin/report/end) | Any long-running operation |

Both tokens are **ProgressToken** types (string or integer) and enable out-of-band progress reporting.

---

## Diagnostic Requests: Workspace vs TextDocument

### textDocument/diagnostic (Pull Model)

**Request Parameters** (`DocumentDiagnosticParams`):
```typescript
{
    textDocument: { uri: string },
    previousResultId?: string,  // SINGULAR string for incremental updates
    partialResultToken?: ProgressToken,
    workDoneToken?: ProgressToken
}
```

**Key characteristics:**
- Standard request/response pattern with matching ID
- Response includes `resultId` (server-provided version)
- Uses `previousResultId` (singular) for incremental diagnostics
- Response returns `items` array with diagnostics
- Blocking call - await response before continuing

**Example request:**
```json
{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "textDocument/diagnostic",
    "params": {
        "textDocument": { "uri": "file:///path/to/file.py" },
        "previousResultId": "6"  // From previous response
    }
}
```

**Example response:**
```json
{
    "jsonrpc": "2.0",
    "id": 5,
    "result": {
        "kind": "full",
        "resultId": "7",  // New diagnostic version
        "items": [...]
    }
}
```

### workspace/diagnostic (Streaming Model)

**Request Parameters** (`WorkspaceDiagnosticParams`):
```typescript
{
    previousResultIds: [{ uri: string, value: string }],  // ARRAY of {uri, value}
    partialResultToken?: ProgressToken,
    workDoneToken?: ProgressToken
}
```

**Key characteristics:**
- Fire-and-forget pattern (request never resolves)
- Server streams results via `$/progress` using `partialResultToken`
- Uses `previousResultIds` (array) for multiple documents
- Progress lifecycle: `begin` → `report` → `end` via `workDoneToken`
- **No response awaited** - diagnostics arrive exclusively via notifications

**Example request:**
```json
{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "workspace/diagnostic",
    "params": {
        "partialResultToken": "abc-123",
        "workDoneToken": "xyz-789",
        "previousResultIds": [
            { "uri": "file:///path/to/file.py", "value": "6" }
        ]
    }
}
```

**Server streams via $/progress:**
```json
// Progress begin
{
    "jsonrpc": "2.0",
    "method": "$/progress",
    "params": {
        "token": "xyz-789",  // workDoneToken
        "value": { "kind": "begin", "title": "Analyzing..." }
    }
}

// Diagnostic report with items
{
    "jsonrpc": "2.0",
    "method": "$/progress",
    "params": {
        "token": "abc-123",  // partialResultToken
        "value": {
            "items": [
                {
                    "uri": "file:///path/to/file.py",
                    "version": 3,
                    "kind": "full",
                    "diagnostics": [...]
                }
            ]
        }
    }
}

// Progress end
{
    "jsonrpc": "2.0",
    "method": "$/progress",
    "params": {
        "token": "xyz-789",
        "value": { "kind": "end" }
    }
}
```

---

## Version Tracking: Critical Distinction

### Document Version (Client-Managed)

- **Purpose**: Track content edits for `textDocument/didChange`
- **Who manages**: Client
- **Lifecycle**: Starts at 1, increments on each change, never resets
- **Used in**: `didChange.version`, `WorkspaceDiagnosticCache.version`

```python
@dataclass
class FileState:
    document_version: int = 0  # Increment on didChange
```

### Diagnostic Version / resultId (Server-Managed)

- **Purpose**: Track diagnostic computation state
- **Who manages**: Server (internal integer, exposed as `resultId` string)
- **Lifecycle**: Resets to 0 on file open, increments on each recomputation
- **Relationship**: `resultId` = `diagnostic_version.toString()`

**Key insight**: `resultId` in diagnostic responses is just the server's internal diagnostic version converted to a string.

```typescript
// Server-side (BasedPyright)
const result: DocumentDiagnosticReport = {
    kind: 'full',
    resultId: sourceFile?.getDiagnosticVersion()?.toString(),  // Integer → String
    items: [],
};
```

**Version increment on recompute:**
```typescript
// packages/pyright-internal/src/analyzer/sourceFile.ts (L1129-1131)
private _recomputeDiagnostics(configOptions: ConfigOptions) {
    this._writableData.diagnosticVersion++;  // Incremented each time
```

```python
@dataclass
class FileState:
    last_result_id: Optional[str] = None  # Cached resultId from server
```

### On Document Close

When closing a document:
- Reset `last_result_id` to `None` (diagnostic version no longer valid)
- Keep `document_version` (content history preserved)
- Set `is_open` to `False`

```python
async def close_text_document(self, uri: str) -> None:
    if uri in self._file_states:
        self._file_states[uri].last_result_id = None  # Reset diagnostic version
        self._file_states[uri].is_open = False
```

### Unchanged Response Optimization

When sending `textDocument/diagnostic` with `previousResultId`, the server can return `kind: 'unchanged'` if diagnostics haven't been recomputed:

```json
{
    "jsonrpc": "2.0",
    "id": 5,
    "result": {
        "kind": "unchanged",
        "resultId": "7"
    }
}
```

```typescript
// Server-side logic (packages/pyright-internal/src/languageServerBase.ts L1602-1607)
if (diagnosticsVersion === previousResultId) {
    result.kind = 'unchanged';
    result.resultId = diagnosticsVersion.toString();
    delete result.items;  // No need to send items
}
```

This saves bandwidth when diagnostics are current.

---

## CLI Version Management

Your CLI tracks one version per file: **client document version**. The server maintains an internal diagnostic version that resets to 0 on file open.

### Version Lifecycle

| Event | Client Version | Server Diagnostic Version | Action |
|-------|----------------|---------------------------|--------|
| Open file | Set/continue version (e.g., 5) | Server resets to 0 | Send `didOpen` with version |
| Change file | Increment (5 → 6) | Server recomputes | Send `didChange` with new version |
| Close file | Keep version unchanged | Unchanged | Send `didClose` |
| Reopen file | Continue/increment (6 → 7) | Server resets to 0 | Send `didOpen` with new version |

### Implementation Pattern

```python
@dataclass
class FileVersionTracker:
    versions: dict[str, int] = field(default_factory=dict)
    diagnostics: dict[str, list[dict]] = field(default_factory=dict)
    
    def next_version(self, uri: str) -> int:
        """Get next version number for uri. Increments from last value."""
        current = self.versions.get(uri, 0)
        next_v = current + 1
        self.versions[uri] = next_v
        return next_v
    
    def on_file_open(self, uri: str, content: str) -> None:
        version = self.next_version(uri)
        self._send({
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {"uri": uri, "version": version, "text": content}
            }
        })
    
    def on_file_change(self, uri: str, content: str) -> None:
        version = self.next_version(uri)
        self._send({
            "method": "textDocument/didChange",
            "params": {
                "textDocument": {"uri": uri, "version": version},
                "contentChanges": [{"text": content}]
            }
        })
    
    def on_file_close(self, uri: str) -> None:
        # Version persists for next open
        self._send({
            "method": "textDocument/didClose",
            "params": {"textDocument": {"uri": uri}}
        })
    
    def on_diagnostics(self, params: dict) -> None:
        uri = params["uri"]
        version = params.get("version")
        diagnostics = params.get("diagnostics", [])
        
        # Only store if version matches current
        if version == self.versions.get(uri):
            self.diagnostics[uri] = diagnostics
```

### Server Internal Behavior

When a file is opened, the server resets its internal diagnostic version to 0:

```typescript
// BasedPyright: packages/pyright-internal/src/analyzer/program.ts (L447-453)
sourceFileInfo.isOpenByClient = true;
// Reset the diagnostic version so we force an update to the
// diagnostics, which can change based on whether the file is open.
sourceFileInfo.diagnosticsVersion = 0;
```

---

## Stale resultId Detection

When a `textDocument/diagnostic` response arrives, the server may return the same `resultId` if the document hasn't changed. You MUST detect and skip stale results.

### Numeric Comparison

```python
def _result_id_greater(new_id: str, cached_id: str) -> bool:
    """Compare two resultIds. Returns True if new_id is newer than cached_id."""
    if not new_id or not cached_id:
        return bool(new_id)  # Treat empty as older
    try:
        return int(new_id) > int(cached_id)  # Numeric comparison
    except ValueError:
        return new_id > cached_id  # Fallback to lexicographic
```

### Update Logic

```python
def _process_diagnostic_response(self, result: dict, context_uri: str) -> None:
    result_id = result.get("resultId")
    state = self._file_states[context_uri]
    cached_id = state.last_result_id

    if cached_id is None or _result_id_greater(result_id, cached_id):
        # New result - update cache
        state.last_result_id = result_id
        state.diagnostics = result.get("items", [])
    else:
        # Stale result - skip (document unchanged)
        log_info(f"Skipping stale resultId '{result_id}' (cached: '{cached_id}')")
```

---

## Common Mistakes and Fixes

### Mistake 1: Adding Non-Existent `version` Parameter

**Wrong:**
```python
params={
    "partialResultToken": token,
    "workDoneToken": work_done_token,
    "version": version,  # ❌ This parameter doesn't exist!
    "previousResultIds": [],
}
```

**Correct:**
```python
params={
    "partialResultToken": token,
    "workDoneToken": work_done_token,
    "previousResultIds": [],  # ✅ No version parameter
}
```

The `workspace/diagnostic` request does NOT accept a `version` parameter. Version tracking is done via `previousResultIds` array.

### Mistake 2: Regenerating Tokens Each Request

**Wrong:**
```python
async def request_diagnostics(self) -> None:
    # Generate NEW tokens every time ❌
    token = str(uuid.uuid4())
    work_done_token = str(uuid.uuid4())
```

**Correct:**
```python
# In __init__:
self._workspace_diagnostic_tokens: Optional[dict[str, str]] = None

async def request_diagnostics(self) -> None:
    # Initialize constant tokens ONCE
    if self._workspace_diagnostic_tokens is None:
        self._workspace_diagnostic_tokens = {
            "partial_result_token": str(uuid.uuid4()),
            "work_done_token": str(uuid.uuid4()),
        }

    tokens = self._workspace_diagnostic_tokens  # Reuse same tokens
```

Tokens must remain constant throughout the session for proper progress tracking.

**Token reset behavior**: Tokens persist across server restarts and connection drops. When reconnecting, initialize new tokens; do not reuse stale tokens from a previous connection session.

### Mistake 3: Confusing previousResultId vs previousResultIds

| Request | Parameter Name | Type | Format |
|---------|---------------|------|--------|
| `textDocument/diagnostic` | `previousResultId` | Singular string | `"6"` |
| `workspace/diagnostic` | `previousResultIds` | Array | `[{uri, value}]` |

**Wrong:**
```python
# Using array format for textDocument/diagnostic ❌
{"previousResultIds": [{"uri": uri, "value": "6"}]}
```

**Correct:**
```python
# Using singular string for textDocument/diagnostic ✅
{"previousResultId": "6"}
```

### Mistake 4: Awaiting Response for workspace/diagnostic

**Wrong:**
```python
# Registering workspace/diagnostic as pending request ❌
result = await self.send_request("workspace/diagnostic", params)
```

**Correct:**
```python
# Fire-and-forget - don't register as pending request ✅
request_id = self._next_request_id()
msg = LSPMessage(id=request_id, method="workspace/diagnostic", params=params)
await self._send_message(msg)
# No await for response - diagnostics arrive via $/progress
```

The `workspace/diagnostic` request promise never resolves. Diagnostics arrive exclusively via `$/progress` notifications.

### Mistake 5: Not Auto-Opening Documents

Before sending `didChange` or `textDocument/diagnostic`, ensure the document is open:

```python
async def change_text_document(self, uri: str, text: str, open_text: Optional[str] = None) -> None:
    # Open first if not already open
    state = self._file_states.get(uri)
    if not state or not state.is_open:
        if open_text is not None:
            await self.open_text_document(uri, open_text)
        else:
            self._file_states[uri] = FileState(document_version=1, is_open=True)

    # Then send didChange
    state.document_version += 1
```

---

## Diagnostic Caching Pattern

Cache diagnostics in three places for query efficiency:

1. **Global `_diagnostics` dict**: Quick lookup by URI
2. **`FileState.diagnostics`**: Per-file state cache
3. **`WorkspaceDiagnosticCache`**: Workspace-wide cache with version tracking

```python
@dataclass
class WorkspaceDiagnosticCache:
    version: Optional[int]  # Document version when computed
    diagnostics: list[dict]  # Cached diagnostic items
```

**Update all three on every diagnostic arrival:**
```python
def _store_diagnostics(self, items: list[dict]) -> None:
    for item in items:
        uri = item.get("uri", "")
        diagnostics = item.get("diagnostics", [])
        version = item.get("version")

        if uri and diagnostics is not None:
            self._diagnostics[uri] = diagnostics
            if uri in self._file_states:
                self._file_states[uri].diagnostics = diagnostics
            self._workspace_diagnostics[uri] = WorkspaceDiagnosticCache(
                version=version, diagnostics=diagnostics
            )
```

**Query helper:**
```python
def is_diagnostic_current(self, uri: str, client_version: int) -> bool:
    """Check if cached diagnostics match current document version."""
    cached = self._workspace_diagnostics.get(uri)
    if cached is None:
        return False
    return cached.version == client_version
```

---

## Building previousResultIds Array

For `workspace/diagnostic` requests, build the array from file states:

```python
def _build_previous_result_ids(self) -> list[dict[str, str]]:
    """Build previousResultIds from FileState.last_result_id."""
    result = []
    for uri, state in self._file_states.items():
        if state.last_result_id:
            result.append({"uri": uri, "value": state.last_result_id})
    return result
```

This extracts the cached `resultId` values from previous `textDocument/diagnostic` responses.

---

## Implementation Checklist

Before considering LSP diagnostic implementation complete:

- [ ] **Token handling**: Constant tokens for workspace diagnostics (not regenerated)
- [ ] **Version separation**: Document version (client) vs resultId (server) tracked separately
- [ ] **Stale detection**: `_result_id_greater()` comparison before updating cache
- [ ] **Fire-and-forget**: workspace/diagnostic not registered as pending request
- [ ] **Auto-open**: Documents opened before didChange/textDocument/diagnostic
- [ ] **Caching**: Three-way caching (global, per-file, workspace)
- [ ] **Progress handling**: Both `partialResultToken` and `workDoneToken` tracked
- [ ] **Parameter names**: `previousResultId` (singular) vs `previousResultIds` (array)
- [ ] **No version parameter**: workspace/diagnostic doesn't accept version parameter

---

## Reference Files

The `reference/` subdirectory contains LSP specification excerpts relevant to this guide:

- **`reference/3.17.md`** - LSP 3.17 pull diagnostics spec (textDocument/diagnostic, workspace/diagnostic, version tracking)

---

## When to Use This Skill

Use this skill when:
- Implementing LSP diagnostic features (pull model)
- Debugging diagnostic versioning issues
- Handling `$/progress` notifications
- Confused about `previousResultId` vs `previousResultIds`
- Building workspace diagnostics with streaming
- Implementing stale result detection
- Setting up token-based progress tracking
