# Remediation — Unify a Drifted ADR Log

Use when an ADR log predates the canonical template or accumulated custom
conventions: model-invented formats beside CLI output, custom link verbs,
rationale in `## Status`, missing reverse links, dead `Superseded` claims.

## Constraints (non-negotiable)

- Append-only. Bodies of accepted records freeze; never rewrite history.
- Sanctioned mutations only: status and relationship lines, made through
  `adr new -s` / `adr link` (or exact-format hand edits where the CLI has no
  reverse-only operation).
- Relocate facts, never delete them. Trimming `## Status` prose moves those
  sentences into Context/History, preserving meaning.

## Procedure

1. **Single-source the template.** Run `$SKILL_DIR/bin/sync-template [adr-dir]`.
   All future `adr new` output then matches the model format by construction.
2. **Inventory.** Dump every `## Status` block (`sed -n '/## Status/,/## Context/p' docs/adr/*.md`).
   List link verbs in use and flag non-canonical ones.
3. **Remap verbs** to the canonical table in `SKILL.md` (Relationship Heuristics):
   `implements/supports/derives from/enforces` → `Relates to`;
   `refines/refined by` → `Amends/Amended by`. One link line per relation —
   delete exact duplicates.
4. **Link-integrity audit.** Every forward link needs its reverse:
   `Supercedes↔Superceded by`, `Amends↔Amended by`, `Clarifies↔Clarified by`,
   `Relates to↔Relates to`. Script:
   ```python
   import re, pathlib
   links = {}
   for f in sorted(pathlib.Path("docs/adr").glob("00*.md")):
       status = f.read_text().split("## Status")[1].split("## Context")[0]
       links[f.name[:4]] = set(re.findall(r"\]\((00\d\d)-[^)]*\.md\)", status))
   for src, tgts in links.items():
       for t in tgts:
           if src not in links.get(t, set()):
               print(f"dangling: {src} -> {t}")
   ```
   Add missing reverses in exact CLI format. Context-body mentions (such as a
   numbering-collision note) are not relationship lines — leave them.
5. **Trim `## Status`** to the status word plus relationship lines. Move
   rationale into Context (`Note:`) and draft history into a `History:`
   paragraph at the top of Context.
6. **Dead `Superseded` claims.** A `Superseded` status with no superseding
   record is a dangling pointer. Mint the missing decision with
   `EDITOR=true adr new -s <ref> <title>` (retroactive: original date on
   `Date:`, recording date noted in Context). The CLI inserts both link sides.
7. **Verify.** Re-run the audit (expect clean), `adr list` (numbering intact),
   and `pytest tests/adr`.

## Worked case

`everything-claude-code` ADRs 0001–0022 (2026-10-30): installed
`docs/adr/templates/template.md` via sync script, remapped 6 verbs across 8
records, closed 7 dangling links, relocated status prose in 0014/0015/0016,
minted retroactive 0023 superseding 0002, deduped 0008/0009. Bodies of
accepted records unchanged.
