# Rules — Authoring and Harness Scoping

Rules are Markdown files under `rules/`. Frontmatter scopes a rule: `paths:` by
touched project files, `agents:` by harness. A rule without either key is
always-on and loads everywhere.

## Who reads which tree

| Harness | Rule tree | Assembly |
| ------- | --------- | -------- |
| pi | `~/.pi/agent/rules` | `pi-better-rules`, directory symlinks into this repo's `rules/` |
| Claude Code, Codex, Antigravity | `~/.claude/rules` and its siblings | external `distributions/` tree, absent from this repo |
| any | `<project>/.pi/rules` | project rules; an identical relative path replaces the global copy |

Two properties decide where a rule belongs:

1. pi walks the directories symlinked under `~/.pi/agent/rules`, so every `*.md` in
   a linked directory reaches every pi system prompt.
2. `pi-better-rules` honours `paths:` and `agents:`
   (`~/development/ai/pi-better-rules/src/scanner.ts`). A rule reaches pi only when
   both filters allow it.

## Harness scoping

`agents:` frontmatter scopes a rule to named harnesses. The harness ids are `pi`,
`claude`, `codex`, and `agy`.

| `agents:` value | Behaviour |
| --------------- | --------- |
| absent | every harness loads the rule |
| list of ids | only the listed harnesses load it |
| empty list | no harness loads it |
| malformed | the loader warns and loads the rule |

`paths:` still applies independently. A rule loads only when both filters pass.

`rules/common/tool-preferences-bash.md` declares `agents: [claude, codex, agy]`.
pi skips the bash block; the non-pi trees keep it. `Rianico/pi-better-rules` owns
the loader change (`src/scanner.ts` `parseRule`, and `docs/rules-authoring.md`).
Until that release lands, pi still loads the file.

## Bash tool choices vs everything else

`rules/common/tool-preferences-bash.md` owns the preferred binary for a shell
command: `rg`, `fd`, `eza`, `uv`, `pnpm`, `tsx`, `oxlint`, `oxfmt`. It declares
the non-pi harnesses, so pi drops the file whole.

`rules/common/tool-preferences.md` keeps every preference a binary check cannot
enforce: version pinning and workspaces (`.python-version`, `.tool-versions`,
`pnpm -r`, `packageManager`, `.nvmrc`), one command per call, `read` over `cat`,
line endings, paths, code navigation, `$SKILL_DIR` resolution, and runtime
build/test commands (`tsc`, `vitest`, `vite`, cargo, go, asdf).

## Authoring rule

Add a bash binary preference to `rules/common/tool-preferences-bash.md`. Add any
other tool preference to `rules/common/tool-preferences.md`. Split a bullet that
mixes both: the binary choice moves, the workflow rule stays. Keep the split
file-granular, so a harness can drop one file without a content edit.
