#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
General rename for skills and subskills.

Usage:
  # skill
  uv run $SKILL_DIR/scripts/rename.py <old_skill> <new_skill> [--dry-run]
  uv run $SKILL_DIR/scripts/rename.py toolchain toolchain-wiki --dry-run

  # subskill
  uv run $SKILL_DIR/scripts/rename.py --parent <parent_skill> <old_sub> <new_sub> [--dry-run]
  uv run $SKILL_DIR/scripts/rename.py --parent toolchain-wiki oxc oxc2 --dry-run

Tool owns bytes; model proofreads intent. The script handles:
  - mv skills/<old> -> skills/<new>  (skill) or skills/<parent>/subskills/<old> -> .../<new> (subskill)
  - frontmatter name, TRIGGER, heading, keeps prompt, managed-by, depends-on, $SKILL_DIR pointers
  - canonical references + scaffold wrapper (generalized via scan)

Information boundary: deterministic file moves + replacements; model supplies intent (names).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


def repo_root_from_script(script_path: pathlib.Path) -> pathlib.Path:
    # script at <repo>/skills/<name>/scripts/rename.py
    # parents[0]=scripts, [1]=<name>, [2]=skills, [3]=repo (for toolchain depth)
    # for deeper ai-engineering depth: parents[0]=scripts, [1]=skill-authoring, [2]=subskills, [3]=ai-engineering-expert, [4]=skills, [5]=repo
    p = script_path.resolve()
    for _ in range(10):
        if (p / "skills").is_dir() and (p / "pyproject.toml").exists():
            return p
        p = p.parent
    return (
        script_path.resolve().parents[3]
        if len(script_path.resolve().parents) > 3
        else script_path.resolve().parent
    )


def _title(s: str) -> str:
    # toolchain-wiki -> Toolchain Wiki, oxc -> Oxc
    return s.replace("-", " ").replace("_", " ").title()


def _apply_pairs_single_pass(text: str, pairs: list[tuple[str, str]]) -> str:
    # Single-pass replacement to avoid double wiki-wiki / triple temp when new contains old.
    # Build regex matching any old sorted longest first, replace without re-scanning new text.
    if not pairs:
        return text
    # sort longest first for regex alternation priority
    pairs_sorted = sorted(pairs, key=lambda x: len(x[0]), reverse=True)
    mapping = {old: new for old, new in pairs_sorted}
    # escape and join
    pattern = re.compile("|".join(re.escape(old) for old, _ in pairs_sorted))
    return pattern.sub(lambda m: mapping[m.group(0)], text)
def build_skill_pairs(old: str, new: str) -> list[tuple[str, str]]:
    """Pairs for top-level skill rename. Mirrors the previously hardcoded toolchain pairs, but parameterized."""
    old_title = _title(old)
    new_title = _title(new)
    old_upper = old.upper()
    new_upper = new.upper()
    old_space = old.replace("-", " ").replace("_", " ")
    new_space = new.replace("-", " ").replace("_", " ")
    old_space_title = _title(old)
    new_space_title = _title(new)
    pairs: list[tuple[str, str]] = [
        (f"name: {old}", f"name: {new}"),
        (f"TRIGGER: {old}", f"TRIGGER: {new}"),
        # Native router description - handle both title case and lower space variants
        (f"Native {old_space_title} router", f"Native {new_space_title} router"),
        (f"Native {old_space} router", f"Native {new_space} router"),
        (f"Native {old_title} router", f"Native {new_title} router"),
        (f"Native {old_title} wiki router", f"Native {new_title} wiki router"),
        (f"# {old_title} Wiki", f"# {new_title} Wiki"),
        (f"# {old_title}", f"# {new_title}"),
        (f"keeps `{old_upper}` prompt", f"keeps `{new_upper}` prompt"),
        (f"keeps `{old_upper}-WIKI` prompt", f"keeps `{new_upper}-WIKI` prompt"),
        (f"{old}/subskills", f"{new}/subskills"),
        (f"depends-on: [{old}]", f"depends-on: [{new}]"),
        (f"`{old}`", f"`{new}`"),
        (f"(canonical: `{old}", f"(canonical: `{new}"),
        (f"(see `{old}", f"(see `{new}"),
        (f"managed-by: {old}", f"managed-by: {new}"),
        # $SKILL_DIR pointers from scaffold wrapper
        (f"$SKILL_DIR/../../{old}/", f"$SKILL_DIR/../../{new}/"),
        (f"`{old}/subskills/oxc`", f"`{new}/subskills/oxc`"),
        (f"`{old}/subskills", f"`{new}/subskills"),
        # generic toolchain-wiki specific variants normalized: if old is toolchain and new is toolchain-wiki, we need Native toolchain -> Native toolchain wiki
        # already covered via title, but ensure the exact toolchain string from previous script is present
        # additional generic: manage: [old] -> manage: [new] is covered via depends-on? add manage as well
        (f"manage: [{old}]", f"manage: [{new}]"),
        # handle backticked subskill header like `toolchain/subskills/oxc` without trailing
        (f"`{old}/subskills/oxc", f"`{new}/subskills/oxc"),
    ]
    # Deduplicate while preserving
    seen: set[tuple[str, str]] = set()
    uniq: list[tuple[str, str]] = []
    for o, n in pairs:
        if o == n:
            continue
        if (o, n) not in seen:
            seen.add((o, n))
            uniq.append((o, n))
    # Sort longest first to avoid prefix double-replace (e.g. "(canonical: `toolchain" before "toolchain/subskills")
    uniq.sort(key=lambda x: len(x[0]), reverse=True)
    return uniq


def build_subskill_pairs(parent: str, old: str, new: str) -> list[tuple[str, str]]:
    """Pairs for subskill rename under a parent skill."""
    old_title = _title(old)
    new_title = _title(new)
    pairs: list[tuple[str, str]] = [
        (f"name: {old}", f"name: {new}"),
        (f"# {old_title}", f"# {new_title}"),
        (f"`{old}`", f"`{new}`"),
        (f"subskills/{old}/", f"subskills/{new}/"),
        (f"subskills/{old}", f"subskills/{new}"),
        (f"$SKILL_DIR/subskills/{old}", f"$SKILL_DIR/subskills/{new}"),
        (
            f"$SKILL_DIR/../../{parent}/subskills/{old}",
            f"$SKILL_DIR/../../{parent}/subskills/{new}",
        ),
        (f"`{old}/", f"`{new}/"),
        (f"{parent}/subskills/{old}", f"{parent}/subskills/{new}"),
        (f"manage: [{old}]", f"manage: [{new}]"),  # single entry
        (f"manage: [{old},", f"manage: [{new},"),  # first of many
        (f", {old},", f", {new},"),  # middle
        (f", {old}]", f", {new}]"),  # last
        (f"[{old},", f"[{new},"),  # inline list without manage prefix
        (f", {old}]", f", {new}]"),
        (f"/{old}`", f"/{new}`"),
        (f"/{old}/", f"/{new}/"),
    ]
    seen: set[tuple[str, str]] = set()
    uniq: list[tuple[str, str]] = []
    for o, n in pairs:
        if o == n:
            continue
        if (o, n) not in seen:
            seen.add((o, n))
            uniq.append((o, n))
    uniq.sort(key=lambda x: len(x[0]), reverse=True)
    return uniq


def main() -> None:
    ap = argparse.ArgumentParser(description="General rename for skills and subskills")
    ap.add_argument(
        "old_name", help="Current skill name (or old subskill name when --parent is used)"
    )
    ap.add_argument("new_name", help="New skill/subskill name")
    ap.add_argument(
        "--parent",
        dest="parent",
        default=None,
        help="When renaming a subskill, the parent skill name (e.g. toolchain-wiki)",
    )
    ap.add_argument("--dry-run", action="store_true", help="preview without writing")
    ap.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")
    args = ap.parse_args()

    script_path = pathlib.Path(__file__)
    repo_root = (
        args.cwd.resolve() if args.cwd else repo_root_from_script(script_path)
    )
    # SAFETY: args.cwd is optional override constrained to repo root via skills/ existence check below; new_name/old_name validated via directory existence

    if not (repo_root / "skills").is_dir():
        print(
            f"error: cannot locate repo root from {script_path} (guessed {repo_root})",
            file=sys.stderr,
        )
        sys.exit(2)

    skills_dir = repo_root / "skills"
    is_subskill = args.parent is not None

    if is_subskill:
        parent = args.parent
        old_sub = args.old_name
        new_sub = args.new_name
        old_dir = skills_dir / parent / "subskills" / old_sub
        new_dir = skills_dir / parent / "subskills" / new_sub
        if not old_dir.is_dir():
            print(f"error: subskill parent/{old_sub} not found: {old_dir}", file=sys.stderr)
            sys.exit(2)
        if new_dir.exists():
            print(f"error: target subskill already exists: {new_dir}", file=sys.stderr)
            sys.exit(2)
        if old_sub == new_sub:
            print(f"no-op: already {old_sub}")
            sys.exit(0)
        print(f"rename subskill: {parent}/{old_sub} -> {parent}/{new_sub} (repo: {repo_root})")
        if args.dry_run:
            print("dry-run: no writes")
        # 1. mv directory
        if not args.dry_run:
            old_dir.rename(new_dir)
            print(f"moved {old_dir.relative_to(repo_root)} -> {new_dir.relative_to(repo_root)}")
        else:
            print(
                f"  [dry-run] would move {old_dir.relative_to(repo_root)} -> {new_dir.relative_to(repo_root)}"
            )

        pairs = build_subskill_pairs(parent, old_sub, new_sub)
        # Files to patch: all SKILL.md that could reference this subskill, plus the moved subskill itself
        files_to_patch: list[pathlib.Path] = []
        # the moved subskill's SKILL.md
        files_to_patch.append(new_dir / "SKILL.md" if not args.dry_run else old_dir / "SKILL.md")
        # parent router
        files_to_patch.append(skills_dir / parent / "SKILL.md")
        # sibling subskills
        parent_subskills = skills_dir / parent / "subskills"
        if parent_subskills.is_dir():
            for sub in parent_subskills.iterdir():
                if sub.is_dir():
                    files_to_patch.append(sub / "SKILL.md")
        # any other skill that might reference it (scan all SKILL.md)
        for f in skills_dir.rglob("SKILL.md"):
            if f not in files_to_patch:
                files_to_patch.append(f)
        # scaffold wrapper that references toolchain/oxc etc.
        files_to_patch.append(
            repo_root / "skills" / "scaffold" / "subskills" / "typescript-scaffolding" / "SKILL.md"
        )
        files_to_patch.append(
            repo_root
            / "skills"
            / "scaffold"
            / "subskills"
            / "typescript-scaffolding"
            / "references"
            / "README.md"
        )
        # oxc references README if parent is toolchain
        files_to_patch.append(
            skills_dir / parent / "subskills" / new_sub / "references" / "README.md"
            if not args.dry_run
            else skills_dir / parent / "subskills" / old_sub / "references" / "README.md"
        )
        # also scan references/README.md generically
        for f in skills_dir.rglob("README.md"):
            if f not in files_to_patch:
                files_to_patch.append(f)
    else:
        old = args.old_name
        new = args.new_name
        old_dir = skills_dir / old
        new_dir = skills_dir / new
        has_old = old_dir.is_dir()
        has_new = new_dir.is_dir()
        if has_old and has_new:
            print(f"error: both skills/{old} and skills/{new} exist — ambiguous", file=sys.stderr)
            sys.exit(2)
        if not has_old and not has_new:
            print(f"error: neither skills/{old} nor skills/{new} exists", file=sys.stderr)
            sys.exit(2)
        # Determine direction: we want to move old -> new regardless of which currently exists?
        # If old exists, it's old -> new. If new exists and old doesn't, user likely wants to reverse? But we treat old_name as current, so old must exist.
        if not has_old:
            print(
                f"error: skill '{old}' not found (found '{new}' instead). Did you swap args?",
                file=sys.stderr,
            )
            sys.exit(2)
        if old == new:
            print(f"no-op: already {old}")
            sys.exit(0)
        print(f"rename skill: {old} -> {new} (repo: {repo_root})")
        if args.dry_run:
            print("dry-run: no writes")
        if not args.dry_run:
            old_dir.rename(new_dir)
            print(f"moved {old_dir.relative_to(repo_root)} -> {new_dir.relative_to(repo_root)}")
        else:
            print(
                f"  [dry-run] would move {old_dir.relative_to(repo_root)} -> {new_dir.relative_to(repo_root)}"
            )

        pairs = build_skill_pairs(old, new)
        # Files to patch: prefer similar list to previous script but generalized via scan
        dst = new_dir if not args.dry_run else old_dir
        files_to_patch = []
        # router SKILL.md (now at dst)
        files_to_patch.append(dst / "SKILL.md")
        # subskills (if any)
        subskills_dir = dst / "subskills"
        if subskills_dir.exists() or (old_dir / "subskills").exists():
            sd = subskills_dir if not args.dry_run else old_dir / "subskills"
            if sd.is_dir():
                for sub in sd.iterdir():
                    if sub.is_dir():
                        files_to_patch.append(sub / "SKILL.md")
            # also fallback to known subskills list for dry-run when dst doesn't exist yet
            for sub in ["oxc", "typecheck", "worktree"]:
                p = dst / "subskills" / sub / "SKILL.md"
                if p not in files_to_patch:
                    files_to_patch.append(p)
                p2 = (old_dir if args.dry_run else dst) / "subskills" / sub / "SKILL.md"
                if p2 not in files_to_patch:
                    files_to_patch.append(p2)
        # collect all other SKILL.md that reference this skill
        for f in skills_dir.rglob("SKILL.md"):
            if f not in files_to_patch:
                files_to_patch.append(f)
        # also references README.md that may contain $SKILL_DIR pointers
        for f in skills_dir.rglob("README.md"):
            if f not in files_to_patch:
                files_to_patch.append(f)
        # scaffold wrapper specific
        files_to_patch.append(
            repo_root / "skills" / "scaffold" / "subskills" / "typescript-scaffolding" / "SKILL.md"
        )
        files_to_patch.append(
            repo_root
            / "skills"
            / "scaffold"
            / "subskills"
            / "typescript-scaffolding"
            / "references"
            / "README.md"
        )
        # oxc references README (when renaming toolchain)
        files_to_patch.append(dst / "subskills" / "oxc" / "references" / "README.md")
        files_to_patch.append(
            skills_dir / new / "subskills" / "oxc" / "references" / "README.md"
            if not args.dry_run
            else skills_dir / old / "subskills" / "oxc" / "references" / "README.md"
        )

    # Deduplicate files_to_patch
    seen_p: set[pathlib.Path] = set()
    uniq_patch: list[pathlib.Path] = []
    for f in files_to_patch:
        rf = f.resolve() if f.exists() else f
        if rf not in seen_p:
            seen_p.add(rf)
            uniq_patch.append(f)
    files_to_patch = uniq_patch

    # Apply pairs
    for f in files_to_patch:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")  # ast-grep-ignore: python-path-traversal
        orig = text
        text = _apply_pairs_single_pass(text, pairs)
        if text != orig:
            if args.dry_run:
                print(f"  [dry-run] would patch {f.relative_to(repo_root)}")
            else:
                f.write_text(text, encoding="utf-8")
                print(f"  patched {f.relative_to(repo_root)}")

    # Sanity for toolchain case
    if not is_subskill:
        for f in files_to_patch:
            if f.exists() and f.read_text().count(f"{args.new_name}-wiki-wiki") > 0:
                print(f"warning: double wiki-wiki remaining in {f}", file=sys.stderr)

    print(
        f"done: {args.old_name} -> {args.new_name}"
        + (f" (parent {args.parent})" if is_subskill else "")
    )


if __name__ == "__main__":
    main()
