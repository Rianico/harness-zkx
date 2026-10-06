"""The native typecheck gate has no budget checker anymore.

`uv run basedpyright --warnings` is now the only gate, so an empty
`.basedpyright/baseline.json` is the sole remaining suppression layer: any file
entry there hides warnings invisibly. This test forbids entries outright.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

BASELINE = Path(__file__).resolve().parents[1] / ".basedpyright" / "baseline.json"


def test_native_gate_baseline_has_no_file_entries() -> None:
    baseline = cast(dict[str, object], json.loads(BASELINE.read_text(encoding="utf-8")))
    files = baseline.get("files", {})
    assert not files, (
        f"{BASELINE} must contain no file entries: found {files!r}. "
        "The native gate 'uv run basedpyright --warnings' has no budget checker "
        "anymore, so a non-empty baseline silently masks warnings that no CI "
        "gate can see."
    )
