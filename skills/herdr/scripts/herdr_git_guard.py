"""herdr-git-guard — refuse an outbound payload that cites a SHA naming no commit.

Every backticked 7-40 lowercase-hex token in a reply or ticket body must name a
commit in the lane's own repository, checked before anything is written or sent.
A token that is deliberately not a commit is waived by name, loudly.
Stdlib plus `herdr_cli` and `herdr_lease`.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import herdr_lease
from herdr_cli import UsageError

__all__ = [
    "SHA_SHAPED_BACKTICKED_RE",
    "ALLOW_UNRESOLVABLE_SHA",
    "GIT_LOCATION_REDIRECT_VARS",
    "GIT_VERDICT_NEUTRAL_LOCATION_VARS",
    "backticked_sha_tokens",
    "git_location_redirect",
    "git_can_resolve_commits",
    "names_a_commit",
    "unresolvable_sha_tokens",
    "lane_git_dir",
    "require_resolvable_shas",
]


# ── an outbound payload may not cite a SHA that resolves to nothing (#247 D2) ─────────────

# A backticked 7-40 lowercase-hex token is an *instruction* — "do not rewrite `8d9fa742`" — and an
# instruction that names no commit points at nothing. The rule is deliberately narrow: the pattern
# matches a whole code span, so a bare hex word in prose stays prose. The measurement that chose it
# (#247 D2) scanned 668 `.md` files (`.lane/tickets`, `skills/**`, `docs/**`, `.lane/reports`): 37
# distinct non-resolving tokens appear bare, and reading those as instructions would have refused 6
# innocent files whose backticked hex is a decimal (`1234567`), a binary literal (`0b00000011`) or an
# 8-hex review-record id. The narrow rule still refuses 10 files — 4 tickets, 4 docs, and 2 stored
# reply payloads — whose backticked tokens are review ids and mutant labels that no shape rule can
# tell apart from an abbreviation, so a genuinely intentional non-resolving token is waived BY NAME
# with `--allow-unresolvable-sha <TOKEN>`, reported on stderr, never a silent bypass.
SHA_SHAPED_BACKTICKED_RE = re.compile(r"`([0-9a-f]{7,40})`")
ALLOW_UNRESOLVABLE_SHA = "--allow-unresolvable-sha"

# Git location overrides the guard inherits through `subprocess.run` that actually move the objects
# `git rev-parse` reads, so a probe run with one set answers about another repository. `GIT_DIR` and
# `GIT_COMMON_DIR` relocate the whole repository, `GIT_OBJECT_DIRECTORY` replaces its object store,
# and `GIT_ALTERNATE_OBJECT_DIRECTORIES` adds foreign ones. Each outranks `cwd`, so the verdict is
# unverifiable rather than a false negative. Measured, not assumed: with only `GIT_INDEX_FILE` or
# `GIT_WORK_TREE` set the probe's verdict is byte-identical to a clean environment (#247
# D2-rework-2), so those two are deliberately absent here — skipping on them would excuse a refusal
# the probe can answer, a silent false pass the other way. They never skip for that reason alone:
# neither name is read here, so a skip with one set can only come from the generic "no work tree"
# path — a non-existent `GIT_WORK_TREE`, say, makes `git rev-parse --is-inside-work-tree` exit 128
# and the check is reported unchecked, never passed. `herdr_bootstrap` refuses on them because its
# question is tracked state, which the index and the work tree do decide (#238).
GIT_LOCATION_REDIRECT_VARS: tuple[str, ...] = (
    "GIT_DIR",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)
# Git's remaining location overrides: they move the index or the work tree, which decide `git
# status`, never which commit a SHA names. Together with the tuple above they are git's whole
# location family, held to `tests/git_env.GIT_LOCATION_VARS` by a pin so neither list can drift
# alone.
GIT_VERDICT_NEUTRAL_LOCATION_VARS: tuple[str, ...] = ("GIT_INDEX_FILE", "GIT_WORK_TREE")


def backticked_sha_tokens(payload: str) -> list[str]:
    """Distinct backticked 7-40 lowercase-hex tokens, in first-appearance order."""
    return list(dict.fromkeys(SHA_SHAPED_BACKTICKED_RE.findall(payload)))


def git_location_redirect(env: Mapping[str, str]) -> str | None:
    """The object-store override in `env`, or None when git would answer about `cwd`.

    Same question as `herdr_bootstrap._git_location_is_redirected` asks (#238) — does the caller's
    environment point git away from this lane? — but a deliberately different policy: bootstrap
    refuses, because it guards an irreversible append to a possibly-tracked tree, while this guard
    skips and delivers, because a dead-SHA advisory must not block a coordination message and the
    override is caller-environment-only (no harness script exports it, `scripts/check.sh` unsets it,
    `tests/` scrubs it, and no payload can force it). Answered with the offending variable's name so
    the skip line can say why. Each name here makes `git_can_resolve_commits` and `names_a_commit`
    answer about another repository's objects, so their verdict is unverifiable rather than a false
    negative; the overrides that leave that verdict unchanged are not read here.
    """
    return next((name for name in GIT_LOCATION_REDIRECT_VARS if env.get(name)), None)


def git_can_resolve_commits(cwd: Path) -> bool:
    """Whether `git rev-parse` can answer about commits in `cwd` at all.

    A missing git binary, or a directory outside every work tree, answers False. That answer is
    "unverifiable", and it must never be read as "unresolvable".
    """
    try:
        done = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return done.returncode == 0


def names_a_commit(token: str, cwd: Path) -> bool:
    """`git rev-parse --verify <token>^{commit}`: whether the token names a commit in `cwd`."""
    try:
        done = subprocess.run(
            ["git", "rev-parse", "--verify", f"{token}^{{commit}}"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return done.returncode == 0


def unresolvable_sha_tokens(
    payload: str, *, cwd: Path, env: Mapping[str, str] | None = None
) -> list[str] | None:
    """Backticked SHA-shaped tokens in `payload` that name no commit; None when unverifiable.

    `None` means git could not answer in `cwd` — no repository, no binary, or one of
    `GIT_LOCATION_REDIRECT_VARS` in `env` (the process environment when `env` is omitted) pointing
    the probe at another repository's objects — so the caller can report the check as skipped
    instead of claiming every token in a payload is dead, or letting a token resolve in a repository
    that is not this lane's.
    `[]` means nothing to verify or every cited token resolves, which is why a payload with no such
    token passes.
    """
    tokens = backticked_sha_tokens(payload)
    if not tokens:
        return []
    if git_location_redirect(os.environ if env is None else env) is not None:
        return None
    if not git_can_resolve_commits(cwd):
        return None
    return [token for token in tokens if not names_a_commit(token, cwd)]


def lane_git_dir(env: Mapping[str, str]) -> Path | None:
    """The lane repository the guard resolves against, or None when no anchor resolves.

    Deliberately the store anchor `herdr-lease` already resolves (#229) rather than the ambient
    cwd: the same payload must get the same verdict from any working directory. Only a broken
    anchor leaves this None, and the guard then falls back to where the helper itself was invoked.
    """
    try:
        return herdr_lease.resolve_base_dir(env=env)
    except Exception:
        return None


def require_resolvable_shas(
    payload: str,
    *,
    payload_path: str,
    waived: Sequence[str] = (),
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    origin: str = "herdr-reply",
    refusal_action: str = "record or submit the reply",
) -> None:
    """Refuse a payload whose backticked SHA-shaped token names no commit (#247 D2).

    Runs on the payload BODY `read_payload` returned, which is the only text it is ever handed:
    the envelope and the pointer are composed later, and envelope fields are never backticked, so
    a drifted copy in the ticket or in the envelope is not caught here. Runs before anything is
    written, so a refused payload leaves no record and consumes no lease — the persist-first
    ordering (#231) is untouched. Loud by construction: the refusal names every dead token and the
    payload path; a token waived by `--allow-unresolvable-sha` is named on stderr; and a git that
    cannot answer — no work tree, no binary, or one of `GIT_LOCATION_REDIRECT_VARS` pointing it at
    another repository's objects — is reported as a skipped check, never as a pass.

    Shared by the reply and dispatch paths: `origin` names the helper in the stderr lines and
    `refusal_action` names what the refusal declines to do, so neither path reports under the
    other's name.
    """
    tokens = backticked_sha_tokens(payload)
    if not tokens:
        return
    directory = cwd if cwd is not None else Path.cwd()
    environment = os.environ if env is None else env
    verdict = unresolvable_sha_tokens(payload, cwd=directory, env=environment)
    if verdict is None:
        listed = ", ".join(f"`{token}`" for token in tokens)
        redirect = git_location_redirect(environment)
        reason = (
            f"git's location is redirected by {redirect}, so a token could resolve in another "
            "repository"
            if redirect is not None
            else f"git cannot resolve commits in {directory} (no work tree, or no git binary)"
        )
        print(
            f"{origin}: SHA guard skipped for {payload_path}: {reason}; unchecked: {listed}",
            file=sys.stderr,
        )
        return
    vouched = set(waived)
    for token in verdict:
        if token in vouched:
            print(
                f"{origin}: SHA guard waived `{token}` ({ALLOW_UNRESOLVABLE_SHA}): it names "
                "no commit in this lane",
                file=sys.stderr,
            )
    dead = [token for token in verdict if token not in vouched]
    if dead:
        listed = ", ".join(f"`{token}`" for token in dead)
        raise UsageError(
            f"payload {payload_path} names a SHA-shaped token that resolves to no commit: "
            f"{listed}. A backticked 7-40 hex token is an instruction, so correct it — or waive "
            f"an intentional one with {ALLOW_UNRESOLVABLE_SHA} <TOKEN>. Refusing to "
            f"{refusal_action}"
        )
