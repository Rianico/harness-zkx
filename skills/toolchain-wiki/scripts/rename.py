#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
Deprecated shim for toolchain rename (proxy).

Canonical: skills/ai-engineering-expert/subskills/skill-authoring/scripts/rename.py
Use: uv run $SKILL_DIR/../../ai-engineering-expert/subskills/skill-authoring/scripts/rename.py <old> <new> [--dry-run]
     or  uv run $SKILL_DIR/scripts/rename.py --to <target>

Tool owns bytes in rename.py; this file is a thin proxy.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


def repo_root_from_script(p: pathlib.Path) -> pathlib.Path:
    cur = p.resolve()
    for _ in range(10):
        if (cur / "skills").is_dir() and (cur / "pyproject.toml").exists():
            return cur
        cur = cur.parent
    return p.resolve().parents[3] if len(p.resolve().parents) > 3 else p.resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Deprecated shim: rename toolchain <-> toolchain-wiki")
    ap.add_argument("--to", dest="target", required=True, choices=["toolchain", "toolchain-wiki"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cwd", type=pathlib.Path, default=None)
    args = ap.parse_args()

    script_path = pathlib.Path(__file__)
    repo_root = args.cwd.resolve() if args.cwd else repo_root_from_script(script_path)
    skills_dir = repo_root / "skills"
    has_wiki = (skills_dir / "toolchain-wiki").is_dir()
    has_plain = (skills_dir / "toolchain").is_dir()
    if has_wiki and has_plain:
        print(
            "error: both skills/toolchain and skills/toolchain-wiki exist — ambiguous",
            file=sys.stderr,
        )
        sys.exit(2)
    if not has_wiki and not has_plain:
        print("error: neither skills/toolchain nor skills/toolchain-wiki exists", file=sys.stderr)
        sys.exit(2)
    current = "toolchain-wiki" if has_wiki else "toolchain"
    target = args.target
    if current == target:
        print(f"no-op: already {current}")
        sys.exit(0)

    # canonical general script
    general = (
        repo_root
        / "skills"
        / "ai-engineering-expert"
        / "subskills"
        / "skill-authoring"
        / "scripts"
        / "rename.py"
    )
    cmd = [sys.executable, str(general), current, target]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.cwd:
        cmd.extend(["--cwd", str(args.cwd)])
    print(f"[shim] delegating to general rename: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
