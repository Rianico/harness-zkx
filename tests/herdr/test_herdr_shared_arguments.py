"""Pin for the shared argument declarations (ticket #238-W3).

Every parser that declares one of the families in `herdr_cli.SHARED_ARGUMENTS` must declare
it with the same dest, action, type, metavar, nargs, required, and default. The help sentence
stays per script, so it is pinned against `shared_arguments_golden.json`, harvested from the
pre-refactor tree (commit 630eab12) before any call was replaced. Regenerate that file only
alongside a deliberate behaviour change.

Refutability: change one dest or one help in `herdr_cli.add_shared_argument` and the
per-(script, family) case fails, naming the script and the flag. Remove one declaration from a
`build_parser` and the same case fails on the missing flag. Rename one inherited dest and
`test_inheritance_boundary_pins_the_dests_prompt_reads` fails, because the dest names that
`herdr_prompt` reads out of `herdr_dispatch`'s namespace are literals here.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections.abc import Iterator, Mapping
from pathlib import Path

import herdr_agy_bridge
import herdr_bootstrap
import herdr_cli
import herdr_dispatch
import herdr_label
import herdr_lease
import herdr_overview
import herdr_pane
import herdr_prompt
import herdr_reply
import herdr_transcript
import herdr_wait
import herdr_worktree
import pytest

from tests.herdr.stub import SCRIPTS_DIR

GOLDEN_PATH = Path(__file__).with_name("shared_arguments_golden.json")
GOLDEN: Mapping[str, list[dict[str, object]]] = json.loads(GOLDEN_PATH.read_text())

MODULES = {
    "herdr_agy_bridge.py": herdr_agy_bridge,
    "herdr_bootstrap.py": herdr_bootstrap,
    "herdr_dispatch.py": herdr_dispatch,
    "herdr_label.py": herdr_label,
    "herdr_lease.py": herdr_lease,
    "herdr_overview.py": herdr_overview,
    "herdr_pane.py": herdr_pane,
    "herdr_prompt.py": herdr_prompt,
    "herdr_reply.py": herdr_reply,
    "herdr_transcript.py": herdr_transcript,
    "herdr_wait.py": herdr_wait,
    "herdr_worktree.py": herdr_worktree,
}

SHARED_LONG_OPTIONS = frozenset(
    option for spec in herdr_cli.SHARED_ARGUMENTS.values() for option in spec.options
)

# `herdr_dispatch.Options` inherits `herdr_prompt.Options` and hands the namespace to
# `prompt_agents()`, so these dests are read by code that lives in the parent module.
INHERITED_FAMILIES = (
    "--json",
    "--wait",
    "--no-wait",
    "--until",
    "--timeout",
    "--no-caller-context",
    "--verbose",
)
INHERITED_DESTS = frozenset(
    {"json", "wait", "no_wait", "until", "timeout", "no_caller_context", "verbose"}
)


def _scalar(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_scalar(item) for item in value]
    return f"<{type(value).__name__}>"


def _type_name(value: object) -> str | None:
    name = getattr(value, "__name__", None)
    return name if isinstance(name, str) else None


def declarations(parser: argparse.ArgumentParser) -> list[dict[str, object]]:
    """Collect every declaration of a shared family, subparsers included, in parse order."""
    found: list[dict[str, object]] = []
    for action in parser._actions:
        long_options = [option for option in action.option_strings if option.startswith("--")]
        family = next((option for option in long_options if option in SHARED_LONG_OPTIONS), None)
        if family is not None:
            found.append(
                {
                    "family": family,
                    "option_strings": list(action.option_strings),
                    "dest": action.dest,
                    "action": type(action).__name__,
                    "type": _type_name(action.type),
                    "default": _scalar(action.default),
                    "metavar": _scalar(action.metavar),
                    "nargs": _scalar(action.nargs),
                    "required": bool(action.required),
                    "choices": _scalar(None if action.choices is None else list(action.choices)),
                    "help": action.help,
                }
            )
        if isinstance(action, argparse._SubParsersAction):
            for sub in action.choices.values():
                found.extend(declarations(sub))
    return found


def _cases() -> Iterator[tuple[str, str]]:
    for script, golden in GOLDEN.items():
        for index, declaration in enumerate(golden):
            yield script, f"{index:02d}-{declaration['family']}"


@pytest.mark.parametrize(("script", "label"), list(_cases()))
def test_every_shared_declaration_matches_the_frozen_table(script: str, label: str) -> None:
    """One (script, family) case: dest, action, type, default, metavar, nargs, help, required."""
    index = int(label.split("-", 1)[0])
    expected = GOLDEN[script][index]
    live = declarations(MODULES[script].build_parser())
    assert index < len(live), (
        f"{script}: missing declaration {index} for {expected['family']}; "
        f"the parser now declares {[d['family'] for d in live]}"
    )
    actual = live[index]
    for field in (
        "family",
        "dest",
        "action",
        "type",
        "default",
        "metavar",
        "nargs",
        "required",
        "choices",
        "option_strings",
        "help",
    ):
        assert actual[field] == expected[field], (
            f"{script}: {expected['family']} {field}: {actual[field]!r} != {expected[field]!r}"
        )


@pytest.mark.parametrize("family", sorted(SHARED_LONG_OPTIONS))
def test_a_shared_family_has_one_dest_and_one_default_across_parsers(family: str) -> None:
    """A shared family may vary its help; its dest and non-parameterised fields may not."""
    declaring = {
        script: [d for d in declarations(module.build_parser()) if d["family"] == family]
        for script, module in MODULES.items()
    }
    declaring = {script: found for script, found in declaring.items() if found}
    assert declaring, f"{family} is declared nowhere"
    for script, found in declaring.items():
        for declaration in found:
            assert (
                declaration["dest"]
                == herdr_cli.SHARED_ARGUMENTS[family.removeprefix("--").replace("-", "_")].dest
            ), f"{script}: {family} dest drifted"


def test_inheritance_boundary_pins_the_dests_prompt_reads() -> None:
    """`herdr_dispatch` inherits `herdr_prompt.Options`; the dests must be the inherited names."""
    prompt = {
        d["family"]: d
        for d in declarations(herdr_prompt.build_parser())
        if d["family"] in INHERITED_FAMILIES
    }
    dispatch = {
        d["family"]: d
        for d in declarations(herdr_dispatch.build_parser())
        if d["family"] in INHERITED_FAMILIES
    }
    assert set(prompt) == set(INHERITED_FAMILIES)
    assert set(dispatch) == set(INHERITED_FAMILIES)
    for family in INHERITED_FAMILIES:
        parent, child = prompt[family], dispatch[family]
        assert child["dest"] in INHERITED_DESTS, f"herdr_dispatch {family} dest {child['dest']!r}"
        assert parent["dest"] in INHERITED_DESTS, f"herdr_prompt {family} dest {parent['dest']!r}"
        for field in ("dest", "action", "type", "default", "metavar", "nargs", "required"):
            assert child[field] == parent[field], (
                f"{family} {field}: {child[field]!r} != {parent[field]!r}"
            )


def test_builder_refuses_a_dest_override_and_an_unknown_family() -> None:
    """The builder owns `dest`: a caller cannot move the namespace attribute."""
    parser = argparse.ArgumentParser()
    with pytest.raises(TypeError, match="not overridable: dest"):
        herdr_cli.add_shared_argument(parser, "json", help="x", dest="other")  # type: ignore[call-arg]
    with pytest.raises(KeyError):
        herdr_cli.add_shared_argument(parser, "no-such-family", help="x")


def test_every_shared_declaration_in_the_scripts_goes_through_the_builder() -> None:
    """No `build_parser` may hand-write a shared family; that is the drift surface."""
    offenders: list[str] = []
    for path in sorted(SCRIPTS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr == "add_shared_argument":
                continue
            if func.attr != "add_argument":
                continue
            first = node.args[0] if node.args else None
            if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                continue
            if first.value in SHARED_LONG_OPTIONS:
                offenders.append(f"{path.name}:{node.lineno} {first.value}")
    assert offenders == [], f"hand-written shared declarations: {offenders}"
