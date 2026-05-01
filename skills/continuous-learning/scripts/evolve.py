#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "pydantic"]
# ///
"""
Evolve command for continuous learning system.

Clusters related instincts and proposes draft skills.

Eval 5.3: evolve Command
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

from hooks.observe.instinct_manager import InstinctManager


def get_homunculus_dir() -> Path:
    """Get the homunculus data directory."""
    home = Path(os.environ.get("HOME", "~")).expanduser()
    return home / ".claude" / "lsz" / "homunculus"


def cluster_instincts_by_domain(
    instincts: list[dict],
    min_size: int = 2,
) -> dict[str, list[dict]]:
    """Group instincts by domain and filter by minimum cluster size."""
    by_domain: dict[str, list[dict]] = defaultdict(list)

    for inst in instincts:
        domain = inst["frontmatter"].get("domain", "unknown")
        by_domain[domain].append(inst)

    # Filter by minimum size
    return {d: insts for d, insts in by_domain.items() if len(insts) >= min_size}


def propose_skill_from_cluster(domain: str, instincts: list[dict]) -> dict:
    """Generate a draft skill proposal from a cluster of instincts."""
    # Aggregate triggers
    triggers = [i["frontmatter"]["trigger"] for i in instincts]

    # Calculate average confidence
    confidences = [i["frontmatter"]["confidence"] for i in instincts]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    # Collect evidence count
    total_evidence = sum(i["frontmatter"].get("evidence_count", 0) for i in instincts)

    # Extract actions
    actions = []
    for i in instincts:
        body = i.get("body", "")
        if "## Action" in body:
            # Extract action section
            parts = body.split("## Action")
            if len(parts) > 1:
                action_text = parts[1].split("##")[0].strip()
                actions.append(action_text)

    # Build proposal
    proposal = {
        "domain": domain,
        "instinct_count": len(instincts),
        "average_confidence": round(avg_confidence, 2),
        "total_evidence": total_evidence,
        "triggers": triggers,
        "sample_actions": actions[:3],  # Include up to 3 sample actions
        "proposed_skill_id": f"{domain}-expert",
        "source_instincts": [i["frontmatter"]["id"] for i in instincts],
    }

    return proposal


def main() -> int:
    """Main entry point for evolve command."""
    parser = argparse.ArgumentParser(description="Cluster instincts into skills")
    parser.add_argument("--min-size", type=int, default=2, help="Minimum cluster size")
    parser.add_argument("--domain", help="Filter by domain")
    parser.add_argument("--output-dir", help="Output directory for draft skills")
    parser.add_argument("--approve", action="store_true", help="Auto-approve proposals")
    parser.add_argument("--dry-run", action="store_true", help="Show proposals without creating")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    homunculus_dir = get_homunculus_dir()
    manager = InstinctManager(homunculus_dir)

    # List all instincts
    instincts = manager.list_instincts()

    if not instincts:
        if args.json:
            print(json.dumps({"clusters": [], "message": "No instincts found"}))
        else:
            print("No instincts found to cluster.")
        return 0

    # Filter by domain if specified
    if args.domain:
        instincts = [i for i in instincts if i["frontmatter"].get("domain") == args.domain]

    # Cluster by domain
    clusters = cluster_instincts_by_domain(instincts, min_size=args.min_size)

    if not clusters:
        if args.json:
            print(json.dumps({"clusters": [], "message": f"No clusters found with min_size={args.min_size}"}))
        else:
            print(f"No clusters found with minimum size {args.min_size}.")
        return 0

    # Generate proposals
    proposals = []
    for domain, insts in clusters.items():
        proposal = propose_skill_from_cluster(domain, insts)
        proposals.append(proposal)

    if args.json:
        output = {
            "clusters": [
                {
                    "domain": p["domain"],
                    "instinct_count": p["instinct_count"],
                    "average_confidence": p["average_confidence"],
                    "triggers": p["triggers"],
                }
                for p in proposals
            ],
            "proposals": proposals,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Found {len(clusters)} cluster(s):\n")
        for proposal in proposals:
            print(f"Domain: {proposal['domain']}")
            print(f"  Instincts: {proposal['instinct_count']}")
            print(f"  Avg Confidence: {proposal['average_confidence']}")
            print(f"  Total Evidence: {proposal['total_evidence']}")
            print(f"  Triggers: {', '.join(proposal['triggers'][:3])}")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
