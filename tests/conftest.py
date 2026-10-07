"""Session-wide test hygiene for the harness suite.

A stray git override in the caller's environment outranks repo-local config:
`GIT_DIR`/`GIT_WORK_TREE` beat both `cwd=` and `git -C`, and
`GIT_AUTHOR_*`/`GIT_COMMITTER_*` beat `user.name`/`user.email`. Git exports the
resolved identity into every hook it runs, so without a scrub the identity of the
commit that triggered the pre-commit gate leaks into the tests it spawns and the
fixture identity loses. Scrubbing both classes once here makes each test's
`cwd=`/`-C` isolation and fixture identity real, whatever the caller exported.
"""

from __future__ import annotations

import os

import pytest

from tests.git_env import GIT_IDENTITY_VARS, GIT_LOCATION_VARS


@pytest.fixture(scope="session", autouse=True)
def _isolate_git_overrides() -> None:
    """Drop every ambient git repo-location and identity override for the session."""
    for name in (*GIT_LOCATION_VARS, *GIT_IDENTITY_VARS):
        _ = os.environ.pop(name, None)
