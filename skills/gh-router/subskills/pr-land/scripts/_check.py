"""The `--check` preflight: the CheckReport result and its two entry adapters.

`check_trailers_report` is the data-only twin the draft phase consumes; `check_trailers` is
the historical stdout adapter kept for the CLI entry and the tests. Both read mergeability
and the range authority through `_github`, and every subprocess call this module makes goes
through the qualified `_github.run_command(...)` lookup so the tests' single patch point
still intercepts. That scope is pr-land's own modules: the range/repo-root authority helper
in `lib/range_authority.py` spawns its own `subprocess.run` coverage, outside the seam — the
one spawn our own modules never make directly.
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import _github
from _errors import PrError, RefusalError
from _github import _digest_range_spec, resolve_base
from _squash import (
    build_squash_message,
    check_squash_body,
    check_squash_title,
    check_title_length,
    pr_co_author_trailers,
    resolve_squash_message,
)

_LIB_DIR = str(Path(__file__).resolve().parents[3] / "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)
from range_authority import RangeRefusal

__all__ = [
    "CheckReport",
    "check_trailers",
    "check_trailers_report",
]


@dataclass(frozen=True, slots=True)
class CheckReport:
    """Outcome of the --check preflight: gate code, trailers, and the PR it evaluated.

    ``body`` is the cleaned squash text a merge would commit; ``authored_body`` is
    the description exactly as supplied or fetched, so the draft can write the
    human-facing `pr_body.md` (Mermaid and `<details>` included) from it.
    """

    exit_code: int
    trailers: str = ""
    pr_number: str | None = None
    pr_url: str | None = None
    body: str = ""
    authored_body: str = ""
    note: str = ""


def check_trailers_report(
    repo: str,
    head_ref: str,
    body: str,
    body_supplied: bool,
    title: str = "",
    template_path: Path | None = None,
    cwd: Path | None = None,
    squash_message_override: str | None = None,
    squash_message_supplied: bool = False,
) -> CheckReport:
    """Run the --check merge gates and report the trailers a merge would append.

    Data-only twin of check_trailers: refusals and remediation still go to stderr,
    but the trailers and the resolved body come back in the report so the draft
    phase can write them to disk instead of stdout. Exit codes are unchanged.
    """
    owner = repo.split("/")[0]
    res = _github.run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls?head={owner}:{head_ref}&state=open",
            "--jq",
            ".[0].number",
        ],
        cwd=cwd,
    )
    if res.returncode != 0:
        raise PrError(
            f"failed to query open PR for head {head_ref}: {res.stderr.strip() or 'gh api failed'}"
        )
    found = res.stdout.strip()
    if not found or found == "null":
        if not body_supplied:
            print(f"no open PR for head {head_ref}", file=sys.stderr)
            return CheckReport(exit_code=2, note=f"no open PR for head {head_ref}")

        if title:
            try:
                check_squash_title(title, 9999)
            except RefusalError:
                return CheckReport(exit_code=1, body=body, authored_body=body)

        try:
            resolved_msg = resolve_squash_message(
                body,
                explicit=squash_message_override,
                supplied=squash_message_supplied,
                template_path=template_path,
            )
        except RefusalError:
            return CheckReport(exit_code=1, body=body, authored_body=body)

        try:
            check_squash_body(resolved_msg, title=title)
        except RefusalError:
            return CheckReport(exit_code=1, body=resolved_msg, authored_body=body)

        try:
            base = resolve_base(None, repo, cwd=cwd)
            digest_range = _digest_range_spec(base, head_ref, cwd=cwd)
        except RefusalError as exc:
            print(f"{exc}", file=sys.stderr)
            return CheckReport(exit_code=1, body=body, authored_body=body)
        except RangeRefusal:
            digest_range = None
        log_res: subprocess.CompletedProcess[str] | None = None
        if digest_range is not None:
            log_res = _github.run_command(
                ["git", "log", digest_range, "--pretty=format:\t%an\t%ae"],
                cwd=cwd,
            )
        if log_res is None or log_res.returncode != 0:
            log_res = _github.run_command(
                ["git", "log", "-1", "--pretty=format:\t%an\t%ae", head_ref],
                cwd=cwd,
            )
        tsv = log_res.stdout if log_res.returncode == 0 else ""

        merger = ""
        user_res = _github.run_command(["gh", "api", "user", "--jq", ".login"], cwd=cwd)
        if user_res.returncode == 0 and user_res.stdout.strip():
            merger = user_res.stdout.strip()
        if not merger:
            cfg_res = _github.run_command(["git", "config", "user.email"], cwd=cwd)
            if cfg_res.returncode == 0:
                merger = cfg_res.stdout.strip()

        new_trailers = pr_co_author_trailers(tsv, merger=merger, body=resolved_msg)
        note = (
            ""
            if new_trailers.strip()
            else f"no co-author trailers would be appended for {head_ref}"
        )
        return CheckReport(
            exit_code=0, trailers=new_trailers, body=resolved_msg, authored_body=body, note=note
        )

    num = found
    url = f"https://github.com/{repo}/pull/{num}"

    try:
        if title.strip():
            check_squash_title(title, num)
        else:
            check_title_length(title, num)
    except RefusalError:
        return CheckReport(exit_code=1, pr_number=num, pr_url=url, authored_body=body)

    if not body_supplied:
        body_res = _github.run_command(
            ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", '.body // ""'],
            cwd=cwd,
        )
        if body_res.returncode != 0:
            raise PrError(
                f"failed to fetch body for PR #{num}: {body_res.stderr.strip() or 'gh api failed'}"
            )
        body = body_res.stdout

    try:
        resolved_msg = resolve_squash_message(
            body,
            explicit=squash_message_override,
            supplied=squash_message_supplied,
            template_path=template_path,
        )
    except RefusalError:
        return CheckReport(exit_code=1, pr_number=num, pr_url=url, body=body, authored_body=body)

    try:
        check_squash_body(
            resolved_msg,
            title=title,
            pr_link=f"https://github.com/{repo}/pull/{num}",
        )
    except RefusalError:
        return CheckReport(
            exit_code=1, pr_number=num, pr_url=url, body=resolved_msg, authored_body=body
        )

    merger_res = _github.run_command(
        ["gh", "api", "user", "--jq", ".login"],
        cwd=cwd,
    )
    if merger_res.returncode != 0:
        raise PrError(
            f"failed to resolve current user login via gh api user: {merger_res.stderr.strip() or 'gh api user failed'}"
        )
    merger = merger_res.stdout.strip()

    tsv_res = _github.run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls/{num}/commits",
            "--jq",
            '.[] | [(.author.login // ""), (.commit.author.name // ""), (.commit.author.email // "")] | @tsv',
        ],
        cwd=cwd,
    )
    if tsv_res.returncode != 0:
        print(
            f"refusing --check: could not enumerate PR #{num} commit authors (check network / GH_TOKEN scopes); re-run",
            file=sys.stderr,
        )
        return CheckReport(
            exit_code=1, pr_number=num, pr_url=url, body=resolved_msg, authored_body=body
        )
    tsv = tsv_res.stdout

    try:
        _ = build_squash_message(resolved_msg, merger, tsv)
    except RefusalError:
        return CheckReport(
            exit_code=1, pr_number=num, pr_url=url, body=resolved_msg, authored_body=body
        )

    new_trailers = pr_co_author_trailers(tsv, merger=merger, body=resolved_msg)
    note = "" if new_trailers.strip() else f"no co-author trailers would be appended for #{num}"
    return CheckReport(
        exit_code=0,
        trailers=new_trailers,
        pr_number=num,
        pr_url=url,
        body=resolved_msg,
        authored_body=body,
        note=note,
    )


def check_trailers(
    repo: str,
    head_ref: str,
    body: str,
    body_supplied: bool,
    title: str = "",
    template_path: Path | None = None,
    cwd: Path | None = None,
    squash_message_override: str | None = None,
    squash_message_supplied: bool = False,
) -> int:
    """Backward-compatible --check gate: report the result, print trailers to stdout."""
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
    if report.exit_code == 0:
        if report.trailers.strip():
            print(report.trailers, end="")
        else:
            print(report.note, file=sys.stderr)
    return report.exit_code
