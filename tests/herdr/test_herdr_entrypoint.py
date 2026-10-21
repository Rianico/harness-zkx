"""The shared CLI entrypoint and the primitives it absorbed (#266 T2a).

These pin the behaviour the 12 helpers used to spell themselves: environment defaulting,
parsing into the caller's namespace, the `prog: message` taxonomy, and the delivery-timeout
exit status. A regression here would change every helper at once, so each property is
asserted directly rather than through one CLI.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import herdr_cli
import pytest


@dataclass
class Options:
    """Stand-in for a helper's options dataclass."""

    name: str = ""
    loud: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="herdr-test", add_help=False)
    _ = parser.add_argument("name")
    _ = parser.add_argument("--loud", action="store_true")
    return parser


class Timeout(Exception):
    """Stand-in for a helper's `WaitTimeout`."""


def test_entrypoint_parses_into_the_callers_namespace() -> None:
    seen: list[Options] = []

    def action(options: Options, env: Mapping[str, str]) -> int:
        seen.append(options)
        assert env["SEED"] == "1"
        return herdr_cli.EXIT_OK

    code = herdr_cli.entrypoint(
        "herdr-test",
        build_parser,
        action,
        namespace=Options(),
        argv=["work"],
        env={"SEED": "1"},
    )

    assert code == herdr_cli.EXIT_OK
    assert len(seen) == 1
    assert seen[0].name == "work"
    assert seen[0].loud is False


def test_entrypoint_maps_usage_error_to_exit_usage(capsys: pytest.CaptureFixture[str]) -> None:
    def action(_options: Options, _env: Mapping[str, str]) -> int:
        raise herdr_cli.UsageError("missing precondition")

    code = herdr_cli.entrypoint(
        "herdr-test", build_parser, action, namespace=Options(), argv=["work"]
    )

    assert code == herdr_cli.EXIT_USAGE
    assert capsys.readouterr().err == "herdr-test: missing precondition\n"


def test_entrypoint_maps_engine_error_to_exit_herdr(capsys: pytest.CaptureFixture[str]) -> None:
    def action(_options: Options, _env: Mapping[str, str]) -> int:
        raise herdr_cli.HerdrError("herdr answered badly")

    code = herdr_cli.entrypoint(
        "herdr-test", build_parser, action, namespace=Options(), argv=["work"]
    )

    assert code == herdr_cli.EXIT_HERDR
    assert capsys.readouterr().err == "herdr-test: herdr answered badly\n"


def test_entrypoint_maps_the_declared_timeout_to_its_own_status(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def action(_options: Options, _env: Mapping[str, str]) -> int:
        raise Timeout("delivered but not settled")

    code = herdr_cli.entrypoint(
        "herdr-test",
        build_parser,
        action,
        namespace=Options(),
        argv=["work"],
        timeout=(Timeout, 4),
    )

    assert code == 4
    assert capsys.readouterr().err == "herdr-test: delivered but not settled\n"


def test_entrypoint_reraises_an_undeclared_exception() -> None:
    def action(_options: Options, _env: Mapping[str, str]) -> int:
        raise Timeout("not declared here")

    with pytest.raises(Timeout):
        _ = herdr_cli.entrypoint(
            "herdr-test", build_parser, action, namespace=Options(), argv=["work"]
        )


def test_entrypoint_runs_before_parse_and_keeps_its_refusal(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def before_parse(parser: argparse.ArgumentParser, raw: Sequence[str]) -> None:
        if "--ticket" in raw:
            parser.error("--ticket needs a value")

    def action(_options: Options, _env: Mapping[str, str]) -> int:
        return herdr_cli.EXIT_OK

    with pytest.raises(SystemExit) as cancelled:
        _ = herdr_cli.entrypoint(
            "herdr-test",
            build_parser,
            action,
            namespace=Options(),
            argv=["work", "--ticket"],
            before_parse=before_parse,
        )

    assert cancelled.value.code == herdr_cli.EXIT_USAGE
    assert "--ticket needs a value" in capsys.readouterr().err
