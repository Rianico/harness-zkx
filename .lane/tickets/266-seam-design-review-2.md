# Review ticket 2: methodology lens on the pr-land seam (#266, ADR-0021)

Ticket ID: `#266-seam-design-review-2`. Same agent, same cwd. **Read-only**: do not edit, create, or delete any file. Report findings only.

## Rulings on your first review

Confirmed against the code and folded in: state-coverage gaps (`pr_state`, `body_state`, `worktree_clean`), the missing squash preview after `draft.json` deletion, the read-only push hazard, `_remote_branch_exists` hardcoding `origin` (`_github.py:290`), `stamp_changelog` non-idempotence (`_changelog.py:126`), the branch-scoped leaf default, and the widened migration list. Gating the title before creation under `--merge` is adopted.

**Rejected: your finding 10 (`--ready` for a reused draft PR).** I checked for automation callers and found none. The repo's only non-test reference to `pr.py` is a hint string at `scripts/changelog-gate.py:399`; `.github/workflows/tests.yml:36` mentions `pr.py --watch` only in a comment explaining why CI guards it differently; `skills/branch-worktree-pr/scripts/{open_pr,merge_pr}.py` is a separate older implementation; `pr.sh` is an exec shim the model runs. The maintainer's ruling is stronger than my check: **every script in this repo is designed for an LLM caller.** Unattended automation is out of scope by design, so a transition the caller can paste is a complete capability. Re-open this only by naming a caller class that exists in the repo with a file path.

Also note: two of your line citations were off (the title gate is `pr.py:578`, not `675`/`758`). Keep citing lines you have read.

## Changed since your review

Read the current text, not your memory of it:

1. `docs/adr/0021-pr-land-derives-state-and-emits-facts-instead-of-persisting-artifacts.md` (working tree, uncommitted) — decision items 1-4 and Consequences revised.
2. `gh issue view 266 --repo Rianico/harness-zkx` — 9-item acceptance spec, migration list, and a provenance paragraph recording which findings were folded and which was rejected.
3. `GLOSSARY.md` — five entries under **Pull Request Lifecycle**.

Deltas to verify: divergence moved from the judgment list to mechanical impossibility (refusing only on mutating commands); `--status` never refuses; the default leaf is the head-ref slug; the squash preview stays an output; the predicate set gained `pr_state`, `body_state`, `worktree_clean`; the push precondition is scoped to `create_or_reuse_pr`; stamp recovery must push a stranded commit; the `--merge` title gate runs before creation.

## New task

Review the same target through two methodology lenses. Enter **keel in its Judgment state** — the target is fixed, do not propose a different design. Finish Open with evidence if the target is infeasible.

### A. `ai-engineering-expert`

Read `.agents/skills/ai-engineering-expert/SKILL.md` completely. Load the subskills you need from `skills/ai-engineering-expert/subskills/<name>/SKILL.md` — `verification`, `writing-for-agents`, `skill-authoring`, `subagent-engineering` are the likely ones. Then judge:

1. **Formal substrate vs semantic reasoner.** The ADR reserves mechanical constraints for checks and judgment for the model. Does the design actually land that way, or does it push a mechanical constraint into markdown steering that a check should own? Name any item where the ADR describes a rule the code must merely *obey*.
2. **EDD (`verification` subskill).** Take #266's 9 items. Which are falsifiable by a command or test, and which are unverifiable prose? Name each unverifiable item.
3. **Context pressure asymmetry.** `--status` and the refusal payloads are read by a model with minimum context. Are they complete enough to act on without re-reading the code, and short enough not to crowd it? Would the reviewer ever need to explore to act?
4. **Writing for agents.** For the transition list and `refusals[]` shape as specified in #266 and ADR-0021 item 3: are the completion criteria explicit, the leading words unambiguous, and the payload pointer-first? Quote the weakest line.
5. **Pruning no-ops.** Which of the 9 items could be deleted with no measurable change in agent behaviour? Answer per item.

### B. `keel` (Judgment state)

Read `.agents/skills/keel/SKILL.md` completely, plus the references it points you to. Then judge:

1. **Responsibility and authority.** pr-land holds no state. Is the authority split between git, `gh`, and the tool declared clearly enough that a future maintainer cannot create a second source of truth?
2. **Interfaces and contracts.** The interface is the predicate set, the transition list, and the refusal classes. Which parts are durable, and which will drift the moment implementation starts? Where is the contract not yet pinned?
3. **Dependency, state, and recovery.** Derived state means `git` and `gh` are hard dependencies. What is the declared behaviour when either is unavailable or unauthenticated, and who owns recovery?
4. **Structural seams.** Is `.lsz/gh-router/` plus stdout the right seam? Does the tool-owned prefix create a second authority alongside `scripts/state.sh` (which already derives branch/PR orientation), and is the boundary between them stated?
5. **Guards and exceptions.** The refusal classification splits mechanical impossibility, contract violations, and judgment calls. Is the boundary principled, or will the first convenient exception erode it? Name the most likely erosion case.
6. **Migration, retirement, deletion.** What is retired (`draft.json`, `--out-dir`, scaffold signature, `is_untouched_scaffold`) and what becomes dead? Is anything retired while a live consumer remains — check `pr-refine`, `pr-enhance`, `tests/`, and `scripts/state.sh`, not just `pr-land`.
7. **Rewrite risk.** Nine items in one PR. Is that a refactor or a rewrite in disguise? Which items could land independently and which are genuinely coupled?

## Deliverable

Severity-ordered (`blocker` / `major` / `minor`). Each finding: one-line claim, evidence (`file:line` you read, or the skill section), the failure scenario, and the smallest change that fixes it. End with **Checked and clean** (what you examined and found sound) and **Not checked** (what you skipped). Mark anything you could not verify. Keep it under 150 lines. Do not restate the ADR and do not propose a rewrite.

## Reply

Write the reply to a file, then:

```
uv run skills/herdr/scripts/herdr_reply.py pi --file <your-reply-file>
```

Status word: `DONE`, `BLOCKED`, or `FAILED`. Put the findings in the reply, not only in the file.
