"""Shared utilities for skill-comply scripts."""

from __future__ import annotations

import re


def extract_yaml(text: str) -> str:
    """Extract YAML from LLM output, stripping markdown fences and commentary.

    Finds the first YAML block (starting with a top-level key: at line start)
    and extracts everything from there to the end.
    """
    text = text.strip()

    # Remove markdown fences if present
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]

    # Find the first line that starts with a top-level key (no indentation)
    # This is a line that starts with a letter/underscore, followed by
    # letters/numbers/underscores, then a colon (value can be on same line or next)
    for i, line in enumerate(lines):
        # Match a top-level key (no leading whitespace)
        # Key followed by colon, optionally with value on same line
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*:\s*", line):
            # Return everything from this line to the end
            return "\n".join(lines[i:])

    # If no top-level key found, return the stripped text
    return "\n".join(lines)
