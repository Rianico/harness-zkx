"""Reply store durability: one index file per record, no lost rows, no clobbering (#231).

These cases drive the store functions `herdr-reply` itself calls (`record_reply`, `get_reply`,
`list_replies`), because the store is the contract delivery depends on: 16 concurrent replies
must leave 16 resolvable rows, an unreadable index must be preserved rather than written over,
and a row must resolve only while its payload still matches its digest.
"""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import herdr_lease
import herdr_reply
import pytest
import yaml

LANE = Path(".lane")
REPLIES = LANE / "replies"
LEDGER = LANE / "replies.yaml"
PARALLEL = 16
STAMP = "20260101T000000000Z"


def index_write_seam() -> str:
    """The store's single index-write entry point, whichever revision names it (#231 F1).

    This revision writes one create-only sidecar per record (`_write_reply_index`); the
    pre-#231 revision rewrote the whole ledger (`_write_replies`). Hooking whichever exists
    lets the same case interleave two `record_reply` calls on either revision.
    """
    for name in ("_write_reply_index", "_write_replies"):
        if hasattr(herdr_lease, name):
            return name
    raise AssertionError("herdr_lease exposes no index-write seam to interleave")


def failing_write(exc: BaseException) -> Callable[..., Any]:
    """A stand-in index write that always fails, for the durability cases."""

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise exc

    return fail


def entry_for(
    payload: str,
    *,
    record_id: str,
    sender: str = "reviewer",
    task_id: str = "#231#task",
) -> dict[str, Any]:
    """A complete, metadata-only row: the shape the store now holds."""
    return {
        "id": record_id,
        "recorded_at": STAMP,
        "sender": sender,
        "caller": "orchestrator",
        "ticket_id": "#231",
        "task_id": task_id,
        "in_reply_to": task_id,
        "status": "completed",
        "shape": "complete",
        "evidence": "evidence",
        "sha": "deadbeef",
        "digest": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "bytes": len(payload.encode("utf-8")),
        "artifacts": 2,
    }


def legacy_row(
    payload: str,
    *,
    record_id: str,
    sender: str = "reviewer",
    task_id: str = "#231#legacy",
    digest: str | None = None,
) -> dict[str, Any]:
    """A row in the pre-#231 ledger shape, `status_line` and artifact list included."""
    return {
        "id": record_id,
        "recorded_at": STAMP,
        "sender": sender,
        "caller": "orchestrator",
        "ticket_id": "#231",
        "in_reply_to": task_id,
        "status_line": payload.splitlines()[0],
        "status": "completed",
        "shape": "complete",
        "evidence": "Evidence",
        "sha": "deadbeef",
        "digest": digest or hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "bytes": len(payload.encode("utf-8")),
        "artifacts": ["tests/herdr/test_herdr_reply.py"],
        "payload": f"{REPLIES.as_posix()}/{record_id}.md",
    }


def write_body(base: Path, record_id: str, payload: str) -> Path:
    path = base / REPLIES / f"{record_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(payload, encoding="utf-8")
    return path


def write_legacy(base: Path, rows: list[Mapping[str, Any]], *, damage: str = "") -> Path:
    path = base / LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump({"replies": list(rows)}, sort_keys=False) + damage
    _ = path.write_text(text, encoding="utf-8")
    return path


# ── F1: the directory is the index, so concurrency cannot lose a row ─────────────────


def test_parallel_replies_keep_every_row(tmp_path: Path) -> None:
    """16 concurrent replies leave 16 rows, 16 resolvable ids, and no missing payload."""
    base = tmp_path
    released = threading.Barrier(PARALLEL)

    def record(index: int) -> dict[str, Any]:
        body = f"COMPLETED deadbeef\n\n## Evidence\n- shard {index} passed\n"
        entry = entry_for(body, record_id=f"row-{index:02d}")
        _ = released.wait()
        return herdr_lease.record_reply(entry, body, base_dir=base)

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        stored = list(pool.map(record, range(PARALLEL)))

    rows = herdr_lease.list_replies(limit=100, base_dir=base)
    ids = sorted(row["id"] for row in rows)
    assert ids == [f"row-{index:02d}" for index in range(PARALLEL)], f"lost rows: {ids}"

    # Every pointer the reply path could deliver names a row the reader re-derives...
    for row in stored:
        resolved = herdr_lease.get_reply(str(row["id"]), base_dir=base)
        assert resolved is not None, f"pointer names an unresolvable record: {row['id']}"
        assert resolved["digest"] == row["digest"]

    # ...and every row's payload file is still on disk.
    bodies = sorted((base / REPLIES).glob("*.md"))
    assert len(bodies) == PARALLEL


def test_interleaved_pair_keeps_both_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two replies whose index writes interleave: each keeps its own row.

    Row B is recorded by a second call site while row A is already past its read and before
    its write — the schedule the old whole-ledger read-modify-write lost. The interleave is
    injected through the store's own index-write seam; the `injected` guard keeps B's own
    write from being re-interleaved.
    """
    base = tmp_path
    body_a = "COMPLETED deadbeef\n\n## Evidence\n- a\n"
    body_b = "COMPLETED deadbeef\n\n## Evidence\n- b\n"
    entry_a = entry_for(body_a, record_id="row-A")
    entry_b = entry_for(body_b, record_id="row-B")
    real = getattr(herdr_lease, index_write_seam())
    injected: list[bool] = []

    def interleaving_write(*args: Any, **kwargs: Any) -> Any:
        if not injected:
            injected.append(True)
            _ = herdr_lease.record_reply(entry_b, body_b, base_dir=base)
        return real(*args, **kwargs)

    monkeypatch.setattr(herdr_lease, index_write_seam(), interleaving_write)

    _ = herdr_lease.record_reply(entry_a, body_a, base_dir=base)

    assert injected == [True], "the index write was never observed"
    rows = herdr_lease.list_replies(limit=10, base_dir=base)
    assert sorted(row["id"] for row in rows) == ["row-A", "row-B"]
    for record_id in ("row-A", "row-B"):
        assert herdr_lease.get_reply(record_id, base_dir=base) is not None


def test_id_collision_regenerates_a_suffixed_id(tmp_path: Path) -> None:
    """A taken id is regenerated, and the record that holds it keeps its own body."""
    base = tmp_path
    first_body = "COMPLETED deadbeef\n\n## Evidence\n- first\n"
    second_body = "COMPLETED deadbeef\n\n## Evidence\n- second\n"

    first = herdr_lease.record_reply(
        entry_for(first_body, record_id="taken"), first_body, base_dir=base
    )
    second = herdr_lease.record_reply(
        entry_for(second_body, record_id="taken"), second_body, base_dir=base
    )

    assert first["id"] == "taken"
    assert second["id"].startswith("taken-") and second["id"] != "taken"
    rows = herdr_lease.list_replies(limit=10, base_dir=base)
    assert sorted(row["id"] for row in rows) == sorted(["taken", second["id"]])
    kept = herdr_lease.get_reply("taken", base_dir=base)
    assert kept is not None
    assert kept["digest"] == hashlib.sha256(first_body.encode("utf-8")).hexdigest()
    assert (base / REPLIES / "taken.md").read_text(encoding="utf-8") == first_body


def test_index_write_is_create_only_and_publishes_complete_files(tmp_path: Path) -> None:
    """A sidecar appears complete or not at all, and a taken path is never overwritten.

    The record path publishes through this seam; a reader running while a reply is being
    recorded must never catch a zero-length or half-written index file, which F2's rule would
    have to quarantine as damaged.
    """
    path = tmp_path / "row.yaml"
    first = {"id": "row", "sender": "reviewer", "digest": "0" * 64}
    herdr_lease._write_reply_index(path, first)
    published = yaml.safe_dump(first, sort_keys=False).encode("utf-8")

    assert path.read_bytes() == published
    with pytest.raises(FileExistsError):
        herdr_lease._write_reply_index(path, {"id": "other"})

    assert path.read_bytes() == published
    assert [entry.name for entry in tmp_path.iterdir()] == ["row.yaml"]


def test_sidecar_write_failure_leaves_no_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-C3: a failed record unlinks its body, so no unreachable record survives."""
    base = tmp_path
    body = "COMPLETED deadbeef\n\n## Evidence\n- 660 passed\n"
    entry = entry_for(body, record_id="row-fail")
    monkeypatch.setattr(
        herdr_lease, index_write_seam(), failing_write(OSError("no space left on device"))
    )

    with pytest.raises(OSError):
        _ = herdr_lease.record_reply(entry, body, base_dir=base)

    assert list((base / REPLIES).glob("*.md")) == []
    assert herdr_lease.list_replies(limit=10, base_dir=base) == []


# ── F2: an unreadable index is preserved, never clobbered ────────────────────────────


def test_unreadable_legacy_ledger_is_preserved(tmp_path: Path) -> None:
    """A parse failure moves the ledger aside byte-for-byte and stops the read."""
    base = tmp_path
    prior_body = "COMPLETED deadbeef\n\n## Evidence\n- prior\n"
    _ = write_body(base, "prior", prior_body)
    ledger = write_legacy(
        base, [legacy_row(prior_body, record_id="prior")], damage="\n: broken [oops\n"
    )
    damaged = ledger.read_bytes()

    with pytest.raises(herdr_lease.UsageError) as caught:
        _ = herdr_lease.list_replies(base_dir=base)

    assert "replies.yaml" in str(caught.value)
    assert not ledger.exists()
    preserved = sorted((base / LANE).glob("replies.yaml.corrupt-*"))
    assert len(preserved) == 1
    assert preserved[0].read_bytes() == damaged
    assert "prior" in preserved[0].read_text(encoding="utf-8")
    # Nothing was destroyed: the prior body is byte-identical, and a reply recorded after
    # the quarantine lands on the sidecar path.
    assert (base / REPLIES / "prior.md").read_text(encoding="utf-8") == prior_body
    new_body = "COMPLETED deadbeef\n\n## Evidence\n- new\n"
    stored = herdr_lease.record_reply(
        entry_for(new_body, record_id="row-new"), new_body, base_dir=base
    )
    assert stored["id"] == "row-new"
    assert (base / REPLIES / "row-new.yaml").is_file()
    assert [row["id"] for row in herdr_lease.list_replies(limit=10, base_dir=base)] == ["row-new"]


def test_unreadable_sidecar_is_preserved(tmp_path: Path) -> None:
    """The same rule for one record's index file, not just the legacy ledger."""
    base = tmp_path
    sidecar = base / REPLIES / "row-bad.yaml"
    sidecar.parent.mkdir(parents=True)
    _ = sidecar.write_text("\tid: [oops\n", encoding="utf-8")
    damaged = sidecar.read_bytes()

    with pytest.raises(herdr_lease.UsageError) as caught:
        _ = herdr_lease.list_replies(base_dir=base)

    assert "row-bad.yaml" in str(caught.value)
    assert not sidecar.exists()
    preserved = sorted((base / REPLIES).glob("row-bad.yaml.corrupt-*"))
    assert len(preserved) == 1
    assert preserved[0].read_bytes() == damaged


# ── legacy compatibility: read-only, merged on read, never rewritten ────────────────


def test_legacy_ledger_rows_resolve_and_the_file_is_never_rewritten(tmp_path: Path) -> None:
    base = tmp_path
    body = "COMPLETED deadbeef\n\n## Evidence\n- legacy row\n"
    row = legacy_row(body, record_id="legacy-1")
    _ = write_body(base, "legacy-1", body)
    ledger = write_legacy(base, [row])
    before = ledger.read_bytes()

    resolved = herdr_lease.get_reply("legacy-1", base_dir=base)
    assert resolved is not None
    assert resolved["digest"] == row["digest"]

    new_body = "COMPLETED deadbeef\n\n## Evidence\n- new\n"
    _ = herdr_lease.record_reply(entry_for(new_body, record_id="row-new"), new_body, base_dir=base)

    assert ledger.read_bytes() == before, "the legacy ledger is read-only: never rewritten"
    ids = sorted(row_["id"] for row_ in herdr_lease.list_replies(limit=10, base_dir=base))
    assert ids == ["legacy-1", "row-new"]
    for record_id in ids:
        assert herdr_lease.get_reply(record_id, base_dir=base) is not None


def test_sidecar_row_wins_over_a_legacy_row_with_the_same_id(tmp_path: Path) -> None:
    base = tmp_path
    body = "COMPLETED deadbeef\n\n## Evidence\n- shared id\n"
    _ = write_body(base, "shared", body)
    _ = write_legacy(base, [legacy_row(body, record_id="shared", sender="impostor")])
    sidecar = base / REPLIES / "shared.yaml"
    _ = sidecar.write_text(
        yaml.safe_dump(legacy_row(body, record_id="shared"), sort_keys=False), encoding="utf-8"
    )

    rows = herdr_lease.list_replies(limit=10, base_dir=base)

    assert len(rows) == 1
    assert rows[0]["sender"] == "reviewer"


# ── F-C1: a row resolves only while its payload matches its digest ───────────────────


def test_get_reply_requires_the_payload_file(tmp_path: Path) -> None:
    """A hand-written row with no body file is listed, but never resolves."""
    base = tmp_path
    forged = legacy_row("COMPLETED deadbeef\n\n## Evidence\n- forged\n", record_id="forged")
    _ = write_legacy(base, [forged])

    assert [row["id"] for row in herdr_lease.list_replies(limit=10, base_dir=base)] == ["forged"]
    assert herdr_lease.get_reply("forged", base_dir=base) is None


def test_get_reply_requires_the_payload_digest(tmp_path: Path) -> None:
    """A tampered body stops resolving: the digest is what binds prompt text to a record."""
    base = tmp_path
    body = "COMPLETED deadbeef\n\n## Evidence\n- scanned clean\n"
    row = legacy_row(body, record_id="tampered")
    _ = write_body(base, "tampered", body)
    _ = write_legacy(base, [row])
    assert herdr_lease.get_reply("tampered", base_dir=base) is not None

    _ = (base / REPLIES / "tampered.md").write_text("COMPLETED deadbeef\n\n## Evidence\n- edited\n")

    assert herdr_lease.get_reply("tampered", base_dir=base) is None


# ── F3: the stored row is metadata only, drawn from a closed label vocabulary ────────


def test_the_stored_row_carries_no_payload_text(tmp_path: Path) -> None:
    base = tmp_path
    canaries = ("SECRETCANARYLINE1", "SECRETCANARYHEADING", "/home/u/.aws/credentials")
    payload = (
        f"COMPLETED {canaries[0]}\n\n"
        f"## Evidence {canaries[1]}\n"
        f"- scanned {canaries[2]} and tests/herdr/test_herdr_reply.py\n"
    )
    mapped, sha, _line = herdr_reply.parse_status_line(payload)
    shape, heading = herdr_reply.payload_shape(payload)
    entry = herdr_reply.build_reply_entry(
        payload,
        sender="reviewer",
        caller="orchestrator",
        ticket_id="#231",
        task_id="#231#task",
        in_reply_to="#231#task",
        mapped=mapped,
        sha=sha,
        shape=shape,
        evidence=heading,
    )

    stored = herdr_lease.record_reply(entry, payload, base_dir=base)

    assert set(stored) == {
        "id",
        "recorded_at",
        "sender",
        "caller",
        "ticket_id",
        "task_id",
        "in_reply_to",
        "status",
        "shape",
        "evidence",
        "sha",
        "digest",
        "bytes",
        "payload",
        "artifacts",
    }
    assert stored["status"] == "completed"
    assert stored["sha"] is None, "a non-hex second token is never stored as a sha"
    assert stored["artifacts"] == 2, "the row counts cited artifacts (no paths stored)"
    assert stored["evidence"] == "evidence"
    assert "status_line" not in stored
    dumped = yaml.safe_dump(stored, sort_keys=False)
    for canary in canaries:
        assert canary not in dumped


@pytest.mark.parametrize(
    ("heading", "label"),
    [
        ("Evidence", "evidence"),
        ("Verification", "verification"),
        ("Artifacts", "artifacts"),
        ("Test output", "tests output"),
        ("Gate output", "gate output"),
        ("Validation output", "validation output"),
        ("Benchmark results", "benchmark results"),
        ("Reproduced", "reproduction"),
        ("Gates", "gate"),
        ("CI", "ci"),
        ("What I ran", "section"),
        ("```", "fenced block"),
        (None, None),
    ],
)
def test_evidence_label_is_a_closed_vocabulary(heading: str | None, label: str | None) -> None:
    """The label names the section without copying arbitrary heading text into the ledger."""
    rendered = herdr_reply.evidence_label(heading)
    assert rendered == label
    for word in (rendered or "").split():
        assert word in herdr_reply.EVIDENCE_LABEL_WORDS
        assert len(rendered or "") <= 40


def test_a_heading_cannot_smuggle_text_into_the_label() -> None:
    canary = "SECRETCANARYWEIRD"
    for heading in (f"Evidence {canary}", f"{canary} Evidence", f"{canary}", f"Logs: {canary}"):
        label = herdr_reply.evidence_label(heading)
        assert canary not in (label or "")
        for word in (label or "").split():
            assert word in herdr_reply.EVIDENCE_LABEL_WORDS


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("deadbeef", "deadbeef"),
        ("abc", None),
        ("0" * 40, "0" * 40),
        ("0" * 41, None),
        ("deadbeez", None),
        ("ABCDEF12", None),
    ],
)
def test_sha_is_stored_only_when_it_is_hex(token: str, expected: str | None) -> None:
    payload = f"COMPLETED {token}\n\n## Evidence\n- 660 passed\n"
    mapped, sha, _line = herdr_reply.parse_status_line(payload)
    shape, heading = herdr_reply.payload_shape(payload)
    entry = herdr_reply.build_reply_entry(
        payload,
        sender="reviewer",
        caller="orchestrator",
        ticket_id="#231",
        task_id="#231#task",
        in_reply_to="#231#task",
        mapped=mapped,
        sha=sha,
        shape=shape,
        evidence=heading,
    )
    assert entry["sha"] == expected
