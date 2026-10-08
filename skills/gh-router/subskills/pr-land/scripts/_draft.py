"""The `--check` draft phase: `draft.json` + `pr_body.md` for curl-free curation.

`run_draft_phase` turns `_check.check_trailers_report` plus the resolved landing range into
the two artifacts, keeping stdout to counts, the paths, and one curation hint. Its
subprocess reads go through the qualified `_github.run_command(...)` lookup so the tests'
single patch point still intercepts them — the seam covers every subprocess call in pr-land's
own modules. The range/repo-root authority helper in `lib/range_authority.py` spawns its own
`subprocess.run` coverage, outside that seam.
"""

import json
import sys
from pathlib import Path

import _github
from _check import CheckReport, check_trailers_report
from _errors import PrError, RefusalError
from _github import _authority_resolve, resolve_base
from _options import PrOptions
from _squash import insert_trailers

_LIB_DIR = str(Path(__file__).resolve().parents[3] / "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)
from range_authority import (
    MalformedSpec,
    RangeRefusal,
    RangeResolution,
    find_repo_root,
    get_commit_summary,
)

__all__ = [
    "DRAFT_BODY_MAX_LINES",
    "DRAFT_BODY_PLACEHOLDER",
    "DRAFT_OUT_DIR",
    "DRAFT_SCHEMA",
    "_draft_dirty",
    "_draft_range",
    "build_draft_payload",
    "cap_draft_body",
    "draft_commits",
    "resolve_out_dir",
    "run_draft_phase",
]


DRAFT_OUT_DIR = Path(".lsz") / "tmp"
DRAFT_SCHEMA = "gh-router/pr-land/draft@1"

DRAFT_BODY_MAX_LINES = 15
DRAFT_BODY_PLACEHOLDER = (
    "<!-- draft: no authored PR body resolved; replace this file with the curated description -->\n"
    "## Summary\n\n## What Changed\n\n## Blast Radius & Safety\n\n## Evidence\n"
)


def resolve_out_dir(out_dir: Path | None, cwd: Path | None = None) -> Path:
    """Resolve the draft output directory (default <repo-root>/.lsz/tmp).

    An explicit --out-dir resolves against the working directory; the default
    resolves against the repository root so every --check in a checkout lands in
    the same place.
    """
    base = cwd or Path.cwd()
    if out_dir is not None:
        target = out_dir if out_dir.is_absolute() else base / out_dir
        return target.resolve()
    try:
        root = find_repo_root(base)
    except RuntimeError:
        root = base.resolve()
    return (root / DRAFT_OUT_DIR).resolve()


def cap_draft_body(text: str, max_lines: int = DRAFT_BODY_MAX_LINES) -> tuple[str, int]:
    """Cap a commit body at *max_lines*; return (capped text, omitted line count)."""
    lines = text.strip("\n").splitlines()
    if len(lines) <= max_lines:
        return ("\n".join(lines), 0)
    return ("\n".join(lines[:max_lines]), len(lines) - max_lines)


def draft_commits(
    range_resolution: RangeResolution | None, cwd: Path | None = None
) -> list[dict[str, object]]:
    """One row per range commit: full SHA pointer, subject, and a capped body."""
    if range_resolution is None:
        return []
    base = cwd or Path.cwd()
    try:
        root = find_repo_root(base)
    except RuntimeError:
        root = base.resolve()
    rows: list[dict[str, object]] = []
    for sha in range_resolution.commits:
        summary = get_commit_summary(root, sha) or {}
        body_text, omitted = cap_draft_body(str(summary.get("body", "")))
        rows.append(
            {
                "sha": sha,
                "short_sha": str(summary.get("sha", sha[:7])),
                "author": str(summary.get("author", "")),
                "subject": str(summary.get("subject", "")),
                "body": body_text,
                "body_lines": len(body_text.splitlines()) if body_text else 0,
                "body_omitted_lines": omitted,
            }
        )
    return rows


def _draft_range(
    base: str | None, head_ref: str, cwd: Path | None = None
) -> RangeResolution | None:
    """Resolve the landing range through the shared authority; None when it cannot."""
    specs = [f"{base}..{head_ref}"] if base else []
    specs.append(head_ref)
    for spec in specs:
        try:
            return _authority_resolve(spec, "..", cwd)
        except RangeRefusal, MalformedSpec:
            continue
    return None


def build_draft_payload(
    *,
    repo: str,
    head_ref: str,
    base: str | None,
    title: str,
    report: CheckReport,
    range_resolution: RangeResolution | None,
    commits: list[dict[str, object]],
    counts: dict[str, int],
    dirty: dict[str, list[str]],
    squash_body: str,
    draft_path: Path,
    body_path: Path,
    hint: str,
) -> dict[str, object]:
    """Assemble the JSON-only draft payload (no YAML view, no full stdout dump)."""
    return {
        "schema": DRAFT_SCHEMA,
        "repo": repo,
        "head": head_ref,
        "base": base,
        "title": title,
        "pr_number": report.pr_number,
        "pr_url": report.pr_url,
        "status": "ok" if report.exit_code == 0 else "refused",
        "exit_code": report.exit_code,
        "note": report.note,
        "range": range_resolution.to_dict() if range_resolution is not None else None,
        "counts": counts,
        "commits": commits,
        "dirty": dirty,
        "trailers": report.trailers,
        "squash_body": squash_body,
        "draft_path": str(draft_path),
        "body_path": str(body_path),
        "hint": hint,
    }


def _draft_dirty(cwd: Path | None = None) -> dict[str, list[str]]:
    """Advisory working-tree reading for draft.json; empty lists when clean or unreadable."""
    empty: dict[str, list[str]] = {"porcelain": [], "diff_stat": []}
    try:
        root = find_repo_root(cwd or Path.cwd())
    except RuntimeError:
        root = (cwd or Path.cwd()).resolve()
    try:
        porcelain = [
            line
            for line in _github.run_command(
                ["git", "--no-optional-locks", "status", "--porcelain"],
                cwd=root,
            ).stdout.splitlines()
            if line.strip()
        ]
        if not porcelain:
            return empty
        diff_stat = [
            line
            for line in _github.run_command(
                ["git", "--no-optional-locks", "diff", "HEAD", "--stat", "--", "."],
                cwd=root,
            ).stdout.splitlines()
            if line.strip()
        ]
    except PrError, OSError, RuntimeError:
        return empty
    return {"porcelain": porcelain[:20], "diff_stat": diff_stat[-8:]}


def run_draft_phase(
    *,
    options: PrOptions,
    repo: str,
    head_ref: str,
    title: str,
    body: str,
    body_supplied: bool,
    squash_message_override: str | None,
    squash_message_supplied: bool,
    template_path: Path | None = None,
    cwd: Path | None = None,
) -> int:
    """Emit draft.json + pr_body.md for --check, keep stdout small, return the gate code.

    Every --check run writes both files, even a refused one: the gate verdict is
    the exit code (and stderr), while the full text stays on disk. `pr_body.md`
    carries the authored description (Mermaid and `<details>` kept) plus the
    trailers a merge would append; `draft.json`'s `squash_body` is the cleaned
    text a merge would commit. stdout carries only counts, the two paths, and one
    curation hint.
    """
    out_dir = resolve_out_dir(options.out_dir, cwd=cwd)
    draft_path = out_dir / "draft.json"
    body_path = out_dir / "pr_body.md"

    report = check_trailers_report(
        repo=repo,
        head_ref=head_ref,
        body=body,
        body_supplied=body_supplied,
        title=title,
        template_path=template_path,
        cwd=cwd,
        squash_message_override=squash_message_override,
        squash_message_supplied=squash_message_supplied,
    )

    if report.exit_code == 0 and report.note:
        print(report.note, file=sys.stderr)

    squash_body = report.body.strip("\n")
    authored_body = report.authored_body.strip("\n")
    if report.exit_code == 0 and authored_body:
        body_text = insert_trailers(authored_body, report.trailers)
    elif authored_body:
        body_text = authored_body + "\n"
    else:
        body_text = DRAFT_BODY_PLACEHOLDER
    if not body_text.endswith("\n"):
        body_text += "\n"

    try:
        base: str | None = resolve_base(options.base, repo, cwd=cwd)
    except RefusalError as exc:
        print(f"{exc}", file=sys.stderr)
        base = None

    range_resolution = _draft_range(base, head_ref, cwd)
    commits = draft_commits(range_resolution, cwd)
    if not commits and not options.title_supplied and title:
        print(
            f"warning: no unique commits in range; draft title {title!r} is a guess "
            "-- pass --title explicitly",
            file=sys.stderr,
        )
    dirty = _draft_dirty(cwd)
    dirty_files = len(dirty["porcelain"])

    counts = {
        "commits": len(commits),
        "only_in_base": range_resolution.counts.only_in_base if range_resolution else 0,
        "trailers": sum(1 for line in report.trailers.splitlines() if line.strip()),
        "body_lines": len(body_text.splitlines()),
        "dirty_files": dirty_files,
    }
    hint = (
        f"curate {body_path.name} to <=5 bullets "
        "(Core + Root for fix + Risk:Door + Proof + Links), "
        "drop wip/fixup trivia, strip Mermaid/details/checklist; "
        f"then land with --body-file {body_path} "
        '(spec: CONTEXT.md "Curated Squash Message" + pr-land SKILL.md Squash Shape)'
    )
    payload = build_draft_payload(
        repo=repo,
        head_ref=head_ref,
        base=base,
        title=title,
        report=report,
        range_resolution=range_resolution,
        commits=commits,
        counts=counts,
        squash_body=squash_body,
        dirty=dirty,
        draft_path=draft_path,
        body_path=body_path,
        hint=hint,
    )

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        _ = draft_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        _ = body_path.write_text(body_text, encoding="utf-8")
    except OSError as exc:
        raise PrError(f"cannot write draft files under {out_dir}: {exc}") from exc

    print(f"commits: {counts['commits']}")
    print(f"trailers: {counts['trailers']}")
    print(f"draft: {draft_path}")
    print(f"body: {body_path}")
    print(f"hint: {hint}")
    return report.exit_code
