#!/usr/bin/env python3
# pyright: reportMissingImports=false
# /// script
# requires-python = ">=3.14"
# dependencies = ["pydantic"]
# ///

"""harness-audit edit workload: scan pi session JSONL for edit tool failures.

Parse JSONL line-by-line, pair ``edit`` toolCall -> toolResult, compute
success/failure stats, classify rejections by domain error code
(E_UNKNOWN_ANCHOR, E_FOREIGN_ANCHOR, E_MALFORMED_ANCHOR, E_BATCH_ABORT,
E_TARGET_LOST, ...), and flag diagnostic patterns (numeric line-number
anchors, cross-file leaked anchors). Read-only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

CODE_RE = re.compile(r"\b(E_[A-Z_]+)\b")
QUOTED_RE = re.compile(r'"([^"]+)"')
SERVED_FOR_RE = re.compile(r"served for ([^;\s]+)")
NUMERIC_RE = re.compile(r"^\d+$")

KNOWN_CODES = (
    "E_UNKNOWN_ANCHOR",
    "E_FOREIGN_ANCHOR",
    "E_MALFORMED_ANCHOR",
    "E_BATCH_ABORT",
    "E_TARGET_LOST",
)
# Domain codes observed in the wild but outside the core set above.
EXTRA_CODES = ("E_STALE_ANCHOR", "E_UNSERVED_RANGE")


# ── Pydantic domain models ──
class NextTurn(BaseModel):
    jsonl_line: int = Field(ge=1)
    role: str
    type: str
    preview: str = Field(max_length=240)

    model_config: ClassVar[ConfigDict] = {"strict": True}


class EditFailure(BaseModel):
    jsonl_line: int = Field(ge=1)
    toolCallId: str
    file: str
    code: str
    category: str = "?"
    anchors: list[str] = Field(default_factory=list)
    numeric_anchors: list[str] = Field(default_factory=list)
    foreign_served_for: str | None = None
    message_preview: str = ""
    next_turns: list[NextTurn] = Field(default_factory=list)

    model_config: ClassVar[ConfigDict] = {"strict": True}


class EditAuditResult(BaseModel):
    session_path: str
    session_file: str
    record_count: int = Field(ge=0)
    parse_errors: int = Field(ge=0)
    edit_count: int = Field(ge=0)
    success_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)
    failure_rate: float = Field(ge=0.0, le=1.0)
    by_code: dict[str, int] = Field(default_factory=dict)
    by_file: dict[str, int] = Field(default_factory=dict)
    numeric_anchor_failures: int = Field(ge=0)
    foreign_leak_failures: int = Field(ge=0)
    failures: list[EditFailure] = Field(default_factory=list)

    model_config: ClassVar[ConfigDict] = {"strict": True}


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def resolve_session(target: str) -> Path | None:
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
    roots: list[Path] = []
    env_root = os.environ.get("PI_SESSIONS_DIR")
    if env_root:
        roots.append(Path(env_root).expanduser())
    roots.append(Path.home() / ".pi" / "agent" / "sessions")
    alt = Path.home() / ".pi" / "sessions"
    if alt not in roots:
        roots.append(alt)
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
                    mtime = 0
                candidates.append((mtime, f))
            elif "_" in stem:
                uuid_part = stem.rsplit("_", 1)[-1]
                if needle == uuid_part or needle in uuid_part:
                    try:
                        mtime = f.stat().st_mtime
                    except OSError:
                        mtime = 0
                    candidates.append((mtime, f))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1].resolve()


def _preview_for_msg(msg: dict[str, Any]) -> str:
    try:
        cnt = msg.get("content")
        if isinstance(cnt, str):
            return cnt[:120].replace("\n", " ⏎ ")
        if isinstance(cnt, list):
            for it in cnt:
                if not isinstance(it, dict):
                    continue
                t = it.get("type")
                if t == "text" and isinstance(it.get("text"), str):
                    return it["text"][:120].replace("\n", " ⏎ ")
                if t == "toolCall" and isinstance(it.get("name"), str):
                    cmd = ""
                    args = it.get("arguments") or {}
                    if isinstance(args, dict):
                        cmd = str(args.get("command") or args.get("cmd") or args.get("file") or "")[
                            :80
                        ]
                    return f"toolCall:{it.get('name')}:{cmd}".replace("\n", " ⏎ ")
        return str(msg.get("role", ""))[:120]
    except Exception:
        return ""


def _call_anchors(args: dict[str, Any]) -> list[str]:
    anchors: list[str] = []
    edits = args.get("edits")
    if isinstance(edits, list):
        for e in edits:
            if not isinstance(e, dict):
                continue
            for key in ("anchor_from", "anchor_to"):
                v = e.get(key)
                if isinstance(v, str) and v and v not in anchors:
                    anchors.append(v)
    return anchors


def _result_text(msg: dict[str, Any]) -> str:
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                t = c.get("text")
                if isinstance(t, str):
                    parts.append(t)
        return "".join(parts)
    return ""


def classify(text: str) -> str:
    m = CODE_RE.search(text)
    if m:
        return m.group(1)
    return "E_NO_CODE" if text else "E_EMPTY_RESULT"


def categorize(code: str, numeric_anchors: list[str], is_leak: bool) -> str:
    """Deterministic triage bucket: N/F/B/T/M/H, '?' when unrecognized."""
    if numeric_anchors:
        return "N"
    if is_leak or code == "E_FOREIGN_ANCHOR":
        return "F"
    direct = {"E_BATCH_ABORT": "B", "E_TARGET_LOST": "T", "E_MALFORMED_ANCHOR": "M"}
    if code in direct:
        return direct[code]
    if code in ("E_UNKNOWN_ANCHOR", *EXTRA_CODES):
        return "H"
    return "?"


def scan(path: Path, with_context: int = 0) -> dict[str, Any]:
    calls: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    parse_errors = 0
    record_count = 0
    edit_count = 0
    success_count = 0
    by_code: dict[str, int] = {}
    by_file: dict[str, int] = {}
    numeric_anchor_failures = 0
    foreign_leak_failures = 0
    unknown_codes: set[str] = set()
    full_by_line: dict[int, list[dict[str, Any]]] = {}
    fp = path.open("r", encoding="utf-8", errors="replace")
    with fp:
        for idx, raw in enumerate(fp, start=1):
            record_count = idx
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if not isinstance(rec, dict) or rec.get("type") != "message":
                continue
            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            if role == "assistant":
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "toolCall" and item.get("name") == "edit":
                        tc_id = item.get("id") or ""
                        args = item.get("arguments")
                        if not isinstance(args, dict):
                            args = {}
                        if tc_id:
                            calls[tc_id] = {
                                "jsonl_line": idx,
                                "file": str(args.get("file") or ""),
                                "anchors": _call_anchors(args),
                            }
            elif role == "toolResult" and msg.get("toolName") == "edit":
                tc_id = str(msg.get("toolCallId") or "")
                text = _result_text(msg)
                is_error = bool(msg.get("isError"))
                edit_count += 1
                if not is_error:
                    success_count += 1
                    continue
                code = classify(text)
                if code not in (*KNOWN_CODES, *EXTRA_CODES, "E_NO_CODE", "E_EMPTY_RESULT"):
                    unknown_codes.add(code)
                by_code[code] = by_code.get(code, 0) + 1
                call = calls.get(tc_id)
                if call is None and "|" in tc_id:
                    prefix, suffix = tc_id.split("|", 1)
                    call = calls.get(prefix) or calls.get(suffix)
                file = ""
                if call:
                    file = call.get("file") or ""
                if not file:
                    pm = re.search(r"\(([^)]+)\)", text)
                    if pm:
                        file = pm.group(1)
                if file:
                    by_file[file] = by_file.get(file, 0) + 1
                quoted = QUOTED_RE.findall(text)
                call_anchors = call.get("anchors", []) if call else []
                seen: list[str] = []
                for a in [*quoted, *call_anchors]:
                    if a not in seen:
                        seen.append(a)
                numeric = [a for a in seen if NUMERIC_RE.match(a)]
                if numeric:
                    numeric_anchor_failures += 1
                served_for: str | None = None
                served_matches = SERVED_FOR_RE.findall(text)
                if served_matches:
                    served_for = served_matches[-1].rstrip(";,.")
                is_leak = code == "E_FOREIGN_ANCHOR" or (
                    served_for is not None and file and served_for != file
                )
                if is_leak:
                    foreign_leak_failures += 1
                failures.append(
                    {
                        "jsonl_line": idx,
                        "toolCallId": tc_id,
                        "file": file,
                        "code": code,
                        "category": categorize(code, numeric, bool(is_leak)),
                        "anchors": seen,
                        "numeric_anchors": numeric,
                        "foreign_served_for": served_for if is_leak else None,
                        "message_preview": text[:240].replace("\n", " ⏎ "),
                    }
                )
    if with_context > 0 and failures:
        line_to_preview: dict[int, dict[str, Any]] = {}
        ordered_lines: list[int] = []
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fp2:
                for idx2, raw2 in enumerate(fp2, start=1):
                    raw2 = raw2.strip()
                    if not raw2:
                        continue
                    try:
                        rec2 = json.loads(raw2)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(rec2, dict) or rec2.get("type") != "message":
                        continue
                    msg2 = rec2.get("message")
                    if not isinstance(msg2, dict):
                        continue
                    preview = _preview_for_msg(msg2)
                    role2 = str(msg2.get("role") or rec2.get("type") or "?")
                    t2 = str(msg2.get("toolName") or msg2.get("type") or role2)
                    line_to_preview[idx2] = {
                        "jsonl_line": idx2,
                        "role": role2,
                        "type": t2,
                        "preview": preview,
                        "full": msg2,
                    }
                    ordered_lines.append(idx2)
        except OSError:
            pass
        ordered_lines.sort()
        for f in failures:
            ctx: list[dict[str, Any]] = []
            for ln in ordered_lines:
                if ln <= f["jsonl_line"]:
                    continue
                if len(ctx) >= with_context:
                    break
                info = line_to_preview.get(ln)
                if info:
                    ctx.append(
                        {
                            "jsonl_line": info["jsonl_line"],
                            "role": info["role"],
                            "type": info["type"],
                            "preview": info["preview"],
                        }
                    )
            f["next_turns"] = ctx
            full_by_line[f["jsonl_line"]] = [
                line_to_preview[ln]["full"]
                for ln in [c["jsonl_line"] for c in ctx]
                if ln in line_to_preview
            ]
    typed_failures: list[EditFailure] = []
    for f in failures:
        if "next_turns" not in f:
            f["next_turns"] = []
        try:
            typed_failures.append(EditFailure.model_validate(f))
        except ValidationError as ve:
            eprint(f"validation error at line {f.get('jsonl_line')}: {ve}")
            raise
    failure_count = len(typed_failures)
    for _code in sorted(unknown_codes):
        eprint(
            f"warning: unrecognized edit error code {_code!r} (not in KNOWN_CODES); categorized as '?'"
        )
    audit_raw = {
        "session_path": str(path),
        "session_file": path.name,
        "record_count": record_count,
        "parse_errors": parse_errors,
        "edit_count": edit_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "failure_rate": (failure_count / edit_count) if edit_count else 0.0,
        "by_code": by_code,
        "by_file": by_file,
        "numeric_anchor_failures": numeric_anchor_failures,
        "foreign_leak_failures": foreign_leak_failures,
        "failures": [o.model_dump() for o in typed_failures],
        "full_context_by_line": full_by_line,
    }
    try:
        _ = EditAuditResult.model_validate(audit_raw)
    except ValidationError as ve:
        eprint(f"audit result validation failed: {ve}")
        raise
    return audit_raw


def format_text(audit: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"session: {audit['session_path']}")
    lines.append(
        f"records: {audit['record_count']}  edit calls: {audit['edit_count']}  "
        f"ok: {audit['success_count']}  failed: {audit['failure_count']}  "
        f"rate: {audit['failure_rate'] * 100:.1f}%"
    )
    if audit["parse_errors"]:
        lines.append(f"parse errors (skipped lines): {audit['parse_errors']}")
    lines.append("")
    if audit["edit_count"] == 0:
        lines.append("No edit toolResults found.")
        lines.append("")
    elif not audit["failures"]:
        lines.append(f"All {audit['edit_count']} edits succeeded.")
        lines.append("")
    else:
        lines.append("Failures by code:")
        for code, n in sorted(audit["by_code"].items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  {code}: {n}")
        lines.append("")
        lines.append(
            f"Patterns: numeric-anchor failures: {audit['numeric_anchor_failures']}  "
            f"foreign-leak failures: {audit['foreign_leak_failures']}"
        )
        lines.append("")
        lines.append(f"{'#':>3}  {'jsonl':>5}  {'cat':<3}  {'code':<18}  file / anchors")
        lines.append("─" * 72)
        for i, f in enumerate(audit["failures"], start=1):
            anchors = ",".join(f["anchors"][:4])
            if len(f["anchors"]) > 4:
                anchors += ",…"
            target = f["file"] or "(unknown file)"
            lines.append(
                f"{i:>3}  {f['jsonl_line']:>5}  {f.get('category', '?'):<3}  {f['code']:<18}  {target} [{anchors}]"
            )
            if f.get("numeric_anchors"):
                lines.append(
                    f"       numeric anchors (line numbers?): {','.join(f['numeric_anchors'])}"
                )
            if f.get("foreign_served_for"):
                lines.append(f"       served for: {f['foreign_served_for']}")
        lines.append("")
        if any(f.get("next_turns") for f in audit["failures"]):
            lines.append("Next turns after each failure (with --with-context):")
            for f in audit["failures"]:
                ctx = f.get("next_turns") or []
                if ctx:
                    previews = " | ".join(f"{c['role']}:{c['preview'][:60]}" for c in ctx)
                    lines.append(f"  line {f['jsonl_line']} → {previews}")
            lines.append("")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="audit_edits.py",
        description="Scan pi session JSONL for edit tool failures.",
    )
    _ = ap.add_argument("target", help="session id (uuid) or path to *.jsonl")
    _ = ap.add_argument(
        "--json", action="store_true", dest="as_json", help="emit JSON instead of text"
    )
    _ = ap.add_argument(
        "--with-context",
        type=int,
        default=0,
        help="attach next N turns after each failure for triage (default: 0, recommend 3)",
    )
    _ = ap.add_argument(
        "--dump-context",
        type=str,
        default=None,
        help="write per-failure context JSON to dir (implies --with-context 3 when unset)",
    )
    args = ap.parse_args()
    if args.with_context < 0 and args.dump_context is None:
        eprint("error: --with-context must be >= 0")
        sys.exit(1)
    if args.dump_context is not None and args.with_context <= 0:
        args.with_context = 3
        eprint("note: --dump-context implies --with-context 3")
    resolved = resolve_session(args.target)
    if resolved is None:
        eprint(f"error: no session found for target {args.target!r}")
        eprint(
            "hint: pass an absolute path to a *.jsonl file, or a session id like 01a03e51-b378-786f-819d-f570bc26497c"
        )
        eprint("searched: $PI_SESSIONS_DIR (if set) and ~/.pi/agent/sessions/")
        sys.exit(2)
    if not resolved.is_file():
        eprint(f"error: resolved path is not a file: {resolved}")
        sys.exit(2)
    try:
        audit = scan(resolved, with_context=args.with_context)
    except OSError as exc:
        eprint(f"error: cannot read {resolved}: {exc}")
        sys.exit(2)
    full_by_line = audit.pop("full_context_by_line", {})
    will_dump = args.dump_context is not None
    if will_dump:
        assert args.dump_context is not None
        dump_dir = Path(args.dump_context).expanduser()
        dump_dir.mkdir(parents=True, exist_ok=True)
        for f in audit["failures"]:
            full_ctx = full_by_line.get(f["jsonl_line"], [])
            out = dump_dir / f"edit-failure-{f['jsonl_line']}.json"
            payload = {
                "failure": f,
                "next_turns_full": full_ctx,
            }
            _ = out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        audit["dump_context_dir"] = str(dump_dir.resolve())
    if args.as_json:
        json.dump(dict(audit), sys.stdout, ensure_ascii=False, indent=2)
        _ = sys.stdout.write("\n")
    else:
        _ = sys.stdout.write(format_text(audit))
        if will_dump:
            _ = sys.stdout.write(f"Context dump dir: {audit['dump_context_dir']}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
