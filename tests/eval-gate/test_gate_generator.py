"""Tests for eval-gate stack discovery, runner synthesis, and execution."""

import json
import subprocess
import sys
from pathlib import Path

# Module-level sys.path insert per LSZ convention
SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "eval-gate"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from gate_generator import (
    detect_stack,
    format_worker_feedback,
    get_project_slug_with_hash,
    grade_semantic_assertions,
    resolve_workflow_dir,
    synthesize_gate_script,
    synthesize_unified_gate,
    update_regression_ledger,
)


def test_detect_stack_rust(tmp_path):
    """Detects Rust project when Cargo.toml is present."""
    (tmp_path / "Cargo.toml").write_text("[package]\nname = 'demo'", encoding="utf-8")
    profile = detect_stack(tmp_path)
    assert profile.name == "rust"
    assert profile.package_manager == "cargo"
    check_ids = [c.id for c in profile.checks]
    assert "BUILD-01" in check_ids
    assert "LINT-01" in check_ids
    assert "TEST-01" in check_ids


def test_detect_stack_typescript(tmp_path):
    """Detects TypeScript project with package.json and tsconfig.json."""
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "vitest"}}), encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    profile = detect_stack(tmp_path)
    assert profile.name == "typescript"
    check_phases = [c.phase for c in profile.checks]
    assert "test" in check_phases


def test_detect_stack_python(tmp_path):
    """Detects Python project with pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'", encoding="utf-8")
    profile = detect_stack(tmp_path)
    assert profile.name == "python"
    check_phases = [c.phase for c in profile.checks]
    assert "test" in check_phases


def test_detect_stack_go(tmp_path):
    """Detects Go project with go.mod."""
    (tmp_path / "go.mod").write_text("module demo\n\ngo 1.22", encoding="utf-8")
    profile = detect_stack(tmp_path)
    assert profile.name == "go"
    assert profile.package_manager == "go"
    check_ids = [c.id for c in profile.checks]
    assert "BUILD-01" in check_ids
    assert "VET-01" in check_ids
    assert "TEST-01" in check_ids


def test_detect_stack_generic(tmp_path):
    """Falls back to generic stack when no recognized manifest is present."""
    profile = detect_stack(tmp_path)
    assert profile.name == "generic"


def test_synthesize_gate_script_execution(tmp_path):
    """Synthesizes an executable gate script and verifies its JSON output."""
    output_dir = tmp_path / "eval_run"
    custom_checks = [
        {"id": "ECHO-01", "phase": "build", "command": ["echo", "hello"], "description": "Echo check"},
        {"id": "TRUE-01", "phase": "test", "command": ["true"], "description": "True test"},
    ]
    script_path = synthesize_gate_script(
        repo_root=tmp_path,
        output_dir=output_dir,
        custom_criteria=custom_checks,
    )
    assert script_path.exists()

    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "pass"
    assert data["score"] == 100
    assert "ECHO-01" in data["criteria"]
    assert data["criteria"]["ECHO-01"]["status"] == "pass"
    assert len(data["issues"]) == 0


def test_synthesize_gate_script_failure_reporting(tmp_path):
    """Synthesizes a gate script with a failing command and verifies structured failure reporting."""
    output_dir = tmp_path / "eval_run_fail"
    custom_checks = [
        {"id": "PASS-01", "phase": "build", "command": ["true"], "description": "Passing check"},
        {"id": "FAIL-01", "phase": "test", "command": [sys.executable, "-c", "import sys; sys.exit(1)"], "description": "Failing check"},
    ]
    script_path = synthesize_gate_script(
        repo_root=tmp_path,
        output_dir=output_dir,
        custom_criteria=custom_checks,
    )

    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["status"] == "fail"
    assert data["score"] == 50
    assert data["criteria"]["FAIL-01"]["status"] == "fail"
    assert len(data["issues"]) > 0


def test_get_project_slug_with_hash(tmp_path):
    """Verifies format of project slug containing folder name and 12-char SHA-256 hash."""
    project_dir = tmp_path / "sample-app"
    project_dir.mkdir()
    slug = get_project_slug_with_hash(project_dir)
    assert slug.startswith("sample-app-")
    parts = slug.rsplit("-", 1)
    assert len(parts[1]) == 12


def test_resolve_workflow_dir(tmp_path):
    """Verifies workflow directory resolution with base override and default ~/.pi path."""
    project_dir = tmp_path / "my-repo"
    project_dir.mkdir()

    # 1. With base_dir override
    custom_base = tmp_path / "custom_workflows"
    p1 = resolve_workflow_dir(project_dir, topic="auth-login", base_dir=custom_base)
    assert p1 == (custom_base / "auth-login").resolve()
    assert p1.exists()

    # 2. Default ~/.pi resolution
    p2 = resolve_workflow_dir(project_dir, topic="auth-login")
    assert ".pi" in str(p2)
    assert "workflows" in str(p2)
    assert "projects" in str(p2)
    assert p2.name == "auth-login"
    assert p2.exists()


def test_synthesize_unified_gate(tmp_path):
    """Synthesizes unified gate producing gate.json, run_evals.py, and initial ledger.json."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname = 'test'", encoding="utf-8")

    out_dir = tmp_path / "workflows" / "test-gate"
    gate_path, script_path = synthesize_unified_gate(
        repo_root=repo,
        topic="feature-x",
        output_dir=out_dir,
    )

    assert gate_path.exists()
    assert script_path.exists()
    ledger_path = out_dir / "ledger.json"
    assert ledger_path.exists()

    gate_data = json.loads(gate_path.read_text(encoding="utf-8"))
    assert gate_data["gate_version"] == 2
    assert gate_data["target"] == "feature-x"
    assert gate_data["deterministic_floor"]["stack"] == "python"
    assert len(gate_data["semantic_ceiling"]["assertions"]) >= 4

    ledger_data = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger_data["best_score"] == 0
    assert ledger_data["immutable_invariants"] == []


def test_grade_semantic_assertions_all_pass():
    """Calculates score 10 when all assertions pass."""
    assertions = [
        {"id": "SEM-01", "statement": "Does not swallow errors", "critical": True},
        {"id": "SEM-02", "statement": "Refutable tests present", "critical": True},
    ]
    grader_results = [
        {"id": "SEM-01", "passed": True, "evidence": "file.py:10", "reasoning": "Proper raise"},
        {"id": "SEM-02", "passed": True, "evidence": "test.py:20", "reasoning": "Refutable assertion"},
    ]
    score, graded, issues = grade_semantic_assertions(assertions, grader_results)
    assert score == 10
    assert len(graded) == 2
    assert len(issues) == 0


def test_grade_semantic_assertions_critical_failure_caps_score():
    """Ensures critical assertion failure caps score to 7 even if ratio is high."""
    assertions = [
        {"id": "SEM-01", "statement": "Feature A works", "critical": False},
        {"id": "SEM-02", "statement": "Feature B works", "critical": False},
        {"id": "SEM-03", "statement": "Feature C works", "critical": False},
        {"id": "SEM-04", "statement": "No empty catch swallows", "critical": True},
    ]
    # 3 out of 4 pass -> normally round(0.75 * 9) + 1 = 8, but critical failed so capped at 7
    grader_results = [
        {"id": "SEM-01", "passed": True},
        {"id": "SEM-02", "passed": True},
        {"id": "SEM-03", "passed": True},
        {"id": "SEM-04", "passed": False, "evidence": "app.ts:42", "reasoning": "catch {} found"},
    ]
    score, graded, issues = grade_semantic_assertions(assertions, grader_results)
    assert score == 7
    assert len(issues) == 1
    assert "SEM-04" in issues[0]
    assert "app.ts:42" in issues[0]


def test_update_regression_ledger_and_anti_thrashing(tmp_path):
    """Tracks invariants across iterations and detects whac-a-mole regressions."""
    ledger_file = tmp_path / "ledger.json"

    # Loop 1: TEST-01 and LINT-01 pass
    data1 = update_regression_ledger(
        ledger_path=ledger_file,
        loop=1,
        floor_status="pass",
        semantic_score=8,
        passed_items=["TEST-01", "LINT-01"],
        failed_items=[],
        git_commit="commit_aaa",
    )
    assert set(data1["immutable_invariants"]) == {"TEST-01", "LINT-01"}
    assert data1["best_score"] == 8
    assert data1["best_commit"] == "commit_aaa"
    assert len(data1["history"][0]["regressions"]) == 0

    # Loop 2: LINT-01 passes, but TEST-01 fails (regression!)
    data2 = update_regression_ledger(
        ledger_path=ledger_file,
        loop=2,
        floor_status="fail",
        semantic_score=6,
        passed_items=["LINT-01"],
        failed_items=["TEST-01"],
        git_commit="commit_bbb",
    )
    assert data2["best_score"] == 8
    assert data2["best_commit"] == "commit_aaa"  # Preserved earlier best checkpoint
    assert "TEST-01" in data2["history"][1]["regressions"]


def test_format_worker_feedback():
    """Generates structured worker feedback with regression alerts and autoresearch checkpoint."""
    ledger = {
        "best_score": 9,
        "best_commit": "abc12345678",
        "immutable_invariants": ["TEST-01", "LINT-01"],
        "history": [
            {"loop": 1, "regressions": []},
            {"loop": 2, "regressions": ["TEST-01"]},
        ],
    }
    feedback = format_worker_feedback(ledger, ["TEST-01: assertion error on line 55"])
    assert "🚨 REGRESSION ALERT" in feedback
    assert "- [REGRESSION] TEST-01" in feedback
    assert "## Preserved Invariants" in feedback
    assert "- [INVARIANT] TEST-01" in feedback
    assert "Autoresearch Checkpoint: Best score 9/10 at git commit abc12345" in feedback


def test_cli_subcommands(tmp_path):
    """Tests CLI subcommands: resolve-dir, grade-assertions, and update-ledger."""
    script_file = SCRIPTS_DIR / "gate_generator.py"
    repo = tmp_path / "repo"
    repo.mkdir()

    # 1. resolve-dir
    res = subprocess.run(
        [sys.executable, str(script_file), "resolve-dir", "--repo-root", str(repo), "--topic", "t1", "--base-dir", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "t1" in res.stdout

    # 2. grade-assertions
    gate_file = tmp_path / "gate.json"
    gate_file.write_text(json.dumps({
        "semantic_ceiling": {
            "assertions": [{"id": "SEM-01", "statement": "Test pass", "critical": True}]
        }
    }), encoding="utf-8")
    graders_file = tmp_path / "graders.json"
    graders_file.write_text(json.dumps([{"id": "SEM-01", "passed": True, "evidence": "x", "reasoning": "y"}]), encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script_file), "grade-assertions", "--assertions", str(gate_file), "--grader-results", str(graders_file)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    grade_data = json.loads(res.stdout)
    assert grade_data["score"] == 10

    # 3. update-ledger
    ledger_file = tmp_path / "ledger.json"
    feedback_file = tmp_path / "feedback.md"
    res = subprocess.run(
        [
            sys.executable,
            str(script_file),
            "update-ledger",
            "--ledger-path",
            str(ledger_file),
            "--loop",
            "1",
            "--floor-status",
            "pass",
            "--semantic-score",
            "9",
            "--passed-items",
            "TEST-01,LINT-01",
            "--failed-items",
            "",
            "--git-commit",
            "abcdef123456",
            "--emit-feedback",
            str(feedback_file),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert feedback_file.exists()
    assert "Autoresearch Checkpoint" in feedback_file.read_text(encoding="utf-8")

