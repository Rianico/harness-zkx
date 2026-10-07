# Agent Command Grammar

Machine-Targeted STE Flavor: the structural rules a model-primary artifact adds on top of the shared rules. Read [plain-language.md](../../../references/plain-language.md) first. It owns the lexical dial, mode selection, and every sentence-level rule. Those rules include active voice, nominalizations, banned words, one term per concept, normative keywords, and pinned-text rewrites.

Apply this file to tool/function descriptions, error messages, system prompts, inter-agent instructions (`herdr`), and procedural runbooks (`AGENTS.md`, procedural `SKILL.md` bodies).

| Rule | Limit |
| --- | --- |
| [Single action per sentence](#single-action-per-sentence) | 1 action, ≤20 words per instruction (STE Rule 5.1) |
| [Front-loaded branching guards](#front-loaded-branching-guards) | `If <condition>, then <action>` |
| [Technical token insulation](#technical-token-insulation) | Backtick every code token |

## Single action per sentence

- Limit each sentence to exactly one action.
- Never join consecutive actions with `and then`, semicolons, or comma splices.
- Compound sentences tempt the model into premature completion or partial step execution.

**Bad:**
> Read the configuration file and then extract the database credentials, verifying they are non-empty.

**Good:**
> Read the configuration file. Extract the database credentials. Verify the credentials are non-empty.

## Front-loaded branching guards

Place conditional checks and guards before the action: `If <condition>, then <action>`.

- Trailing conditions (`<action> if <condition>`) cause agents to begin generating tool calls before attending to the guard.
- Front-loading forces the model to evaluate the prerequisite state before emitting the command.

**Bad:**
> Roll back the migration if any integration test fails.

**Good:**
> If any integration test fails, roll back the migration.

**Bad:**
> Dispatch worker tasks once the queue size exceeds 100 items.

**Good:**
> When the queue size exceeds 100 items, dispatch worker tasks.

## Technical token insulation

Wrap every code symbol, CLI command, parameter, file path, and HTTP method in backticks (`` `...` ``):

- Backticking shields tokens from natural language tokenization ambiguity.
- Deterministic linters exclude inline code spans from prose word count calculations.

**Bad:**
> Run uv run pytest on tests/unit/test_auth.py with the verbose flag.

**Good:**
> Run `uv run pytest -v` on `tests/unit/test_auth.py`.
