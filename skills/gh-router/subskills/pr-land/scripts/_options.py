"""The parsed CLI option container shared by the pr-land command modules.

A leaf module: `_github.resolve_title_and_body` and `_draft.run_draft_phase` both annotate
with `PrOptions`, so the class lives here — keeping it in `pr.py` would make both siblings
import the entry script back, which `reportImportCycles` rejects as an error.
"""

from dataclasses import dataclass
from pathlib import Path

from _errors import UsageError


@dataclass(frozen=True)
class PrOptions:
    base: str | None = None
    head: str | None = None
    title: str | None = None
    body: str | None = None
    body_file: Path | None = None
    out: Path | None = None
    watch: bool = False
    merge: bool = False
    check: bool = False
    status: bool = False
    json_output: bool = False
    draft: bool = False
    no_stamp: bool = False
    title_supplied: bool = False
    body_supplied: bool = False
    squash_message: str | None = None
    squash_message_file: Path | None = None
    squash_message_supplied: bool = False
    verbose: bool = False
    force_scaffold: bool = False


def read_user_file(
    path: Path,
    *,
    kind: str,
    display: str,
    encoding: str = "utf-8",
) -> str:
    """Read a caller-supplied file or raise UsageError naming it.

    One home for the `--squash-message-file` / `--body-file` reads. `kind`
    names the flag for the error; `encoding` stays caller-chosen because the
    squash message needs BOM-stripping (`utf-8-sig`, F11) while bodies do not.
    """
    if not path.is_file():
        raise UsageError(f"{kind} file not found or not readable: {display}")
    try:
        return path.read_text(encoding=encoding)
    except OSError as exc:
        raise UsageError(f"{kind} file not found or not readable: {display}") from exc


def resolve_squash_override(options: PrOptions, cwd: Path | None = None) -> tuple[str | None, bool]:
    """Read the explicit squash message: flag text or `--squash-message-file`."""
    explicit = options.squash_message
    if options.squash_message_file:
        mf = (
            options.squash_message_file
            if options.squash_message_file.is_absolute()
            else ((cwd or Path.cwd()) / options.squash_message_file)
        )
        # utf-8-sig drops a BOM so `\ufeff## Summary` never rides in as prose (F11).
        explicit = read_user_file(
            mf,
            kind="squash message",
            display=str(options.squash_message_file),
            encoding="utf-8-sig",
        )
    return explicit, options.squash_message_supplied
