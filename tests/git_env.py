"""Hermetic git environment for tests.

`GIT_DIR`/`GIT_WORK_TREE` outrank both `cwd=` and `git -C`, so a test that
isolates a throwaway repo by cwd alone still writes whichever repo the parent
process points `GIT_DIR` at. A leaked override is how a test suite can flag a
real repository `core.bare = true` and stamp a fixture identity into its shared
config. Build every child env with `git_env()` so that cannot happen.
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


def scrub_git_location_vars(env: dict[str, str]) -> dict[str, str]:
    """Remove every git repo-location override from `env`, in place."""
    for name in GIT_LOCATION_VARS:
        _ = env.pop(name, None)
    return env


def git_env(**overrides: str) -> dict[str, str]:
    """A child-process env with every ambient git override removed.

    `overrides` are scrub-proof: they are merged first, so a caller cannot
    accidentally reintroduce a repo-location override it meant to pin.
    """
    return scrub_git_location_vars({**os.environ, **overrides})
