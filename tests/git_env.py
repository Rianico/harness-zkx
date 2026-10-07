"""Hermetic git environment for tests.

Two classes of ambient git override outrank repo-local config.

`GIT_DIR`/`GIT_WORK_TREE` outrank both `cwd=` and `git -C`, so a test that
isolates a throwaway repo by cwd alone still writes whichever repo the parent
process points `GIT_DIR` at. A leaked override is how a test suite can flag a
real repository `core.bare = true` and stamp a fixture identity into its shared
config.

`GIT_AUTHOR_*`/`GIT_COMMITTER_*` outrank the repo-local `user.name`/`user.email`,
and git exports the resolved values into every hook it runs. A nested repo a test
creates then commits as the outer commit's identity, and the fixture identity
loses. Build every child env with `git_env()` so neither class can happen.
"""

from __future__ import annotations

import os

# git's own repo-location overrides. Each one outranks `cwd` and `-C`.
GIT_LOCATION_VARS: tuple[str, ...] = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)

# git's own commit-identity overrides. Each one outranks the repo-local
# `user.name`/`user.email`; git exports the resolved value of all six into every
# hook environment, which is how an outer commit's identity reaches a nested repo.
GIT_IDENTITY_VARS: tuple[str, ...] = (
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_AUTHOR_DATE",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL",
    "GIT_COMMITTER_DATE",
)


def scrub_git_location_vars(env: dict[str, str]) -> dict[str, str]:
    """Remove every git repo-location override from `env`, in place."""
    for name in GIT_LOCATION_VARS:
        _ = env.pop(name, None)
    return env


def scrub_git_identity_vars(env: dict[str, str]) -> dict[str, str]:
    """Remove every git commit-identity override from `env`, in place."""
    for name in GIT_IDENTITY_VARS:
        _ = env.pop(name, None)
    return env


def scrub_git_vars(env: dict[str, str]) -> dict[str, str]:
    """Remove both override classes — location and identity — from `env`, in place."""
    return scrub_git_identity_vars(scrub_git_location_vars(env))


def git_env(**overrides: str) -> dict[str, str]:
    """A child-process env with every ambient git override removed.

    Both classes are scrubbed from the ambient environment. A repo-location
    `override` is then scrubbed again after the merge, so a caller cannot
    reintroduce one it meant to pin: with `cwd`/`-C` already defeated, pinning a
    location is never legitimate. An identity `override` survives, because
    pinning a fixture commit's author is a deliberate, call-site-visible choice.
    """
    env = {**scrub_git_vars(dict(os.environ)), **overrides}
    return scrub_git_location_vars(env)
