"""Session-wide test hygiene for the harness suite.

A stray `GIT_DIR`/`GIT_WORK_TREE` in the caller's environment outranks both
`cwd=` and `git -C`, so a test that isolates a throwaway repo by cwd alone still
writes the ambient repo's shared config. That is how a suite can flag a real
repository `core.bare = true` and stamp a fixture identity into it. Scrubbing
once here makes each test's `cwd=`/`-C` isolation real, whatever the caller
exported.
"""

from __future__ import annotations

import os

import pytest

from tests.git_env import GIT_LOCATION_VARS


@pytest.fixture(scope="session", autouse=True)
def _isolate_git_location_vars() -> None:
    """Drop every ambient git repo-location override for the whole session."""
    for name in GIT_LOCATION_VARS:
        _ = os.environ.pop(name, None)
