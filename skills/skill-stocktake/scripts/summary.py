#!/usr/bin/env python3
"""Phase 3 summary table generator for skill-stocktake.

Reads results.json and outputs formatted markdown summary table.

Usage:
    python summary.py [OPTIONS]

Options:
    --results PATH   Path to results.json (default: ~/.claude/skills/skill-stocktake/results.json)
    --output FORMAT  Output format: markdown (default) or json
    --group-by GROUP Group by: verdict (default) or skill
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_RESULTS = Path.home() / ".claude" / "skills" / "skill-stocktake" / "results.json"


def load_results(path: Path) -> dict:
    """Load results.json."""
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    with open(path) as f:
        return json.load(f)


def format_markdown_summary(data: dict, group_by: str = "verdict") -> str:
    """Format results as markdown summary table."""
    lines = []

    # Header with metadata
    evaluated_at = data.get("evaluated_at", "unknown")
    mode = data.get("mode", "unknown")
    progress = data.get("batch_progress", {})
    total = progress.get("total", 0)
    status = progress.get("status", "unknown")

    lines.append(f"**Evaluated:** {evaluated_at}")
    lines.append(f"**Mode:** {mode}")
    lines.append(f"**Status:** {status} ({total} skills)")
    lines.append("")

    # Group skills
    skills = data.get("skills", {})

    if group_by == "verdict":
        # Group by verdict
        by_verdict: dict[str, list[tuple[str, dict]]] = defaultdict(list)
        for name, info in skills.items():
            verdict = info.get("verdict", "Unknown")
            by_verdict[verdict].append((name, info))

        # Order: Keep, Improve, Update, Merge, Retire
        verdict_order = ["Keep", "Improve", "Update", "Merge", "Retire"]

        for verdict in verdict_order:
            if verdict not in by_verdict:
                continue

            items = by_verdict[verdict]
            lines.append(f"### {verdict} ({len(items)})")
            lines.append("")
            lines.append("| Skill | 7d | Reason |")
            lines.append("|-------|-----|--------|")

            for name, info in sorted(items, key=lambda x: x[0]):
                use_7d = info.get("use_7d", 0)
                reason = info.get("reason", "")
                # Truncate long reasons
                if len(reason) > 80:
                    reason = reason[:77] + "..."
                reason = reason.replace("|", "\\|")
                lines.append(f"| {name} | {use_7d} | {reason} |")

            lines.append("")

    else:
        # Flat table sorted by name
        lines.append("| Skill | 7d | Verdict | Reason |")
        lines.append("|-------|-----|---------|--------|")

        for name in sorted(skills.keys()):
            info = skills[name]
            use_7d = info.get("use_7d", 0)
            verdict = info.get("verdict", "Unknown")
            reason = info.get("reason", "")
            if len(reason) > 60:
                reason = reason[:57] + "..."
            reason = reason.replace("|", "\\|")
            lines.append(f"| {name} | {use_7d} | {verdict} | {reason} |")

    # Summary counts
    lines.append("### Summary")
    lines.append("")

    counts: dict[str, int] = defaultdict(int)
    for info in skills.values():
        counts[info.get("verdict", "Unknown")] += 1

    lines.append("| Verdict | Count |")
    lines.append("|---------|-------|")
    for verdict in ["Keep", "Improve", "Update", "Merge", "Retire"]:
        lines.append(f"| {verdict} | {counts.get(verdict, 0)} |")

    return "\n".join(lines)


def format_json_summary(data: dict) -> str:
    """Format results as compact JSON summary."""
    skills = data.get("skills", {})

    summary = {
        "evaluated_at": data.get("evaluated_at"),
        "mode": data.get("mode"),
        "total": len(skills),
        "by_verdict": defaultdict(list),
        "skills": [],
    }

    for name, info in sorted(skills.items()):
        summary["skills"].append({
            "name": name,
            "verdict": info.get("verdict"),
            "use_7d": info.get("use_7d", 0),
            "reason": info.get("reason", "")[:100],
        })
        summary["by_verdict"][info.get("verdict", "Unknown")].append(name)

    summary["by_verdict"] = dict(summary["by_verdict"])
    return json.dumps(summary, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3 summary table generator")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--group-by", choices=["verdict", "skill"], default="verdict")

    args = parser.parse_args(argv)

    try:
        data = load_results(args.results)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.output == "json":
        print(format_json_summary(data))
    else:
        print(format_markdown_summary(data, args.group_by))

    return 0


if __name__ == "__main__":
    sys.exit(main())
