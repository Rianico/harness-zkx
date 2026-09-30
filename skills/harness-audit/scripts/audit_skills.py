#!/usr/bin/env python3
# pyright: reportMissingImports=false
# /// script
# requires-python = ">=3.14"
# dependencies = ["pydantic", "pyyaml"]
# ///

"""harness-audit: scan pi session JSONL for skill discovery & trigger capture.

Workload 3:
1. scan: Discovers installed skills, counts invocations, flags dead skills and
   zero-skill friction sessions.
2. capture: Extracts real session turns into trigger eval ledgers with dual snapshots
   (macro git provenance + micro routing description).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any, ClassVar, NoReturn, override

import yaml
from pydantic import BaseModel, ConfigDict, Field


# ── Domain Models ──
class DualSnapshot(BaseModel):
    git_commit: str
    date: str
    dirty: bool
    captured_description: str

    model_config: ClassVar[ConfigDict] = {"strict": True}


class Observation(BaseModel):
    command: str
    exit_code: int
    output: str

    model_config: ClassVar[ConfigDict] = {"strict": True}


class CaseRecord(BaseModel):
    id: str
    intent: str
    expect: str
    root_goal: str
    snapshot: DualSnapshot
    observation: Observation | None = None
    prompt: str | None = None

    model_config: ClassVar[ConfigDict] = {"strict": True}


class ZeroSkillFrictionSession(BaseModel):
    session_id: str
    path: str
    error_count: int = Field(ge=0)
    root_goal: str = ""

    model_config: ClassVar[ConfigDict] = {"strict": True}


class ScanResult(BaseModel):
    lookback_days: int = Field(ge=0)
    sessions_scanned: int = Field(ge=0)
    skill_invocations: dict[str, int]
    dead_skills: list[str]
    zero_skill_friction_sessions: list[ZeroSkillFrictionSession]

    model_config: ClassVar[ConfigDict] = {"strict": True}


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


class CustomArgumentParser(argparse.ArgumentParser):
    @override
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        eprint(f"error: {message}")
        sys.exit(1)


# ── Session & Skill Resolution ──
def get_session_roots(custom_roots: list[Path] | None = None) -> list[Path]:
    if custom_roots is not None:
        return [r.resolve() for r in custom_roots]
    env_root = os.environ.get("PI_SESSIONS_DIR")
    if env_root:
        return [Path(env_root).expanduser().resolve()]
    roots: list[Path] = [
        Path.home() / ".pi" / "agent" / "sessions",
        Path.home() / ".pi" / "sessions",
    ]
    return [r.resolve() for r in roots]


def resolve_session(target: str, custom_roots: list[Path] | None = None) -> Path | None:
    p = Path(target).expanduser()
    if p.is_file():
        return p.resolve()
    rel = Path.cwd() / target
    if rel.is_file():
        return rel.resolve()
    raw = target.strip()
    needle = raw
    if needle.endswith(".jsonl"):
        needle = needle[:-6]
    if "/" in needle:
        needle = needle.rsplit("/", 1)[-1]
    roots = get_session_roots(custom_roots)
    candidates: list[tuple[float, Path]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for f in root.rglob("*.jsonl"):
            name = f.name
            stem = name[:-6] if name.endswith(".jsonl") else name
            if needle in stem or needle in name or stem.endswith(needle) or needle == stem:
                try:
                    mtime = f.stat().st_mtime
                except OSError:
                    mtime = 0.0
                candidates.append((mtime, f))
            elif "_" in stem:
                uuid_part = stem.rsplit("_", 1)[-1]
                if needle == uuid_part or needle in uuid_part:
                    try:
                        mtime = f.stat().st_mtime
                    except OSError:
                        mtime = 0.0
                    candidates.append((mtime, f))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1].resolve()


def get_skill_roots(custom_roots: list[Path] | None = None) -> list[Path]:
    if custom_roots is not None:
        return [r.resolve() for r in custom_roots]
    env_skill = os.environ.get("PI_SKILLS_DIR")
    if env_skill:
        return [Path(env_skill).expanduser().resolve()]
    roots: list[Path] = [
        Path.cwd() / ".agents" / "skills",
        Path.cwd() / "skills",
        Path.home() / ".agents" / "skills",
        Path.home() / ".pi" / "agent" / "skills",
    ]
    return [r.resolve() for r in roots]


def discover_skills(skill_roots: list[Path] | None = None) -> dict[str, Path]:
    roots = get_skill_roots(skill_roots)
    found: dict[str, Path] = {}
    for r in roots:
        if not r.is_dir():
            continue
        try:
            for entry in r.iterdir():
                if entry.is_dir() and (entry / "SKILL.md").is_file():
                    if entry.name not in found:
                        found[entry.name] = entry
        except OSError:
            continue
    return found


def resolve_skill(name: str, skill_roots: list[Path] | None = None) -> Path | None:
    skills = discover_skills(skill_roots)
    if name in skills:
        return skills[name]
    for r in get_skill_roots(skill_roots):
        cand = r / name
        if cand.is_dir() and (cand / "SKILL.md").is_file():
            return cand
    return None


def extract_skill_description(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                if isinstance(fm, dict):
                    desc = fm.get("description", "")
                    if isinstance(desc, str):
                        return desc.strip()
            except Exception:
                pass
    return ""


def get_git_snapshot(skill_dir: Path) -> tuple[str, bool]:
    real_dir = skill_dir.resolve()
    commit = "unknown"
    dirty = False
    try:
        proc_log = subprocess.run(
            ["git", "-C", str(real_dir), "log", "-1", "--format=%h"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc_log.returncode == 0 and proc_log.stdout.strip():
            commit = proc_log.stdout.strip()
    except Exception:
        pass

    try:
        proc_stat = subprocess.run(
            ["git", "-C", str(real_dir), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc_stat.returncode == 0:
            dirty = bool(proc_stat.stdout.strip())
    except Exception:
        pass

    return commit, dirty


# ── Parsing Helpers ──
def _extract_skill_from_tool_call(tc_name: str, args: dict[str, Any]) -> str | None:
    if not (tc_name in ("read_skill", "Skill", "skill") or tc_name.endswith("_skill")):
        return None

    if args.get("path"):
        p = Path(str(args["path"]))
        if p.name.lower() == "skill.md":
            return p.parent.name
        return p.name
    if args.get("skill"):
        return str(args["skill"])
    if args.get("name"):
        return str(args["name"])
    if tc_name.endswith("_skill") and tc_name != "_skill":
        return tc_name[:-6]
    return None


def _extract_slash_commands(text: str) -> list[str]:
    return re.findall(r"/skill(?::|\s+)([a-zA-Z0-9_\-\.]+)", text)


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                txt = item.get("text")
                if isinstance(txt, str):
                    parts.append(txt)
        return "".join(parts)
    return ""


# ── Scan Workload ──
def parse_session_file(path: Path) -> tuple[str, dict[str, int], int, str]:
    session_id = ""
    invocations: dict[str, int] = {}
    error_count = 0
    root_goal = ""

    try:
        fp = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return session_id, invocations, error_count, root_goal

    with fp:
        for raw in fp:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            if not isinstance(rec, dict):
                continue

            rec_type = rec.get("type")
            if rec_type == "session":
                if not session_id and rec.get("id"):
                    session_id = str(rec["id"])
                continue

            if rec_type != "message":
                continue

            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "")
            content = msg.get("content")

            # First user prompt -> root_goal
            if role == "user" and not root_goal:
                user_text = _extract_text_content(content).strip()
                if user_text:
                    root_goal = user_text

            # Slash commands in text
            msg_text = _extract_text_content(content)
            for sk in _extract_slash_commands(msg_text):
                invocations[sk] = invocations.get(sk, 0) + 1

            # Tool calls
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "toolCall":
                        tc_name = str(item.get("name") or "")
                        args = item.get("arguments") or {}
                        if not isinstance(args, dict):
                            args = {}
                        sk = _extract_skill_from_tool_call(tc_name, args)
                        if sk:
                            invocations[sk] = invocations.get(sk, 0) + 1

            for tc in msg.get("toolCalls", []):
                if isinstance(tc, dict):
                    tc_name = str(tc.get("name") or "")
                    args = tc.get("arguments") or {}
                    if not isinstance(args, dict):
                        args = {}
                    sk = _extract_skill_from_tool_call(tc_name, args)
                    if sk:
                        invocations[sk] = invocations.get(sk, 0) + 1

            # Tool errors
            if role == "toolResult":
                is_err = bool(
                    msg.get("isError")
                    or rec.get("isError")
                    or msg.get("is_error")
                    or rec.get("is_error")
                    or (msg.get("exitCode") not in (0, None))
                    or (msg.get("exit_code") not in (0, None))
                )
                if is_err:
                    error_count += 1

    if not session_id:
        name = path.name
        stem = name[:-6] if name.endswith(".jsonl") else name
        session_id = stem.rsplit("_", 1)[-1] if "_" in stem else stem

    return session_id, invocations, error_count, root_goal


def scan(
    days: int = 30,
    roots: list[Path] | None = None,
    skill_roots: list[Path] | None = None,
) -> ScanResult:
    session_roots = get_session_roots(roots)
    now = time.time()
    cutoff = now - (days * 86400)
    session_files: list[Path] = []
    seen: set[Path] = set()

    for root in session_roots:
        if not root.is_dir():
            continue
        for f in root.rglob("*.jsonl"):
            try:
                rf = f.resolve()
                if rf in seen:
                    continue
                seen.add(rf)
                mtime = f.stat().st_mtime
                if mtime >= cutoff:
                    session_files.append(rf)
            except OSError:
                continue

    total_invocations: dict[str, int] = {}
    zero_skill_sessions: list[ZeroSkillFrictionSession] = []

    for sf in session_files:
        sid, invs, err_count, goal = parse_session_file(sf)
        for sk, count in invs.items():
            total_invocations[sk] = total_invocations.get(sk, 0) + count

        total_skills_loaded = sum(invs.values())
        if total_skills_loaded == 0 and err_count >= 3:
            zero_skill_sessions.append(
                ZeroSkillFrictionSession(
                    session_id=sid,
                    path=str(sf),
                    error_count=err_count,
                    root_goal=goal,
                )
            )

    installed = discover_skills(skill_roots)
    dead_skills = sorted(s for s in installed if total_invocations.get(s, 0) == 0)

    return ScanResult(
        lookback_days=days,
        sessions_scanned=len(session_files),
        skill_invocations=total_invocations,
        dead_skills=dead_skills,
        zero_skill_friction_sessions=zero_skill_sessions,
    )


# ── Capture Workload ──
def parse_session_for_capture(
    session_path: Path,
) -> tuple[str, list[dict[str, Any]], dict[str, str]]:
    root_goal = ""
    turns: list[dict[str, Any]] = []
    call_commands: dict[str, str] = {}

    try:
        fp = session_path.open("r", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise OSError(f"cannot open {session_path}: {exc}") from exc

    with fp:
        for idx, raw in enumerate(fp, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            if not isinstance(rec, dict):
                continue

            if rec.get("type") != "message":
                continue

            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "")
            content = msg.get("content")

            if role == "user" and not root_goal:
                user_text = _extract_text_content(content).strip()
                if user_text:
                    root_goal = user_text

            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "toolCall":
                        t_id = str(item.get("id") or "")
                        args = item.get("arguments") or {}
                        if not isinstance(args, dict):
                            args = {}
                        cmd = args.get("command") or args.get("cmd") or ""
                        if t_id and cmd:
                            call_commands[t_id] = str(cmd)

            for tc in msg.get("toolCalls", []):
                if isinstance(tc, dict):
                    t_id = str(tc.get("id") or "")
                    args = tc.get("arguments") or {}
                    if not isinstance(args, dict):
                        args = {}
                    cmd = args.get("command") or args.get("cmd") or ""
                    if t_id and cmd:
                        call_commands[t_id] = str(cmd)

            turns.append({
                "line": idx,
                "turn_index": len(turns) + 1,
                "role": role,
                "msg": msg,
                "rec": rec,
            })

    return root_goal, turns, call_commands


def turn_to_case_payload(
    turn: dict[str, Any], call_commands: dict[str, str]
) -> tuple[str, Any]:
    role = turn["role"]
    msg = turn["msg"]
    rec = turn["rec"]

    if role == "toolResult":
        tc_id = str(msg.get("toolCallId") or "")
        cmd = call_commands.get(tc_id, "")
        if not cmd and "|" in tc_id:
            for part in tc_id.split("|"):
                if part in call_commands:
                    cmd = call_commands[part]
                    break
        if not cmd:
            cmd = str(msg.get("command") or "")

        exit_code = msg.get("exitCode")
        if exit_code is None:
            exit_code = msg.get("exit_code")
        if exit_code is None:
            is_err = bool(
                msg.get("isError")
                or rec.get("isError")
                or msg.get("is_error")
                or rec.get("is_error")
            )
            exit_code = 1 if is_err else 0

        text = _extract_text_content(msg.get("content"))
        return "observation", {
            "command": cmd,
            "exit_code": int(exit_code),
            "output": text.strip(),
        }

    # For user or assistant prompt turns
    text = _extract_text_content(msg.get("content"))
    return "prompt", text.strip()


def capture(
    session_target: str | Path,
    skill_name: str,
    expect: str,
    intent: str | None = None,
    turn: int | None = None,
    evals_dir: Path | None = None,
    skill_roots: list[Path] | None = None,
    custom_session_roots: list[Path] | None = None,
) -> dict[str, Any]:
    if expect not in ("trigger", "no-trigger"):
        raise ValueError(f"Invalid expect '{expect}', must be 'trigger' or 'no-trigger'")

    if intent is None:
        intent = "in_domain" if expect == "trigger" else "hard_negative"
    elif intent not in ("in_domain", "hard_negative"):
        raise ValueError(
            f"Invalid intent '{intent}', must be 'in_domain' or 'hard_negative'"
        )

    session_path = resolve_session(str(session_target), custom_session_roots)
    if session_path is None:
        raise FileNotFoundError(f"Session not found: {session_target}")

    skill_dir = resolve_skill(skill_name, skill_roots)
    if skill_dir is None:
        raise ValueError(f"Skill not found: {skill_name}")

    captured_desc = extract_skill_description(skill_dir)
    git_commit, dirty = get_git_snapshot(skill_dir)
    today = date.today().isoformat()

    root_goal, turns, call_commands = parse_session_for_capture(session_path)
    if not turns:
        raise ValueError(f"Session contains no turns: {session_path}")

    selected_turn: dict[str, Any] | None = None
    if turn is not None:
        if turn < 1 or turn > len(turns):
            raise ValueError(f"Turn {turn} is out of bounds (1..{len(turns)})")
        selected_turn = turns[turn - 1]
    else:
        if expect == "trigger":
            for t in reversed(turns):
                if t["role"] == "toolResult":
                    is_err = bool(
                        t["msg"].get("isError")
                        or t["rec"].get("isError")
                        or t["msg"].get("is_error")
                        or t["rec"].get("is_error")
                        or (t["msg"].get("exitCode") not in (0, None))
                        or (t["msg"].get("exit_code") not in (0, None))
                    )
                    if is_err:
                        selected_turn = t
                        break
            if selected_turn is None:
                for t in reversed(turns):
                    if t["role"] == "user":
                        selected_turn = t
                        break
            if selected_turn is None:
                selected_turn = turns[-1]
        else:  # no-trigger
            for t in reversed(turns):
                if t["role"] == "toolResult":
                    is_err = bool(
                        t["msg"].get("isError")
                        or t["rec"].get("isError")
                        or t["msg"].get("is_error")
                        or t["rec"].get("is_error")
                        or (t["msg"].get("exitCode") not in (0, None))
                        or (t["msg"].get("exit_code") not in (0, None))
                    )
                    if not is_err:
                        selected_turn = t
                        break
            if selected_turn is None:
                for t in reversed(turns):
                    if t["role"] == "user":
                        selected_turn = t
                        break
            if selected_turn is None:
                selected_turn = turns[-1]

    payload_type, payload_data = turn_to_case_payload(selected_turn, call_commands)

    if evals_dir is None:
        env_evals = os.environ.get("PI_EVALS_DIR")
        target_evals_dir = (
            Path(env_evals).expanduser()
            if env_evals
            else Path.home() / ".pi" / "agent" / "evals"
        )
    else:
        target_evals_dir = evals_dir.resolve()

    target_evals_dir.mkdir(parents=True, exist_ok=True)
    eval_file = target_evals_dir / f"{skill_name}.yaml"

    existing_cases: list[dict[str, Any]] = []
    if eval_file.is_file():
        try:
            content = eval_file.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            if isinstance(data, list):
                existing_cases = data
            elif isinstance(data, dict):
                existing_cases = [data]
        except Exception:
            existing_cases = []

    existing_ids = {
        str(c["id"]) for c in existing_cases if "id" in c
    }
    case_num = len(existing_cases) + 1
    case_id = f"case_{case_num:03d}"
    while case_id in existing_ids:
        case_num += 1
        case_id = f"case_{case_num:03d}"

    snapshot = DualSnapshot(
        git_commit=git_commit,
        date=today,
        dirty=dirty,
        captured_description=captured_desc,
    )

    if payload_type == "observation":
        obs = Observation(
            command=payload_data["command"],
            exit_code=payload_data["exit_code"],
            output=payload_data["output"],
        )
        case_rec = CaseRecord(
            id=case_id,
            intent=intent,
            expect=expect,
            root_goal=root_goal,
            snapshot=snapshot,
            observation=obs,
        )
    else:
        case_rec = CaseRecord(
            id=case_id,
            intent=intent,
            expect=expect,
            root_goal=root_goal,
            snapshot=snapshot,
            prompt=str(payload_data),
        )

    case_dict = case_rec.model_dump(exclude_none=True)
    existing_cases.append(case_dict)
    _ = eval_file.write_text(
        yaml.dump(existing_cases, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return case_dict


# ── CLI Entrypoint ──
def build_parser() -> CustomArgumentParser:
    parser = CustomArgumentParser(
        prog="audit_skills.py",
        description="Audit skill discovery and capture session trigger evals.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", parser_class=CustomArgumentParser)

    # scan subparser
    scan_p = subparsers.add_parser("scan", help="Scan sessions for skill metrics and dead skills.")
    _ = scan_p.add_argument(
        "--days",
        type=int,
        default=30,
        help="Lookback window in days (default: 30)",
    )
    _ = scan_p.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON",
    )

    # capture subparser
    cap_p = subparsers.add_parser(
        "capture",
        help="Capture session turn into trigger eval ledger.",
    )
    _ = cap_p.add_argument("session", help="Session UUID or path to session JSONL")
    _ = cap_p.add_argument("--skill", required=True, help="Target skill name")
    _ = cap_p.add_argument(
        "--expect",
        required=True,
        choices=["trigger", "no-trigger"],
        help="Expected behavior (trigger | no-trigger)",
    )
    _ = cap_p.add_argument(
        "--intent",
        choices=["in_domain", "hard_negative"],
        default=None,
        help="Intent category (default: in_domain for trigger, hard_negative for no-trigger)",
    )
    _ = cap_p.add_argument(
        "--turn",
        type=int,
        default=None,
        help="Specific turn number (1-based)",
    )
    _ = cap_p.add_argument(
        "--json",
        action="store_true",
        help="Output captured case as JSON",
    )

    return parser


def main() -> None:
    # Default to 'scan' if no subcommand provided
    if len(sys.argv) == 1:
        sys.argv.insert(1, "scan")
    elif sys.argv[1] not in ("scan", "capture", "-h", "--help"):
        sys.argv.insert(1, "scan")

    parser = build_parser()
    args = parser.parse_args()

    if args.subcommand == "scan":
        if args.days < 0:
            eprint("error: --days must be non-negative")
            sys.exit(1)

        result = scan(days=args.days)
        if args.json:
            print(json.dumps(result.model_dump(), indent=2))
        else:
            print(f"Skill Discovery Audit (lookback: {result.lookback_days} days)")
            print("=" * 45)
            print(f"Sessions scanned: {result.sessions_scanned}")
            print("\nSkill Invocations:")
            if result.skill_invocations:
                for s, cnt in sorted(result.skill_invocations.items()):
                    print(f"  - {s}: {cnt}")
            else:
                print("  (none)")

            print(f"\nDead Skills ({len(result.dead_skills)}):")
            if result.dead_skills:
                for s in result.dead_skills:
                    print(f"  - {s}")
            else:
                print("  (none)")

            print(
                f"\nZero-Skill Friction Sessions ({len(result.zero_skill_friction_sessions)}):"
            )
            if result.zero_skill_friction_sessions:
                for z in result.zero_skill_friction_sessions:
                    goal_prev = f' - "{z.root_goal[:50]}..."' if z.root_goal else ""
                    print(f"  - {z.session_id} ({z.error_count} errors){goal_prev}")
            else:
                print("  (none)")
        sys.exit(0)

    if args.subcommand == "capture":
        # Resolve session first: exit code 2 if not found
        session_file = resolve_session(args.session)
        if session_file is None:
            eprint(f"error: session not found: {args.session}")
            sys.exit(2)

        # Resolve skill: exit code 1 if not found
        skill_dir = resolve_skill(args.skill)
        if skill_dir is None:
            eprint(f"error: skill not found: {args.skill}")
            sys.exit(1)

        try:
            case_data = capture(
                session_target=session_file,
                skill_name=args.skill,
                expect=args.expect,
                intent=args.intent,
                turn=args.turn,
            )
            if args.json:
                print(json.dumps(case_data, indent=2))
            else:
                print(
                    f"Captured case '{case_data['id']}' for skill '{args.skill}' "
                    f"(expect={case_data['expect']}, intent={case_data['intent']})"
                )
            sys.exit(0)
        except Exception as e:
            eprint(f"error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
