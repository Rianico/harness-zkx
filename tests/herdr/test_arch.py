"""Pin the extracted modules' dependency direction: neither may reach `herdr_reply`.

`hrg-t1`/`hrg-t2` moved `herdr_evidence` and `herdr_git_guard` out of `herdr_reply`, and the
re-export shim keeps every moved name valid on `herdr_reply` — which makes the seam a
convention the shim itself can quietly undo: a future `from herdr_reply import …` inside an
extracted module would re-merge the seam one call site at a time, in either direction. These
pins hold the direction as a checked invariant on two layers:

* static — an AST walk forbids a `herdr_reply` import in the module source at any indentation.
  A text search would false-positive on `herdr_evidence.py`'s moved comment citing
  `tests/herdr/test_herdr_reply.py`, which is prose, not a dependency.
* transitive — importing the module in a fresh interpreter must not load `herdr_reply`
  through any chain. One interpreter per module: `herdr_reply` imports both modules itself,
  so a shared interpreter would trivially "leak" it in the other direction.

The pins forbid reaching `herdr_reply` only; the extracted modules' other dependencies
(`herdr_cli`, `herdr_lease`, stdlib, anything legitimate added later) are not frozen here.
"""

from __future__ import annotations

import ast
import subprocess
import sys

import pytest

from tests.herdr.stub import SCRIPTS_DIR

EXTRACTED = ("herdr_evidence", "herdr_git_guard")


def _imported_roots(tree: ast.AST) -> set[str]:
    """Top-level module names imported at any depth of the tree, absolute imports only."""
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize("module", EXTRACTED)
def test_source_never_imports_herdr_reply(module: str) -> None:
    """Static: no `import herdr_reply` / `from herdr_reply import …` line exists."""
    path = SCRIPTS_DIR / f"{module}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert "herdr_reply" not in _imported_roots(tree), (
        f"{module}.py imports herdr_reply: the extraction seam reached back"
    )


@pytest.mark.parametrize("module", EXTRACTED)
def test_importing_the_module_never_loads_herdr_reply(module: str) -> None:
    """Transitive: a fresh interpreter that imports only `module` never loads herdr_reply."""
    probe = (
        "import sys\n"
        f"sys.path.insert(0, {str(SCRIPTS_DIR)!r})\n"
        f"import {module}\n"
        "sys.exit(1 if 'herdr_reply' in sys.modules else 0)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, (
        f"importing {module} loaded herdr_reply "
        f"(rc={done.returncode}): {done.stderr.strip() or 'herdr_reply in sys.modules'}"
    )
