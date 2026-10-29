"""Tests for code-review gate logic, diff scanning, and skill conformance."""

import sys
from pathlib import Path

import yaml
from pydantic import BaseModel

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


def test_compute_route_remediate_on_high_issue():
    """HIGH severity finding routes to remediate even with score >= 8."""
    findings = [
        Finding(
            severity="HIGH",
            invariant="EDD-Intent",
            location="pyrightconfig.json:51",
            defect="Added suppression",
            remediation="Fix type issue",
        )
    ]
    route = compute_route(score=9, findings=findings, sot_in_sync=True)
    assert route == "remediate"


def test_compute_route_continue_on_info_issue():
    """INFO severity finding (ratchet shrink) does not block route continue."""
    findings = [
        Finding(
            severity="INFO",
            invariant="EDD-Intent",
            location="config/suppressions.pin:1",
            defect="Suppression baseline or ratchet pin shrunk (5 -> 4)",
            remediation="Verify shrink",
        )
    ]
    route = compute_route(score=9, findings=findings, sot_in_sync=True)
    assert route == "continue"


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


def test_scan_diff_detects_ratchet_pin_widening():
    """Diff scanner detects widening edits to baselines or ratchet pins."""
    diff = """
--- a/config/suppressions.pin
+++ b/config/suppressions.pin
@@ -1,2 +1,2 @@
-count: 4
+count: 5
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"
    assert findings[0].invariant == "EDD-Intent"
    assert "widened" in findings[0].defect


def test_scan_diff_detects_ratchet_pin_shrink_as_info():
    """Diff scanner detects shrinking baselines and classifies as INFO."""
    diff = """
--- a/config/suppressions.pin
+++ b/config/suppressions.pin
@@ -1,2 +1,2 @@
-count: 5
+count: 4
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "INFO"
    assert findings[0].invariant == "EDD-Intent"
    assert "shrunk" in findings[0].defect


def test_scan_diff_detects_suppression_widening_in_config():
    """Diff scanner detects added type-check suppression in pyrightconfig.json."""
    diff = """
--- a/pyrightconfig.json
+++ b/pyrightconfig.json
@@ -50,6 +50,7 @@
     "reportUnusedParameter": false,
+    "reportUnusedImport": false,
     "reportPrivateUsage": false
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"
    assert findings[0].location == "pyrightconfig.json:51"
    assert "Added suppression" in findings[0].defect


def test_scan_diff_does_not_false_positive_on_source_file_with_suppress():
    """Diff scanner does not flag normal source files containing 'suppress' in name."""
    diff = """
--- a/src/suppress_warnings.py
+++ b/src/suppress_warnings.py
@@ -1,2 +1,2 @@
-def suppress_warnings(log): pass
+def suppress_warnings(log, *, strict: bool = False) -> None: return None
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 0


def test_scan_diff_does_not_skip_blocking_checks_in_baseline_named_source_files():
    """Source files named *baseline* or *ratchet* must not skip BLOCKING checks."""
    diff_arch = """
--- a/core/baseline_policy.py
+++ b/core/baseline_policy.py
@@ -1,2 +1,3 @@
+from fastapi import APIRouter
 def resolve_policy(x):
     return x
"""
    findings_arch = scan_diff_for_red_flags(diff_arch)
    assert len(findings_arch) == 1
    assert findings_arch[0].severity == "BLOCKING"
    assert findings_arch[0].invariant == "Clean-Architecture"

    diff_swallow = """
--- a/src/baseline_utils.py
+++ b/src/baseline_utils.py
@@ -1,2 +1,3 @@
 def handle():
+    try: do_something()
+    except Exception: pass
"""
    findings_swallow = scan_diff_for_red_flags(diff_swallow)
    assert any(
        f.severity == "BLOCKING" and "Silent error swallowing" in f.defect for f in findings_swallow
    )


def test_scan_diff_leak_flip_does_not_occur_on_deleted_file():
    """A deleted file must not leak its removed lines into the previous file."""
    diff = """
--- a/config/known-issues-baseline.txt
+++ b/config/known-issues-baseline.txt
@@ -1,1 +1,3 @@
 issue-1
+issue-2
+issue-3
--- a/config/retired-cache.json
+++ /dev/null
@@ -1,5 +0,0 @@
-{"a": 1}
-{"b": 2}
-{"c": 3}
-{"d": 4}
-{"e": 5}
"""
    findings = scan_diff_for_red_flags(diff)
    # The baseline widened (+2/-0 entries), so it must be HIGH, not INFO
    baseline_findings = [f for f in findings if "known-issues-baseline.txt" in f.location]
    assert len(baseline_findings) == 1
    assert baseline_findings[0].severity == "HIGH"
    assert "widened" in baseline_findings[0].defect


def test_scan_diff_negative_type_test_passes_cleanly():
    """@ts-expect-error in test file is an assertion, not a suppression."""
    diff = """
--- a/tests/types.test.ts
+++ b/tests/types.test.ts
@@ -1,2 +1,3 @@
+// @ts-expect-error - asserting wrong-arity call is rejected
 const res = fn(1, 2, 3);
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 0


def test_scan_diff_first_hunk_line_not_overwritten():
    """First hunk at line 1 must not be overwritten by later hunks."""
    diff = """
--- a/config/suppressions.pin
+++ b/config/suppressions.pin
@@ -1,2 +1,2 @@
-count: 9
+count: 8
@@ -120,2 +120,2 @@
-id: abc
+id: def
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].location == "config/suppressions.pin:1"


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


def test_scan_diff_detects_multiline_empty_except_python():
    """Diff scanner detects multi-line empty except pass in Python."""
    diff = """
--- a/src/service.py
+++ b/src/service.py
@@ -10,3 +10,6 @@
 def run():
     try:
         work()
+    except Exception:
+        # silently ignored
+        pass
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"
    assert findings[0].invariant == "EDD-Intent"
    assert findings[0].location == "src/service.py:13"
    assert "Silent error swallowing" in findings[0].defect


def test_scan_diff_detects_multiline_empty_except_with_ellipsis_python():
    """Diff scanner detects multi-line empty except with ellipsis in Python."""
    diff = """
--- a/src/worker.py
+++ b/src/worker.py
@@ -5,3 +5,5 @@
 def poll():
     try:
         poll_once()
+    except:
+        ...
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"
    assert findings[0].location == "src/worker.py:8"


def test_scan_diff_detects_multiline_empty_catch_javascript():
    """Diff scanner detects multi-line empty catch in TypeScript/JavaScript."""
    diff = """
--- a/src/client.ts
+++ b/src/client.ts
@@ -20,3 +20,6 @@
 function request() {
     try {
         send();
+    } catch (err) {
+        // ignore error
+    }
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"
    assert findings[0].location == "src/client.ts:23"
    assert "Silent error swallowing" in findings[0].defect


def test_scan_diff_multiline_empty_except_opener_outside_hunk_emits_no_blocking():
    """Hunk starting inside docstring emits no BLOCKING findings."""
    diff = """
--- a/docs/example.py
+++ b/docs/example.py
@@ -130,4 +130,7 @@ def documented():
     Never do this:
+    except Exception:
+        pass
+    # noqa: E501
     Done.
     \"\"\"
"""
    findings = scan_diff_for_red_flags(diff)
    assert not any(f.severity == "BLOCKING" for f in findings)
    assert any(f.severity == "HIGH" for f in findings)


def test_scan_diff_context_except_with_added_pass_detected():
    """Context except line with newly added empty pass is detected as HIGH."""
    diff = """
--- a/svc/worker.py
+++ b/svc/worker.py
@@ -5,4 +5,5 @@ def run():
     try:
         work()
     except Exception:
+        pass
     return None
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"
    assert findings[0].location == "svc/worker.py:7"


def test_scan_diff_ignores_single_line_string_fixtures():
    """Single-line string literals containing suppression syntax produce no findings."""
    diff = """
--- a/tests/test_x.py
+++ b/tests/test_x.py
@@ -1,2 +1,4 @@
 def test_x():
+    fixture = "except Exception: pass"
+    note = "# noqa: E501 is allowed here"
     assert fixture
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 0


def test_scan_diff_ignores_typescript_comments_and_strings():
    """Commented out catches or string literals in TypeScript produce no findings."""
    diff = """
--- a/web/client.ts
+++ b/web/client.ts
@@ -1,3 +1,5 @@
 // Never write this:
+// catch (e) {}
+const msg = "catch (e) {}";
 export const x = 1;
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 0


def test_scan_diff_detects_vue_eslint_suppression():
    """HTML comment eslint-disable in Vue templates is detected as INFO."""
    diff = """
--- a/web/App.vue
+++ b/web/App.vue
@@ -1,3 +1,4 @@
 <template>
+  <!-- eslint-disable-next-line -->
   <div />
 </template>
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "INFO"
    assert "eslint-disable" in findings[0].defect


def test_scan_diff_ignores_js_doc_and_template_literals():
    """Diff scanner ignores documented catch in JSDoc block comments and backtick templates."""
    diff = """
--- a/web/util.ts
+++ b/web/util.ts
@@ -1,3 +1,7 @@
 /**
  * Never do this:
+ * catch (e) {}
+ * except Exception: pass
  */
 export const ok = 1;
--- a/web/doc.ts
+++ b/web/doc.ts
@@ -1,3 +1,6 @@
 const sample = `
+  catch (e) {}
+  except Exception: pass
 `;
 export const ok = 1;
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 0


def test_scan_diff_detects_multiline_block_comment_suppression():
    """Multi-line /* ... */ block comment with eslint-disable is detected as INFO."""
    diff = """
--- a/web/App.vue
+++ b/web/App.vue
@@ -1,3 +1,6 @@
+/*
+ * eslint-disable-next-line
+ */
 const a = 1;
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "INFO"
    assert "eslint-disable" in findings[0].defect


def test_scan_diff_does_not_flag_handled_exceptions():
    """Diff scanner allows exceptions with actual handling logic or logging."""
    diff = """
--- a/src/service.py
+++ b/src/service.py
@@ -10,3 +10,7 @@
 def run():
     try:
         work()
+    except Exception as exc:
+        logger.error("work failed: %s", exc)
+        raise
--- a/src/client.ts
+++ b/src/client.ts
@@ -20,3 +20,6 @@
 function request() {
     try {
         send();
+    } catch (err) {
+        console.error(err);
+    }
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 0


def test_scan_diff_ignores_triple_quoted_string_fixtures():
    """Diff scanner ignores docstrings and triple-quoted string fixtures in Python."""
    diff = """
--- a/tests/test_scanner.py
+++ b/tests/test_scanner.py
@@ -10,3 +10,12 @@
 def test_fixture():
+    fixture = \"\"\"
+--- a/pyrightconfig.json
++++ b/pyrightconfig.json
+@@ -1,2 +1,3 @@
++    "reportUnusedImport": false,
+--- a/src/foo.py
++++ b/src/foo.py
++    except Exception: pass
+\"\"\"
+    assert fixture is not None
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 0


def test_scan_diff_no_duplicate_findings_in_pin_files():
    """Baseline pin files report holistic widening without duplicate per-line checks."""
    diff = """
--- a/config/lint-suppressions.json
+++ b/config/lint-suppressions.json
@@ -1,2 +1,3 @@
 {
+  "reportAny": false
 }
"""
    findings = scan_diff_for_red_flags(diff)
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"
    assert "widened" in findings[0].defect


def test_scan_diff_does_not_flag_code_suppression_regex_in_source():
    """Regex definitions containing suppression names without comment prefixes are not flagged."""
    diff = """
--- a/src/rules.py
+++ b/src/rules.py
@@ -1,2 +1,3 @@
+pattern = re.compile(r"eslint-disable|pragma: no cover")
 def check(text):
     return pattern.search(text)
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


class _Frontmatter(BaseModel):
    """The SKILL.md frontmatter contract this test asserts on; extra keys stay the skill's business."""

    name: str
    description: str


def test_skill_frontmatter_and_context_load():
    """Ensure SKILL.md adheres to LSZ context-load policy and frontmatter schemas."""
    skill_md = SKILL_DIR / "SKILL.md"
    assert skill_md.exists()

    content = skill_md.read_text(encoding="utf-8")
    assert content.startswith("---")
    parts = content.split("---", 2)
    assert len(parts) >= 3

    meta = _Frontmatter.model_validate(yaml.safe_load(parts[1]))
    assert meta.name == "code-review"
    description = meta.description.strip()

    # Description budget: <= 300 chars
    assert len(description) <= 300, f"Description too long ({len(description)} chars)"
    # Must contain trigger vocabulary
    assert any(kw in description.lower() for kw in ["use when", "trigger", "when"]), (
        "Description lacks trigger vocabulary"
    )


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
