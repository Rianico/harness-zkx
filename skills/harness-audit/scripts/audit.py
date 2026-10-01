#!/usr/bin/env python3
# pyright: reportMissingImports=false
# /// script
# requires-python = ">=3.14"
# dependencies = ["pydantic"]
# ///

"""harness-audit: scan pi session JSONL for oversized bash outputs.

Resolve target (path or session id), scan JSONL line-by-line, pair
bash toolCall -> toolResult for command preview, classify by line
count, and report trimtable savings. Read-only; --emit-filtered
writes a sibling copy. --with-context attaches following turns for triage.

Accepts both record shapes: native ``type == "message"`` and the pi event-stream
``message_end`` (benchmark harness ``stdout.jsonl``), which carries the identical
``message`` payload. A scan that reads records but pairs no bash results exits ``3``
(schema warning) instead of reporting a false all-clear. ``--census`` adds
per-tool delivered-line counts; delivery-cap footers surface ``produced_lines`` /
``omitted_lines`` next to ``lines``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, ClassVar, Protocol, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_THRESHOLD = 20
DEFAULT_KEEP = 10
# Exit 3 = "scanned records, found nothing to scan" — deliberately distinct from 0 (clean).
EXIT_SCHEMA = 3
# Pi logs one turn in two shapes: native sessions use {"type": "message", "message": {...}};
# pi event-stream logs (benchmark harness stdout.jsonl) use "message_end" with the identical
# "message" payload. Accepting both stops a stream log from being read as empty (and "clean").
MESSAGE_RECORD_TYPES = frozenset({"message", "message_end"})
# Delivery-cap footer: "[Showing lines A-B of Z (50.0KB limit). Use offset=… to continue]".
# The trailing "(N.NKB limit)" is load-bearing — a stricter "of Z]" pattern never matches.
TRUNCATION_FOOTER_RE = re.compile(r"\[Showing lines (\d+)-(\d+) of (\d+) \(([\d.]+)KB limit\)")
# Census rows are always emitted for these five, zero-filled when unused, so "all five tools"
# is a stable shape rather than a set that silently drops tools with no calls.
CENSUS_TOOLS = ("bash", "read", "edit", "write", "undo_last_edit")


class ToolCensus(BaseModel):
    """Delivered-vs-produced line accounting for one tool across the session."""

    calls: int = Field(ge=0)
    lines: int = Field(ge=0)
    chars: int = Field(ge=0)
    truncated_calls: int = Field(ge=0)
    omitted_lines: int = Field(ge=0)

    model_config: ClassVar[ConfigDict] = {"strict": True}


# ── Pydantic domain models (A: type-safe owned script + B: replaceable-handle catalog) ──
class NextTurn(BaseModel):
    jsonl_line: int = Field(ge=1)
    role: str
    type: str
    preview: str = Field(max_length=240)

    model_config: ClassVar[ConfigDict] = {"strict": True}


class OversizedEntry(BaseModel):
    jsonl_line: int = Field(ge=1)
    toolCallId: str
    command: str
    command_preview: str
    lines: int = Field(ge=0)
    chars: int = Field(ge=0)
    produced_lines: int = Field(default=0, ge=0)
    omitted_lines: int = Field(default=0, ge=0)
    oversized: bool
    isError: bool
    next_turns: list[NextTurn] = Field(default_factory=list)

    model_config: ClassVar[ConfigDict] = {"strict": True}


# Two loss models coexist and both are correct. ``lines`` is the trim-table estimate: it keeps
# a ``2*keep_head_tail + 1``-line window and sums Σ(n − (2k+1)) over entries above the
# threshold. The stricter headline Σ(n − threshold) differs by exactly one line per entry —
# a definition difference, not an off-by-one bug.
class EstimatedSavings(BaseModel):
    lines: int = Field(ge=0)
    chars: int = Field(ge=0)
    keep_head_tail: int = Field(ge=0)

    model_config: ClassVar[ConfigDict] = {"strict": True}


class AuditResult(BaseModel):
    session_path: str
    session_file: str
    threshold: int = Field(ge=0)
    record_count: int = Field(ge=0)
    parse_errors: int = Field(ge=0)
    bash_count: int = Field(ge=0)
    oversized_count: int = Field(ge=0)
    total_lines: int = Field(ge=0)
    total_chars: int = Field(ge=0)
    total_produced_lines: int = Field(default=0, ge=0)
    total_omitted_lines: int = Field(default=0, ge=0)
    truncated_count: int = Field(default=0, ge=0)
    tool_census: dict[str, ToolCensus] = Field(default_factory=dict)
    oversized: list[OversizedEntry] = Field(default_factory=list)
    all: list[OversizedEntry] = Field(
        default_factory=list
    )  # all bash entries, alias to avoid shadowing
    estimated_savings: EstimatedSavings

    model_config: ClassVar[ConfigDict] = {"strict": True, "populate_by_name": True}


# Bucket triage — makes A/B/C/D explicit at type level (A=refine owned, B=replace one-off)
class TriagedEntry(BaseModel):
    entry: OversizedEntry
    bucket: str = Field(pattern="^[ABCD]$")  # A refine script, B replace bash, C filter, D keep
    manageable: bool
    replaceable_with: str | None = None
    reason: str

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


def count_lines(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def message_of(rec: dict[str, Any]) -> dict[str, Any] | None:
    """The canonical ``message`` payload of a record, or ``None`` for anything else.

    Native pi sessions log ``type == "message"``; pi event-stream logs (the benchmark
    harness ``stdout.jsonl``) log ``message_end`` with an identical ``message`` payload.
    Both are accepted so an event stream is never read as an empty — and falsely
    "clean" — session.
    """
    if rec.get("type") not in MESSAGE_RECORD_TYPES:
        return None
    msg = rec.get("message")
    return msg if isinstance(msg, dict) else None


def result_text(msg: dict[str, Any]) -> str:
    """Join every ``text`` block of a ``toolResult`` message."""
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


def truncation_of(text: str) -> tuple[int, int] | None:
    """``(produced_lines, omitted_lines)`` from a delivery-cap footer, else ``None``.

    The footer is ``[Showing lines A-B of Z (50.0KB limit). Use offset=… to continue]``.
    """
    m = TRUNCATION_FOOTER_RE.search(text)
    if m is None:
        return None
    produced = int(m.group(3))
    return produced, max(0, produced - count_lines(text))


def truncate_body(text: str, keep: int) -> tuple[str, int]:
    lines = text.splitlines()
    n = len(lines)
    if n <= keep * 2:
        return text, 0
    head = lines[:keep]
    tail = lines[-keep:] if keep > 0 else []
    omitted = n - len(head) - len(tail)
    marker = f" … [{omitted} lines omitted] …"
    if keep == 0:
        truncated = marker + "\n"
    else:
        truncated = "\n".join(head) + "\n" + marker + "\n" + "\n".join(tail)
        if text.endswith("\n"):
            truncated += "\n"
    return truncated, omitted


class _Args(Protocol):
    """The CLI surface, declared so `argparse`'s `Namespace` stops leaking `Any`."""

    target: str
    threshold: int
    as_json: bool
    emit_filtered: bool
    keep_head_tail: int
    with_context: int
    dump_context: str | None
    census: bool


class _TurnRow(TypedDict):
    """One JSONL turn, as serialized into `next_turns` and `--dump-context` payloads."""

    jsonl_line: int
    role: str
    type: str
    preview: str


class _PreviewRow(_TurnRow):
    """A `_TurnRow` plus the full message body, kept only for `--dump-context`."""

    full: dict[str, object]


def _preview_for_msg(msg: dict[str, Any]) -> str:
    try:
        role = msg.get("role", "")
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
                        cmd = str(args.get("command") or args.get("cmd") or "")[:80]
                    return f"toolCall:{it.get('name')}:{cmd}".replace("\n", " ⏎ ")
        return str(role)[:120]
    except Exception:
        return ""


def scan(path: Path, threshold: int, with_context: int = 0) -> dict[str, Any]:
    call_commands: dict[str, str] = {}
    entries: list[dict[str, Any]] = []
    total_lines = 0
    total_chars = 0
    parse_errors = 0
    record_count = 0
    census: dict[str, dict[str, int]] = {
        t: {"calls": 0, "lines": 0, "chars": 0, "truncated_calls": 0, "omitted_lines": 0}
        for t in CENSUS_TOOLS
    }
    try:
        fp = path.open("r", encoding="utf-8", errors="replace")
    except OSError as exc:
        eprint(f"cannot open {path}: {exc}")
        sys.exit(2)
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
                    if item.get("type") == "toolCall" and item.get("name") == "bash":
                        tc_id = item.get("id") or ""
                        args = item.get("arguments") or {}
                        cmd = ""
                        if isinstance(args, dict):
                            cmd = args.get("command") or args.get("cmd") or ""
                        if tc_id and isinstance(cmd, str):
                            call_commands[tc_id] = cmd
            elif role == "toolResult":
                tool_name = msg.get("toolName")
                tool_key = tool_name if isinstance(tool_name, str) and tool_name else "unknown"
                text = result_text(msg)
                nlines = count_lines(text)
                nchars = len(text)
                trunc = truncation_of(text)
                produced = nlines if trunc is None else trunc[0]
                omitted = 0 if trunc is None else trunc[1]
                row = census.setdefault(
                    tool_key,
                    {
                        "calls": 0,
                        "lines": 0,
                        "chars": 0,
                        "truncated_calls": 0,
                        "omitted_lines": 0,
                    },
                )
                row["calls"] += 1
                row["lines"] += nlines
                row["chars"] += nchars
                if trunc is not None:
                    row["truncated_calls"] += 1
                    row["omitted_lines"] += omitted
                if tool_name != "bash":
                    continue
                total_lines += nlines
                total_chars += nchars
                oversized = nlines > threshold
                tc_id = msg.get("toolCallId") or ""
                cmd_preview = ""
                if tc_id in call_commands:
                    cmd_preview = call_commands[tc_id]
                elif "|" in tc_id:
                    prefix = tc_id.split("|", 1)[0]
                    cmd_preview = call_commands.get(prefix, "")
                    if not cmd_preview:
                        suffix = tc_id.split("|", 1)[1]
                        cmd_preview = call_commands.get(suffix, "")
                is_error = bool(msg.get("isError"))
                entries.append(
                    {
                        "jsonl_line": idx,
                        "toolCallId": tc_id,
                        "command": cmd_preview,
                        "command_preview": (cmd_preview[:120] + "…")
                        if len(cmd_preview) > 120
                        else cmd_preview,
                        "lines": nlines,
                        "chars": nchars,
                        "produced_lines": produced,
                        "omitted_lines": omitted,
                        "oversized": oversized,
                        "isError": is_error,
                    }
                )
    oversized_entries = [e for e in entries if e["oversized"]]
    # attach following context if requested
    if with_context > 0 and oversized_entries:
        # second pass: collect previews for all message lines
        line_to_preview: dict[int, _PreviewRow] = {}
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
                    msg2 = message_of(rec2)
                    if msg2 is None:
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
        for e in oversized_entries:
            ctx: list[_TurnRow] = []
            # find next N lines after e's line
            for ln in ordered_lines:
                if ln <= e["jsonl_line"]:
                    continue
                if len(ctx) >= with_context:
                    break
                info = line_to_preview.get(ln)
                if info:
                    # store bounded preview, not full unbounded body (full kept for --dump-context)
                    ctx.append(
                        {
                            "jsonl_line": info["jsonl_line"],
                            "role": info["role"],
                            "type": info["type"],
                            "preview": info["preview"],
                        }
                    )
            e["next_turns"] = ctx
            # also store full bodies separately for dump (lazy, only if needed later)
            e["_next_full"] = [
                line_to_preview[ln]["full"]
                for ln in [c["jsonl_line"] for c in ctx]
                if ln in line_to_preview
            ]

    est_keep = DEFAULT_KEEP
    savings_lines = 0
    savings_chars = 0
    for e in oversized_entries:
        n = e["lines"]
        if n > est_keep * 2:
            removed = n - (est_keep * 2 + 1)
            savings_lines += removed
            avg = e["chars"] / n if n else 0
            try:
                savings_chars += int(removed * avg)
            except ValueError, OverflowError, TypeError:
                savings_chars += removed * 40
    # ── Validate via Pydantic (A: owned script type-safe, B: replaceable-handle ready) ──
    # Build typed entries; ValidationError surfaces bad shapes immediately (fail-loud)
    typed_oversized: list[OversizedEntry] = []
    typed_all: list[OversizedEntry] = []
    for e in entries:
        # ensure next_turns exists for model (default [])
        if "next_turns" not in e:
            e["next_turns"] = []
        # coerce next_turns list elements to NextTurn dicts already shaped
        try:
            typed = OversizedEntry.model_validate(e)
        except ValidationError as ve:
            eprint(f"validation error at line {e.get('jsonl_line')}: {ve}")
            raise
        typed_all.append(typed)
        if typed.oversized:
            typed_oversized.append(typed)
    # also validate savings/overall via AuditResult (strict)
    total_omitted_lines = sum(r["omitted_lines"] for r in census.values())
    total_produced_lines = sum(r["lines"] + r["omitted_lines"] for r in census.values())
    truncated_count = sum(r["truncated_calls"] for r in census.values())
    audit_raw = {
        "session_path": str(path),
        "session_file": path.name,
        "threshold": threshold,
        "record_count": record_count,
        "parse_errors": parse_errors,
        "bash_count": len(typed_all),
        "oversized_count": len(typed_oversized),
        "total_lines": total_lines,
        "total_chars": total_chars,
        "total_produced_lines": total_produced_lines,
        "total_omitted_lines": total_omitted_lines,
        "truncated_count": truncated_count,
        "oversized": [o.model_dump() for o in typed_oversized],
        "all": [a.model_dump() for a in typed_all],
        "tool_census": {k: dict(v) for k, v in sorted(census.items())},
        "estimated_savings": {
            "lines": savings_lines,
            "chars": savings_chars,
            "keep_head_tail": est_keep,
        },
    }
    # final top-level validation (ensures AuditResult contract holds; cheap, fail-loud)
    try:
        _ = AuditResult.model_validate(audit_raw)
    except ValidationError as ve:
        eprint(f"audit result validation failed: {ve}")
        raise
    return audit_raw


def emit_filtered(path: Path, threshold: int, keep: int) -> Path:
    out_path = path.with_suffix("").with_suffix("")
    if path.suffix == ".jsonl":
        out_path = path.with_name(path.stem + ".filtered.jsonl")
    else:
        out_path = Path(str(path) + ".filtered.jsonl")
    with (
        path.open("r", encoding="utf-8", errors="replace") as fin,
        out_path.open("w", encoding="utf-8") as fout,
    ):
        for raw in fin:
            stripped = raw.strip()
            if not stripped:
                _ = fout.write(raw)
                continue
            try:
                rec = json.loads(stripped)
            except json.JSONDecodeError:
                _ = fout.write(raw)
                continue
            msg = message_of(rec) if isinstance(rec, dict) else None
            if (
                msg is not None
                and msg.get("role") == "toolResult"
                and msg.get("toolName") == "bash"
            ):
                content_list = msg.get("content")
                if isinstance(content_list, list) and content_list:
                    text_parts: list[str] = []
                    for c in content_list:
                        if (
                            isinstance(c, dict)
                            and c.get("type") == "text"
                            and isinstance(c.get("text"), str)
                        ):
                            text_parts.append(c["text"])
                    combined = "".join(text_parts)
                    if count_lines(combined) > threshold:
                        truncated, _ = truncate_body(combined, keep)
                        new_content = [{"type": "text", "text": truncated}]
                        msg["content"] = new_content
                        rec["message"] = msg
                        _ = fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        continue
            _ = fout.write(json.dumps(rec, ensure_ascii=False) + "\n" if stripped else raw)
    return out_path


def format_text(audit: dict[str, Any], keep: int, census: bool = False) -> str:
    lines: list[str] = []
    lines.append(f"session: {audit['session_path']}")
    lines.append(
        f"records: {audit['record_count']}  bash toolResults: {audit['bash_count']}  threshold: >{audit['threshold']} lines"
    )
    if audit["parse_errors"]:
        lines.append(f"parse errors (skipped lines): {audit['parse_errors']}")
    lines.append("")
    if not audit["oversized"]:
        if audit["bash_count"] == 0:
            lines.append("No bash toolResults found.")
        else:
            lines.append(f"All {audit['bash_count']} bash outputs within threshold.")
        lines.append("")
    else:
        lines.append(f"Oversized bash outputs: {audit['oversized_count']} / {audit['bash_count']}")
        lines.append("")
        lines.append(f"{'#':>3}  {'jsonl':>5}  {'lines':>5}  {'chars':>7}  command")
        lines.append("─" * 72)
        for i, e in enumerate(audit["oversized"], start=1):
            cmd = e["command_preview"] or "(no paired toolCall — id " + e["toolCallId"][:24] + "…)"
            cmd = cmd.replace("\n", " ⏎ ")
            lines.append(f"{i:>3}  {e['jsonl_line']:>5}  {e['lines']:>5}  {e['chars']:>7}  {cmd}")
            if e.get("omitted_lines"):
                lines.append(
                    f"       (delivery cap: {e['produced_lines']} lines produced, {e['omitted_lines']} omitted)"
                )
        lines.append("")
        lines.append(f"Truncation preview (keep {keep} head + {keep} tail + marker):")
        for e in audit["oversized"]:
            n = e["lines"]
            if n > keep * 2:
                removed = n - (keep * 2 + 1)
                lines.append(f"  line {e['jsonl_line']}: {n} → {keep * 2 + 1} lines (−{removed})")
        lines.append("")
        # show next-turns preview if present
        if any("next_turns" in e for e in audit["oversized"]):
            lines.append("Next turns after each oversized (with --with-context):")
            for e in audit["oversized"]:
                ctx = e.get("next_turns") or []
                if ctx:
                    previews = " | ".join(f"{c['role']}:{c['preview'][:60]}" for c in ctx)
                    lines.append(f"  line {e['jsonl_line']} → {previews}")
            lines.append("")
    est = audit["estimated_savings"]
    lines.append(f"Total bash output: {audit['total_lines']} lines / {audit['total_chars']} chars")
    if audit.get("total_omitted_lines"):
        lines.append(
            f"Produced but not delivered (delivery cap): {audit['total_omitted_lines']} lines omitted "
            f"across {audit['truncated_count']} tool results, all tools"
        )
    if census and audit.get("tool_census"):
        lines.append("")
        lines.append("Tool census (delivered lines; truncated = hit the delivery cap):")
        lines.append(
            f"  {'tool':<18}{'calls':>7}{'lines':>10}{'chars':>12}{'truncated':>11}{'omitted':>10}"
        )
        for tool, row in audit["tool_census"].items():
            lines.append(
                f"  {tool:<18}{row['calls']:>7}{row['lines']:>10}{row['chars']:>12}{row['truncated_calls']:>11}{row['omitted_lines']:>10}"
            )
    if audit["oversized_count"]:
        lines.append(
            f"Estimated savings if truncated (keep {est['keep_head_tail']} each side): −{est['lines']} lines / −{est['chars']} chars  (~{est['chars'] // 4} tokens @ 4 chars/token)"
        )
        lines.append("")
        lines.append(
            "Refine: oversized outputs above are trimtable — use --emit-filtered to write a filtered copy,"
        )
        lines.append("or adjust --threshold / --keep-head-tail to taste.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="audit.py", description="Scan pi session JSONL for oversized bash outputs."
    )
    _ = ap.add_argument("target", help="session id (uuid) or path to *.jsonl")
    _ = ap.add_argument(
        "--threshold", type=int, default=DEFAULT_THRESHOLD, help="line threshold (default: 20)"
    )
    _ = ap.add_argument(
        "--json", action="store_true", dest="as_json", help="emit JSON instead of text"
    )
    _ = ap.add_argument(
        "--emit-filtered",
        action="store_true",
        help="write <session>.filtered.jsonl with truncated bodies",
    )
    _ = ap.add_argument(
        "--keep-head-tail",
        type=int,
        default=DEFAULT_KEEP,
        help="lines to keep each side when truncating (default: 10)",
    )
    _ = ap.add_argument(
        "--with-context",
        type=int,
        default=0,
        help="attach next N turns after each oversized result for triage (default: 0, recommend 3)",
    )
    _ = ap.add_argument(
        "--dump-context",
        type=str,
        default=None,
        help="write per-entry context JSON to dir (requires --with-context >0)",
    )
    _ = ap.add_argument(
        "--census",
        action="store_true",
        help="also print the delivered-line census for every tool (read, bash, edit, …)",
    )
    args = cast(_Args, cast(object, ap.parse_args()))
    if args.threshold < 0:
        eprint("error: --threshold must be >= 0")
        sys.exit(1)
    if args.keep_head_tail < 0:
        eprint("error: --keep-head-tail must be >= 0")
        sys.exit(1)
    if args.with_context < 0:
        eprint("error: --with-context must be >= 0")
        sys.exit(1)
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
    audit = scan(resolved, args.threshold, with_context=args.with_context)
    # strip internal _next_full before output unless dump requested
    will_dump = args.dump_context is not None and args.with_context > 0
    if will_dump:
        assert args.dump_context is not None
        dump_dir = Path(args.dump_context).expanduser()
        dump_dir.mkdir(parents=True, exist_ok=True)
        for e in cast("list[dict[str, object]]", audit["oversized"]):
            full_ctx = e.get("_next_full") or []
            # write one file per oversized entry
            out = dump_dir / f"oversized-{e['jsonl_line']}.json"
            payload = {
                "oversized": {k: v for k, v in e.items() if not k.startswith("_")},
                "next_turns_full": full_ctx,
            }
            _ = out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        audit["dump_context_dir"] = str(dump_dir.resolve())
    # remove internal key from json output
    for e in audit["oversized"]:
        e.pop("_next_full", None)
    if args.keep_head_tail != DEFAULT_KEEP and audit["oversized_count"]:
        savings_lines = 0
        savings_chars = 0
        for e in audit["oversized"]:
            n = e["lines"]
            k = args.keep_head_tail
            if n > k * 2:
                removed = n - (k * 2 + 1)
                savings_lines += removed
                avg = e["chars"] / n if n else 0
                try:
                    savings_chars += int(removed * avg)
                except ValueError, OverflowError, TypeError:
                    savings_chars += removed * 40
        audit["estimated_savings"] = {
            "lines": savings_lines,
            "chars": savings_chars,
            "keep_head_tail": args.keep_head_tail,
        }
    filtered_path = None
    if args.emit_filtered:
        filtered_path = emit_filtered(resolved, args.threshold, args.keep_head_tail)
        audit["filtered_path"] = str(filtered_path)
    if args.as_json:
        out = dict(audit)
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        _ = sys.stdout.write("\n")
    else:
        _ = sys.stdout.write(format_text(audit, args.keep_head_tail, census=args.census))
        if filtered_path is not None:
            _ = sys.stdout.write(f"Filtered copy: {filtered_path}\n")
        if will_dump:
            _ = sys.stdout.write(f"Context dump dir: {audit['dump_context_dir']}\n")
    if audit["record_count"] > 0 and audit["bash_count"] == 0:
        eprint(
            f"WARNING: scanned {audit['record_count']} records but found 0 bash toolResults — "
            "the session schema may be unrecognized (pi event-stream logs must expose "
            "'message_end' records carrying a 'message' payload), or this session used no bash. "
            "Exit 3 means 'scanned, nothing to scan'; it is NOT a clean result."
        )
        sys.exit(EXIT_SCHEMA)
    sys.exit(0)


if __name__ == "__main__":
    main()
