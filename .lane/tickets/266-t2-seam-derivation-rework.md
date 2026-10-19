# TICKET: #266-t2-seam-derivation — REWORK (bounded)

Verdict from the TM's adversarial review of `b2aca52b` + `1d9f7a73`: **REWORK.** Two contract breaches are proven, not argued: `--status` can exit 1, and the branch-scoped leaf is not branch-scoped. Six minors ride along because they sit in the same files and the review round is already open.

Do not amend the two commits. Add a follow-up commit and report all SHAs. Keep the change set to the files named below.

## R1 — blocker: `--status` must never exit non-zero

`_status.py:526`, `_status.py:527`, `_status.py:585`. `_head_sha`, `_worktree_clean` and the `gh pr checks` read call `_github.run_command` with no `try`. T2 made `run_command` raise `PrError` on timeout/`OSError` (`_github.py:133`), so a failure there escapes `collect_status`, lands in `main`'s `except PrError`, and returns 1 with no JSON. The reviewer proved it twice by patching `run_command` to raise on `git rev-parse HEAD` and on `gh pr checks`: exit 1, nothing on stdout. The existing `test_gh_failure_is_a_structured_refusal_not_a_traceback` misses it because `_query_pr` fails first and masks the later reads.

**Fix**: wrap those three reads and degrade — `note_gh(...)` for the checks read, and safe defaults (`sha = ""`, `clean = True`) for the git reads. The pinned contract is exit 0 on every path.

## R2 — major: the leaf slug is not injective

`_status.py:153-156`. `re.sub(r"[^A-Za-z0-9._-]+", "-", head_ref)` collapses `feat/x`, `feat-x`, `feat.x` and every non-ASCII branch to the same leaf, so `.lsz/gh-router/feat-x.md` written on `feat/x` is reported on `feat-x` as that branch's artifact — the cross-branch pickup ADR-0021 §2 exists to remove.

**Fix**: make the mapping injective (for example percent-encode each disallowed character), and freeze it with a test asserting `head_slug("feat/x") != head_slug("feat-x") != head_slug("feat.x")`. A slug that must stay filename-safe and directory-safe.

## R3 — minor: a git failure must not be reported as a `gh` failure

`_status.py:262-272`, `_status.py:254`. A `git rev-parse HEAD` timeout is reported as `code: gh_offline`, `reason: "github is unreachable…"`, `remedy: check the network connection`. Also `auth_markers` matches the substring `auth`, so any message containing `author`/`authors` is classified `gh_unauthenticated`.

**Fix**: thread the failing tool into the refusal builder and apply `gh` markers only when the command was `gh`; match `authenticat` rather than `auth`.

## R4 — minor: `--status` must not print refusal prose

`_status.py:713-722`. `resolve_squash_message` writes its refusals to stderr before raising; `--status` swallows the exception but not the prose, so a read-only exit-0 command emits `refusing squash merge: PR body is empty…` on stderr.

**Fix**: redirect stdout/stderr around that advisory call (the preview is advisory there; the gate still prints it normally).

## R5 — minor: restore the weakened assertion

`tests/gh-router/test_pr_land_range_authority.py:257`. "the dry-run trailers equal the digest commit set" became `assert "trailers: 2" in stdout` plus a self-referential `len(expected) == 2`; trailer identity is no longer tied to the range.

**Fix**: assert the trailer text or the merge payload, not a count.

## R6 — minor: cover the new predicate's false branch

`test_dirty_block_reports_uncommitted_work` was removed from `tests/gh-router/test_pr_draft_phase.py` with no replacement, and `worktree_clean` is asserted only in the clean case (`test_pr_status.py:156`). `_draft._draft_dirty` now has no caller and survives as an unused `dir(pr)` re-export (`_draft.py:297`).

**Fix**: add `--status` cases for `worktree_clean is False`, and drop or re-point `_draft_dirty`.

## R7 — minor: stale names in remediation text

`_squash.py:824` tells the author to edit "the candidate `pr_body.md`" — a file no longer produced anywhere. `pr-land/SKILL.md:64` says "A message that reproduces `pr_body.md` is refused".

**Fix**: name the actual leaf (`.lsz/gh-router/<slug>.md`). Do not touch `docs/` — the ADR amendment is the TM's.

## R8 — minor: the stamp hard-fail can state a false diagnosis

`pr.py:623-637`. `stamp_changelog` returns False both when the ledger lacks the entry and when the commit succeeded but the push failed (`_changelog.py:303-311`), yet the refusal says the ledger "carries no `(#N)` entry" and asks the caller to add one that already exists locally. The exit code, PR url and ready re-run remedy are correct.

**Fix**: word the reason as "the stamp did not complete (see the warning above); the entry must exist and be pushed".

## Verification Contract (GDD/EDD)

- **Check Command**: `bash scripts/check.sh` (baseline on this branch: 2942 passed, 1 skipped), plus `uv run pytest tests/gh-router -q`.
- **Required Evidence**:
  - R1: the reviewer's counterexample reproduced *before* the fix (patched `run_command` → exit 1, no JSON) and shown *after* (exit 0 with valid JSON), plus a regression test that patches each of the three reads to raise and asserts exit 0.
  - R2: the injectivity test, quoting the three distinct slugs.
  - R3: a test showing a `git` timeout is not labelled `gh_offline`, and that `"author"` in a message does not trigger `gh_unauthenticated`.
  - R4: the body-less `--status` run showing stderr is empty while exit stays 0.
  - R5, R6: the restored/added assertions quoted.
  - Gate output showing `All gates passed.` and the final total; all SHAs; `git diff --stat`.

Reply with the standard template to the caller (`uv run skills/herdr/scripts/herdr_reply.py pi --file <payload> --ticket '#266-t2-seam-derivation'`). Commit locally; do not push, open a PR, or merge.
