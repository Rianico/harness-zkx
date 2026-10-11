"""Pin for the shared argument declarations (ticket #238-W3).

Every parser that declares one of the families in `herdr_cli.SHARED_ARGUMENTS` must declare
it with the same dest, action, type, metavar, nargs, required, default, and const. The help
sentence stays per script, so it is pinned against `shared_arguments_golden.json`, harvested
with `declarations()` below from the pre-refactor tree (commit 630eab12) before any call was
replaced, subparsers included. Regenerate that file only alongside a deliberate behaviour
change, and only with this same walker: `declarations()` is the single collector, so a
subparser-bearing script cannot drop out of the fixture again.

Refutability: change a dest, an action, a type, a metavar, an nargs, a required, a default, or
a const in `herdr_cli.SHARED_ARGUMENTS`, or change one caller's help sentence, and the
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
from typing import cast

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
                    "const": _scalar(getattr(action, "const", None)),
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


# The fields a family's declarations must agree on unless the table marks them `varying`.
FROZEN_FIELDS = (
    "dest",
    "action",
    "type",
    "default",
    "metavar",
    "nargs",
    "required",
    "choices",
    "const",
)

# The fields the per-declaration golden comparison checks. It must cover every `FROZEN_FIELDS`
# entry: the consensus table below drops a field two siblings disagree on, and that is safe only
# because this comparison still catches a drift in that field against `GOLDEN`.
# `test_every_frozen_field_is_compared_against_the_fixture` pins that the coverage holds.
COMPARED_FIELDS = (
    "family",
    "dest",
    "action",
    "type",
    "default",
    "metavar",
    "nargs",
    "required",
    "choices",
    "const",
    "option_strings",
    "help",
)


def _frozen_by_family() -> dict[str, dict[str, object]]:
    """Per family: the field values its golden declarations agree on, and only those.

    A field two golden declarations of the same family disagree on is a parameterised one,
    so it drops out: `--role` defaults to `""`, `None`, and `"assistant"` depending on the
    script, and `--tab` carries its own metavar, nargs, and const.
    """
    frozen: dict[str, dict[str, object]] = {}
    for entries in GOLDEN.values():
        for declaration in entries:
            family = str(declaration["family"])
            agreed = frozen.setdefault(
                family, {field: declaration[field] for field in FROZEN_FIELDS}
            )
            for field in FROZEN_FIELDS:
                if field in agreed and declaration[field] != agreed[field]:
                    del agreed[field]
    return frozen


FROZEN_BY_FAMILY = _frozen_by_family()


@pytest.mark.parametrize(("script", "label"), list(_cases()))
def test_every_shared_declaration_matches_the_frozen_table(script: str, label: str) -> None:
    """One (script, family) case: every frozen field, `help` and `option_strings` included."""
    index = int(label.split("-", 1)[0])
    expected = GOLDEN[script][index]
    live = declarations(MODULES[script].build_parser())
    assert index < len(live), (
        f"{script}: missing declaration {index} for {expected['family']}; "
        f"the parser now declares {[d['family'] for d in live]}"
    )
    actual = live[index]
    for field in COMPARED_FIELDS:
        assert actual[field] == expected[field], (
            f"{script}: {expected['family']} {field}: {actual[field]!r} != {expected[field]!r}"
        )


def test_every_frozen_field_is_compared_against_the_fixture() -> None:
    """Every `FROZEN_FIELDS` entry survives into the per-declaration golden comparison.

    `_frozen_by_family` DELETES a field two golden siblings disagree on, and the consensus test
    at :210 then skips it. That is only safe because `test_every_shared_declaration_matches_the_
    frozen_table` still compares the field against `GOLDEN`, so a drift in it always fails. Measured
    at the base: the fixture comparison iterates all nine `FROZEN_FIELDS` (plus `family`,
    `option_strings`, `help`), so no field can drift invisibly. This pin holds that relation: drop a
    `FROZEN_FIELDS` entry from `COMPARED_FIELDS` and a field a family does not agree on becomes
    unchecked here, so the assertion fails naming it. Dropping the same entry from both literals
    leaves their relation intact, so `COMPARED_FIELDS` is also anchored on the fixture itself: its
    key set must equal the golden declaration's key set, which a two-literal edit cannot move.
    """
    missing = sorted(set(FROZEN_FIELDS) - set(COMPARED_FIELDS))
    assert missing == [], (
        f"FROZEN_FIELDS that no per-declaration comparison checks: {missing}; a field the "
        f"consensus table drops would then be free to drift invisibly"
    )
    for script, entries in GOLDEN.items():
        assert entries, f"{script}: the fixture lists no declarations"
        for index, entry in enumerate(entries):
            assert set(COMPARED_FIELDS) == set(entry), (
                f"{script}[{index}]: COMPARED_FIELDS {sorted(COMPARED_FIELDS)} != fixture keys "
                f"{sorted(entry)}; the comparison must cover exactly the frozen fields"
            )


@pytest.mark.parametrize("family", sorted(SHARED_LONG_OPTIONS))
def test_the_fixture_declares_every_parameterised_field(family: str) -> None:
    """Every `FROZEN_FIELDS` entry the fixture's siblings disagree on is declared `varying`.

    `_frozen_by_family` infers a parameterised field from fixture disagreement alone. This pin
    makes that designation explicit data: a field the fixture varies but the table does not declare
    `varying` fails, naming the family and the field. `test_a_shared_family_declares_the_frozen_
    fields_in_every_parser` asserts the other direction only for `dest` and the `spec.kwargs` keys,
    so this covers `nargs`, `required`, `choices`, and `const` too. The relation is a subset, not
    an equality: `--settle` names `default` as varying while its siblings agree (measured), which
    is legal.
    """
    key = family.removeprefix("--").replace("-", "_")
    varying = set(herdr_cli.SHARED_ARGUMENTS[key].varying)
    agreed = set(FROZEN_BY_FAMILY[family])
    disagreed = set(FROZEN_FIELDS) - agreed
    undeclared = sorted(disagreed - varying)
    assert undeclared == [], (
        f"{family}: the fixture varies {undeclared}, but the table does not declare them `varying`"
    )


@pytest.mark.parametrize("family", sorted(SHARED_LONG_OPTIONS))
def test_a_shared_family_declares_the_frozen_fields_in_every_parser(family: str) -> None:
    """Every parser declaring `family` reproduces the frozen field set for that family.

    The expectation comes from `shared_arguments_golden.json`, never from the live table:
    `add_shared_argument` always passes `dest=spec.dest`, so comparing a parser against the
    table moves both sides together and cannot fail. Comparing against the fixture is what
    makes a table-side change to a dest, a default, or an action fail here, naming the script
    and the flag. Only a field the table marks `varying` (or one the fixture itself shows
    differing between scripts) may differ per script.
    """
    spec = herdr_cli.SHARED_ARGUMENTS[family.removeprefix("--").replace("-", "_")]
    frozen = FROZEN_BY_FAMILY[family]
    for field in ("dest", *spec.kwargs):
        if field not in spec.varying:
            assert field in frozen, (
                f"{family}: {field} is not parameterised, so the fixture must freeze it"
            )
    declaring = {
        script: [d for d in declarations(module.build_parser()) if d["family"] == family]
        for script, module in MODULES.items()
    }
    declaring = {script: found for script, found in declaring.items() if found}
    assert declaring, f"{family} is declared nowhere"
    for script, found in declaring.items():
        for declaration in found:
            for field, expected in frozen.items():
                assert declaration[field] == expected, (
                    f"{script}: {family} {field}: {declaration[field]!r} != {expected!r}"
                )


def test_the_fixture_covers_every_script_that_declares_a_shared_family() -> None:
    """The fixture lists every declaring script, subparser-bearing ones included.

    This is what stops a harvest walker that skips subparsers from leaving a script unpinned:
    a live declaration with no fixture entry fails here, instead of silently going unchecked.
    """
    live = {script: declarations(module.build_parser()) for script, module in MODULES.items()}
    live = {script: found for script, found in live.items() if found}
    assert set(live) == set(GOLDEN), (
        f"fixture covers {sorted(GOLDEN)} but the parsers declare in {sorted(live)}"
    )
    for script, found in live.items():
        assert [d["family"] for d in found] == [d["family"] for d in GOLDEN[script]], (
            f"{script}: fixture declares {[d['family'] for d in GOLDEN[script]]} "
            f"but the parser declares {[d['family'] for d in found]}"
        )
    golden_families = {str(d["family"]) for entries in GOLDEN.values() for d in entries}
    assert golden_families == set(SHARED_LONG_OPTIONS), (
        f"fixture families {sorted(golden_families)} != table families "
        f"{sorted(SHARED_LONG_OPTIONS)}"
    )


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


def test_the_shared_argument_table_is_read_only() -> None:
    """The table and each family's kwargs are frozen: an in-place edit must raise.

    A frozen dataclass blocks rebinding `kwargs`, not an in-place edit of the mapping, so
    without the proxy `SHARED_ARGUMENTS["json"].kwargs["action"] = "store_false"` would
    invert `--json` for every parser built afterwards in the same process.
    """
    table = cast("dict[str, object]", herdr_cli.SHARED_ARGUMENTS)
    with pytest.raises(TypeError):
        table["json"] = table["json"]
    kwargs = cast("dict[str, object]", herdr_cli.SHARED_ARGUMENTS["json"].kwargs)
    with pytest.raises(TypeError):
        kwargs["action"] = "store_false"


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
            literals = {
                argument.value
                for argument in node.args
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
            }
            hits = sorted(literals & SHARED_LONG_OPTIONS)
            if hits:
                offenders.append(f"{path.name}:{node.lineno} {', '.join(hits)}")
    assert offenders == [], f"hand-written shared declarations: {offenders}"
