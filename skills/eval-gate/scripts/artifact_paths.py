#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""Resolve generated-artifact paths from the single source of truth (`.lsz/config.yaml`).

Skills used to inline their own artifact layouts — `.lsz/{date}/{timestamp}_{topic}/eval/run-1/`
in one place, a hardcoded `~/.pi/workflows/projects/...` in another. Every divergent copy is a
place the layout can drift, so the layout now lives in one config file and every consumer asks
this module (or the CLI) for the path.

The workflow VM has no filesystem access, so dynamic-workflow nodes cannot read the config
themselves: they run `artifact_paths.py resolve ...` and forward the printed path as `evalDir`.

Usage:
  uv run skills/eval-gate/scripts/artifact_paths.py show
  uv run skills/eval-gate/scripts/artifact_paths.py resolve --kind eval --topic auth --run 2
  uv run skills/eval-gate/scripts/artifact_paths.py resolve --kind tasks
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

CONFIG_RELPATH = Path(".lsz") / "config.yaml"

DEFAULT_BASE = ".lsz"
DEFAULT_PATTERN = "{date}/{time}_{topic}/{kind}"
DEFAULT_KINDS: dict[str, str] = {"eval": "eval", "tasks": "tmp/tasks", "pr": "tmp"}
DEFAULT_GATE_STORE = "~/.pi/workflows/projects"


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Effective artifact layout, already resolved against the repo root."""

    repo_root: Path
    base: Path
    pattern: str
    kinds: dict[str, str]
    gate_store: Path
    source: str


def repo_root_of(start: Path | None = None) -> Path:
    """Repo root for `start` (walk upward for a `.git`, else use `start`)."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def _as_path(raw: object, *, base: Path | None = None) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw.strip()).expanduser()
    if not path.is_absolute() and base is not None:
        path = base / path
    return path


def load_config(repo_root: Path | None = None) -> StorageConfig:
    """Read `.lsz/config.yaml`, falling back to the documented defaults.

    A missing file is not an error: the skill must work in a repo that never adopted the
    config. A malformed file is an error — silently ignoring a broken config would resolve
    paths the operator did not ask for.
    """
    root = (repo_root or repo_root_of()).resolve()
    config_path = root / CONFIG_RELPATH
    base = root / DEFAULT_BASE
    pattern = DEFAULT_PATTERN
    kinds = dict(DEFAULT_KINDS)
    gate_store = Path(DEFAULT_GATE_STORE).expanduser()
    source = "defaults (no .lsz/config.yaml)"

    if config_path.is_file():
        import yaml  # noqa: PLC0415 — kept local so a missing PyYAML only affects the config path

        parsed: object = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if parsed is not None and not isinstance(parsed, dict):
            raise ValueError(f"{config_path}: expected a mapping at the top level")
        storage = (parsed or {}).get("storage") if isinstance(parsed, dict) else None
        if storage is not None and not isinstance(storage, dict):
            raise ValueError(f"{config_path}: `storage` must be a mapping")

        if isinstance(storage, dict):
            base = _as_path(storage.get("base"), base=root) or base
            raw_pattern = storage.get("pattern")
            if isinstance(raw_pattern, str) and raw_pattern.strip():
                pattern = raw_pattern.strip()
            raw_kinds = storage.get("kinds")
            if isinstance(raw_kinds, dict):
                for key, value in raw_kinds.items():
                    if isinstance(key, str) and isinstance(value, str) and value.strip():
                        kinds[key] = value.strip()
            gate_store = _as_path(storage.get("gate_store")) or gate_store
        source = str(config_path)

    return StorageConfig(
        repo_root=root,
        base=base,
        pattern=pattern,
        kinds=kinds,
        gate_store=gate_store,
        source=source,
    )


def kind_segment(config: StorageConfig, kind: str) -> str:
    """Directory segment for a logical kind, defaulting to the kind name itself."""
    return config.kinds.get(kind, kind)


def kind_dir(kind: str, repo_root: Path | None = None) -> Path:
    """Directory that holds every artifact of one kind (no run/topic layout)."""
    config = load_config(repo_root)
    return config.base / kind_segment(config, kind)


def run_dir(
    topic: str,
    kind: str = "eval",
    repo_root: Path | None = None,
    when: datetime | None = None,
    run: int | None = None,
) -> Path:
    """Run directory for `topic`, expanding the configured pattern.

    `when` is injected rather than read from the clock so callers and tests get the same path.
    `run` appends the conventional `run-N` level when given.
    """
    config = load_config(repo_root)
    stamp = when or datetime.now()
    rendered = (
        config.pattern.replace("{date}", stamp.strftime("%Y-%m-%d"))
        .replace("{time}", stamp.strftime("%H%M%S"))
        .replace("{topic}", topic)
        .replace("{kind}", kind_segment(config, kind))
    )
    target = config.base / rendered.strip("/")
    if run is not None:
        target = target / f"run-{run}"
    return target


def describe(repo_root: Path | None = None) -> dict[str, object]:
    """Effective config plus the resolved sample paths, for `show`."""
    config = load_config(repo_root)
    when = datetime(2026, 1, 2, 3, 4, 5)
    return {
        "source": config.source,
        "repo_root": str(config.repo_root),
        "base": str(config.base),
        "pattern": config.pattern,
        "kinds": config.kinds,
        "gate_store": str(config.gate_store),
        "examples": {
            "eval": str(run_dir("example", "eval", config.repo_root, when, run=1)),
            "tasks": str(kind_dir("tasks", config.repo_root)),
            "pr": str(kind_dir("pr", config.repo_root)),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve generated-artifact paths")
    _ = parser.add_argument("--repo-root", default=None, help="Repo root (default: discovered)")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Print the effective config as JSON")
    _ = show.add_argument("--repo-root", default=None, help="Repo root (default: discovered)")

    resolve = sub.add_parser("resolve", help="Print one artifact path")
    _ = resolve.add_argument("--kind", required=True, help="Logical kind (eval, tasks, pr)")
    _ = resolve.add_argument("--topic", default=None, help="Topic; required for a run layout")
    _ = resolve.add_argument("--run", type=int, default=None, help="Append run-N")
    _ = resolve.add_argument("--repo-root", default=None, help="Repo root (default: discovered)")

    args = parser.parse_args(argv)
    root = Path(args.repo_root) if args.repo_root else None
    try:
        if args.command == "show":
            print(json.dumps(describe(root), indent=2))
            return 0
        if args.topic:
            print(run_dir(args.topic, args.kind, root, run=args.run))
        else:
            print(kind_dir(args.kind, root))
        return 0
    except (ValueError, OSError) as exc:
        print(f"artifact_paths: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
