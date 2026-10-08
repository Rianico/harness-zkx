"""Copy detector + strict shape gate on the explicit squash message (T2).

The landing contract splits the two artifacts: the PR body keeps the full detail
(Mermaid and `<details>` included, for humans), and the squash message is the
curated overview. T1 made the explicit `--squash-message` / `--squash-message-file`
the only way to merge, so the strict half lives there: a description pasted back
refuses as *mechanic copy* (the detector), and the overview shape holds (contract
headings only, no checkbox/Mermaid/token, <= 15 lines, <= 5 bullets). The `--check`
preview path keeps its strip behaviour, pinned here so the split cannot invert.

Fixture: the repo's own shipped PR template, comments dropped and its slots filled
(the #220 body shape). The same template-shaped text in both slots refuses.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.git_env import git_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"
TEMPLATE = REPO_ROOT / ".github" / "pull_request_template.md"

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

import _github as github_mod  # noqa: E402
from pr import (  # noqa: E402
    COPY_OVERLAP_THRESHOLD,
    COPY_TOKEN_FLOOR,
    SQUASH_MESSAGE_MAX_LINES,
    RefusalError,
    _copy_tokens,
    _fenced_line_mask,
    check_explicit_squash_message,
    check_squash_body,
    clean_squash_body,
    copy_body_coverage,
    copy_overlap,
    merge_pr,
    refuse_mechanic_copy,
    resolve_squash_message,
)

# --- fixtures ---


def _template_shaped_body() -> str:
    """The shipped template, comments dropped and every slot filled in.

    This is the #220 body shape: `## Summary` prose, a `## What Changed` bullet, the
    `Door:`/`Rollback / containment:` pair, pasted Evidence, and the procedural
    sections a real description carries.
    """
    raw = TEMPLATE.read_text(encoding="utf-8")
    body = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
    fills = {
        "-": "- bound the retry loop, cap the poll budget, and fail fast on a conflicting head",
        "**Door:** one-way / two-way": "**Door:** two-way",
        "**Downstream consumers:**": (
            "**Downstream consumers:** pr-enhance, pr-refine, gh-release share the preflight"
        ),
        "**Breaking changes:**": "**Breaking changes:** none; the two flags stay additive",
        "**Data / state invariants:**": (
            "**Data / state invariants:** draft.json keeps its published shape"
        ),
        "**Rollback / containment:**": ("**Rollback / containment:** revert the squash commit"),
        "**Before (command + output):**": "**Before (command + output):** 3 failed -> 0 passed",
        "**After (command + output):**": "**After (command + output):** 0 failed -> 3 passed",
    }
    filled = "\n".join(fills.get(line.strip(), line) for line in body.splitlines())
    return filled.replace(
        "## Summary\n",
        "## Summary\nThe draft phase and the squash gate landed together, so one preflight\n"
        "now decides every landing and the overview stays separate from the description.\n",
        1,
    )


def _light_paraphrase(body: str) -> str:
    """The same body with four words reworded: near-identical, not identical."""
    reworded = body.replace(
        "bound the retry loop, cap the poll budget, and fail fast on a conflicting head",
        "bound the retry loop, cap the poll budget, and fail fast on a conflicting branch",
    )
    reworded = reworded.replace(
        "so one preflight\nnow decides every landing",
        "so a single preflight\nnow decides each landing",
    )
    assert reworded != body
    return reworded


SHORT_BODY = "## Summary\nreal change lands now\n"
LONG_BODY = _template_shaped_body()


# --- the copy detector ---


def test_copy_detector_scores_identical_text_as_full_overlap(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Identical texts share every shingle: 1.0, and the refusal names the spec.

    Mutation: flip `overlap > COPY_OVERLAP_THRESHOLD` to `overlap >= 2.0` in
    `refuse_mechanic_copy` -> no refusal, the `pytest.raises` block fails.
    """
    body = LONG_BODY
    assert copy_overlap(body, body) == 1.0
    with pytest.raises(RefusalError):
        refuse_mechanic_copy(body, body)
    err = capsys.readouterr().err
    assert "mechanic copy" in err
    assert "CONTEXT.md" in err and "pr-land/SKILL.md" in err


def test_copy_detector_ignores_co_authored_by_trailers() -> None:
    """Trailers are dropped before fingerprinting, so they never add overlap.

    Mutation: delete the `is_trailer_line` filter in `_copy_tokens` -> the two
    token streams gain distinct shingles and the 1.0 equality fails.
    """
    plain = LONG_BODY
    with_trailer = LONG_BODY.rstrip("\n") + "\n\nCo-authored-by: Outsider <out@x.io>\n"
    assert copy_overlap(with_trailer, plain) == 1.0


def test_resolve_squash_message_refuses_the_body_copied_into_the_squash_slot(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The #220 template shape in both slots refuses through the decision point.

    Mutation: drop the `refuse_mechanic_copy` call in `resolve_squash_message` ->
    the explicit is accepted, no `RefusalError`, the `pytest.raises` fails.
    """
    body = LONG_BODY
    with pytest.raises(RefusalError):
        resolve_squash_message(body, explicit=body, supplied=True)
    err = capsys.readouterr().err
    assert "mechanic copy" in err
    assert "CONTEXT.md" in err and "pr-land/SKILL.md" in err


def test_full_template_into_the_squash_slot_refuses_as_copy(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The raw shipped template in both slots reports copy, not the raw-token gate.

    The copy check runs before the raw-token gate, so the ticket's "full template
    into the squash slot" case keeps its copy message plus the spec pointer even
    though the template still holds the `CODE_AUTHORS` comment.

    Mutation: move `refuse_mechanic_copy(...)` below `refuse_raw_token(body)` in
    `resolve_squash_message` -> the raw token refuses first, so the
    "mechanic copy" assertion fails.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "CODE_AUTHORS" in template
    with pytest.raises(RefusalError):
        resolve_squash_message(template, explicit=template, supplied=True)
    err = capsys.readouterr().err
    assert "mechanic copy" in err
    assert "CODE_AUTHORS" not in err
    assert "CONTEXT.md" in err and "pr-land/SKILL.md" in err


def test_near_identical_paraphrase_still_refuses(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A light rewording stays above the overlap threshold and refuses.

    Mutation: raise `COPY_OVERLAP_THRESHOLD` to 0.95 -> the measured 0.84 no longer
    refuses, the `pytest.raises` block fails.
    """
    body = LONG_BODY
    paraphrase = _light_paraphrase(body)
    assert copy_overlap(paraphrase, body) > COPY_OVERLAP_THRESHOLD
    with pytest.raises(RefusalError):
        resolve_squash_message(body, explicit=paraphrase, supplied=True)
    assert "mechanic copy" in capsys.readouterr().err


def test_copy_check_is_skipped_below_the_token_floor() -> None:
    """A text under `COPY_TOKEN_FLOOR` tokens scores 0.0, so nothing is flagged.

    Mutation: change the floor guard `< COPY_TOKEN_FLOOR` to `< 0` in
    `copy_overlap` -> the identical short texts score 1.0, failing the 0.0 assert.
    """
    assert len(SHORT_BODY.split()) < COPY_TOKEN_FLOOR
    assert copy_overlap(SHORT_BODY, SHORT_BODY) == 0.0
    assert copy_overlap(SHORT_BODY, LONG_BODY) == 0.0


def test_short_honest_body_passes_the_explicit_path() -> None:
    """A short honest body under the floor resolves; curation is not copying.

    Mutation: change the floor guard `< COPY_TOKEN_FLOOR` to `< 0` in
    `copy_overlap` -> `SHORT_BODY` scores 1.0 against itself and the resolve call
    raises instead of returning the cleaned text.
    """
    out = resolve_squash_message(SHORT_BODY, explicit=SHORT_BODY, supplied=True)
    assert out == clean_squash_body(SHORT_BODY)


def test_curated_overview_over_a_long_description_is_not_copy() -> None:
    """An overview sharing little text with a long description stays under threshold.

    Mutation: make `copy_overlap` return 1.0 unconditionally -> the overview now
    refuses and the resolve call raises, failing the assertions.
    """
    overview = (
        "## Summary\n"
        "feat(pr-land): curate the squash overview\n"
        "- draft first, then merge with an explicit message\n"
        "- the copy detector guards the overview\n"
        "- only the contract section names are headings\n"
        "- at most five bullets\n"
        "- the preview path still strips ephemera\n"
    )
    overlap = copy_overlap(overview, LONG_BODY)
    assert overlap <= COPY_OVERLAP_THRESHOLD
    out = resolve_squash_message(LONG_BODY, explicit=overview, supplied=True)
    check_squash_body(out)


def test_heading_free_bullets_only_message_satisfies_core() -> None:
    """Core reads from pre-section prose, so a bullets-only message still has Core.

    `split_squash_sections` leaves a heading-free body wholly in prose, which is
    what the Core gate counts.

    Mutation: drop the `or "\\n".join(prose).strip()` half of the Core check in
    `check_squash_body` -> this bullets-only message refuses, and the assertions fail.
    """
    bullets_only = "- bound the retry loop\n- cap the poll budget\n- fail fast on conflicts\n"
    resolved = resolve_squash_message(SHORT_BODY, explicit=bullets_only, supplied=True)
    check_squash_body(resolved)


# --- the strict shape gate ---


def test_shape_gate_refuses_a_non_contract_heading(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`## Landing` is not one of the contract's section names.

    Mutation: drop the `_non_contract_heading` branch in
    `check_explicit_squash_message` -> no refusal, the `pytest.raises` fails.
    """
    with pytest.raises(RefusalError):
        check_explicit_squash_message("## Landing\nsquash the branch\n")
    assert "non-contract heading" in capsys.readouterr().err


def test_shape_gate_refuses_a_checkbox(capsys: pytest.CaptureFixture[str]) -> None:
    """A markdown checkbox is a review artifact, not part of the message.

    Mutation: drop the `CHECKBOX_RE.match` branch in `check_explicit_squash_message`
    -> no refusal, the `pytest.raises` fails.
    """
    with pytest.raises(RefusalError):
        check_explicit_squash_message("## Summary\n- [ ] tests green\n")
    assert "markdown checkbox" in capsys.readouterr().err


def test_shape_gate_refuses_a_mermaid_fence(capsys: pytest.CaptureFixture[str]) -> None:
    """Mermaid stays in the PR body; the explicit message refuses it.

    Mutation: drop the `MERMAID_UNCLOSED_OPENER_RE.search` branch in
    `check_explicit_squash_message` -> no refusal, the `pytest.raises` fails.
    """
    with pytest.raises(RefusalError):
        check_explicit_squash_message("## Summary\n```mermaid\nflowchart LR\n  A --> B\n```\n")
    assert "Mermaid" in capsys.readouterr().err


def test_shape_gate_refuses_the_raw_code_authors_token(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The raw CODE_AUTHORS token refuses on the explicit message itself.

    Mutation: drop `refuse_raw_token(msg)` (keep the PR-body call) in
    `check_explicit_squash_message` -> no refusal, the `pytest.raises` fails.
    """
    with pytest.raises(RefusalError):
        check_explicit_squash_message("## Summary\n<!-- CODE_AUTHORS -->\n")
    assert "CODE_AUTHORS" in capsys.readouterr().err


def test_shape_gate_refuses_one_line_over_the_cap(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The overview stays one screen: 16 lines is over the 15-line cap.

    Mutation: raise `SQUASH_MESSAGE_MAX_LINES` to 16 -> no refusal, the
    `pytest.raises` block fails.
    """
    message = "## Summary\n" + "".join(f"detail line {i}\n" for i in range(1, 16))
    assert len(message.splitlines()) == SQUASH_MESSAGE_MAX_LINES + 1
    with pytest.raises(RefusalError):
        check_explicit_squash_message(message)
    assert f"{SQUASH_MESSAGE_MAX_LINES + 1} lines" in capsys.readouterr().err


def test_shape_gate_accepts_a_title_with_five_bullets_and_a_contract_heading() -> None:
    """One title line, one contract heading, five bullets: the overview shape.

    Mutation: lower `SQUASH_BODY_MAX_BULLETS` to 4 -> the fifth bullet refuses and
    the call raises, failing the test.
    """
    check_explicit_squash_message(
        "## Summary\n"
        "feat(pr-land): curate the squash overview\n"
        "- draft first, then merge explicitly\n"
        "- the copy detector guards the overview\n"
        "- contract headings only\n"
        "- at most five bullets\n"
        "- the preview path still strips ephemera\n"
    )


@pytest.mark.parametrize(
    "heading",
    [
        "## Summary",
        "## What Changed",
        "## Root Cause",
        "## Blast Radius & Safety",
        "## Evidence",
        "## Links",
    ],
)
def test_shape_gate_allows_every_contract_heading(heading: str) -> None:
    """Every contract section name is a legal heading; only non-contract names refuse.

    Mutation: make `_non_contract_heading` return the line for every heading (drop
    the `_section_key` check) -> each contract heading refuses and this fails.
    """
    check_explicit_squash_message(f"{heading}\nbody line\n")


def test_shape_gate_runs_on_the_inline_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The inline explicit message is refused by the shape gate, not just the file.

    Mutation: delete the `check_explicit_squash_message(...)` call in
    `resolve_squash_message` -> the checkbox survives and no refusal is raised.
    """
    with pytest.raises(RefusalError):
        resolve_squash_message(
            SHORT_BODY, explicit="## Summary\n- [ ] tests green\n", supplied=True
        )
    assert "markdown checkbox" in capsys.readouterr().err


# --- end to end: --check gates both flags, the preview path still strips ---

GH_STUB = """#!/usr/bin/env bash
echo "$@" >> "$GH_LOG"
for arg in "$@"; do
  if [[ "$arg" =~ pulls\\?head= ]]; then echo "null"; exit 0; fi
  if [[ "$arg" == "user" ]]; then echo "merger-user"; exit 0; fi
done
exit 0
"""


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=git_env(), check=True)


def _git(repo: Path, *args: str) -> None:
    _ = _run(["git", "-C", str(repo), *args])


def _make_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    _ = _run(["git", "init", "-b", "main", str(repo)])
    for key, value in (
        ("user.name", "Copy Synthetic"),
        ("user.email", "copy@x.io"),
        ("commit.gpgsign", "false"),
    ):
        _ = _run(["git", "-C", str(repo), "config", key, value])
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-m", "chore: base")
    _git(repo, "remote", "add", "origin", "https://github.com/test/copy.git")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _git(repo, "checkout", "-b", "feat-copy")
    _ = (repo / "one.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "one.txt")
    _git(repo, "commit", "-m", "feat: one")


def _gh_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text(GH_STUB, encoding="utf-8")
    gh.chmod(0o755)
    return git_env(
        PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}", GH_LOG=str(tmp_path / "gh.log")
    )


def _run_merge(repo: Path, env: dict[str, str], *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--merge",
            "--head",
            "feat-copy",
            "--title",
            "feat: x",
            *extra,
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )


def _run_check(repo: Path, env: dict[str, str], *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--check",
            "--head",
            "feat-copy",
            "--title",
            "feat(pr-land): shape probe",
            *extra,
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )


def _refusals(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.startswith("refusing squash message:")]


def _draft(repo: Path) -> dict[str, Any]:
    return json.loads((repo / ".lsz" / "tmp" / "draft.json").read_text(encoding="utf-8"))


def test_check_gates_inline_and_file_on_the_copy_refusal(tmp_path: Path) -> None:
    """`--squash-message` and `--squash-message-file` share one copy refusal and code.

    Mutation: drop the `refuse_mechanic_copy` call in `resolve_squash_message` ->
    both runs exit 0, so the returncode and refusal assertions fail.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text(LONG_BODY, encoding="utf-8")
    msg_file = tmp_path / "msg.md"
    _ = msg_file.write_text(LONG_BODY, encoding="utf-8")

    inline = _run_check(repo, env, "--body-file", str(body_file), "--squash-message", LONG_BODY)
    from_file = _run_check(
        repo, env, "--body-file", str(body_file), "--squash-message-file", str(msg_file)
    )

    assert inline.returncode == 1, inline.stderr
    assert from_file.returncode == 1, from_file.stderr
    assert "mechanic copy" in inline.stderr
    assert _refusals(inline.stderr) == _refusals(from_file.stderr)
    assert _draft(repo)["status"] == "refused"


def test_check_gates_inline_and_file_on_the_shape_refusal(tmp_path: Path) -> None:
    """A checkbox message refuses identically through both flags.

    Mutation: delete the `check_explicit_squash_message(...)` call in
    `resolve_squash_message` -> both runs exit 0, the parity assertions fail.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text(SHORT_BODY, encoding="utf-8")
    bad = "## Summary\n- [ ] tests green\n"
    msg_file = tmp_path / "msg.md"
    _ = msg_file.write_text(bad, encoding="utf-8")

    inline = _run_check(repo, env, "--body-file", str(body_file), "--squash-message", bad)
    from_file = _run_check(
        repo, env, "--body-file", str(body_file), "--squash-message-file", str(msg_file)
    )

    assert inline.returncode == 1, inline.stderr
    assert from_file.returncode == 1, from_file.stderr
    assert "markdown checkbox" in inline.stderr
    assert inline.returncode == from_file.returncode
    assert _refusals(inline.stderr) == _refusals(from_file.stderr)


def test_check_preview_path_still_strips_mermaid_and_checkboxes(tmp_path: Path) -> None:
    """With no explicit message the preview path strips ephemera instead of refusing.

    Mutation: insert `check_explicit_squash_message(body)` in the fallback branch
    of `resolve_squash_message` (gate the preview body before cleaning) -> the run
    exits 1 and the strip assertions fail.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text(
        "## Summary\nreal change\n\n"
        "```mermaid\nflowchart LR\n  A --> B\n```\n\n"
        "<details><summary>trace</summary>\nsecret\n</details>\n\n"
        "- [x] tests green\n",
        encoding="utf-8",
    )

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert len(r.stdout.splitlines()) == 5, r.stdout
    squash_body = str(_draft(repo)["squash_body"])
    assert "mermaid" not in squash_body
    assert "flowchart" not in squash_body
    assert "[x]" not in squash_body
    assert "real change" in squash_body


def test_merge_path_refuses_a_body_copied_into_the_squash_slot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The merge path refuses the copy before any PUT: the gate is not preview-only.

    Mutation: drop the `refuse_mechanic_copy` call in `resolve_squash_message` ->
    the merge runs and a `/merge` PUT appears, so the last assertion fails.
    """
    monkeypatch.chdir(tmp_path)
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        joined = " ".join(cmd)
        if "mergeable_state" in joined:
            out = "clean"
        elif "api user" in joined:
            out = "merger"
        elif "/commits" in joined:
            out = "ghuser\tWf Zyx\twf@x.io\n"
        else:
            out = '{"merged":true}'
        return subprocess.CompletedProcess(cmd, 0, out + "\n", "")

    monkeypatch.setattr(github_mod, "run_command", fake_run)

    merged = merge_pr(
        "test/repo",
        "7",
        "main",
        "feat: x",
        LONG_BODY,
        squash_message_override=LONG_BODY,
        squash_message_supplied=True,
    )

    assert merged is False
    assert "mechanic copy" in capsys.readouterr().err
    assert not [c for c in calls if len(c) > 2 and c[1] == "api" and "/merge" in c[2]]


def test_merge_path_shape_gate_refuses_before_any_gh_call(tmp_path: Path) -> None:
    """The merge path refuses the checkbox message with exit 1 and no gh call, both flags.

    Mutation: delete the `check_explicit_squash_message(...)` call in `main()`'s
    merge guard -> the message is silently stripped to the empty-usage error
    (exit 2, "--squash-message is empty"), so the code and message asserts fail.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    bad = "## Summary\n- [ ] tests green\n"
    msg_file = tmp_path / "msg.md"
    _ = msg_file.write_text(bad, encoding="utf-8")

    inline = _run_merge(repo, env, "--squash-message", bad)
    from_file = _run_merge(repo, env, "--squash-message-file", str(msg_file))

    assert inline.returncode == 1, inline.stderr
    assert from_file.returncode == 1, from_file.stderr
    assert "markdown checkbox" in inline.stderr
    assert _refusals(inline.stderr) == _refusals(from_file.stderr)
    gh_log = tmp_path / "gh.log"
    assert not gh_log.exists() or gh_log.read_text(encoding="utf-8") == ""


# --- adversarial-review fixes: F1-F11 ---


@pytest.mark.parametrize("fence", ["```", "~~~", "````"])
def test_shape_gate_refuses_every_mermaid_fence_character(
    fence: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Backtick, tilde and 4-backtick Mermaid fences all refuse (F1).

    Mutation: revert `MERMAID_UNCLOSED_OPENER_RE` to backtick-only -> the tilde and
    4-backtick cases stop matching and their `pytest.raises` blocks fail.
    """
    with pytest.raises(RefusalError):
        check_explicit_squash_message(f"## Summary\n{fence}mermaid\ngraph TD\n  A --> B\n{fence}\n")
    assert "Mermaid" in capsys.readouterr().err


@pytest.mark.parametrize("fence", ["```", "~~~", "````"])
def test_preview_strips_mermaid_with_either_fence_character(fence: str) -> None:
    """The `--check` preview strips a tilde or 4-backtick Mermaid fence too (F1).

    Mutation: revert `MERMAID_FENCE_RE` to the backtick-only pattern -> `clean_squash_body`
    leaves the `~~~mermaid`/four-backtick fence in place, so these assertions fail.
    """
    raw = f"## Summary\nreal\n\n{fence}mermaid\ngraph TD\n  A --> B\n{fence}\n"
    cleaned = clean_squash_body(raw)
    assert "mermaid" not in cleaned
    assert "graph TD" not in cleaned
    assert "real" in cleaned


def test_shape_gate_still_allows_a_quoted_diff_fence() -> None:
    """Widening the Mermaid patterns never touches a diff quote (F1)."""
    check_explicit_squash_message("## Summary\n- changed the gate\n```diff\n-gone\n+kept\n```\n")


def test_fenced_line_mask_flags_balanced_spans_only() -> None:
    """Shared mask: a closed span is quoted, an unclosed tilde fence quotes nothing (F3)."""
    text = "a\n```\nb\n```\nc\n~~~\nd\n"
    assert _fenced_line_mask(text) == [False, True, True, True, False, False, False]


def test_shape_gate_passes_quoted_heading_and_checkbox_inside_a_fence() -> None:
    """An honest message quoting a log/diff passes (F3).

    Mutation: drop the `if quoted[index]: continue` branch -> the quoted `# run the gate`
    and `- [ ] quoted` lines refuse and this test fails.
    """
    check_explicit_squash_message(
        "## Summary\nx\n```bash\n# run the gate\nuv run pytest\n```\n\n```\n- [ ] quoted\n```\n"
    )


def test_shape_gate_still_refuses_the_constructs_outside_a_fence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Outside a fence the same `#`/`- [ ]` constructs still refuse (F3)."""
    with pytest.raises(RefusalError):
        check_explicit_squash_message("## Summary\nx\n# run the gate\n")
    assert "non-contract heading" in capsys.readouterr().err
    with pytest.raises(RefusalError):
        check_explicit_squash_message("## Summary\nx\n- [ ] tests green\n")
    assert "markdown checkbox" in capsys.readouterr().err


def test_shape_gate_still_refuses_an_unclosed_fence(capsys: pytest.CaptureFixture[str]) -> None:
    """An unclosed fence quotes nothing, so its `#` line still refuses (F3)."""
    with pytest.raises(RefusalError):
        check_explicit_squash_message("## Summary\nx\n```bash\n# run the gate\n")
    assert "non-contract heading" in capsys.readouterr().err


def test_copy_tokens_casefold_and_fold_intra_token_dashes() -> None:
    """`casefold()` and intra-token `-`/`_` folding normalize the copy fingerprint (F4).

    Mutation: restore `.lower()` and drop the `[-_]+` fold -> `fail-fast` no longer matches
    `fail fast` and `Stra\u00dfe` no longer matches `STRASSE`, failing the asserts.
    """
    assert _copy_tokens("fail-fast") == _copy_tokens("fail fast") == _copy_tokens("fail_fast")
    assert _copy_tokens("Stra\u00dfe") == _copy_tokens("STRASSE")


def test_copy_overlap_treats_hyphen_and_space_spellings_as_identical() -> None:
    """A hyphen respelling is the same shingles: Jaccard 1.0 (F4)."""
    filler = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi"
    hyphen = filler + " rho sigma tau fail-fast on a conflicting head every time"
    spaced = hyphen.replace("fail-fast", "fail fast")
    assert copy_overlap(spaced, hyphen) == 1.0


def test_copy_metric_refuses_an_appended_message_by_body_coverage() -> None:
    """Appending ~25% novel tokens evades Jaccard but coverage catches it (F5).

    Mutation: revert `refuse_mechanic_copy` to the Jaccard-only condition -> the appended
    message passes and the `pytest.raises` block fails.
    """
    filler_count = len(_copy_tokens(LONG_BODY)) // 4 + 1
    filler = " ".join(f"novel{i}" for i in range(filler_count))
    appended = LONG_BODY + "\n" + filler + "\n"
    assert copy_overlap(appended, LONG_BODY) <= COPY_OVERLAP_THRESHOLD
    assert copy_body_coverage(appended, LONG_BODY) > COPY_OVERLAP_THRESHOLD
    with pytest.raises(RefusalError):
        refuse_mechanic_copy(appended, LONG_BODY)


def test_copy_metric_boundaries_drop_and_reorder_remain_evasions() -> None:
    """Dropping ~20% and reordering lines beat BOTH metrics: deliberate boundaries (F5).

    Pinned so the boundary is intentional: if either future change makes these refuse, the
    `refuse_mechanic_copy` calls raise and this test fails.
    """
    lines = LONG_BODY.splitlines()
    dropped = "\n".join(lines[: int(len(lines) * 0.8)]) + "\n"
    reordered = "\n".join([lines[0], *reversed(lines[1:])]) + "\n"
    for variant in (dropped, reordered):
        assert copy_overlap(variant, LONG_BODY) <= COPY_OVERLAP_THRESHOLD
        assert copy_body_coverage(variant, LONG_BODY) <= COPY_OVERLAP_THRESHOLD
        refuse_mechanic_copy(variant, LONG_BODY)  # under both thresholds: no refusal


@pytest.mark.parametrize("marker", ["1. ", "2) ", "12. "])
def test_shape_gate_refuses_an_ordered_checkbox(
    marker: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """An ordered task item is still a checkbox (F6).

    Mutation: revert `CHECKBOX_RE` to drop the ordered-marker alternation -> `1. [ ] x`
    is not matched and the `pytest.raises` block fails.
    """
    with pytest.raises(RefusalError):
        check_explicit_squash_message(f"## Summary\n{marker}[ ] tests green\n")
    assert "markdown checkbox" in capsys.readouterr().err


def test_shape_gate_refuses_a_flush_heading(capsys: pytest.CaptureFixture[str]) -> None:
    """`##Heading` with no space is a heading (F7).

    Mutation: revert `HEADING_RE` to the space-required pattern -> `##Heading` reads as
    prose and the `pytest.raises` block fails.
    """
    with pytest.raises(RefusalError):
        check_explicit_squash_message("##Heading\nx\n")
    assert "non-contract heading" in capsys.readouterr().err


def test_shape_gate_line_budget_ignores_a_trailing_blank_line() -> None:
    """A 15-line file ending in a blank line stays 15 (F9).

    Mutation: drop the `while lines and not lines[-1].strip(): lines.pop()` -> the trailing
    blank counts and the message refuses, failing this test.
    """
    message = "## Summary\n" + "".join(f"line {i}\n" for i in range(1, 15)) + "\n"
    assert len(message.splitlines()) == SQUASH_MESSAGE_MAX_LINES + 1
    check_explicit_squash_message(message)


def test_squash_message_file_bom_is_stripped(tmp_path: Path) -> None:
    """A BOM on the message file never rides in as prose (F11).

    Mutation: restore `read_text(encoding="utf-8")` in `resolve_squash_override` -> the
    BOM-prefixed `## Summary` line reads as prose, so the BOM reaches `squash_body` and the
    `startswith`/`not in` asserts fail.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text(SHORT_BODY, encoding="utf-8")
    msg_file = tmp_path / "msg.md"
    _ = msg_file.write_bytes(b"\xef\xbb\xbf## Summary\nbound the retry loop\n")

    r = _run_check(repo, env, "--body-file", str(body_file), "--squash-message-file", str(msg_file))

    assert r.returncode == 0, r.stderr
    squash = str(_draft(repo)["squash_body"])
    assert squash.startswith("## Summary")
    assert "\ufeff" not in squash


def test_merge_main_guard_refuses_copy_before_any_gh_call(tmp_path: Path) -> None:
    """`--merge` with the body pasted into both slots refuses with zero gh calls (F2).

    Mutation: drop the new `refuse_mechanic_copy(...)` call from `main()`'s merge guard ->
    the run reaches `merge_pr`, prints `PR <url>`, stamps, readies and exits only later, so
    the stdout and gh-log asserts fail.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text(LONG_BODY, encoding="utf-8")
    msg_file = tmp_path / "msg.md"
    _ = msg_file.write_text(LONG_BODY, encoding="utf-8")

    r = _run_merge(repo, env, "--body-file", str(body_file), "--squash-message-file", str(msg_file))

    assert r.returncode == 1, r.stderr
    assert r.stderr.count("mechanic copy") == 1
    assert "PR http" not in r.stdout
    gh_log = tmp_path / "gh.log"
    assert not gh_log.exists() or gh_log.read_text(encoding="utf-8") == ""


def test_check_preview_end_to_end_strips_a_tilde_mermaid_fence(tmp_path: Path) -> None:
    """The `--check` preview strips a `~~~mermaid` fence, not just backticks (F1).

    Mutation: revert `MERMAID_FENCE_RE` to backtick-only -> the tilde fence survives into
    `squash_body` and the `not in` asserts fail.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text(
        "## Summary\nreal change\n\n~~~mermaid\ngraph TD\n  A --> B\n~~~\n", encoding="utf-8"
    )

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert len(r.stdout.splitlines()) == 5
    squash = str(_draft(repo)["squash_body"])
    assert "mermaid" not in squash
    assert "graph TD" not in squash
    assert "real change" in squash
