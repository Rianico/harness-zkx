"""Each declared CLI surface (`_Args`) must match its parser's `add_argument` set.

`cast(_Args, cast(object, parser.parse_args()))` is a claim the type checker believes: nothing ties
the protocol's fields to the `add_argument` calls that actually populate the namespace, so a parser
that grows an argument without growing its protocol silently widens the `Any` it was written to
close. This test ties the two statically, without adding a `build_parser` seam to every script.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Scoped, so a scratch render under the gitignored `.lsz/` cannot inject a second protocol.
SEARCH_DIRS = ("scripts", "skills", "lib", "tests")
PROTOCOL_NAME = "_Args"
DECLARATION = f"class {PROTOCOL_NAME}("


def cli_sources() -> list[Path]:
    """Every source file that declares a CLI-surface protocol."""
    return [
        path
        for root in SEARCH_DIRS
        for path in sorted((REPO_ROOT / root).rglob("*.py"))
        if DECLARATION in path.read_text(encoding="utf-8")
    ]


def declared_fields(source: str) -> set[str]:
    """The annotated field names of the `_Args` class in `source`."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ClassDef) and node.name == PROTOCOL_NAME:
            return {
                statement.target.id
                for statement in node.body
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
            }
    raise AssertionError(f"no `class {PROTOCOL_NAME}` in the source")


def dest_of(call: ast.Call) -> str | None:
    """The `argparse` dest one `add_argument` call produces, or None when it is not static."""
    for keyword in call.keywords:
        if keyword.arg == "dest" and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, str):
                return keyword.value.value
    flags = [
        argument.value
        for argument in call.args
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
    ]
    if not flags:
        return None
    # `argparse` derives the dest from the first long option, else from the first flag.
    long_flags = [flag for flag in flags if flag.startswith("--")]
    chosen = long_flags[0] if long_flags else flags[0]
    return chosen.lstrip("-").replace("-", "_")


def parser_dests(source: str) -> set[str]:
    """The dests every `add_argument` call in `source` produces."""
    dests: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_argument":
                dest = dest_of(node)
                if dest is not None:
                    dests.add(dest)
    return dests


def test_declared_cli_surfaces_match_their_parsers() -> None:
    sources = cli_sources()
    assert sources, "no `_Args` protocol found — SEARCH_DIRS is stale"

    mismatches: dict[str, dict[str, list[str]]] = {}
    for path in sources:
        source = path.read_text(encoding="utf-8")
        declared, parsed = declared_fields(source), parser_dests(source)
        if declared != parsed:
            mismatches[str(path.relative_to(REPO_ROOT))] = {
                "in_parser_only": sorted(parsed - declared),
                "in_protocol_only": sorted(declared - parsed),
            }

    assert not mismatches, f"CLI surface drift — fix the protocol or the parser: {mismatches}"


def test_the_detectors_see_drift() -> None:
    """Refutation guard: the detectors must catch a protocol its parser has outgrown."""
    source = "\n".join(
        [
            f"class {PROTOCOL_NAME}(Protocol):",
            "    only_declared: str",
            "",
            "",
            "def build() -> None:",
            "    parser = argparse.ArgumentParser()",
            '    parser.add_argument("--only-parsed")',
            '    parser.add_argument("-v", "--verbose")',
            '    parser.add_argument("--json", dest="as_json")',
        ]
    )

    assert declared_fields(source) == {"only_declared"}
    assert parser_dests(source) == {"only_parsed", "verbose", "as_json"}
