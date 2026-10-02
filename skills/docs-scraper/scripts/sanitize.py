#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
Threat and prompt-injection sanitization for untrusted documents.

Usage:
  python sanitize.py <file>         # Scan and strip
  python sanitize.py --check <file> # Scan only, report findings
"""

import argparse
import re
import sys
from pathlib import Path

# ── Codepoint tables ─────────────────────────────────────────────────────────

# Zero-width / invisible spacers
ZERO_WIDTH_CODEPOINTS: dict[str, str] = {
    "\u200b": "ZWSP",
    "\u200c": "ZWNJ",
    "\u200d": "ZWJ",
    "\u2060": "WJ",
    "\ufeff": "ZWNBSP/BOM",
    "\u00ad": "SOFT_HYPHEN",
    "\u034f": "CGJ",
    "\u180e": "MONGOLIAN_VOWEL_SEPARATOR",
    "\u2061": "FUNCTION_APPLICATION",
    "\u2062": "INVISIBLE_TIMES",
    "\u2063": "INVISIBLE_SEPARATOR",
    "\u2064": "INVISIBLE_PLUS",
}

# Trojan Source Bidi controls (CVE-2021-42574)
BIDI_CONTROLS: dict[str, str] = {
    "\u200e": "LRM",
    "\u200f": "RLM",
    "\u061c": "ALM",
    "\u202a": "LRE",
    "\u202b": "RLE",
    "\u202c": "PDF",
    "\u202d": "LRO",
    "\u202e": "RLO",
    "\u2066": "LRI",
    "\u2067": "RLI",
    "\u2068": "FSI",
    "\u2069": "PDI",
}

# Invisible letter / filler codepoints
INVISIBLE_FILLERS: dict[str, str] = {
    "\u115f": "HANGUL_CHOSEONG_FILLER",
    "\u1160": "HANGUL_JUNGSEONG_FILLER",
    "\u3164": "HANGUL_CAE_OM",
    "\uffa0": "HALFWIDTH_HANGUL_FILLER",
    "\u206a": "INHIBIT_SYMMETRIC_SWAPPING",
    "\u206b": "ACTIVATE_SYMMETRIC_SWAPPING",
    "\u206c": "INHIBIT_ARABIC_FORM_SHAPING",
    "\u206d": "ACTIVATE_ARABIC_FORM_SHAPING",
    "\u206e": "NATIONAL_DIGIT_SHAPES",
    "\u206f": "NOMINAL_DIGIT_SHAPES",
}

ALL_STRIP_CODEPOINTS = {**ZERO_WIDTH_CODEPOINTS, **BIDI_CONTROLS, **INVISIBLE_FILLERS}

# ── Injection patterns ───────────────────────────────────────────────────────

INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"ignore\s+(all|any|the)\s+(previous|prior)\s+(instructions?|prompts?)",
        re.IGNORECASE,
    ),
    re.compile(r"system\s+override", re.IGNORECASE),
    re.compile(r"developer\s+mode", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+\S+\s+mode", re.IGNORECASE),
]


def scan_text_for_injections(text: str) -> list[str]:
    """Scan text for prompt injection / hijack patterns.

    Returns list of matched strings (can be empty if clean).
    """
    findings: list[str] = []
    for pattern in INJECTION_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(match.group(0))
    return findings


def strip_dangerous_codepoints(text: str) -> tuple[str, list[str]]:
    """Remove zero-width, bidi control, and invisible filler codepoints.

    Returns (cleaned_text, list_of_removal_descriptions).
    """
    removals: list[str] = []
    for cp, name in ALL_STRIP_CODEPOINTS.items():
        if cp in text:
            count = text.count(cp)
            removals.append(f"U+{ord(cp):04X} {name}: {count} occurrence(s)")
            text = text.replace(cp, "")
    return text, removals


def sanitize(text: str, check_only: bool = False) -> tuple[str, dict[str, object]]:
    """Full sanitization pipeline.

    Returns (sanitized_text, report_dict).
    """
    report: dict[str, object] = {
        "codepoints_removed": [],
        "injections_found": [],
        "clean": True,
    }

    cleaned, removals = strip_dangerous_codepoints(text)
    if removals:
        report["codepoints_removed"] = removals
        report["clean"] = False

    injections = scan_text_for_injections(cleaned)
    if injections:
        report["injections_found"] = injections
        report["clean"] = False

    if check_only:
        return text, report
    return cleaned, report


# ── CLI ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanitize untrusted documents for LLM consumption")
    parser.add_argument("file", type=Path, help="File to sanitize")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Scan only, do not modify file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file (default: overwrite input or stdout for --check)",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    text = args.file.read_text(encoding="utf-8")
    cleaned, report = sanitize(text, check_only=args.check)

    # Print report
    cp_list = report["codepoints_removed"]
    if isinstance(cp_list, list) and cp_list:
        print(f"\nRemoved {len(cp_list)} dangerous codepoint group(s):")
        for r in cp_list:
            print(f"  - {r}")
    else:
        print("\nNo dangerous codepoints found.")

    inj_list = report["injections_found"]
    if isinstance(inj_list, list) and inj_list:
        print(f"\n⚠️  Found {len(inj_list)} injection pattern(s):")
        for inj in inj_list:
            print(f"  - {inj}")
    else:
        print("No injection patterns found.")

    if report["clean"]:
        print("\n✅ Document is clean.")
    else:
        print("\n⚠️  Document contains threats.")

    # Write output
    if args.check:
        # scan only — no modification
        pass
    elif args.output:
        args.output.write_text(cleaned, encoding="utf-8")
        print(f"Sanitized output written to: {args.output}")
    else:
        args.file.write_text(cleaned, encoding="utf-8")
        print(f"Sanitized in-place: {args.file}")

    if not report["clean"] and not args.check:
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
