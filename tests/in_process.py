"""In-process runner for scripts that tests previously spawned as subprocesses.

Each herdr helper and ``validate-deps.py`` is a plain ``python <script> <args>``
CLI whose contract is (argv, env, stdin) -> (stdout, stderr, exit code). Running
that contract through ``runpy`` keeps every observable behavior a test asserts
on — fresh ``__main__`` globals per call, ``SystemExit`` codes, tracebacks as
``returncode=1`` — while dropping the per-call interpreter and ``uv run``
startup that dominated the suite's wall time.

Not faithful to a real subprocess in two ways that matter: a hung script blocks
the worker (there is no timeout to fire), and a script that mutates process
globals it does not restore leaks into the next call. The snapshot/restore in
    :meth:`run_script_in_process` covers argv, ``sys.path``, cwd, environ, and the
    standard streams; hang risk is accepted because the suite fakes clocks and
    network, so nothing sleeps on real I/O.
"""

from __future__ import annotations

import contextlib
import io
import os
import runpy
import subprocess
import sys
import traceback
from collections.abc import Mapping
from pathlib import Path


def run_script_in_process(
    argv: list[str],
    *,
    env: Mapping[str, str] | None = None,
    stdin: str | None = None,
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``argv[1]`` as ``__main__`` with ``argv[2:]``, mirroring one subprocess.

    With ``env``, the script sees exactly that environment (extra ambient
    variables are removed, like ``subprocess.run(env=...)``); without it, the
    current environment passes through. With ``cwd``, the script runs there,
    like ``subprocess.run(cwd=...)``. The script's own directory is prepended
    to ``sys.path`` for the call, matching the interpreter's ``sys.path[0]``
    for ``python <script>``, which the flat sibling imports rely on.
    """
    script = argv[1]
    script_dir = str(Path(script).resolve().parent)
    saved_environ = dict(os.environ)
    saved_path = sys.path[:]
    saved_argv = sys.argv[:]
    saved_cwd = os.getcwd()
    saved_stdin = sys.stdin
    out = io.StringIO()
    err = io.StringIO()
    code = 0
    try:
        sys.argv = [script, *argv[2:]]
        sys.path.insert(0, script_dir)
        if cwd is not None:
            os.chdir(cwd)
        # A TextIOWrapper, not a bare StringIO: scripts read `sys.stdin.buffer`,
        # which only a real text-over-binary stack exposes.
        sys.stdin = io.TextIOWrapper(
            io.BytesIO((stdin if stdin is not None else "").encode(encoding="utf-8"))
        )
        if env is not None:
            for key in set(saved_environ) - set(env):
                _ = os.environ.pop(key, None)
            for key, value in env.items():
                os.environ[key] = value
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                _ = runpy.run_path(script, run_name="__main__")
            except SystemExit as exit_exc:
                if isinstance(exit_exc.code, int):
                    code = exit_exc.code
                elif exit_exc.code:
                    # `sys.exit("message")`: the interpreter prints the string and exits 1.
                    _ = err.write(f"{exit_exc.code}\n")
                    code = 1
            except Exception:
                code = 1
                traceback.print_exc(file=err)
    finally:
        os.chdir(saved_cwd)
        sys.path[:] = saved_path
        sys.argv = saved_argv
        sys.stdin = saved_stdin
        os.environ.clear()
        _ = os.environ.update(saved_environ)
    return subprocess.CompletedProcess(
        args=argv, returncode=code, stdout=out.getvalue(), stderr=err.getvalue()
    )
