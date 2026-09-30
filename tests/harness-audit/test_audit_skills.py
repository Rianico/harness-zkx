import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

# conftest adds skills/harness-audit/scripts to sys.path
import audit_skills  # type: ignore[import-not-found]
import pytest
import yaml

_SCRIPT = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "harness-audit"
    / "scripts"
    / "audit_skills.py"
)


# ── Test Helpers ──
def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            _ = f.write(json.dumps(r, ensure_ascii=False) + "\n")


def session_header(sid: str = "test-uuid") -> dict[str, Any]:
    return {
        "type": "session",
        "version": 3,
        "id": sid,
        "timestamp": "2026-09-01T00:00:00Z",
        "cwd": "/tmp",
    }


def user_msg(mid: str, text: str) -> dict[str, Any]:
    return {
        "type": "message",
        "id": mid,
        "parentId": None,
        "timestamp": "2026-09-01T00:00:01Z",
        "message": {
            "role": "user",
            "content": text,
        },
    }


def toolcall_msg(
    mid: str,
    call_id: str,
    name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "message",
        "id": mid,
        "parentId": None,
        "timestamp": "2026-09-01T00:00:02Z",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "toolCall",
                    "id": call_id,
                    "name": name,
                    "arguments": arguments,
                }
            ],
        },
    }


def toolresult_msg(
    mid: str,
    call_id: str,
    tool_name: str,
    text: str,
    is_error: bool = False,
    exit_code: int = 0,
) -> dict[str, Any]:
    return {
        "type": "message",
        "id": mid,
        "parentId": None,
        "timestamp": "2026-09-01T00:00:03Z",
        "message": {
            "role": "toolResult",
            "toolCallId": call_id,
            "toolName": tool_name,
            "content": [{"type": "text", "text": text}],
            "isError": is_error,
            "exitCode": exit_code,
        },
    }


def create_mock_skill(
    root: Path,
    name: str,
    description: str = "Test skill description",
    init_git: bool = False,
) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    content = f"""---
name: {name}
description: >-
  {description}
---

# {name}
Detailed docs.
"""
    _ = skill_md.write_text(content, encoding="utf-8")

    if init_git:
        _ = subprocess.run(
            ["git", "init"],
            cwd=str(skill_dir),
            capture_output=True,
            check=True,
        )
        _ = subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(skill_dir),
            capture_output=True,
            check=True,
        )
        _ = subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(skill_dir),
            capture_output=True,
            check=True,
        )
        _ = subprocess.run(
            ["git", "add", "."],
            cwd=str(skill_dir),
            capture_output=True,
            check=True,
        )
        _ = subprocess.run(
            ["git", "commit", "-m", "initial commit"],
            cwd=str(skill_dir),
            capture_output=True,
            check=True,
        )

    return skill_dir


# ── Group 1: resolve_session ──
def test_resolve_session_direct_path(tmp_path: Path) -> None:
    session_file = tmp_path / "custom_sess.jsonl"
    _ = session_file.write_text("{}\n", encoding="utf-8")
    resolved = audit_skills.resolve_session(str(session_file))
    assert resolved == session_file.resolve()


def test_resolve_session_by_uuid(tmp_path: Path) -> None:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    sess_file = sessions_dir / "2026-09-01T00-00-00_target-uuid-999.jsonl"
    _ = sess_file.write_text("{}\n", encoding="utf-8")

    resolved = audit_skills.resolve_session(
        "target-uuid-999",
        custom_roots=[sessions_dir],
    )
    assert resolved == sess_file.resolve()


def test_resolve_session_missing_returns_none(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty_sessions"
    empty_dir.mkdir(parents=True, exist_ok=True)
    resolved = audit_skills.resolve_session(
        "missing-uuid",
        custom_roots=[empty_dir],
    )
    assert resolved is None


def test_resolve_session_cli_missing_exits_2(tmp_path: Path) -> None:
    res = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "capture",
            "non-existent-session-id",
            "--skill",
            "adr",
            "--expect",
            "trigger",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "session not found" in res.stderr.lower()


# ── Group 2: scan mode ──
def test_scan_detection_of_invocations_and_dead_skills(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _ = create_mock_skill(skills_root, "active_a")
    _ = create_mock_skill(skills_root, "active_b")
    _ = create_mock_skill(skills_root, "dead_skill")

    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)
    sess_file = sessions_root / "sess1.jsonl"

    write_jsonl(
        sess_file,
        [
            session_header("sess1"),
            user_msg("m1", "Please run /skill:active_b on this code"),
            toolcall_msg("m2", "c1", "read_skill", {"path": f"{skills_root}/active_a/SKILL.md"}),
            toolcall_msg("m3", "c2", "Skill", {"skill": "active_a"}),
            toolcall_msg("m4", "c3", "active_b_skill", {}),
            user_msg("m5", "Also try /skill active_a"),
        ],
    )

    result = audit_skills.scan(
        days=30,
        roots=[sessions_root],
        skill_roots=[skills_root],
    )

    assert result.sessions_scanned == 1
    assert result.skill_invocations.get("active_a") == 3
    assert result.skill_invocations.get("active_b") == 2
    assert "dead_skill" in result.dead_skills
    assert "active_a" not in result.dead_skills
    assert "active_b" not in result.dead_skills


def test_scan_zero_skill_friction_session_detection(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _ = create_mock_skill(skills_root, "some_skill")

    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)

    # Session 1: 0 skills, 3 tool errors -> SHOULD be friction session
    sess_friction = sessions_root / "friction.jsonl"
    write_jsonl(
        sess_friction,
        [
            session_header("friction-id"),
            user_msg("m1", "Fix the failing tests"),
            toolcall_msg("m2", "c1", "bash", {"command": "pytest"}),
            toolresult_msg("m3", "c1", "bash", "FAIL test 1", is_error=True, exit_code=1),
            toolcall_msg("m4", "c2", "bash", {"command": "pytest"}),
            toolresult_msg("m5", "c2", "bash", "FAIL test 2", is_error=True, exit_code=1),
            toolcall_msg("m6", "c3", "bash", {"command": "pytest"}),
            toolresult_msg("m7", "c3", "bash", "FAIL test 3", is_error=True, exit_code=1),
        ],
    )

    # Session 2: 1 skill loaded, 4 tool errors -> NOT a zero-skill session
    sess_with_skill = sessions_root / "with_skill.jsonl"
    write_jsonl(
        sess_with_skill,
        [
            session_header("skill-id"),
            user_msg("m1", "Use skill"),
            toolcall_msg("m2", "c0", "read_skill", {"path": f"{skills_root}/some_skill/SKILL.md"}),
            toolcall_msg("m3", "c1", "bash", {"command": "err1"}),
            toolresult_msg("m4", "c1", "bash", "err", is_error=True),
            toolcall_msg("m5", "c2", "bash", {"command": "err2"}),
            toolresult_msg("m6", "c2", "bash", "err", is_error=True),
            toolcall_msg("m7", "c3", "bash", {"command": "err3"}),
            toolresult_msg("m8", "c3", "bash", "err", is_error=True),
        ],
    )

    # Session 3: 0 skills, only 2 tool errors -> NOT friction (< 3 errors)
    sess_low_error = sessions_root / "low_err.jsonl"
    write_jsonl(
        sess_low_error,
        [
            session_header("low-err-id"),
            user_msg("m1", "Task"),
            toolcall_msg("m2", "c1", "bash", {"command": "err1"}),
            toolresult_msg("m3", "c1", "bash", "err", is_error=True),
            toolcall_msg("m4", "c2", "bash", {"command": "err2"}),
            toolresult_msg("m5", "c2", "bash", "err", is_error=True),
        ],
    )

    result = audit_skills.scan(
        days=30,
        roots=[sessions_root],
        skill_roots=[skills_root],
    )

    assert result.sessions_scanned == 3
    assert len(result.zero_skill_friction_sessions) == 1
    friction = result.zero_skill_friction_sessions[0]
    assert friction.session_id == "friction-id"
    assert friction.error_count == 3
    assert friction.root_goal == "Fix the failing tests"


def test_scan_lookback_window_filters_old_sessions(tmp_path: Path) -> None:
    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)
    old_sess = sessions_root / "old.jsonl"
    write_jsonl(old_sess, [session_header("old-uuid")])

    # Set mtime to 60 days ago
    old_mtime = time.time() - (60 * 86400)
    os.utime(old_sess, (old_mtime, old_mtime))

    result = audit_skills.scan(
        days=30,
        roots=[sessions_root],
        skill_roots=[tmp_path],
    )
    assert result.sessions_scanned == 0


def test_scan_cli_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)
    skills_root = tmp_path / "skills"
    _ = create_mock_skill(skills_root, "mock_skill")

    sess_file = sessions_root / "test_sess.jsonl"
    write_jsonl(
        sess_file,
        [
            session_header("json-test"),
            user_msg("m1", "Run /skill:mock_skill"),
        ],
    )

    monkeypatch.setenv("PI_SESSIONS_DIR", str(sessions_root))
    monkeypatch.setenv("PI_SKILLS_DIR", str(skills_root))

    res = subprocess.run(
        [sys.executable, str(_SCRIPT), "scan", "--days", "10", "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["lookback_days"] == 10
    assert data["sessions_scanned"] == 1
    assert data["skill_invocations"]["mock_skill"] == 1
    assert data["dead_skills"] == []


# ── Group 3: capture mode ──
def test_capture_tool_error_observation_dual_snapshot(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _ = create_mock_skill(
        skills_root,
        "merge_tool",
        description="Reconciles git merge and rebase conflicts.",
        init_git=True,
    )

    session_file = tmp_path / "rebase_conflict.jsonl"
    write_jsonl(
        session_file,
        [
            session_header("rebase-session-uuid"),
            user_msg("m1", "Resolve conflict in main branch"),
            toolcall_msg("m2", "call_bash_1", "bash", {"command": "git rebase origin/main"}),
            toolresult_msg(
                "m3",
                "call_bash_1",
                "bash",
                "CONFLICT (content): Merge conflict in file.py",
                is_error=True,
                exit_code=1,
            ),
        ],
    )

    evals_dir = tmp_path / "evals"
    case = audit_skills.capture(
        session_target=session_file,
        skill_name="merge_tool",
        expect="trigger",
        intent="in_domain",
        evals_dir=evals_dir,
        skill_roots=[skills_root],
    )

    assert case["id"] == "case_001"
    assert case["intent"] == "in_domain"
    assert case["expect"] == "trigger"
    assert case["root_goal"] == "Resolve conflict in main branch"

    snapshot = case["snapshot"]
    assert snapshot["git_commit"] != "unknown"
    assert snapshot["dirty"] is False
    assert snapshot["date"] == date.today().isoformat()
    assert "Reconciles git merge" in snapshot["captured_description"]

    assert "observation" in case
    obs = case["observation"]
    assert obs["command"] == "git rebase origin/main"
    assert obs["exit_code"] == 1
    assert "CONFLICT (content)" in obs["output"]
    assert "prompt" not in case

    # Verify saved YAML
    eval_file = evals_dir / "merge_tool.yaml"
    assert eval_file.is_file()
    saved = yaml.safe_load(eval_file.read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["id"] == "case_001"


def test_capture_user_prompt_dual_snapshot(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _ = create_mock_skill(
        skills_root,
        "clean_arch",
        description="Enforces clean architecture boundaries.",
        init_git=False,
    )

    session_file = tmp_path / "prompt_sess.jsonl"
    write_jsonl(
        session_file,
        [
            session_header("prompt-session-uuid"),
            user_msg("m1", "Please format this python script nicely"),
        ],
    )

    evals_dir = tmp_path / "evals"
    case = audit_skills.capture(
        session_target=session_file,
        skill_name="clean_arch",
        expect="no-trigger",
        intent="hard_negative",
        evals_dir=evals_dir,
        skill_roots=[skills_root],
    )

    assert case["id"] == "case_001"
    assert case["intent"] == "hard_negative"
    assert case["expect"] == "no-trigger"
    assert case["prompt"] == "Please format this python script nicely"
    assert "observation" not in case


def test_capture_append_to_existing_eval_yaml(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _ = create_mock_skill(skills_root, "eval_skill", description="Skill description")

    evals_dir = tmp_path / "evals"
    evals_dir.mkdir(parents=True, exist_ok=True)
    existing_case = {
        "id": "case_001",
        "intent": "in_domain",
        "expect": "trigger",
        "root_goal": "Goal 1",
        "snapshot": {
            "git_commit": "abc",
            "date": "2026-09-01",
            "dirty": False,
            "captured_description": "Initial desc",
        },
        "prompt": "Test prompt 1",
    }
    eval_file = evals_dir / "eval_skill.yaml"
    _ = eval_file.write_text(yaml.dump([existing_case]), encoding="utf-8")

    session_file = tmp_path / "sess2.jsonl"
    write_jsonl(
        session_file,
        [
            session_header("sess2"),
            user_msg("m1", "Second goal"),
            user_msg("m2", "Subsequent turn prompt"),
        ],
    )

    case2 = audit_skills.capture(
        session_target=session_file,
        skill_name="eval_skill",
        expect="no-trigger",
        turn=2,
        evals_dir=evals_dir,
        skill_roots=[skills_root],
    )

    assert case2["id"] == "case_002"
    saved = yaml.safe_load(eval_file.read_text(encoding="utf-8"))
    assert len(saved) == 2
    assert saved[0]["id"] == "case_001"
    assert saved[1]["id"] == "case_002"
    assert saved[1]["prompt"] == "Subsequent turn prompt"


def test_capture_missing_session_cli_exit_2(tmp_path: Path) -> None:
    res = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "capture",
            str(tmp_path / "nonexistent.jsonl"),
            "--skill",
            "adr",
            "--expect",
            "trigger",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "session not found" in res.stderr.lower()


def test_capture_missing_skill_cli_exit_1(tmp_path: Path) -> None:
    session_file = tmp_path / "valid.jsonl"
    write_jsonl(session_file, [session_header("valid-sess"), user_msg("m1", "test")])

    res = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "capture",
            str(session_file),
            "--skill",
            "completely_missing_skill",
            "--expect",
            "trigger",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "skill not found" in res.stderr.lower()


# ── Group 4: CLI Subprocess & Help ──
def test_cli_help() -> None:
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "usage: audit_skills.py" in res.stdout
    assert "scan" in res.stdout
    assert "capture" in res.stdout


def test_cli_capture_help() -> None:
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), "capture", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "usage: audit_skills.py capture" in res.stdout
    assert "--skill" in res.stdout
    assert "--expect" in res.stdout


def test_cli_default_scan_invoked_without_subcommand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PI_SESSIONS_DIR", str(sessions_root))

    res = subprocess.run(
        [sys.executable, str(_SCRIPT), "--days", "15", "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["lookback_days"] == 15
    assert data["sessions_scanned"] == 0
