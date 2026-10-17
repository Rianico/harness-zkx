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


def resolve_squash_override(options: PrOptions, cwd: Path | None = None) -> tuple[str | None, bool]:
    """Read the explicit squash message: flag text or `--squash-message-file`."""
    explicit = options.squash_message
    if options.squash_message_file:
        mf = (
            options.squash_message_file
            if options.squash_message_file.is_absolute()
            else ((cwd or Path.cwd()) / options.squash_message_file)
        )
        if not mf.is_file():
            raise UsageError(
                f"squash message file not found or not readable: {options.squash_message_file}"
            )
        try:
            # utf-8-sig drops a BOM so `\ufeff## Summary` never rides in as prose (F11).
            explicit = mf.read_text(encoding="utf-8-sig")
        except OSError:
            raise UsageError(
                f"squash message file not found or not readable: {options.squash_message_file}"
            ) from None
    return explicit, options.squash_message_supplied
