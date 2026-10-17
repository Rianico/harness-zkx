# 20. A2A Markdown frontmatter envelope

Date: 2026-10-15

## Status

Accepted

## Context

Herdr previously formatted inter-agent messages using a custom Style 2 nested YAML envelope. The envelope rendered `Routing:`, `Hierarchy:`, and `Protocol:` sections with a leading bracket timestamp `[2026-...]`.

This format broke generic Markdown frontmatter parsers. It also lacked standardized agent-to-agent lifecycle semantics. Downstream tools required ad-hoc regex parsers to extract sender addresses, task IDs, and completion signals. Agents could not track task state transitions through standard state machines.

## Decision

We adopt the Linux Foundation and Google Agent2Agent (A2A) protocol schema (`a2a.proto`) for inter-agent envelopes.

Every dispatch and reply message must use standard Markdown frontmatter. The envelope begins with `---` on line 1 and terminates with `---` before the message payload.

The top-level frontmatter schema is strictly limited to canonical A2A fields:

- `id`: unique Task-ID string (for example, `#182-herdr-msg-enhance#overview-rich`).
- `context_id`: agent session ID derived from `CallerContext.session_id`.
- `status`: canonical `TaskStatus` object containing `state` and `timestamp`.
  - `state`: lifecycle state enum (`TASK_STATE_WORKING`, `TASK_STATE_COMPLETED`, `TASK_STATE_FAILED`, `TASK_STATE_INPUT_REQUIRED`).
  - `timestamp`: ISO 8601 UTC timestamp string.
- `metadata`: harness-specific extension fields:
  - `ticket_id`: high-level ticket reference (for example, `#182-herdr-msg-enhance`).
  - `sender`: sender address formatted as `<agent>@<pane_id>` (for example, `refactor-impl@w11:p3`).
  - `receiver`: recipient address formatted as `<agent>@<pane_id>` (for example, `refactor-orch@w11:p1`).
  - `task_group`: task group identifier formatted as `<group_slug>@<tab_id>` (for example, `refactor-herdr@w11:t7`).
  - `in_reply_to`: referenced Task-ID on reply envelopes.

The frontmatter `status.state` field is authoritative for task completion, failure, and required input.

When tasks settle and workers are spawned, lane kick-off automatically reconciles generic names. It sets the tab title to `<task_group>` and caller pane to `<task_group>-orch` if generic.

Physical multiplexer IDs (`pane_id`, `tab_id`) serve as the immutable anchors and source of truth. At dispatch and reply time, the harness runs an active reconciliation pass:
- If a worker process restarted without an agent name, the harness re-registers `herdr agent rename <pane_id> <name>` and `herdr pane rename <pane_id> <name>`.
- If the tab title drifted from `<task_group>`, the harness re-registers `herdr tab rename <tab_id> <task_group>`.
- If the sending orchestrator dropped its name, the harness re-registers `herdr agent rename <pane_id> <task_group>-orch`.

This change is a clean cutover with zero backward compatibility or dual-read shims. The legacy Style 2 format is completely retired.

### Considered Options

- Rejected: RFC 5322 email headers. They lack task lifecycle state machine semantics.
- Rejected: STOMP or NDJSON frames. They destroy Markdown legibility for LLM reasoning and human operators.
- Rejected: Style 2 nested YAML. The custom format requires bespoke parsers and breaks standard Markdown frontmatter tooling.

## Consequences

- All inter-agent messages conform to standard A2A protocol semantics.
- Standard frontmatter parsers parse message envelopes directly without custom regexes.
- Frontmatter `status.state` serves as the single source of truth for task status.
- Lane kick-off reconciliation maintains consistent tab titles and pane names across the task lifecycle.
- Legacy Style 2 envelopes fail immediately because no backward-compatibility shims exist.
- Dispatch and reply scripts must emit valid A2A frontmatter on first release.
