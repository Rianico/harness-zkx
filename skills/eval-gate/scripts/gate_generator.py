#!/usr/bin/env python3
"""Stack-aware Deterministic Gate Generator for Eval-Gate (EDD).

Detects target project toolchains (Rust, TypeScript, Python, Go) and synthesizes
consolidated, executable verification runners outputting unified JSON reports.
Supports Anthropic-style atomic semantic assertions, cumulative regression ledgers,
and Karpathy autoresearch-style checkpointing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CriterionCheck:
    id: str
    phase: str  # build | types | lint | test | security | custom
    command: list[str]
    description: str = ""


@dataclass
class StackProfile:
    name: str  # rust | typescript | python | go | generic
    package_manager: str
    checks: list[CriterionCheck] = field(default_factory=list)


@dataclass
class SemanticAssertion:
    id: str
    statement: str
    critical: bool = True
    category: str = "capability"  # capability | boundary | negative | refutability


def get_project_slug_with_hash(repo_root: Path) -> str:
    """Generate canonical project slug with path hash (e.g. project-2ab274a7089a)."""
    root = repo_root.resolve()
    slug = root.name
    path_hash = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{path_hash}"


def resolve_workflow_dir(repo_root: Path, topic: str, base_dir: Path | None = None) -> Path:
    """Resolve destination directory under ~/.pi/workflows/projects/{project-hash}/{topic}."""
    if base_dir:
        target = Path(base_dir).resolve() / topic
    else:
        project_slug = get_project_slug_with_hash(repo_root)
        target = Path.home() / ".pi" / "workflows" / "projects" / project_slug / topic
    target.mkdir(parents=True, exist_ok=True)
    return target


def detect_stack(repo_root: Path) -> StackProfile:
    """Discover the project's language stack and available toolchains."""
    root = repo_root.resolve()

    # 1. Rust detection
    if (root / "Cargo.toml").exists():
        checks = [
            CriterionCheck("BUILD-01", "build", ["cargo", "check"], "Cargo compilation check"),
            CriterionCheck("LINT-01", "lint", ["cargo", "clippy", "--", "-D", "warnings"], "Clippy linter (zero warnings)"),
            CriterionCheck("TEST-01", "test", ["cargo", "test"], "Cargo test suite"),
        ]
        return StackProfile("rust", "cargo", checks)

    # 2. TypeScript / JavaScript detection
    if (root / "package.json").exists():
        pkg_json = {}
        try:
            pkg_json = json.loads((root / "package.json").read_text(encoding="utf-8"))
        except Exception:
            pass

        scripts = pkg_json.get("scripts", {})
        pm = "npm"
        if (root / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
            pm = "pnpm"
        elif (root / "yarn.lock").exists() and shutil.which("yarn"):
            pm = "yarn"
        elif (root / "bun.lockb").exists() and shutil.which("bun"):
            pm = "bun"

        checks = []
        if (root / "tsconfig.json").exists() and shutil.which("tsc"):
            checks.append(CriterionCheck("TYPES-01", "types", ["npx", "tsc", "--noEmit"], "TypeScript compiler typecheck"))
        elif "build" in scripts:
            checks.append(CriterionCheck("BUILD-01", "build", [pm, "run", "build"], f"{pm} build check"))

        if "lint" in scripts:
            checks.append(CriterionCheck("LINT-01", "lint", [pm, "run", "lint"], f"{pm} lint script"))
        elif shutil.which("eslint"):
            checks.append(CriterionCheck("LINT-01", "lint", ["npx", "eslint", "."], "ESLint style check"))

        if "test" in scripts:
            checks.append(CriterionCheck("TEST-01", "test", [pm, "test"], f"{pm} test suite"))

        return StackProfile("typescript", pm, checks)

    # 3. Python detection
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists() or (root / "requirements.txt").exists():
        has_uv = shutil.which("uv") is not None
        runner = ["uv", "run"] if has_uv else [sys.executable, "-m"]

        checks = []
        if shutil.which("basedpyright"):
            checks.append(CriterionCheck("TYPES-01", "types", [*runner, "basedpyright"], "Basedpyright static types"))
        elif shutil.which("mypy"):
            checks.append(CriterionCheck("TYPES-01", "types", [*runner, "mypy", "."], "Mypy static types"))

        if shutil.which("ruff"):
            checks.append(CriterionCheck("LINT-01", "lint", ["ruff", "check", "."], "Ruff linter"))

        checks.append(CriterionCheck("TEST-01", "test", [*runner, "pytest", "-q", "--tb=no"], "Pytest test suite"))

        return StackProfile("python", "uv" if has_uv else "pip", checks)

    # 4. Go detection
    if (root / "go.mod").exists():
        checks = [
            CriterionCheck("BUILD-01", "build", ["go", "build", "./..."], "Go build check"),
            CriterionCheck("VET-01", "types", ["go", "vet", "./..."], "Go vet check"),
            CriterionCheck("TEST-01", "test", ["go", "test", "./..."], "Go test suite"),
        ]
        return StackProfile("go", "go", checks)

    return StackProfile(
        "generic",
        "shell",
        [CriterionCheck("STAT-01", "build", ["git", "status"], "Repository status check")],
    )


TEMPLATE_SCRIPT = """#!/usr/bin/env python3
\"\"\"Auto-generated consolidated evaluation runner.
Generated by eval-gate (EDD).
\"\"\"

import json
import subprocess
import sys
import time
from pathlib import Path

CHECKS = __CHECKS_JSON__
REPO_ROOT = Path("__REPO_ROOT__")

def run_check(check: dict) -> dict:
    start = time.time()
    cmd = check["command"]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT
        )
        duration = round(time.time() - start, 3)
        issues = []
        if res.returncode != 0:
            lines = [l.strip() for l in (res.stdout + "\\n" + res.stderr).splitlines() if l.strip()]
            issues = lines[-5:] if lines else [f"Command exited with code {res.returncode}"]

        status_str = "passed" if res.returncode == 0 else "failed"
        return {
            "id": check["id"],
            "phase": check["phase"],
            "status": "pass" if res.returncode == 0 else "fail",
            "summary": f"Command `{' '.join(cmd)}` {status_str}",
            "issues": issues,
            "duration": duration,
        }
    except Exception as e:
        return {
            "id": check["id"],
            "phase": check["phase"],
            "status": "fail",
            "summary": f"Execution exception: {e}",
            "issues": [str(e)],
            "duration": round(time.time() - start, 3),
        }

def main():
    results = {}
    global_issues = []
    all_passed = True

    for c in CHECKS:
        out = run_check(c)
        results[c["id"]] = out
        if out["status"] == "fail":
            all_passed = False
            for iss in out["issues"]:
                global_issues.append(f"[{c['id']}] {iss}")

    passed_count = sum(1 for r in results.values() if r["status"] == "pass")
    total_count = len(results)
    score = int((passed_count / total_count) * 100) if total_count > 0 else 100

    report = {
        "status": "pass" if all_passed else "fail",
        "stack": "__STACK_NAME__",
        "score": score,
        "criteria": results,
        "issues": global_issues,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    print(json.dumps(report, indent=2))
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
"""


def synthesize_gate_script(
    repo_root: Path,
    output_dir: Path,
    custom_criteria: list[dict[str, Any]] | None = None,
) -> Path:
    """Generate a consolidated run_evals.py runner script inside output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stack = detect_stack(repo_root)

    checks: list[CriterionCheck] = []
    if custom_criteria:
        for c in custom_criteria:
            cmd = c.get("command")
            if isinstance(cmd, str):
                cmd = cmd.split()
            checks.append(
                CriterionCheck(
                    id=c.get("id", f"CRIT-{len(checks)+1}"),
                    phase=c.get("phase", "custom"),
                    command=cmd or ["true"],
                    description=c.get("description", c.get("intent", "")),
                )
            )
    else:
        checks = stack.checks

    checks_json = json.dumps([asdict(c) for c in checks], indent=2)

    content = TEMPLATE_SCRIPT.replace("__CHECKS_JSON__", checks_json)
    content = content.replace("__REPO_ROOT__", str(repo_root.resolve()))
    content = content.replace("__STACK_NAME__", stack.name)

    script_path = output_dir / "run_evals.py"
    script_path.write_text(content, encoding="utf-8")
    script_path.chmod(0o755)
    return script_path


def synthesize_unified_gate(
    repo_root: Path,
    topic: str,
    output_dir: Path,
    custom_checks: list[dict[str, Any]] | None = None,
    custom_assertions: list[dict[str, Any]] | None = None,
) -> tuple[Path, Path]:
    """Synthesize both gate.json and run_evals.py in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stack = detect_stack(repo_root)
    project_slug = get_project_slug_with_hash(repo_root)

    # 1. Synthesize run_evals.py
    script_path = synthesize_gate_script(repo_root, output_dir, custom_checks)

    # 2. Build assertions list
    assertions: list[SemanticAssertion] = []
    if custom_assertions:
        for a in custom_assertions:
            assertions.append(
                SemanticAssertion(
                    id=a.get("id", f"SEM-{len(assertions)+1}"),
                    statement=a.get("statement", a.get("assertion", "")),
                    critical=a.get("critical", True),
                    category=a.get("category", "capability"),
                )
            )
    else:
        # Default baseline assertions
        assertions = [
            SemanticAssertion("SEM-01", "Implementation satisfies intent without mock-only passes", True, "refutability"),
            SemanticAssertion("SEM-02", "Negative error paths and bad inputs are rejected gracefully", True, "negative"),
            SemanticAssertion("SEM-03", "Clean Architecture boundary preserved (domain does not import delivery/infra)", True, "boundary"),
            SemanticAssertion("SEM-04", "Implementation matches design.md contracts without SOT drift", True, "intent"),
        ]

    checks = stack.checks if not custom_checks else [
        CriterionCheck(c.get("id", f"C-{i}"), c.get("phase", "custom"), c.get("command", ["true"]), c.get("description", ""))
        for i, c in enumerate(custom_checks)
    ]

    gate_payload = {
        "gate_version": 2,
        "target": topic,
        "project_slug": project_slug,
        "deterministic_floor": {
            "stack": stack.name,
            "checks": [asdict(c) for c in checks],
        },
        "semantic_ceiling": {
            "rubric": "Crux-Skeptic",
            "threshold": 8,
            "assertions": [asdict(a) for a in assertions],
        },
    }

    gate_path = output_dir / "gate.json"
    gate_path.write_text(json.dumps(gate_payload, indent=2), encoding="utf-8")

    # 3. Initialize blank ledger.json
    ledger_path = output_dir / "ledger.json"
    if not ledger_path.exists():
        initial_ledger = {
            "project_slug": project_slug,
            "topic": topic,
            "best_score": 0,
            "best_commit": "",
            "immutable_invariants": [],
            "history": [],
        }
        ledger_path.write_text(json.dumps(initial_ledger, indent=2), encoding="utf-8")

    return gate_path, script_path


def grade_semantic_assertions(
    assertions: list[dict[str, Any]],
    grader_results: list[dict[str, Any]],
) -> tuple[int, list[dict[str, Any]], list[str]]:
    """Evaluate Atomic Boolean + CoT Grader results.

    Returns:
        (score: 1-10, graded_assertions: list[dict], issues: list[str])
    """
    results_by_id = {r["id"]: r for r in grader_results if "id" in r}
    graded = []
    issues = []
    total_count = len(assertions)
    passed_count = 0
    critical_failed = False

    for a in assertions:
        aid = a["id"]
        statement = a.get("statement", "")
        critical = a.get("critical", True)
        res = results_by_id.get(aid, {})

        passed = bool(res.get("passed", False))
        evidence = res.get("evidence", "none")
        reasoning = res.get("reasoning", "")

        graded.append({
            "id": aid,
            "statement": statement,
            "passed": passed,
            "critical": critical,
            "evidence": evidence,
            "reasoning": reasoning,
        })

        if passed:
            passed_count += 1
        else:
            if critical:
                critical_failed = True
            issues.append(f"[{aid}] {evidence}: {statement} -> Flaw: {reasoning}")

    # Score calculation on 1-10 scale
    if total_count == 0:
        score = 10
    else:
        ratio = passed_count / total_count
        score = int(round(ratio * 9)) + 1
        if critical_failed and score > 7:
            score = 7  # Critical failure caps score below quality gate

    return score, graded, issues


def update_regression_ledger(
    ledger_path: Path,
    loop: int,
    floor_status: str,
    semantic_score: int,
    passed_items: list[str],
    failed_items: list[str],
    git_commit: str = "",
) -> dict[str, Any]:
    """Update cumulative regression ledger and detect whac-a-mole regressions."""
    data = {"immutable_invariants": [], "history": [], "best_score": 0, "best_commit": ""}
    if ledger_path.exists():
        try:
            data = json.loads(ledger_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    invariants = set(data.get("immutable_invariants", []))
    regressions = []

    # Check for regressions (items that previously passed but now failed)
    for failed in failed_items:
        if failed in invariants:
            regressions.append(failed)

    # Add newly passed items to invariants
    for passed in passed_items:
        invariants.add(passed)

    best_score = data.get("best_score", 0)
    best_commit = data.get("best_commit", "")
    composite_score = semantic_score if floor_status == "pass" else 0

    if composite_score > best_score:
        best_score = composite_score
        best_commit = git_commit

    record = {
        "loop": loop,
        "floor_status": floor_status,
        "semantic_score": semantic_score,
        "composite_score": composite_score,
        "git_commit": git_commit,
        "passed_items": passed_items,
        "failed_items": failed_items,
        "regressions": regressions,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    data["immutable_invariants"] = sorted(list(invariants))
    data["best_score"] = best_score
    data["best_commit"] = best_commit
    data.setdefault("history", []).append(record)

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def format_worker_feedback(ledger: dict[str, Any], active_issues: list[str]) -> str:
    """Format feedback edge payload for the worker agent with anti-thrashing alerts."""
    lines = []
    latest_history = ledger.get("history", [])[-1] if ledger.get("history") else {}
    regressions = latest_history.get("regressions", [])
    if regressions:
        lines.extend([
            "## 🚨 REGRESSION ALERT (Fix Immediately):",
            "The following invariants passed in a prior loop but were BROKEN in the latest cycle:",
        ])
        for reg in regressions:
            lines.append(f"- [REGRESSION] {reg}")
        lines.append("")

    lines.append("## Active Issues to Remediate:")
    if not active_issues:
        lines.append("- No active issues.")
    else:
        for iss in active_issues:
            lines.append(f"- {iss}")

    invariants = ledger.get("immutable_invariants", [])
    if invariants:
        lines.extend([
            "",
            "## Preserved Invariants (Do Not Regress):",
            "The following criteria passed in prior loops and MUST NOT be broken:",
        ])
        for inv in invariants:
            lines.append(f"- [INVARIANT] {inv}")

    best_commit = ledger.get("best_commit")
    best_score = ledger.get("best_score", 0)
    if best_commit:
        lines.extend([
            "",
            f"## Autoresearch Checkpoint: Best score {best_score}/10 at git commit {best_commit[:8]}",
        ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Eval-Gate Stack Discovery & Synthesis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # detect
    detect_parser = subparsers.add_parser("detect", help="Detect repository toolchain stack")
    detect_parser.add_argument("--repo-root", type=str, default=".", help="Root path of target repository")

    # resolve-dir
    res_parser = subparsers.add_parser("resolve-dir", help="Resolve ~/.pi/workflows/projects path")
    res_parser.add_argument("--repo-root", type=str, default=".", help="Root path of target repository")
    res_parser.add_argument("--topic", type=str, required=True, help="Topic / feature name")
    res_parser.add_argument("--base-dir", type=str, help="Optional base directory override")

    # generate-gate
    gen_gate_parser = subparsers.add_parser("generate-gate", aliases=["generate"], help="Generate unified gate.json and run_evals.py")
    gen_gate_parser.add_argument("--repo-root", type=str, default=".", help="Root path of target repository")
    gen_gate_parser.add_argument("--topic", type=str, required=True, help="Topic / feature name")
    gen_gate_parser.add_argument("--output-dir", type=str, help="Output directory override (defaults to ~/.pi path)")
    gen_gate_parser.add_argument("--checks-json", type=str, help="Optional JSON file with custom checks")
    gen_gate_parser.add_argument("--assertions-json", type=str, help="Optional JSON file with semantic assertions")

    # grade-assertions
    grade_parser = subparsers.add_parser("grade-assertions", help="Grade atomic boolean + CoT semantic assertions")
    grade_parser.add_argument("--assertions", type=str, required=True, help="Path to gate.json or assertions.json")
    grade_parser.add_argument("--grader-results", type=str, required=True, help="Path to grader results JSON")
    grade_parser.add_argument("--output", type=str, help="Optional output path for graded results JSON")

    # update-ledger
    ledger_parser = subparsers.add_parser("update-ledger", help="Update regression ledger and emit worker feedback")
    ledger_parser.add_argument("--ledger-path", type=str, required=True, help="Path to ledger.json")
    ledger_parser.add_argument("--loop", type=int, required=True, help="Current loop iteration")
    ledger_parser.add_argument("--floor-status", type=str, required=True, choices=["pass", "fail"], help="Floor status")
    ledger_parser.add_argument("--semantic-score", type=int, required=True, help="Semantic score (1-10)")
    ledger_parser.add_argument("--passed-items", type=str, default="[]", help="JSON array or comma-separated list of passed IDs")
    ledger_parser.add_argument("--failed-items", type=str, default="[]", help="JSON array or comma-separated list of failed IDs")
    ledger_parser.add_argument("--git-commit", type=str, default="", help="Current git commit hash")
    ledger_parser.add_argument("--issues-file", type=str, help="Optional path to report.json or issues.json for active issues")
    ledger_parser.add_argument("--emit-feedback", type=str, help="Optional output path for issues.md feedback")

    args = parser.parse_args()

    if args.command == "detect":
        profile = detect_stack(Path(args.repo_root))
        print(json.dumps(asdict(profile), indent=2))
        return 0

    if args.command == "resolve-dir":
        target = resolve_workflow_dir(
            repo_root=Path(args.repo_root),
            topic=args.topic,
            base_dir=Path(args.base_dir) if args.base_dir else None,
        )
        print(str(target.resolve()))
        return 0

    if args.command in ("generate-gate", "generate"):
        out_dir = Path(args.output_dir) if args.output_dir else resolve_workflow_dir(Path(args.repo_root), args.topic)
        checks = json.loads(Path(args.checks_json).read_text(encoding="utf-8")) if args.checks_json else None
        assertions = json.loads(Path(args.assertions_json).read_text(encoding="utf-8")) if args.assertions_json else None

        gate_path, script_path = synthesize_unified_gate(
            repo_root=Path(args.repo_root),
            topic=args.topic,
            output_dir=out_dir,
            custom_checks=checks,
            custom_assertions=assertions,
        )
        print(f"Generated unified gate: {gate_path}")
        print(f"Generated runner script: {script_path}")
        return 0

    if args.command == "grade-assertions":
        assertions_data = json.loads(Path(args.assertions).read_text(encoding="utf-8"))
        if isinstance(assertions_data, dict):
            assertions = assertions_data.get("semantic_ceiling", {}).get("assertions", [])
            if not assertions:
                assertions = assertions_data.get("assertions", [])
        elif isinstance(assertions_data, list):
            assertions = assertions_data
        else:
            assertions = []

        graders_data = json.loads(Path(args.grader_results).read_text(encoding="utf-8"))
        if isinstance(graders_data, dict):
            grader_results = graders_data.get("results", graders_data.get("evals", []))
        elif isinstance(graders_data, list):
            grader_results = graders_data
        else:
            grader_results = []

        score, graded, issues = grade_semantic_assertions(assertions, grader_results)
        result = {
            "score": score,
            "graded_assertions": graded,
            "issues": issues,
        }
        output_str = json.dumps(result, indent=2)
        if args.output:
            out_p = Path(args.output)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(output_str, encoding="utf-8")
        print(output_str)
        return 0

    if args.command == "update-ledger":
        def parse_items(raw: str) -> list[str]:
            raw = raw.strip()
            if raw.startswith("["):
                try:
                    return json.loads(raw)
                except Exception:
                    pass
            return [x.strip() for x in raw.split(",") if x.strip()]

        passed = parse_items(args.passed_items)
        failed = parse_items(args.failed_items)

        active_issues = []
        if args.issues_file and Path(args.issues_file).exists():
            try:
                iss_data = json.loads(Path(args.issues_file).read_text(encoding="utf-8"))
                if isinstance(iss_data, dict):
                    active_issues = iss_data.get("issues", [])
                elif isinstance(iss_data, list):
                    active_issues = iss_data
            except Exception:
                pass

        if not active_issues:
            active_issues = [f"Failed check: {f}" for f in failed]

        ledger = update_regression_ledger(
            ledger_path=Path(args.ledger_path),
            loop=args.loop,
            floor_status=args.floor_status,
            semantic_score=args.semantic_score,
            passed_items=passed,
            failed_items=failed,
            git_commit=args.git_commit,
        )

        if args.emit_feedback:
            feedback_md = format_worker_feedback(ledger, active_issues)
            feed_p = Path(args.emit_feedback)
            feed_p.parent.mkdir(parents=True, exist_ok=True)
            feed_p.write_text(feedback_md, encoding="utf-8")

        print(json.dumps(ledger, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
