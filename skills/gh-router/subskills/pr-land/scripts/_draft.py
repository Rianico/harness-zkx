"""The `--check` draft phase: `draft.json` + `pr_body.md` for curl-free curation.

`run_draft_phase` turns `_check.check_trailers_report` plus the resolved landing range into
the two artifacts, keeping stdout to counts, the paths, and one curation hint. Its
subprocess reads go through the qualified `_github.run_command(...)` lookup so the tests'
single patch point still intercepts them — the seam covers every subprocess call in pr-land's
own modules. The range/repo-root authority helper in `lib/range_authority.py` spawns its own
`subprocess.run` coverage, outside that seam.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

import _github
from _check import CheckReport, check_trailers_report
from _errors import PrError, RefusalError
from _github import _authority_resolve, resolve_base
from _options import PrOptions
from _squash import (
    CLOSES_LINE_RE,
    DEFAULT_TEMPLATE_PATH,
    FIX_TYPE,
    SQUASH_TITLE_RE,
    insert_trailers,
)

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
    "SCAFFOLD_SIGNATURE_PREFIX",
    "_draft_dirty",
    "_draft_range",
    "build_draft_payload",
    "build_scaffold",
    "cap_draft_body",
    "draft_commits",
    "is_untouched_scaffold",
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

# The candidate pr_body.md scaffold: template shape + mechanical facts + sentinels, signed
# by the sha256 of the lines below its top line so a later --check tells untouched from
# hand-edited. The generator writes no subjective prose.
SCAFFOLD_SIGNATURE_PREFIX = "<!-- draft: scaffold sha256="
_SCAFFOLD_SIGNATURE_SUFFIX = " -->"
_SCAFFOLD_DOOR = "**Door:** <FILL: one-way | two-way>"
_SCAFFOLD_CLOSES_COMMENT = "<!-- Closes #<FILL: issue number or delete> -->"
_SCAFFOLD_SUMMARY_HEADING_RE = re.compile(r"^##\s+Summary\b", re.IGNORECASE)
_SCAFFOLD_ROOT_HEADING_RE = re.compile(r"^##\s+Root Cause\b", re.IGNORECASE)
_SCAFFOLD_BLAST_HEADING_RE = re.compile(r"^##\s+Blast Radius\b", re.IGNORECASE)
# The installed template's unchosen Door literal, replaced by the FILL sentinel. The
# shipped bold puts the colon INSIDE the markers (`**Door:** one-way / two-way`), so the
# asterisks sit on both sides of the colon.
_SCAFFOLD_TEMPLATE_DOOR_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?[*]{0,2}Door[*]{0,2}:[ \t]*[*]{0,2}[ \t]*"
    r"one-way[ \t]*/[ \t]*two-way[ \t]*[*]{0,2}[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
# A bare number delimited in the branch name (feat/260-x, issue-260, 260-fix).
_BRANCH_ISSUE_RE = re.compile(r"(?:^|[/_.\-])(\d{1,6})(?:[/_.\-]|$)")


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


def _diff_facts(range_resolution: RangeResolution | None, cwd: Path | None) -> tuple[int, int, int]:
    """(+additions, -deletions, files touched) across the landing range; zeros when unreadable.

    Mechanical only: `git diff --numstat <merge-base> <head>` through the tests' single
    `_github.run_command` seam. A binary file counts as touched with no line delta.
    """
    if range_resolution is None:
        return (0, 0, 0)
    base = cwd or Path.cwd()
    try:
        root = find_repo_root(base)
    except RuntimeError:
        root = base.resolve()
    try:
        out = _github.run_command(
            [
                "git",
                "--no-optional-locks",
                "diff",
                "--numstat",
                range_resolution.merge_base,
                range_resolution.head_ref,
            ],
            cwd=root,
        ).stdout
    except PrError, OSError, RuntimeError:
        return (0, 0, 0)
    additions = deletions = files = 0
    for line in out.splitlines():
        fields = line.split("\t")
        if len(fields) < 3:
            continue
        files += 1
        if fields[0].isdigit():
            additions += int(fields[0])
        if fields[1].isdigit():
            deletions += int(fields[1])
    return (additions, deletions, files)


def _scaffold_closes(head_ref: str, commits: list[dict[str, object]]) -> list[str]:
    """Detected closing lines: commit-body `Closes #NN` first, then the branch-name number.

    Purely mechanical: a `Closes #12` line in any (capped) commit body wins; failing that a
    bare delimited number in the branch name. With neither, the caller leaves the visible
    FILL slot for the author to fill or delete.
    """
    numbers: list[str] = []
    for commit in commits:
        for line in str(commit.get("body", "")).splitlines():
            if CLOSES_LINE_RE.match(line.strip()):
                for number in re.findall(r"#(\d+)", line):
                    if number not in numbers:
                        numbers.append(number)
    if not numbers:
        match = _BRANCH_ISSUE_RE.search(head_ref.rsplit("/", 1)[-1])
        if match is not None:
            numbers.append(match.group(1))
    return [f"Closes #{number}" for number in numbers]


def _scaffold_root_guidance(title: str) -> str:
    match = SQUASH_TITLE_RE.match(title.strip())
    is_fix = match is not None and match.group("type").casefold() == FIX_TYPE
    if is_fix:
        return (
            "<!-- Root Cause is REQUIRED for a fix: state why the bug happened, "
            "not just what changed. -->"
        )
    return "<!-- Root Cause: keep only for a fix; delete this section for other change types. -->"


def build_scaffold(
    *,
    title: str,
    head_ref: str,
    commits: list[dict[str, object]],
    range_resolution: RangeResolution | None,
    template_text: str,
    cwd: Path | None = None,
) -> str:
    """The candidate pr_body.md: template shape + mechanical facts + unfilled sentinels.

    The generator writes no subjective prose. Over the installed template (or the
    placeholder skeleton when absent) it swaps the unchosen Door literal for a `<FILL:>`
    sentinel, injects the range fact line under Summary and a Root Cause guidance comment,
    and appends the detected closing lines or a visible FILL Closes slot. The result is
    signed: the top line carries the sha256 of every line below it.
    """
    additions, deletions, files = _diff_facts(range_resolution, cwd)
    fact_line = (
        f"<!-- Range: {len(commits)} commits, +{additions}/-{deletions} across {files} files -->"
    )
    closes = _scaffold_closes(head_ref, commits)
    out: list[str] = []
    door_placed = False
    for line in template_text.rstrip("\n").splitlines():
        if _SCAFFOLD_TEMPLATE_DOOR_RE.match(line):
            out.append(_SCAFFOLD_DOOR)
            door_placed = True
            continue
        out.append(line)
        if _SCAFFOLD_SUMMARY_HEADING_RE.match(line):
            out.append(fact_line)
        elif _SCAFFOLD_ROOT_HEADING_RE.match(line):
            out.append(_scaffold_root_guidance(title))
    if not door_placed:
        for index, line in enumerate(out):
            if _SCAFFOLD_BLAST_HEADING_RE.match(line):
                _ = out.insert(index + 1, "")
                out.insert(index + 2, _SCAFFOLD_DOOR)
                break
    out.append("")
    out.extend(closes if closes else [_SCAFFOLD_CLOSES_COMMENT])
    body = "\n".join(out) + "\n"
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"{SCAFFOLD_SIGNATURE_PREFIX}{digest}{_SCAFFOLD_SIGNATURE_SUFFIX}\n{body}"


def is_untouched_scaffold(text: str) -> bool:
    """True when *text*'s top line signs the bytes below it with a matching scaffold hash."""
    first, sep, rest = text.partition("\n")
    if (
        not sep
        or not first.startswith(SCAFFOLD_SIGNATURE_PREFIX)
        or not first.endswith(_SCAFFOLD_SIGNATURE_SUFFIX)
    ):
        return False
    digest = first[len(SCAFFOLD_SIGNATURE_PREFIX) : -len(_SCAFFOLD_SIGNATURE_SUFFIX)]
    return hashlib.sha256(rest.encode("utf-8")).hexdigest() == digest


def _scaffold_template_text(template_path: Path | None, cwd: Path | None) -> str:
    path = template_path if template_path is not None else DEFAULT_TEMPLATE_PATH
    if cwd is not None and not path.is_absolute():
        path = cwd / path
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return DRAFT_BODY_PLACEHOLDER


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

    When no body was supplied the file is the candidate scaffold (see
    `build_scaffold`): written when absent, untouched (signature matches), or
    `--force-scaffold` is passed, and preserved byte-for-byte when the author has
    hand-edited it. The scaffold never feeds the gate — the no-body verdict stays
    the refusal it always was.
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

    authored_body = report.authored_body.strip("\n")
    scaffold_written = False
    if report.exit_code == 0 and authored_body:
        body_text = insert_trailers(authored_body, report.trailers)
    elif authored_body:
        body_text = authored_body + "\n"
    else:
        scaffold = build_scaffold(
            title=title,
            head_ref=head_ref,
            commits=commits,
            range_resolution=range_resolution,
            template_text=_scaffold_template_text(template_path, cwd),
            cwd=cwd,
        )
        existing: str | None
        try:
            existing = body_path.read_text(encoding="utf-8") if body_path.is_file() else None
        except OSError:
            existing = None
        if options.force_scaffold or existing is None or is_untouched_scaffold(existing):
            body_text = scaffold
            scaffold_written = True
        else:
            body_text = existing
    if not body_text.endswith("\n"):
        body_text += "\n"

    counts = {
        "commits": len(commits),
        "only_in_base": range_resolution.counts.only_in_base if range_resolution else 0,
        "trailers": sum(1 for line in report.trailers.splitlines() if line.strip()),
        "body_lines": len(body_text.splitlines()),
        "dirty_files": dirty_files,
    }
    hint = (
        f"body: keep {body_path.name} in the repo's installed PR template shape "
        "(pr-enhance owns the prose); squash: author a separate overview in "
        "--squash-message-file, <=5 bullets (Core + Root for fix + Risk:Door + Proof + Links), "
        "drop wip/fixup trivia, strip Mermaid/details/checklist; "
        f"then land with --body-file {body_path} "
        '(spec: GLOSSARY.md "Curated Squash Message" + pr-land SKILL.md Squash Shape)'
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

    if scaffold_written:
        print(
            f"scaffold: wrote the candidate body at {body_path}; fill every <FILL: …> slot "
            "(or delete the Closes comment), then re-run --check --body-file it",
            file=sys.stderr,
        )

    print(f"commits: {counts['commits']}")
    print(f"trailers: {counts['trailers']}")
    print(f"draft: {draft_path}")
    print(f"body: {body_path}")
    print(f"hint: {hint}")
    return report.exit_code
