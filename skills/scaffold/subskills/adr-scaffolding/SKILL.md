---
name: adr-scaffolding
description: >-
  ADR path scaffolding — writes `.adr-dir` to point the `adr` CLI at `docs/adr` and keeps `.adr-dir` out of version control. Use when initializing or retrofitting an ADR repository, wiring the adr-tools location, or fixing a repo whose `.adr-dir` is missing or tracked.
metadata:
  managed-by: scaffold
---

# ADR Scaffold

Owns the ADR path projection of the scaffold spine. The `adr` CLI (see the `adr` skill) locates its ADR repository through a `.adr-dir` file in the project root; this subskill writes that pointer deterministically and keeps the pointer itself out of version control.

## Deterministic Artifact — Tool Owns Bytes

The ADR path is a single byte source: `.adr-dir` containing the target directory (default `docs/adr`). The `adr` CLI reads `.adr-dir` to resolve where ADRs live, so the file is the contract between the tool and the repo.

```bash
echo "docs/adr" > .adr-dir
```

- `.adr-dir` is a **local pointer**, not project content — it encodes the machine's adr-tools layout, so it belongs in `.gitignore`, never in the commit.
- The ADR directory itself (`docs/adr/`) **is** project content — it holds the ADR markdown files and is tracked normally. Only the `.adr-dir` pointer is ignored.
- `.gitignore` is patched append-only with dedup (never rewrites existing entries), matching the git-flavor convention.

## Steps — Tool Owns Determinism

1. Write the pointer: `echo "docs/adr" > .adr-dir`
2. Ignore the pointer: append `.adr-dir` to `.gitignore` (dedup — skip if already present)
3. Verify: `git status` shows `.adr-dir` as ignored (not untracked) and `docs/adr/` as tracked content; `adr list` resolves the repository

> [!tip] Verification
>
> - `git check-ignore .adr-dir` → prints the path (exit 0) when the ignore is live
> - `git status --short` shows no `.adr-dir` entry
> - `adr list` lists ADRs from `docs/adr/` — confirms the pointer resolves

## Relation to Other Subskills

- Do not duplicate `.gitignore` handling — the git flavor owns the append-only/dedup seam (`append_gitignore`); this subskill adds the single `.adr-dir` entry to that seam.
- ADR lifecycle (create/link/supersede/list/read) is the `adr` skill's domain, not this one. This subskill only wires the path.
- The default ADR directory is `docs/adr`, matching the scaffold template `templates/git/.adr-dir` and the harness `CONTEXT.md` + `docs/adr/` single-context layout.

## Arguments

- `--dir <path>` — override the ADR directory (default `docs/adr`); writes `<path>` into `.adr-dir` and ignores `.adr-dir` regardless of target
