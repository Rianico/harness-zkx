# Review ticket: pr-land state/information seam (#266, ADR-0021)

## Role

You are a reviewer. **Read-only**: do not edit, create, or delete any file in the repo. Report findings only.

## Context

Issue [#265](https://github.com/Rianico/harness-zkx/issues/265) reported four friction points in `gh-router`'s `pr-land`. We designed one fix instead of four patches, recorded as ADR-0021, and filed issue #266 as the acceptance spec. Nothing is implemented yet: the ADR, the glossary entries, and #266 are the whole artifact so far.

Read, in this order:

1. `docs/adr/0021-pr-land-derives-state-and-emits-facts-instead-of-persisting-artifacts.md` — the decision (uncommitted, working tree).
2. `GLOSSARY.md` — the five new entries under **Pull Request Lifecycle**: `PR Landing State`, `Derived State`, `Legal Transition`, `Refusal Class`, `Scaffold Leaf`.
3. `gh issue view 266 --repo Rianico/harness-zkx` — the acceptance spec and migration list.
4. `gh issue view 265 --repo Rianico/harness-zkx` — the original friction report.
5. The code the change lands in: `skills/gh-router/subskills/pr-land/scripts/{pr.py,_draft.py,_check.py,_changelog.py,_github.py,_squash.py}`, plus `skills/gh-router/SKILL.md` and `skills/gh-router/subskills/pr-land/SKILL.md`.

## What to check

Find **potential bugs and logical issues in the workflow** — not style, not wording. Specifically:

1. **State coverage.** Enumerate the states a real `pr-land` run can be in and find the ones ADR-0021's predicate set (`branch_pushed`, `pr_exists`, `pr_draft`, `changelog_stamped`, `head_pushed`, `checks`, `mergeable`, plus `diverged`, `head_stale`, `stamp_failed`) does not cover. Consider at least: `--no-stamp`, `--check` only, detached HEAD, multiple remotes, a branch with no upstream, an existing merged or closed PR, a reused open PR, `--watch` interrupted, a PR opened in another session.
2. **Transition legality.** Are the claimed "legal transitions" actually legal and safe to re-run from any state? Where would a rerun double-act (duplicate PR, duplicate changelog entry, duplicate push)?
3. **Push precondition** (`#266` item 5). Does "push when the remote ref is missing or behind" hold for a branch whose upstream has a different name, for a non-`origin` push remote, and for the `_changelog.py:216` post-stamp push that already exists? Any ordering hazard with `stamp_changelog` committing after the PR exists?
4. **Scaffold policy** (`#266` item 3). Where does "write only when the leaf is absent, otherwise write nothing" bite? Consider repeated body-less `--check` runs, the hand-edit loop, `--force-scaffold`, and the currently pinned body-less exit 2.
5. **Refusal classification.** Scan every `raise RefusalError` site and the stderr warnings. Which ones does ADR-0021 misclassify — a mechanical refusal that actually needs judgment, or a judgment call the script still decides?
6. **Deletion fallout.** What breaks when `draft.json`, `--out-dir`, `is_untouched_scaffold`, and the scaffold signature are removed? Check non-obvious consumers, not just `pr-land` (e.g. `pr-enhance`, `pr-refine`, `state.sh`, tests).
7. **ADR consistency.** Does ADR-0021 contradict ADR-0005, ADR-0010, ADR-0019, or ADR-0003 as written? Is the claimed 0010 exemption defensible, or does the `run-[N]` pattern actually fit better?
8. **Item 4** (`docs-scraper` rate-limit flake). Is a fake clock on `time.time`/`time.sleep` sufficient in `tests/docs-scraper/test_rate_limiting.py`, given `scrapers/base.py:183` and the Retry-After math at `:275`? Name any other test that would still flake.

## Deliverable

A severity-ordered list (`blocker` / `major` / `minor`) where each finding has:

- a one-line claim,
- `file:line` or issue evidence,
- why it is a bug or logical hole (the failure scenario),
- the smallest change that would fix it.

Also list, under **Checked and clean**, the areas you examined where you found nothing. Distinguish "verified clean" from "not checked". Do not propose a rewrite, and do not restate the ADR.

## Reply

When finished, or when blocked, reply with:

```
uv run skills/herdr/scripts/herdr_reply.py pi --file <your-reply-file>
```

Write the reply to a file first. Status word: `DONE` (review complete), `BLOCKED` (needs a decision), or `FAILED`. Keep the reply under 200 lines and put the findings in it — not just a path.
