"""Tests for code-review gate logic, diff scanning, and skill conformance."""

import sys
from pathlib import Path

import yaml

# Module-level sys.path insert per LSZ convention
SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "code-review"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from review_gate import (
    Finding,
    ReviewVerdict,
    compute_route,
    evaluate_goal_gate,
    format_remediation_markdown,
    scan_diff_for_red_flags,
)


def test_compute_route_pass():
    """Score >= 8 with no blocking findings and in-sync SOT routes to continue."""
    route = compute_route(score=9, findings=[], sot_in_sync=True)
    assert route == "continue"


def test_compute_route_remediate_on_low_score():
    """Score below threshold routes to remediate."""
    route = compute_route(score=7, findings=[], sot_in_sync=True)
    assert route == "remediate"


def test_compute_route_remediate_on_blocking_issue():
    """Even high score must remediate if a blocking finding exists."""
    findings = [
        Finding(
            severity="BLOCKING",
            invariant="VDD-Refutability",
            location="tests/test_x.py:10",
            defect="Paper tiger mock",
            remediation="Assert actual returned state",
        )
    ]
    route = compute_route(score=9, findings=findings, sot_in_sync=True)
    assert route == "remediate"


def test_compute_route_remediate_on_sot_drift():
    """SOT drift forces remediation regardless of score."""
    route = compute_route(score=10, findings=[], sot_in_sync=False)
    assert route == "remediate"


def test_compute_route_blocked_on_critical_failure():
    """Very low score with multiple blocking defects blocks the workflow."""
    findings = [
        Finding(
            severity="BLOCKING",
            invariant="Clean-Architecture",
            location="domain/order.py:12",
            defect="ORM imported in domain",
            remediation="Use DTO",
        ),
        Finding(
            severity="BLOCKING",
            invariant="EDD-Intent",
            location="domain/order.py:30",
            defect="Empty exception swallow",
            remediation="Handle error",
        ),
    ]
    route = compute_route(score=3, findings=findings, sot_in_sync=False)
    assert route == "blocked"


def test_scan_diff_detects_empty_exception_swallow():
    """Diff scanner catches empty except blocks."""
    diff = """
--- a/src/service.py
+++ b/src/service.py
@@ -10,3 +10,5 @@
+try:
+    payment.charge()
+except Exception: pass
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "BLOCKING"
    assert findings[0].invariant == "EDD-Intent"
    assert "error swallowing" in findings[0].defect


def test_scan_diff_detects_skipped_test():
    """Diff scanner catches skipped test decorators."""
    diff = """
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -5,3 +5,4 @@
+@pytest.mark.skip(reason="broken")
+def test_login_flow():
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "BLOCKING"
    assert findings[0].invariant == "VDD-Refutability"
    assert "Test skipped" in findings[0].defect


def test_scan_diff_detects_hardcoded_dummy_return():
    """Diff scanner catches hardcoded dummy returns with TODO/FIXME comments."""
    diff = """
--- a/src/logic.py
+++ b/src/logic.py
@@ -20,2 +20,3 @@
+    return True  # TODO: implement real validation
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "BLOCKING"
    assert findings[0].invariant == "EDD-Intent"
    assert "Hardcoded dummy return" in findings[0].defect


def test_scan_diff_detects_clean_architecture_domain_leak():
    """Diff scanner detects delivery/infra imports inside domain/ path."""
    diff = """
--- a/src/domain/entities.py
+++ b/src/domain/entities.py
@@ -1,3 +1,4 @@
+from sqlalchemy import Column, Integer
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "BLOCKING"
    assert findings[0].invariant == "Clean-Architecture"
    assert "Domain layer imports" in findings[0].defect


def test_scan_diff_clean_pass():
    """Clean domain logic without anti-patterns produces zero findings."""
    diff = """
--- a/src/domain/account.py
+++ b/src/domain/account.py
@@ -1,5 +1,9 @@
 class Account:
+    def deposit(self, amount: int) -> None:
+        if amount <= 0:
+            raise ValueError("Amount must be positive")
+        self.balance += amount
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 0


def test_format_remediation_markdown():
    """Markdown remediation formatter enumerates issues clearly."""
    finding = Finding(
        severity="HIGH",
        invariant="Clean-Architecture",
        location="src/domain/user.py:42",
        defect="Leaked framework type",
        remediation="Decouple with value object",
    )
    verdict = ReviewVerdict(
        score=7,
        route="remediate",
        status="FAIL",
        findings=[finding],
        sot_in_sync=False,
        sot_details="design.md missing /api/v2 endpoint route",
    )
    md = format_remediation_markdown(verdict)
    assert "Score 7/10" in md
    assert "Route: remediate" in md
    assert "src/domain/user.py:42" in md
    assert "design.md missing /api/v2" in md


def test_skill_frontmatter_and_context_load():
    """Ensure SKILL.md adheres to LSZ context-load policy and frontmatter schemas."""
    skill_md = SKILL_DIR / "SKILL.md"
    assert skill_md.exists()

    content = skill_md.read_text(encoding="utf-8")
    assert content.startswith("---")
    parts = content.split("---", 2)
    assert len(parts) >= 3

    meta = yaml.safe_load(parts[1])
    assert meta["name"] == "code-review"
    assert "description" in meta
    description = meta["description"].strip()

    # Description budget: <= 300 chars
    assert len(description) <= 300, f"Description too long ({len(description)} chars)"
    # Must contain trigger vocabulary
    assert any(
        kw in description.lower() for kw in ["use when", "trigger", "when"]
    ), "Description lacks trigger vocabulary"


def test_evaluate_goal_gate_pass():
    """Goal is attained when Floor passes, score >= 8, zero blocking, SOT in sync."""
    eval_report = {"status": "pass", "issues": []}
    res = evaluate_goal_gate(
        eval_report=eval_report,
        semantic_score=9,
        semantic_findings=[],
        sot_in_sync=True,
    )
    assert res.goal_attained is True
    assert res.route == "continue"
    assert len(res.remediation_issues) == 0


def test_evaluate_goal_gate_fail_floor():
    """Goal fails if Floor fails even with high semantic score."""
    eval_report = {"status": "fail", "issues": ["cargo test failed in test_auth"]}
    res = evaluate_goal_gate(
        eval_report=eval_report,
        semantic_score=10,
        semantic_findings=[],
        sot_in_sync=True,
    )
    assert res.goal_attained is False
    assert res.route == "remediate"
    assert any("cargo test failed" in iss for iss in res.remediation_issues)


def test_evaluate_goal_gate_fail_semantic():
    """Goal fails if semantic score is low or blocking defect exists."""
    eval_report = {"status": "pass", "issues": []}
    finding = Finding(
        severity="BLOCKING",
        invariant="VDD-Refutability",
        location="tests/test_x.py:12",
        defect="Mock on SUT",
        remediation="Assert actual result",
    )
    res = evaluate_goal_gate(
        eval_report=eval_report,
        semantic_score=6,
        semantic_findings=[finding],
        sot_in_sync=True,
    )
    assert res.goal_attained is False
    assert res.route == "remediate"
    assert any("Mock on SUT" in iss for iss in res.remediation_issues)

