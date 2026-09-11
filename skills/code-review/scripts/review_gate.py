#!/usr/bin/env python3
"""Deterministic verification gate for Crux Code Review.

Provides fast heuristic diff scanning, verdict validation, and routing
computation for subagent-first code reviews.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Finding:
    severity: str  # BLOCKING | HIGH | MEDIUM | LOW
    invariant: str  # VDD-Refutability | EDD-Intent | Clean-Architecture
    location: str  # file:line
    defect: str
    remediation: str


@dataclass
class ReviewVerdict:
    score: int  # 1-10
    route: str  # continue | remediate | blocked
    status: str  # PASS | FAIL
    findings: list[Finding]
    sot_in_sync: bool
    sot_details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "route": self.route,
            "status": self.status,
            "sot_in_sync": self.sot_in_sync,
            "sot_details": self.sot_details,
            "findings": [asdict(f) for f in self.findings],
        }


def compute_route(
    score: int,
    findings: list[Finding],
    sot_in_sync: bool = True,
    threshold: int = 8,
) -> str:
    """Compute the workflow routing decision based on score, findings, and SOT sync."""
    blocking_count = sum(1 for f in findings if f.severity.upper() == "BLOCKING")

    # Critical failure: low score + multiple blocking violations
    if score <= 4 and blocking_count >= 2:
        return "blocked"

    # Clean pass: score meets threshold, zero blocking issues, SOT in sync
    if score >= threshold and blocking_count == 0 and sot_in_sync:
        return "continue"

    # Needs remediation
    return "remediate"


def scan_diff_for_red_flags(diff_text: str) -> list[Finding]:
    """Deterministically scan a unified diff for common anti-patterns."""
    findings: list[Finding] = []
    current_file = ""
    current_line = 0

    lines = diff_text.splitlines()
    for line in lines:
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            continue
        if line.startswith("@@ "):
            # Extract line number from hunk header @@ -a,b +c,d @@
            match = re.search(r"\+(\d+)", line)
            if match:
                current_line = int(match.group(1))
            continue

        if line.startswith("+") and not line.startswith("+++"):
            added = line[1:].strip()

            # Check: Empty exception swallow
            if re.search(r"except\s+(\w+)?:\s*pass\b", added) or re.search(
                r"catch\s*\([^)]*\)\s*\{\s*\}", added
            ):
                findings.append(
                    Finding(
                        severity="BLOCKING",
                        invariant="EDD-Intent",
                        location=f"{current_file}:{current_line}",
                        defect="Silent error swallowing (empty catch/except pass)",
                        remediation="Handle exception explicitly, log failure, or bubble domain error",
                    )
                )

            # Check: Skipped tests in test files
            if "test" in current_file.lower():
                if re.search(r"@(pytest\.mark\.)?skip\b", added) or re.search(
                    r"\b(xit|test\.skip|it\.skip)\b", added
                ):
                    findings.append(
                        Finding(
                            severity="BLOCKING",
                            invariant="VDD-Refutability",
                            location=f"{current_file}:{current_line}",
                            defect="Test skipped or disabled in test suite",
                            remediation="Fix the failing test or remove disabled annotation with evidence",
                        )
                    )

            # Check: Hardcoded temporary returns
            if re.search(r"return\s+(True|False|None|\"mock\"|\"test\").*#\s*(TODO|FIXME)", added):
                findings.append(
                    Finding(
                        severity="BLOCKING",
                        invariant="EDD-Intent",
                        location=f"{current_file}:{current_line}",
                        defect="Hardcoded dummy return value with TODO/FIXME",
                        remediation="Implement actual business domain calculation",
                    )
                )

            # Check: Clean Architecture violation (Domain importing delivery/infra)
            if any(part in current_file.lower() for part in ["domain/", "core/", "entities/"]):
                framework_pattern = r"^\s*(from|import)\s+(fastapi|flask|django|sqlalchemy|requests|httpx|express|axios)\b"
                if re.search(framework_pattern, added):
                    findings.append(
                        Finding(
                            severity="BLOCKING",
                            invariant="Clean-Architecture",
                            location=f"{current_file}:{current_line}",
                            defect=f"Domain layer imports delivery/infrastructure module ({added})",
                            remediation="Invert dependency: domain defines port interface, infra implements adapter",
                        )
                    )

            current_line += 1
        elif not line.startswith("-"):
            current_line += 1

    return findings


@dataclass
class GoalGateResult:
    goal_attained: bool
    route: str  # continue | remediate | blocked
    floor_status: str  # pass | fail
    ceiling_score: int  # 1-10
    blocking_count: int
    sot_in_sync: bool
    remediation_issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_goal_gate(
    eval_report: dict[str, Any] | None,
    semantic_score: int,
    semantic_findings: list[Finding],
    sot_in_sync: bool = True,
    score_threshold: int = 8,
) -> GoalGateResult:
    """Evaluate the composite Goal Gate (Deterministic Floor + Semantic Ceiling)."""
    floor_status = "pass"
    floor_issues: list[str] = []
    if eval_report:
        floor_status = eval_report.get("status", "pass").lower()
        floor_issues = eval_report.get("issues", [])

    blocking_count = sum(1 for f in semantic_findings if f.severity.upper() == "BLOCKING")

    all_remediation: list[str] = [f"[FLOOR] {iss}" for iss in floor_issues]
    for f in semantic_findings:
        if f.severity.upper() in ["BLOCKING", "HIGH"]:
            all_remediation.append(
                f"[CEILING:{f.severity}] {f.location} ({f.invariant}): {f.defect} -> Fix: {f.remediation}"
            )
    if not sot_in_sync:
        all_remediation.append("[CEILING:HIGH] SOT Drift: implementation diverged from design.md")

    # Convergence Predicate:
    # Goal Attained iff Floor == pass AND Semantic Score >= threshold AND Blocking == 0 AND SOT in sync
    goal_attained = (
        floor_status == "pass"
        and semantic_score >= score_threshold
        and blocking_count == 0
        and sot_in_sync
    )

    if goal_attained:
        route = "continue"
    elif semantic_score <= 4 and blocking_count >= 2:
        route = "blocked"
    else:
        route = "remediate"

    return GoalGateResult(
        goal_attained=goal_attained,
        route=route,
        floor_status=floor_status,
        ceiling_score=semantic_score,
        blocking_count=blocking_count,
        sot_in_sync=sot_in_sync,
        remediation_issues=all_remediation,
    )


def format_remediation_markdown(verdict: ReviewVerdict) -> str:
    """Format an issues list ready for handoff to TDD or developer remediation."""
    output = [
        f"## Code Review Verdict: {verdict.status} (Score {verdict.score}/10)",
        f"Route: {verdict.route}",
        "",
        "### Actionable Issues:",
    ]
    if not verdict.findings:
        output.append("- No blocking or high issues found.")
    else:
        for f in verdict.findings:
            output.append(
                f"- [{f.severity}] {f.location} ({f.invariant}): {f.defect} -> Fix: {f.remediation}"
            )

    if not verdict.sot_in_sync:
        output.append(f"- [HIGH] SOT Drift: {verdict.sot_details}")

    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Crux Code Review Gate Helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan-diff command
    scan_parser = subparsers.add_parser("scan-diff", help="Scan diff for deterministic red flags")
    scan_parser.add_argument("--diff-file", type=str, help="Path to git diff file (reads stdin if omitted)")
    scan_parser.add_argument("--json", action="store_true", help="Output findings in JSON")

    # check-verdict command
    verdict_parser = subparsers.add_parser("check-verdict", help="Compute route from score and issues")
    verdict_parser.add_argument("--score", type=int, required=True, help="Review score (1-10)")
    verdict_parser.add_argument("--findings-json", type=str, help="Path to findings JSON file")
    verdict_parser.add_argument("--sot-drift", action="store_true", help="Set if SOT drift was detected")

    # evaluate-goal-gate command
    goal_parser = subparsers.add_parser("evaluate-goal-gate", help="Evaluate composite Goal Gate (Floor + Ceiling)")
    goal_parser.add_argument("--eval-report", type=str, help="Path to eval-gate JSON report")
    goal_parser.add_argument("--score", type=int, required=True, help="Semantic review score (1-10)")
    goal_parser.add_argument("--findings-json", type=str, help="Path to semantic findings JSON")
    goal_parser.add_argument("--sot-drift", action="store_true", help="Set if SOT drift was detected")
    goal_parser.add_argument("--threshold", type=int, default=8, help="Passing score threshold (default: 8)")

    args = parser.parse_args()

    if args.command == "scan-diff":
        if args.diff_file:
            diff_text = Path(args.diff_file).read_text(encoding="utf-8")
        else:
            diff_text = sys.stdin.read()

        findings = scan_diff_for_red_flags(diff_text)
        if args.json:
            print(json.dumps([asdict(f) for f in findings], indent=2))
        else:
            if not findings:
                print("PASS: No deterministic red flags detected.")
            else:
                print(f"WARNING: Detected {len(findings)} deterministic red flag(s):")
                for f in findings:
                    print(f"  [{f.severity}] {f.location}: {f.defect}")

        return 0

    if args.command == "check-verdict":
        findings = []
        if args.findings_json:
            raw = json.loads(Path(args.findings_json).read_text(encoding="utf-8"))
            findings = [Finding(**item) for item in raw]

        route = compute_route(
            score=args.score,
            findings=findings,
            sot_in_sync=not args.sot_drift,
        )
        status = "PASS" if route == "continue" else "FAIL"
        verdict = ReviewVerdict(
            score=args.score,
            route=route,
            status=status,
            findings=findings,
            sot_in_sync=not args.sot_drift,
        )
        print(json.dumps(verdict.to_dict(), indent=2))
        return 0 if route == "continue" else 1

    if args.command == "evaluate-goal-gate":
        eval_data = None
        if args.eval_report:
            eval_data = json.loads(Path(args.eval_report).read_text(encoding="utf-8"))

        findings = []
        if args.findings_json:
            raw = json.loads(Path(args.findings_json).read_text(encoding="utf-8"))
            findings = [Finding(**item) for item in raw]

        res = evaluate_goal_gate(
            eval_report=eval_data,
            semantic_score=args.score,
            semantic_findings=findings,
            sot_in_sync=not args.sot_drift,
            score_threshold=args.threshold,
        )
        print(json.dumps(res.to_dict(), indent=2))
        return 0 if res.goal_attained else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

