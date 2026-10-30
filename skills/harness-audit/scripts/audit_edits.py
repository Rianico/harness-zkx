#!/usr/bin/env python3
# pyright: reportMissingImports=false
# /// script
# requires-python = ">=3.14"
# dependencies = ["pydantic"]
# ///

"""harness-audit edit workload: scan pi session JSONL for edit tool failures.

Parse JSONL line-by-line, pair ``edit`` toolCall -> toolResult, compute
success/failure stats, classify rejections by domain error code against the full
registry in pi-better-edit ``src/domain-errors.ts`` (19 ``E_*`` codes), track the
applied-tier ``W_*`` warnings separately, and flag diagnostic patterns (numeric
line-number anchors, cross-file leaked anchors). Read-only.

Accepts both record shapes: native ``type == "message"`` and the pi event-stream
``message_end``. pi-subagents transcripts (``recordType`` in ``message`` /
``tool_start`` / ``tool_end``, no ``type`` key) are scanned too, either directly or
auto-discovered under ``<session_dir>/subagent-artifacts/*_transcript.jsonl``.
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
WARNING_RE = re.compile(r"\b(W_[A-Z_]+)\b")
QUOTED_RE = re.compile(r'"([^"]+)"')
SERVED_FOR_RE = re.compile(r"served for ([^;\s]+)")
NUMERIC_RE = re.compile(r"^\d+$")

# Mirrors audit.py: scanned records whose schema is unrecognized are not a clean result.
EXIT_SCHEMA = 3

# Source of truth: pi-better-edit src/domain-errors.ts:32-51 (``DomainErrorCode``, 19 codes).
# A ``[E_*]`` line reports a rejection.
ERROR_CODES = (
    "E_BAD_PAYLOAD",
    "E_EMPTY_RANGE",
    "E_STALE_ANCHOR",
    "E_UNKNOWN_ANCHOR",
    "E_FOREIGN_ANCHOR",
    "E_STALE_RANGE",
    "E_TARGET_LOST",
    "E_UNVERIFIED_RANGE",
    "E_MALFORMED_ANCHOR",
    "E_SUSPICIOUS_TEXT",
    "E_BATCH_ABORT",
    "E_NOOP_LOOP",
    "E_UNSUPPORTED_FILE",
    "E_ACCESS",
    "E_NOT_FOUND",
    "E_UNDO_STALE",
    "E_UNDO_UNAVAILABLE",
    "E_UNKNOWN",
    "E_LARGE_FILE",
)
# src/domain-errors.ts:61-67 (``DomainWarningCode``, 6 codes). Applied tier: the mutation was
# written, so a ``W_*`` row is a warning, never a failure.
WARNING_CODES = (
    "W_NEVER_SERVED_SHAPE",
    "W_SERVED_PREFIX_MISMATCH",
    "W_REVERSED_ANCHORS",
    "W_UNICODE_LITERAL",
    "W_LITERAL_BYPASS",
    "W_NOOP",
)
# Seen in older sessions, absent from the current registry — kept recognized so historical
# corpora still classify instead of falling through to '?'.
LEGACY_CODES = ("E_UNSERVED_RANGE",)
KNOWN_CODES = (*ERROR_CODES, *LEGACY_CODES)


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
    source_file: str = ""
    context_key: str = ""
    next_turns: list[NextTurn] = Field(default_factory=list)

    model_config: ClassVar[ConfigDict] = {"strict": True}


class EditWarning(BaseModel):
    """An applied-tier ``W_*`` note: the mutation was applied, so it is not a failure."""

    jsonl_line: int = Field(ge=1)
    toolCallId: str
    file: str
    code: str
    is_error: bool
    message_preview: str = ""
    source_file: str = ""
    context_key: str = ""

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
    warnings: list[EditWarning] = Field(default_factory=list)
    warning_count: int = Field(default=0, ge=0)
    by_warning_code: dict[str, int] = Field(default_factory=dict)
    transcripts: list[str] = Field(default_factory=list)
    transcript_count: int = Field(default=0, ge=0)
    schema_recognized: bool = True
    skipped_files: list[str] = Field(default_factory=list)

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


def message_of(rec: dict[str, Any]) -> dict[str, Any] | None:
    """The canonical ``message`` payload, or ``None``.

    Native pi sessions log ``type == "message"``; pi event-stream logs log
    ``message_end`` with an identical ``message`` payload. Both are accepted.
    """
    if rec.get("type") not in ("message", "message_end"):
        return None
    msg = rec.get("message")
    return msg if isinstance(msg, dict) else None


def _warning_codes(text: str) -> list[str]:
    """Distinct ``W_*`` codes in ``text``, in first-seen order."""
    seen: list[str] = []
    for m in WARNING_RE.finditer(text):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def classify(text: str) -> str:
    m = CODE_RE.search(text)
    if m:
        return m.group(1)
    return "E_NO_CODE" if text else "E_EMPTY_RESULT"


def categorize(code: str, numeric_anchors: list[str], is_leak: bool) -> str:
    """Deterministic triage bucket: N/F/B/T/M/P/R/G/U, '?' when unrecognized."""
    if numeric_anchors:
        return "N"
    if is_leak or code == "E_FOREIGN_ANCHOR":
        return "F"
    direct = {
        "E_BATCH_ABORT": "B",
        "E_TARGET_LOST": "T",
        "E_MALFORMED_ANCHOR": "M",
        "E_BAD_PAYLOAD": "P",  # payload / contract shape
        "E_NOT_FOUND": "R",  # path / limits
        "E_ACCESS": "R",
        "E_UNSUPPORTED_FILE": "R",
        "E_LARGE_FILE": "R",
        "E_SUSPICIOUS_TEXT": "G",  # guard / policy, not a hash problem
        "E_EMPTY_RANGE": "G",
        "E_NOOP_LOOP": "G",
        "E_UNDO_STALE": "U",  # undo lifecycle
        "E_UNDO_UNAVAILABLE": "U",
    }
    if code in direct:
        return direct[code]
    if code in (
        "E_UNKNOWN_ANCHOR",
        "E_STALE_ANCHOR",
        "E_UNSERVED_RANGE",
        "E_STALE_RANGE",
        "E_UNVERIFIED_RANGE",
    ):
        return "H"
    return "?"


def _parse_args_payload(raw: Any) -> dict[str, Any]:
    """Decode a pi-subagents ``tool_start.argsPayload`` (a JSON string) to a dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _ingest_transcript(
    rec: dict[str, Any],
    record_type: str,
    idx: int,
    calls: dict[tuple[str, str], dict[str, Any]],
    results: dict[tuple[str, str], dict[str, Any]],
) -> None:
    """Collect one pi-subagents transcript record into ``calls`` / ``results``.

    Canonical counting rule for transcripts:
    * call args (file, anchors) come from ``tool_start.argsPayload``; the
      assistant ``toolCall`` is a fallback when a transcript omits ``tool_start``;
    * the result body and error flag come from the ``message`` / ``toolResult``
      record; ``tool_end.isError`` is the fallback when no message record exists;
    * results are keyed by ``(runId, toolCallId)`` so the ``tool_end`` +
      ``message`` pair for a single call is counted exactly once.
    """
    run_id = str(rec.get("runId") or "")
    if record_type == "tool_start" and rec.get("toolName") == "edit":
        tc_id = str(rec.get("toolCallId") or "")
        if not tc_id:
            return
        args = _parse_args_payload(rec.get("argsPayload"))
        calls[(run_id, tc_id)] = {
            "jsonl_line": idx,
            "file": str(args.get("file") or ""),
            "anchors": _call_anchors(args),
        }
        return
    if record_type == "tool_end" and rec.get("toolName") == "edit":
        tc_id = str(rec.get("toolCallId") or "")
        if not tc_id:
            return
        key = (run_id, tc_id)
        if key in results:
            return  # the message/toolResult record is canonical
        results[key] = {
            "jsonl_line": idx,
            "toolCallId": tc_id,
            "run_id": run_id,
            "text": "",
            "is_error": bool(rec.get("isError")),
            "source": "tool_end",
        }
        return
    if record_type != "message":
        return
    nested = rec.get("message")
    msg = nested if isinstance(nested, dict) else rec
    role = msg.get("role") or rec.get("role")
    tool_name = msg.get("toolName") or rec.get("toolName")
    if role == "assistant":
        content = msg.get("content")
        if not isinstance(content, list):
            return
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "toolCall" or item.get("name") != "edit":
                continue
            tc_id = str(item.get("id") or "")
            args = item.get("arguments")
            if tc_id and isinstance(args, dict):
                _ = calls.setdefault(
                    (run_id, tc_id),
                    {
                        "jsonl_line": idx,
                        "file": str(args.get("file") or ""),
                        "anchors": _call_anchors(args),
                    },
                )
        return
    if role != "toolResult" or tool_name != "edit":
        return
    tc_id = str(msg.get("toolCallId") or rec.get("toolCallId") or "")
    if not tc_id:
        return
    text = _result_text(msg)
    if not text:
        text = str(rec.get("text") or "")
    is_error = bool(msg.get("isError") if "isError" in msg else rec.get("isError"))
    results[(run_id, tc_id)] = {
        "jsonl_line": idx,
        "toolCallId": tc_id,
        "run_id": run_id,
        "text": text,
        "is_error": is_error,
        "source": "message",
    }


def _context_message(rec: dict[str, Any]) -> dict[str, Any] | None:
    """The body-bearing message for context previews, native or transcript."""
    msg = message_of(rec)
    if msg is not None:
        return msg
    if rec.get("recordType") == "message":
        nested = rec.get("message")
        return nested if isinstance(nested, dict) else rec
    return None


def _process_edit_result(
    idx: int,
    tc_id: str,
    text: str,
    is_error: bool,
    call: dict[str, Any] | None,
    source_file: str,
    context_key: str,
    failures: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    by_code: dict[str, int],
    by_file: dict[str, int],
    by_warning_code: dict[str, int],
    unknown_codes: set[str],
) -> tuple[int, int, int, int]:
    """Tally one edit result; returns (edit, success, numeric, leak) deltas."""
    file = str(call.get("file") or "") if call else ""
    if not file:
        pm = re.search(r"\(([^)]+)\)", text)
        if pm:
            file = pm.group(1)
    for wcode in _warning_codes(text):
        by_warning_code[wcode] = by_warning_code.get(wcode, 0) + 1
        warnings.append(
            {
                "jsonl_line": idx,
                "toolCallId": tc_id,
                "file": file,
                "code": wcode,
                "is_error": is_error,
                "message_preview": text[:240].replace("\n", " ⏎ "),
                "source_file": source_file,
                "context_key": context_key,
            }
        )
    if not is_error:
        return 1, 1, 0, 0
    code = classify(text)
    if code not in (*KNOWN_CODES, "E_NO_CODE", "E_EMPTY_RESULT"):
        unknown_codes.add(code)
    by_code[code] = by_code.get(code, 0) + 1
    if file:
        by_file[file] = by_file.get(file, 0) + 1
    quoted = QUOTED_RE.findall(text)
    call_anchors = call.get("anchors", []) if call else []
    seen: list[str] = []
    for a in [*quoted, *call_anchors]:
        if a not in seen:
            seen.append(a)
    numeric = [a for a in seen if NUMERIC_RE.match(a)]
    numeric_failures = 1 if numeric else 0
    served_for: str | None = None
    served_matches = SERVED_FOR_RE.findall(text)
    if served_matches:
        served_for = served_matches[-1].rstrip(";,.")
    is_leak = code == "E_FOREIGN_ANCHOR" or (served_for is not None and file and served_for != file)
    leaks = 1 if is_leak else 0
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
            "source_file": source_file,
            "context_key": context_key,
        }
    )
    return 1, 0, numeric_failures, leaks


def discover_transcripts(session_path: Path) -> list[Path]:
    """Transcripts pi-subagents writes beside a session file.

    Returns ``<session_dir>/subagent-artifacts/*_transcript.jsonl`` when that
    directory exists. A path already inside ``subagent-artifacts`` is treated as
    a transcript and discovers nothing, so pointing at one file stays scoped.
    """
    parent = session_path.parent
    if parent.name == "subagent-artifacts":
        return []
    artifacts = parent / "subagent-artifacts"
    if not artifacts.is_dir():
        return []
    return sorted(artifacts.glob("*_transcript.jsonl"))


def _lookup_call(
    calls: dict[tuple[str, str], dict[str, Any]], run_id: str, tc_id: str
) -> dict[str, Any] | None:
    """Resolve a call by ``(runId, toolCallId)``.

    Falls back to the run-less key (``run_id == ""``) for main-session records that
    carry no ``runId``, then to the ``|``-split id variants Pi provider bridges emit.
    """
    candidates = [(run_id, tc_id)]
    if run_id:
        candidates.append(("", tc_id))
    for rid, cid in candidates:
        call = calls.get((rid, cid))
        if call is not None:
            return call
        if "|" in cid:
            prefix, suffix = cid.split("|", 1)
            call = calls.get((rid, prefix)) or calls.get((rid, suffix))
            if call is not None:
                return call
    return None


def _scan_one(path: Path, with_context: int = 0) -> dict[str, Any]:
    calls: dict[tuple[str, str], dict[str, Any]] = {}
    results: dict[tuple[str, str], dict[str, Any]] = {}
    parse_errors = 0
    record_count = 0
    schema_recognized = False
    edit_count = 0
    success_count = 0
    by_code: dict[str, int] = {}
    by_file: dict[str, int] = {}
    numeric_anchor_failures = 0
    foreign_leak_failures = 0
    unknown_codes: set[str] = set()
    warnings: list[dict[str, Any]] = []
    by_warning_code: dict[str, int] = {}
    failures: list[dict[str, Any]] = []
    full_by_line: dict[str | int, list[dict[str, Any]]] = {}
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
            if not isinstance(rec, dict):
                continue
            record_type = rec.get("recordType")
            if isinstance(record_type, str):
                if record_type in ("message", "tool_start", "tool_end"):
                    schema_recognized = True
                _ingest_transcript(rec, record_type, idx, calls, results)
                continue
            if rec.get("type") in ("session", "message", "message_end"):
                schema_recognized = True
            msg = message_of(rec)
            if msg is None:
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
                            calls[("", tc_id)] = {
                                "jsonl_line": idx,
                                "file": str(args.get("file") or ""),
                                "anchors": _call_anchors(args),
                            }
            elif role == "toolResult" and msg.get("toolName") == "edit":
                tc_id = str(msg.get("toolCallId") or "")
                results[("", tc_id)] = {
                    "jsonl_line": idx,
                    "toolCallId": tc_id,
                    "run_id": "",
                    "text": _result_text(msg),
                    "is_error": bool(msg.get("isError")),
                    "source": "message",
                }
    for res in sorted(results.values(), key=lambda r: int(r["jsonl_line"])):
        tc_id = str(res["toolCallId"])
        run_id = str(res.get("run_id") or "")
        call = _lookup_call(calls, run_id, tc_id)
        line = int(res["jsonl_line"])
        context_key = f"{path.name}:{line}"
        edit_delta, success_delta, numeric_delta, leak_delta = _process_edit_result(
            int(res["jsonl_line"]),
            tc_id,
            str(res["text"]),
            bool(res["is_error"]),
            call,
            path.name,
            context_key,
            failures,
            warnings,
            by_code,
            by_file,
            by_warning_code,
            unknown_codes,
        )
        edit_count += edit_delta
        success_count += success_delta
        numeric_anchor_failures += numeric_delta
        foreign_leak_failures += leak_delta
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
                    if not isinstance(rec2, dict):
                        continue
                    msg2 = _context_message(rec2)
                    if msg2 is None:
                        continue
                    preview = _preview_for_msg(msg2)
                    role2 = str(
                        msg2.get("role") or rec2.get("recordType") or rec2.get("type") or "?"
                    )
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
            ctx_full = [
                line_to_preview[ln]["full"]
                for ln in [c["jsonl_line"] for c in ctx]
                if ln in line_to_preview
            ]
            # Canonical key is the ``file:line`` context_key; the int jsonl_line alias
            # keeps int-keyed consumers working and makes single/merged shapes uniform.
            full_by_line[f["context_key"]] = ctx_full
            full_by_line[f["jsonl_line"]] = ctx_full
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
    typed_warnings: list[EditWarning] = []
    for w in warnings:
        try:
            typed_warnings.append(EditWarning.model_validate(w))
        except ValidationError as ve:
            eprint(f"validation error at line {w.get('jsonl_line')}: {ve}")
            raise
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
        "warnings": [w.model_dump() for w in typed_warnings],
        "warning_count": len(typed_warnings),
        "by_warning_code": by_warning_code,
        "full_context_by_line": full_by_line,
        "transcripts": [],
        "transcript_count": 0,
        "schema_recognized": schema_recognized,
        "skipped_files": [],
    }
    try:
        _ = EditAuditResult.model_validate(audit_raw)
    except ValidationError as ve:
        eprint(f"audit result validation failed: {ve}")
        raise
    return audit_raw


def _merge_audits(
    main_path: Path, transcript_paths: list[Path], audits: list[dict[str, Any]]
) -> dict[str, Any]:
    """Merge the main-session audit with one audit per discovered transcript."""
    merged: dict[str, Any] = {
        "session_path": str(main_path),
        "session_file": main_path.name,
        "record_count": 0,
        "parse_errors": 0,
        "edit_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "failure_rate": 0.0,
        "by_code": {},
        "by_file": {},
        "numeric_anchor_failures": 0,
        "foreign_leak_failures": 0,
        "failures": [],
        "warnings": [],
        "warning_count": 0,
        "by_warning_code": {},
        "full_context_by_line": {},
        "transcripts": [str(p) for p in transcript_paths],
        "transcript_count": len(transcript_paths),
        "schema_recognized": True,
        "skipped_files": [],
    }
    skipped: list[str] = []
    recognized_nonempty = False
    for audit in audits:
        source_file = str(audit["session_file"])
        if audit["record_count"] > 0 and not audit["schema_recognized"]:
            skipped.append(source_file)
            eprint(
                f"warning: skipping {source_file}: unrecognized schema "
                "(expected pi session 'type'/'message' records or pi-subagents "
                "'recordType'/'tool_start'/'tool_end' transcripts)"
            )
            continue
        if audit["record_count"] > 0:
            recognized_nonempty = True
        merged["record_count"] += audit["record_count"]
        merged["parse_errors"] += audit["parse_errors"]
        merged["edit_count"] += audit["edit_count"]
        merged["success_count"] += audit["success_count"]
        merged["failure_count"] += audit["failure_count"]
        merged["numeric_anchor_failures"] += audit["numeric_anchor_failures"]
        merged["foreign_leak_failures"] += audit["foreign_leak_failures"]
        for key in ("by_code", "by_file", "by_warning_code"):
            for code, n in audit[key].items():
                merged[key][code] = merged[key].get(code, 0) + n
        for f in audit["failures"]:
            merged["failures"].append(dict(f))
        for w in audit["warnings"]:
            merged["warnings"].append(dict(w))
        for ctx_key, ctx in audit["full_context_by_line"].items():
            merged["full_context_by_line"][ctx_key] = ctx
    merged["failure_rate"] = (
        merged["failure_count"] / merged["edit_count"] if merged["edit_count"] else 0.0
    )
    merged["warning_count"] = len(merged["warnings"])
    # Exit non-zero iff NO scanned file yielded recognized records; a single bad file
    # among good ones is skipped (named on stderr) and does not poison valid signal.
    merged["schema_recognized"] = recognized_nonempty
    merged["skipped_files"] = skipped
    try:
        _ = EditAuditResult.model_validate(merged)
    except ValidationError as ve:
        eprint(f"audit result validation failed: {ve}")
        raise
    return merged


def scan(path: Path, with_context: int = 0, transcripts: bool = True) -> dict[str, Any]:
    """Audit one session file, auto-including pi-subagents transcripts beside it.

    When ``transcripts`` is set (default) and ``<session_dir>/subagent-artifacts/``
    holds ``*_transcript.jsonl`` files, their edit traffic is merged into the
    result. Additive ``--json`` keys: ``transcripts`` / ``transcript_count`` (the
    discovered paths) and ``skipped_files`` (unrecognized files, excluded from
    counts and named on stderr); each failure/warning carries ``source_file`` and a
    ``<source_file>:<line>`` ``context_key``. Pass ``transcripts=False`` to audit only
    the given file.
    """
    extra = discover_transcripts(path) if transcripts else []
    if not extra:
        return _scan_one(path, with_context=with_context)
    audits = [_scan_one(path, with_context=with_context)]
    audits.extend(_scan_one(t, with_context=with_context) for t in extra)
    return _merge_audits(path, extra, audits)


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
    if audit.get("transcripts"):
        lines.append(f"transcripts scanned: {audit['transcript_count']}")
        for t in audit["transcripts"]:
            lines.append(f"  {t}")
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
    if audit.get("warnings"):
        lines.append("Applied-tier warnings ([W_*] — the mutation was applied; not a failure):")
        for code, n in sorted(audit["by_warning_code"].items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  {code}: {n}")
        for w in audit["warnings"]:
            target = w["file"] or "(unknown file)"
            state = "after failure" if w["is_error"] else "applied"
            lines.append(f"  line {w['jsonl_line']}  {w['code']}  {target}  ({state})")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="audit_edits.py",
        description=(
            "Scan pi session JSONL for edit tool failures, including pi-subagents "
            "transcripts found in subagent-artifacts/ beside the session."
        ),
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
    _ = ap.add_argument(
        "--no-transcripts",
        action="store_true",
        dest="no_transcripts",
        help=(
            "do not auto-scan <session_dir>/subagent-artifacts/*_transcript.jsonl; "
            "audit only the resolved session file"
        ),
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
        audit = scan(resolved, with_context=args.with_context, transcripts=not args.no_transcripts)
    except OSError as exc:
        eprint(f"error: cannot read {resolved}: {exc}")
        sys.exit(2)
    schema_recognized = bool(audit.pop("schema_recognized", True))
    skipped_files = list(audit.get("skipped_files") or [])
    if (audit["record_count"] > 0 or skipped_files) and not schema_recognized:
        detail = f" Skipped: {', '.join(skipped_files)}." if skipped_files else ""
        eprint(
            "WARNING: scanned input but the schema was not recognized (expected pi session "
            "'type'/'message' records or pi-subagents 'recordType'/'tool_start'/'tool_end' "
            "transcripts). Exit 3 means 'scanned, nothing recognized'; it is NOT a clean "
            f"result.{detail}"
        )
        sys.exit(EXIT_SCHEMA)
    full_by_line = audit.pop("full_context_by_line", {})
    will_dump = args.dump_context is not None
    if will_dump:
        assert args.dump_context is not None
        dump_dir = Path(args.dump_context).expanduser()
        dump_dir.mkdir(parents=True, exist_ok=True)
        for f in audit["failures"]:
            key = f.get("context_key") or f["jsonl_line"]
            full_ctx = full_by_line.get(key, [])
            stem = str(f.get("context_key") or f["jsonl_line"])
            safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)
            out = dump_dir / f"edit-failure-{safe_stem}.json"
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
