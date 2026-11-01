# LSP — Cheatsheet

- **Version:** 3.17
- **Date:** 2026-11-01
- **Source:** [LSP 3.17 specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)
- **Author:** Microsoft
- **Brief:** Decision rules, lifecycle trade-offs, diagnostic versioning rules, and smells for LSP 3.17 client and server work.

## Decision rules

| When you need to | Do this | Because |
| --- | --- | --- |
| stop a server | send `shutdown` request, then `exit` notification, then stop transport | `exit` without `shutdown` kills in-flight cleanup |
| start a server for a CLI tool | initialize lazily on the first request | daemon startup stays fast and idle servers cost nothing |
| start a server for an IDE-like client | initialize eagerly at client start | the first user request must not wait on startup |
| read diagnostics for one file | send `textDocument/diagnostic` with `previousResultId` string | the pull model returns a matching `resultId` |
| read diagnostics for a workspace | send `workspace/diagnostic` and never await it | results stream back through `$/progress` |
| track content edits | increment the client `documentVersion` | servers reject edits with a stale version |
| skip a recompute | send the cached `previousResultId` or `previousResultIds` | unchanged documents return `unchanged` |
| stream partial results | pass a constant `partialResultToken` | a per-request token loses the stream |
| report long work | pass a constant `workDoneToken` and send begin, report, end | the client renders one progress bar per token |
| cancel a request | send `$/cancelRequest` with the original id | the server aborts only that request |
| shut a daemon down | stop child servers before the socket or transport closes | children orphan when the parent dies first |
| re-initialize after shutdown | reset `_initialized`, `_client`, and workspace maps | a stale flag blocks the second `initialize` |

## Lifecycle trade-offs

| Strategy | Startup cost | First request | Idle cost | Pick when |
| --- | --- | --- | --- | --- |
| Lazy initialize | low | slow once | none | CLI tools, short sessions |
| Eager initialize | high | fast | process resident | IDE clients, long sessions |
| One server per workspace | medium | fast | scales with workspaces | isolation matters more than memory |
| One shared server | low | fast | one process | workspaces share a project root |
| In-process client | none | fastest | ties to host | tests and single-language hosts |

## Sequencing rules

| Step | Message | Wait for reply | Notes |
| --- | --- | --- | --- |
| 1 | `initialize` | yes | send client capabilities |
| 2 | `initialized` | no | fire-and-forget notification |
| 3 | requests and notifications | per message type | requests carry an id |
| 4 | `shutdown` | yes | server releases resources |
| 5 | `exit` | no | server process ends |
| 6 | transport stop | no | terminate, then reap |

## Diagnostic and versioning rules

- The client owns the document version. It increments on every edit and never resets.
- The server owns `resultId`. It is a string, and it resets to `0` when the document opens.
- Compare `resultId` values numerically first, then fall back to string order.
- `textDocument/diagnostic` takes `previousResultId` (singular string).
- `workspace/diagnostic` takes `previousResultIds` (array of `{uri, value}`).
- `workspace/diagnostic` accepts no `version` parameter. Reject the idea early.
- On document close, drop `last_result_id`, keep `document_version`, and set `is_open = False`.
- Open a document with `didOpen` before any `didChange` or diagnostic request.

## Tells and smells

### Tells (healthy)

- Every `initialize` has one matching `shutdown` and one `exit`.
- No server process survives daemon teardown.
- `textDocument/diagnostic` responses carry a `resultId` the client cached.
- `$/progress` streams close with an `end` value.
- Repeated diagnostic requests return `unchanged` for untouched files.

### Smells (problems)

| Smell | Cause | Fix |
| --- | --- | --- |
| orphaned server after client exit | transport stopped before `shutdown` and `exit` | send `shutdown`, then `exit`, then stop transport |
| `workspace/diagnostic` request hangs | client awaits a fire-and-forget request | stop awaiting and read `$/progress` |
| diagnostics never refresh | `previousResultId` never updated from the response | cache the returned `resultId` |
| progress bar stuck open | missing `$/progress` `end` for the token | send `end` for every `begin` |
| server rejects `didChange` | stale `documentVersion` | increment the version on each edit |
| second `initialize` ignored | `_initialized` never reset | reset state inside the shutdown path |
| duplicate result streams | token regenerated per request | create tokens once per session |
| diagnostics for closed files | cache not cleared on `didClose` | clear per-document cache on close |

## Quick reference: core methods

| Method | Kind | Purpose |
| --- | --- | --- |
| `initialize` | request | exchange capabilities |
| `initialized` | notification | confirm startup |
| `shutdown` | request | request graceful stop |
| `exit` | notification | end the server process |
| `textDocument/didOpen` | notification | register document content |
| `textDocument/didChange` | notification | publish edits with a version |
| `textDocument/didClose` | notification | release document state |
| `textDocument/diagnostic` | request | pull diagnostics for one document |
| `workspace/diagnostic` | request | pull diagnostics for the workspace |
| `$/progress` | notification | stream partial results and work progress |
| `$/cancelRequest` | notification | cancel a pending request |
| `workspace/didChangeConfiguration` | notification | push settings to the server |
