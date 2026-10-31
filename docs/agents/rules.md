# Rules — Authoring and Harness Scoping

Rules are Markdown files under `rules/`. A `paths:` frontmatter list scopes a rule
to matching project files. A rule without `paths:` is always-on.

## Who reads which tree

| Harness | Rule tree | Assembly |
| ------- | --------- | -------- |
| pi | `~/.pi/agent/rules` | `pi-better-rules`, directory symlinks into this repo's `rules/` |
| Claude Code, Codex, Antigravity | `~/.claude/rules` and its siblings | external `distributions/` tree, absent from this repo |
| any | `<project>/.pi/rules` | project rules; an identical relative path replaces the global copy |

Two properties decide where a rule belongs:

1. pi walks the directories symlinked under `~/.pi/agent/rules`, so every `*.md` in
   a linked directory reaches every pi system prompt.
2. `pi-better-rules` honours only `paths:` (`~/development/ai/pi-better-rules/src/scanner.ts`). It has no harness key and no per-file exclude.

## Bash tool choices vs everything else

`rules/common/tool-preferences-bash.md` owns the preferred binary for a shell
command: `rg`, `fd`, `eza`, `uv`, `pnpm`, `tsx`, `oxlint`, `oxfmt`. The file stays
separate so a harness tree can drop it whole.

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

## Blocked: dropping one file for pi

pi and the non-pi harnesses read the same `rules/common` directory today. No file
edit can omit the bash block for pi alone. One of two external contracts closes
the gap:

1. **Loader key — `pi-better-rules`** (local `~/development/ai/pi-better-rules`,
   vendored at `~/.pi/agent/extensions/rules-injector.ts` and
   `extensions/rules/scanner.ts`). `parseRule` gains an `agents:`
   frontmatter allowlist. An absent key loads for every harness, which keeps
   today's default. A present key loads only when the running harness id is
   listed. pi's id is `pi`. `rules/common/tool-preferences-bash.md` then declares
   `agents: [claude, codex, agy]`. Non-pi assemblies ignore the unknown key, so
   they keep loading the file.
2. **Assembly exclusion — dotfiles tree** (`~/stowfiles/dotfiles/.pi/agent/rules`).
   Replace the `common` directory symlink with per-file symlinks that omit
   `tool-preferences-bash.md`, or materialize a pi tree without it. This works
   with the current loader and needs no code change.

Track the chosen contract in `Rianico/harness-zkx#340`.
