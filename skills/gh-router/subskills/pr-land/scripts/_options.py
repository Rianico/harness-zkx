"""The parsed CLI option container shared by the pr-land command modules.

A leaf module: `_github.resolve_title_and_body` and `_draft.run_draft_phase` both annotate
with `PrOptions`, so the class lives here — keeping it in `pr.py` would make both siblings
import the entry script back, which `reportImportCycles` rejects as an error.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PrOptions:
    base: str | None = None
    head: str | None = None
    title: str | None = None
    body: str | None = None
    body_file: Path | None = None
    out_dir: Path | None = None
    watch: bool = False
    merge: bool = False
    check: bool = False
    draft: bool = False
    no_stamp: bool = False
    title_supplied: bool = False
    body_supplied: bool = False
    squash_message: str | None = None
    squash_message_file: Path | None = None
    squash_message_supplied: bool = False
    verbose: bool = False
