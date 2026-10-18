"""The `--check` draft phase: scaffold leaf plus gate facts, never stored state.

`run_draft_phase` turns `_check.check_trailers_report` plus the resolved landing
range into stdout facts (and the scaffold leaf when no body was supplied),
keeping commentary on stderr. Its subprocess reads go through the qualified
`_github.run_command(...)` lookup so the tests' single patch point still
intercepts them — the seam covers every subprocess call in pr-land's own
modules. The range/repo-root authority helper in `lib/range_authority.py`
spawns its own `subprocess.run` coverage, outside that seam.

The tool never reads an existing artifact to decide anything: a body-less
`--check` writes the scaffold only when the leaf is absent, and otherwise
reports the path plus a deterministic `stale` flag computed against the head
commit. Nothing is persisted about the phase: no stored payload, no scaffold hash,
and no output-directory flag.
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import _github
from _check import CheckReport, check_trailers_report
from _errors import PrError, RefusalError
from _github import _authority_resolve, resolve_base
from _options import PrOptions as PrOptions
from _squash import (
    CLOSES_LINE_RE,
    DEFAULT_TEMPLATE_PATH,
    FIX_TYPE,
    SQUASH_TITLE_RE,
)
from _status import CHECK_SCHEMA as CHECK_SCHEMA
from _status import SCAFFOLD_MARKER_PREFIX as SCAFFOLD_MARKER_PREFIX
from _status import TITLE_BUDGET as TITLE_BUDGET
from _status import TITLE_WORST_CASE_SUFFIX as TITLE_WORST_CASE_SUFFIX
from _status import ArtifactState as ArtifactState
from _status import TitleFacts as TitleFacts
from _status import artifact_stale as artifact_stale
from _status import body_site_with_line as body_site_with_line
from _status import display_path as display_path
from _status import make_refusal as make_refusal
from _status import resolve_artifact_path as resolve_artifact_path

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
    "_draft_range",
    "build_scaffold",
    "cap_draft_body",
    "draft_commits",
    "run_draft_phase",
]


DRAFT_BODY_MAX_LINES = 15
DRAFT_BODY_PLACEHOLDER = (
    "<!-- draft: no authored PR body resolved; replace this file with the curated description -->\n"
    "## Summary\n\n## What Changed\n\n## Blast Radius & Safety\n\n## Evidence\n"
)


# The scaffold leaf (.lsz/gh-router/<slug>.md): template shape + mechanical facts + sentinels.
# The generator writes no subjective prose. The marker names the head commit the
# scaffold was generated from, so a later run reports staleness without deciding
# anything from the artifact's bytes.
def _scaffold_marker(head_sha: str) -> str:
    return f"{SCAFFOLD_MARKER_PREFIX}{head_sha} -->"


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
        except RangeRefusal:
            continue
        except MalformedSpec:
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
    except PrError:
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
    head_sha: str = "",
) -> str:
    """The scaffold leaf (.lsz/gh-router/<slug>.md): template shape + mechanical facts + unfilled sentinels.

    The generator writes no subjective prose. Over the installed template (or the
    placeholder skeleton when absent) it swaps the unchosen Door literal for a `<FILL:>`
    sentinel, injects the range fact line under Summary and a Root Cause guidance comment,
    and appends the detected closing lines or a visible FILL Closes slot. The marker
    top line names the head commit the scaffold was generated from.
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
    return f"{_scaffold_marker(head_sha)}\n{body}"


def _scaffold_template_text(template_path: Path | None, cwd: Path | None) -> str:
    path = template_path if template_path is not None else DEFAULT_TEMPLATE_PATH
    if cwd is not None and not path.is_absolute():
        path = cwd / path
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return DRAFT_BODY_PLACEHOLDER


@dataclass
class CheckPayload:
    """The machine-readable `--check` JSON wire payload; `to_dict()` emits the check schema.

    Kept distinct from `_check.CheckReport` on purpose: `CheckReport` is the
    gate outcome the draft phase branches on (exit code, trailers, body,
    reason, site); this type is the `--json` rendering of that outcome plus
    the invocation facts (schema, repo, head, base, title, artifact, commits).
    `_emit_gate_facts` builds this payload from the report — builders set
    fields, the renderer reads attributes, so no key can be missing at render.
    """

    schema: str = CHECK_SCHEMA
    repo: str = ""
    head: str = ""
    base: str | None = None
    exit_code: int = 0
    title: TitleFacts = field(default_factory=TitleFacts)
    body_site: str = ""
    artifact: ArtifactState = field(default_factory=ArtifactState)
    refusals: list[dict[str, str]] = field(default_factory=list)
    squash_body_preview: str = ""
    scaffold: str = ""
    scaffold_written: bool = False
    commits: int = 0
    trailers: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "repo": self.repo,
            "head": self.head,
            "base": self.base,
            "exit_code": self.exit_code,
            "title": self.title.to_dict(),
            "body_site": self.body_site,
            "artifact": self.artifact.to_dict(),
            "refusals": [dict(entry) for entry in self.refusals],
            "squash_body_preview": self.squash_body_preview,
            "scaffold": self.scaffold,
            "scaffold_written": self.scaffold_written,
            "commits": self.commits,
            "trailers": self.trailers,
        }


def _emit_check_json(payload: dict[str, object]) -> None:
    """Print the machine-readable `--check` report on stdout."""
    print(json.dumps(payload, indent=2))


def _emit_gate_facts(
    report: CheckReport,
    *,
    options: PrOptions,
    repo: str,
    head_ref: str,
    base: str | None,
    title: str,
    title_facts: TitleFacts,
    body_site: str,
    body: str,
    display: str,
    artifact_path: Path,
    sha: str,
    commits: list[dict[str, object]],
    hint: str,
) -> int:
    """Emit the gate facts for a description the caller or the PR supplied.

    Nothing is persisted on this path: facts on stdout (`--json` for machine
    reading), commentary on stderr, the gate verdict as the exit code. A
    `refusals[]` entry on stderr (exit 1 or 2) carries reason, remedy, and site.
    """
    if report.exit_code == 0 and report.note:
        print(report.note, file=sys.stderr)
    preview = report.body.strip("\n") if report.exit_code == 0 else ""
    trailer_count = sum(1 for line in report.trailers.splitlines() if line.strip())
    refusals: list[dict[str, str]] = []
    if report.exit_code != 0:
        reason = report.reason or "one or more merge gates refused"
        site = report.site or body_site_with_line(body_site, body)
        refusals = [
            make_refusal(
                "body_missing" if report.exit_code == 2 else "gate_refused",
                reason,
                "see the gate prose on stderr, fix the defect, then re-run",
                site,
            )
        ]
        print(json.dumps({"refusals": refusals}, indent=2), file=sys.stderr)
    if options.json_output:
        _emit_check_json(
            CheckPayload(
                repo=repo,
                head=head_ref,
                base=base,
                exit_code=report.exit_code,
                title=title_facts,
                body_site=body_site,
                artifact=ArtifactState(path=display, stale=artifact_stale(artifact_path, sha)),
                refusals=refusals,
                squash_body_preview=preview,
                commits=len(commits),
                trailers=trailer_count,
            ).to_dict()
        )
    else:
        derived = not options.title_supplied
        print(f"commits: {len(commits)}")
        print(f"trailers: {trailer_count}")
        print(
            f"title ({'derived' if derived else 'from --title'}): "
            f"{title!r} {len(title)}/{TITLE_BUDGET} chars "
            f"(worst case {title_facts.worst_case_chars}/{TITLE_BUDGET} with ` (#99999)`)"
        )
        if preview.strip():
            print("squash_body_preview:")
            print(preview)
        else:
            print("squash_body_preview: (none — no usable body)")
        print(f"hint: {hint}")
    return report.exit_code


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
    """Run the `--check` gate and emit its facts; write the scaffold leaf when apt.

    Facts go to stdout — counts, the title facts, the squash preview, and the
    scaffold payload when no body was supplied (`--json` for machine reading) —
    commentary goes to stderr. Nothing is persisted except the body-less
    scaffold: written only when the leaf is absent (`--force-scaffold`
    overwrites deliberately); when the leaf exists the tool writes nothing and
    reports the path plus `stale` computed against the head commit. The scaffold
    never feeds the gate — the no-body verdict stays exit 2. A `refusals[]`
    entry on stderr (exit 1 or 2) carries reason, remedy, and site.
    """
    artifact_path = resolve_artifact_path(options.out, head_ref, cwd)
    display = display_path(artifact_path, cwd)
    if options.body_file is not None:
        body_site = f"--body-file {options.body_file}"
    elif options.body is not None:
        body_site = "--body"
    else:
        body_site = display
    derived_title = not options.title_supplied
    title_facts = TitleFacts(text=title, derived=derived_title)

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
    sha = _github.head_sha(cwd)
    hint = (
        f"body: keep {artifact_path.name} in the repo's installed PR template shape "
        "(pr-enhance owns the prose); squash: author a separate overview in "
        "--squash-message-file, <=5 bullets (Core + Root for fix + Risk:Door + Proof + Links), "
        "drop wip/fixup trivia, strip Mermaid/details/checklist; "
        f"then land with --body-file {display} "
        '(spec: GLOSSARY.md "Curated Squash Message" + pr-land SKILL.md Squash Shape)'
    )

    if not body_supplied:
        # An open PR already carries the description: gate on the fetched body
        # and persist nothing. Only when no PR body exists does the scaffold path
        # below run (exit 2).
        probe = check_trailers_report(
            repo=repo,
            head_ref=head_ref,
            body="",
            body_supplied=False,
            title=title,
            template_path=template_path,
            cwd=cwd,
            squash_message_override=squash_message_override,
            squash_message_supplied=squash_message_supplied,
            title_supplied=options.title_supplied,
        )
        if probe.exit_code != 2:
            return _emit_gate_facts(
                probe,
                options=options,
                repo=repo,
                head_ref=head_ref,
                base=base,
                title=title,
                title_facts=title_facts,
                body_site=f"PR #{probe.pr_number}" if probe.pr_number else body_site,
                body=probe.authored_body,
                display=display,
                artifact_path=artifact_path,
                sha=sha,
                commits=commits,
                hint=hint,
            )
        refusals = [
            make_refusal(
                "body_missing",
                "no description supplied; opening a PR requires one",
                f"fill every <FILL:> slot in {display} (or delete the Closes slot), "
                f"then re-run --check --body-file {display}",
                body_site,
            )
        ]
        try:
            existing = (
                artifact_path.read_text(encoding="utf-8") if artifact_path.is_file() else None
            )
        except OSError:
            existing = None
        if existing is None or options.force_scaffold:
            scaffold = build_scaffold(
                title=title,
                head_ref=head_ref,
                commits=commits,
                range_resolution=range_resolution,
                template_text=_scaffold_template_text(template_path, cwd),
                cwd=cwd,
                head_sha=sha,
            )
            try:
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                _ = artifact_path.write_text(scaffold, encoding="utf-8")
            except OSError as exc:
                raise PrError(
                    f"cannot write scaffold leaf under {artifact_path.parent}: {exc}"
                ) from exc
            print(
                f"scaffold: wrote the candidate body at {display}; fill every <FILL:> slot "
                "(or delete the Closes comment), then re-run --check --body-file it",
                file=sys.stderr,
            )
            print(json.dumps({"refusals": refusals}, indent=2), file=sys.stderr)
            if options.json_output:
                _emit_check_json(
                    CheckPayload(
                        repo=repo,
                        head=head_ref,
                        base=base,
                        exit_code=2,
                        title=title_facts,
                        body_site=body_site,
                        artifact=ArtifactState(path=display, stale=False),
                        refusals=refusals,
                        scaffold=scaffold,
                        scaffold_written=True,
                        commits=len(commits),
                    ).to_dict()
                )
            else:
                print(f"commits: {len(commits)}")
                print(f"body: {display}")
                print(f"hint: {hint}")
                print(scaffold, end="" if scaffold.endswith("\n") else "\n")
            return 2
        stale = artifact_stale(artifact_path, sha)
        print(
            f"note: scaffold leaf {display} already exists; wrote nothing "
            "(re-run with --force-scaffold to regenerate, --out another leaf, or reuse it as-is)",
            file=sys.stderr,
        )
        print(json.dumps({"refusals": refusals}, indent=2), file=sys.stderr)
        if options.json_output:
            _emit_check_json(
                CheckPayload(
                    repo=repo,
                    head=head_ref,
                    base=base,
                    exit_code=2,
                    title=title_facts,
                    body_site=body_site,
                    artifact=ArtifactState(path=display, stale=stale),
                    refusals=refusals,
                    commits=len(commits),
                ).to_dict()
            )
        else:
            print(f"commits: {len(commits)}")
            print(f"body: {display}")
            print(f"stale: {str(stale).lower()}")
            print(f"hint: {hint}")
        return 2

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
        title_supplied=options.title_supplied,
    )
    return _emit_gate_facts(
        report,
        options=options,
        repo=repo,
        head_ref=head_ref,
        base=base,
        title=title,
        title_facts=title_facts,
        body_site=body_site,
        body=body,
        display=display,
        artifact_path=artifact_path,
        sha=sha,
        commits=commits,
        hint=hint,
    )
