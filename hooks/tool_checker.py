#!/usr/bin/env python3
"""Shared utility for checking required tools during hook installation."""

import shutil
import sys


def check_tool(tool_name: str) -> tuple[bool, str]:
    """Check if a tool is available on the system PATH.

    Args:
        tool_name: Name of the tool executable to check

    Returns:
        Tuple of (found: bool, path_or_error: str)
    """
    path = shutil.which(tool_name)
    if path:
        return True, path
    return False, f"'{tool_name}' not found in PATH"


def check_tools(
    required: list[str],
    optional: list[str] | None = None,
) -> tuple[bool, list[str]]:
    """Check multiple tools and report status.

    Args:
        required: List of required tool names (installation fails if missing)
        optional: List of optional tool names (warning only if missing)

    Returns:
        Tuple of (all_required_found: bool, messages: list of status strings)
    """
    messages = []
    all_found = True

    for tool in required:
        found, info = check_tool(tool)
        if found:
            messages.append(f"✓ {tool}: {info}")
        else:
            messages.append(f"✗ {tool}: {info}")
            all_found = False

    if optional:
        for tool in optional:
            found, info = check_tool(tool)
            if found:
                messages.append(f"✓ {tool}: {info} (optional)")
            else:
                messages.append(f"⚠ {tool}: {info} (optional, may degrade)")

    return all_found, messages


def print_check_report(
    family_name: str,
    all_found: bool,
    messages: list[str],
) -> None:
    """Print a formatted tool check report.

    Args:
        family_name: Name of the hook family
        all_found: Whether all required tools were found
        messages: List of status messages
    """
    print(f"\n[{family_name}] Tool check:")
    for msg in messages:
        print(f"  {msg}")

    if not all_found:
        print(f"\n[{family_name}] Installation aborted: missing required tools.")


def run_tool_check(
    family_name: str,
    required: list[str],
    optional: list[str] | None = None,
) -> bool:
    """Run tool check and print report.

    Args:
        family_name: Name of the hook family
        required: List of required tool names
        optional: List of optional tool names

    Returns:
        True if all required tools found, False otherwise
    """
    all_found, messages = check_tools(required, optional)
    print_check_report(family_name, all_found, messages)
    return all_found


if __name__ == "__main__":
    # CLI for standalone tool checking
    if len(sys.argv) < 2:
        print("Usage: tool_checker.py <tool1> [tool2] ...")
        print("       tool_checker.py --required uv,jq --optional notify-send")
        sys.exit(1)

    if sys.argv[1].startswith("--"):
        # Parse --required and --optional flags
        required = []
        optional = []
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == "--required" and i + 1 < len(sys.argv):
                required = [t.strip() for t in sys.argv[i + 1].split(",") if t.strip()]
                i += 2
            elif sys.argv[i] == "--optional" and i + 1 < len(sys.argv):
                optional = [t.strip() for t in sys.argv[i + 1].split(",") if t.strip()]
                i += 2
            else:
                i += 1

        all_found, messages = check_tools(required, optional)
        print_check_report("CLI", all_found, messages)
        sys.exit(0 if all_found else 1)
    else:
        # Simple tool list check
        tools = sys.argv[1:]
        all_found, messages = check_tools(tools)
        print_check_report("CLI", all_found, messages)
        sys.exit(0 if all_found else 1)
