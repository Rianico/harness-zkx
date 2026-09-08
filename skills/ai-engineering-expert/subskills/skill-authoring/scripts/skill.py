#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["python-frontmatter>=1.0.0", "pyyaml>=6.0"]
# ///
"""
Skill lifecycle manager — add / remove / rename + dependency & hierarchy wiring.

Generalization of the former `rename.py`. Handles deterministic file moves +
frontmatter wiring; model supplies intent (names, relationships).

Usage:
  # legacy rename (backward compat):
  uv run $SKILL_DIR/scripts/skill.py <old> <new> [--parent P] [--dry-run]
  uv run $SKILL_DIR/scripts/skill.py --parent <parent> <old_sub> <new_sub> [--dry-run]

  # explicit subcommands (preferred):
  uv run $SKILL_DIR/scripts/skill.py rename <old> <new> [--parent P] [--dry-run]
  uv run $SKILL_DIR/scripts/skill.py add <name> [--parent P] [--description DESC] [--depends-on DEP]... [--dry-run]
  uv run $SKILL_DIR/scripts/skill.py remove <name> [--parent P] [--dry-run]
  uv run $SKILL_DIR/scripts/skill.py depend <skill> <dependency> [--parent P] [--dry-run]   # A relies on B
  uv run $SKILL_DIR/scripts/skill.py undepend <skill> <dependency> [--parent P] [--dry-run]
  uv run $SKILL_DIR/scripts/skill.py manage <parent> <child> [--dry-run]   # child is subskill of parent
  uv run $SKILL_DIR/scripts/skill.py unmanage <parent> <child> [--dry-run]

  # global:
  --cwd <path>  repo root override (must contain skills/ + pyproject.toml)
  --dry-run     preview without writing

Examples:
  # split OXC: create two subskills under toolchain-wiki
  uv run $SKILL_DIR/scripts/skill.py add oxlint --parent toolchain-wiki --description "Oxlint..."
  uv run $SKILL_DIR/scripts/skill.py add oxfmt --parent toolchain-wiki
  uv run $SKILL_DIR/scripts/skill.py depend typescript-scaffolding toolchain-wiki
  uv run $SKILL_DIR/scripts/skill.py manage toolchain-wiki oxlint

Information boundary: deterministic file moves + frontmatter replacements;
model supplies intent (names, dependencies, hierarchy).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys

try:
    import frontmatter  # type: ignore[import-not-found]
    import yaml  # type: ignore[import-not-found]

    HAS_FM = True
except Exception:  # noqa: BLE001
    frontmatter = None  # type: ignore[assignment]
    yaml = None  # type: ignore[assignment]
    HAS_FM = False


def repo_root_from_script(script_path: pathlib.Path) -> pathlib.Path:
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
    return s.replace("-", " ").replace("_", " ").title()


def _apply_pairs_single_pass(text: str, pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        return text
    pairs_sorted = sorted(pairs, key=lambda x: len(x[0]), reverse=True)
    mapping = {old: new for old, new in pairs_sorted}
    pattern = re.compile("|".join(re.escape(old) for old, _ in pairs_sorted))
    return pattern.sub(lambda m: mapping[m.group(0)], text)


def build_skill_pairs(old: str, new: str) -> list[tuple[str, str]]:
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
        (f"$SKILL_DIR/../../{old}/", f"$SKILL_DIR/../../{new}/"),
        (f"`{old}/subskills/oxc`", f"`{new}/subskills/oxc`"),
        (f"`{old}/subskills", f"`{new}/subskills"),
        (f"manage: [{old}]", f"manage: [{new}]"),
        (f"`{old}/subskills/oxc", f"`{new}/subskills/oxc"),
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


def build_subskill_pairs(parent: str, old: str, new: str) -> list[tuple[str, str]]:
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
        (f"manage: [{old}]", f"manage: [{new}]"),
        (f"manage: [{old},", f"manage: [{new},"),
        (f", {old},", f", {new},"),
        (f", {old}]", f", {new}]"),
        (f"[{old},", f"[{new},"),
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


# ---------------------------------------------------------------------------
# frontmatter helpers (frontmatter+ yaml when available, else regex fallback)
# ---------------------------------------------------------------------------


def _resolve_skill_file(
    repo_root: pathlib.Path, name: str, parent: str | None
) -> pathlib.Path | None:
    """Return SKILL.md path for skill/subskill if it exists, else None."""
    if parent:
        p = repo_root / "skills" / parent / "subskills" / name / "SKILL.md"
        if p.exists():
            return p
        # also check top-level with same name (for manage moves)
        return None
    p = repo_root / "skills" / name / "SKILL.md"
    if p.exists():
        return p
    # also check if it's a subskill somewhere (search)
    for cand in (repo_root / "skills").rglob("SKILL.md"):
        if cand.parent.name == name and cand.parent.parent.name == "subskills":
            return cand
    return None


def _skill_dir(repo_root: pathlib.Path, name: str, parent: str | None) -> pathlib.Path:
    if parent:
        return repo_root / "skills" / parent / "subskills" / name
    return repo_root / "skills" / name


def _load_meta(path: pathlib.Path) -> tuple[dict, str, str]:
    """Load frontmatter via python-frontmatter if available, else regex parse. Returns (meta, body, raw_text)."""
    text = path.read_text(encoding="utf-8")
    if HAS_FM:
        try:
            post = frontmatter.loads(text)  # type: ignore[union-attr]
            # post.metadata contains top-level keys (name, description, metadata, etc.)
            return dict(post.metadata), str(post.content), text
        except Exception:
            pass
    # fallback: regex parse frontmatter
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text, text
    fm_text, body = m.group(1), m.group(2)
    # naive yaml parse for metadata block if yaml available
    if yaml is not None:
        try:
            data = yaml.safe_load(fm_text)  # type: ignore[union-attr]
            if isinstance(data, dict):
                return data, body, text
        except Exception:
            pass
    return {}, body, text


def _write_meta(path: pathlib.Path, meta: dict, body: str, dry_run: bool = False) -> None:
    """Write SKILL.md with updated meta. Preserves body. Uses frontmatter/yaml if available."""
    if dry_run:
        return
    if HAS_FM:
        # Use frontmatter to dump; ensure description block scalar handling via yaml
        post = frontmatter.Post(body, **meta)  # type: ignore[union-attr]
        # frontmatter.dumps uses yaml.safe_dump; we post-process to ensure block scalars for description
        out = frontmatter.dumps(post)  # type: ignore[union-attr]
        # frontmatter.dumps may inline description; fix via regex if needed (ensure >-)
        # If description exists and is multiline, ensure it uses >-
        if (
            "description" in meta
            and isinstance(meta["description"], str)
            and "\n" in meta["description"]
        ):
            # already handled; but if dump inlined, we fix later via lint fix? keep as is
            pass
        path.write_text(out, encoding="utf-8")
        return
    # fallback: yaml dump frontmatter block
    if yaml is not None:
        fm_text = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)  # type: ignore[union-attr]
        out = f"---\n{fm_text}---\n\n{body.lstrip()}\n"
        path.write_text(out, encoding="utf-8")
        return
    # last resort: minimal write
    path.write_text(f"---\n{meta}\n---\n\n{body}", encoding="utf-8")


def _ensure_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def _update_list_in_meta(
    path: pathlib.Path,
    field_path: str,  # e.g. "metadata.depends-on" or "metadata.manage" or "metadata.managed-by"
    add: str | None = None,
    remove: str | None = None,
    set_value: str | list[str] | None = None,
    dry_run: bool = False,
) -> bool:
    """Update a frontmatter field. Returns True if changed."""
    meta, body, raw = _load_meta(path)
    # field_path may be nested like metadata.depends-on
    parts = field_path.split(".")
    # navigate to parent dict
    cur = meta
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    key = parts[-1]
    orig_val = cur.get(key)

    changed = False

    if set_value is not None:
        # set directly (for managed-by string)
        if isinstance(set_value, list):
            new_val = set_value
        else:
            new_val = set_value
        if orig_val != new_val:
            if new_val is None or (isinstance(new_val, list) and len(new_val) == 0):
                # remove key if empty list and caller wants removal? keep empty list for manage
                # For managed-by, removing means delete key
                if key == "managed-by" and (new_val is None or new_val == ""):
                    cur.pop(key, None)
                else:
                    cur[key] = new_val
            else:
                cur[key] = new_val
            changed = True
    else:
        # list add/remove
        lst = _ensure_list(orig_val)
        orig_set = set(lst)
        new_set = set(lst)
        if add is not None:
            if add not in new_set:
                new_set.add(add)
                # preserve original order + append
                lst = lst + [add] if add not in lst else lst
                # but use sorted? keep insertion order
                # Actually keep original order and append new at end
                if add not in orig_set:
                    lst = _ensure_list(orig_val) + [add] if orig_val is not None else [add]
                    cur[key] = lst
                    changed = True
        if remove is not None:
            if remove in new_set:
                lst = [x for x in _ensure_list(orig_val) if x != remove]
                cur[key] = lst
                changed = True
            else:
                # check if original had it
                pass

    if changed:
        if not dry_run:
            _write_meta(path, meta, body, dry_run=False)
        # cleanup empty metadata dict if needed
        # but keep metadata key even if empty? okay
    return changed


def _skill_title(name: str) -> str:
    return _title(name)


def _create_skill_file(
    path: pathlib.Path, name: str, description: str, managed_by: str | None, dry_run: bool = False
) -> None:
    if dry_run:
        print(f"  [dry-run] would create {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    meta: dict = {"name": name, "description": description}
    if managed_by:
        meta["metadata"] = {"managed-by": managed_by}
    body = f"# {_skill_title(name)}\n\nSkill `{name}` — placeholder. Update SKILL.md body with usage guidance.\n"
    _write_meta(path, meta, body, dry_run=False)
    print(f"  created {path}")


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------


def cmd_add(args: argparse.Namespace, repo_root: pathlib.Path) -> None:
    name: str = args.name
    parent: str | None = args.parent
    description: str = args.description or f"Domain guide for {name}. Use when ... TRIGGER: {name}"
    # ensure description uses block scalar when dumped -> ensure it is set correctly
    # If user provided inline, we keep as is; frontmatter will handle
    depends: list[str] = args.depends_on or []
    dry_run: bool = args.dry_run

    target_dir = _skill_dir(repo_root, name, parent)
    target_file = target_dir / "SKILL.md"

    if target_dir.exists():
        print(
            f"error: {'subskill' if parent else 'skill'} already exists: {target_dir}",
            file=sys.stderr,
        )
        sys.exit(2)
    if parent:
        parent_dir = repo_root / "skills" / parent
        if not parent_dir.is_dir():
            print(f"error: parent skill not found: {parent_dir}", file=sys.stderr)
            sys.exit(2)
    print(
        f"add {'subskill' if parent else 'skill'}: {name}"
        + (f" under {parent}" if parent else "")
        + (f" (repo: {repo_root})")
    )
    if dry_run:
        print("dry-run: no writes")

    # 1. create skill file
    # For subskill, create with managed-by
    if parent:
        _create_skill_file(target_file, name, description, parent, dry_run=dry_run)
    else:
        _create_skill_file(target_file, name, description, None, dry_run=dry_run)

    # 2. wire parent manage list
    if parent:
        parent_file = repo_root / "skills" / parent / "SKILL.md"
        if parent_file.exists():
            changed = _update_list_in_meta(
                parent_file, "metadata.manage", add=name, dry_run=dry_run
            )
            if changed:
                print(
                    f"  {'[dry-run] would update' if dry_run else 'updated'} {parent_file} manage += {name}"
                )
            else:
                print(f"  parent {parent} already manages {name}")
    # 3. wire depends-on if provided
    if depends:
        for dep in depends:
            changed = _update_list_in_meta(
                target_file, "metadata.depends-on", add=dep, dry_run=dry_run
            )
            if changed:
                print(
                    f"  {'[dry-run] would update' if dry_run else 'updated'} {target_file} depends-on += {dep}"
                )
    print("done: add")


def cmd_remove(args: argparse.Namespace, repo_root: pathlib.Path) -> None:
    name: str = args.name
    parent: str | None = args.parent
    dry_run: bool = args.dry_run

    if parent:
        target_dir = repo_root / "skills" / parent / "subskills" / name
        if not target_dir.is_dir():
            print(f"error: subskill not found: {target_dir}", file=sys.stderr)
            sys.exit(2)
        print(f"remove subskill: {parent}/{name} (repo: {repo_root})")
        if dry_run:
            print("dry-run: no writes")
        else:
            try:
                shutil.rmtree(target_dir)
            except OSError as e:
                print(f"error: failed to remove {target_dir}: {e}", file=sys.stderr)
                sys.exit(1)
            print(f"  removed {target_dir}")
        # update parent manage
        parent_file = repo_root / "skills" / parent / "SKILL.md"
        if parent_file.exists():
            changed = _update_list_in_meta(
                parent_file, "metadata.manage", remove=name, dry_run=dry_run
            )
            if changed:
                print(
                    f"  {'[dry-run] would update' if dry_run else 'updated'} {parent_file} manage -= {name}"
                )
        # warn about dependents scanning
        # (optional) scan for depends-on / managed-by references
        for f in (repo_root / "skills").rglob("SKILL.md"):
            if not f.exists():
                continue
            text = f.read_text(encoding="utf-8")
            if name in text and f != parent_file:
                print(
                    f"  note: {f.relative_to(repo_root)} still references {name} (manual cleanup may be needed)"
                )
    else:
        target_dir = repo_root / "skills" / name
        if not target_dir.is_dir():
            print(f"error: skill not found: {target_dir}", file=sys.stderr)
            sys.exit(2)
        print(f"remove skill: {name} (repo: {repo_root})")
        if dry_run:
            print("dry-run: no writes")
        else:
            try:
                shutil.rmtree(target_dir)
            except OSError as e:
                print(f"error: failed to remove {target_dir}: {e}", file=sys.stderr)
                sys.exit(1)
            print(f"  removed {target_dir}")
        # warn about dependents
        for f in (repo_root / "skills").rglob("SKILL.md"):
            if not f.exists():
                continue
            text = f.read_text(encoding="utf-8")
            if name in text:
                print(f"  note: {f.relative_to(repo_root)} still references {name}")
    print("done: remove")


def cmd_depend(args: argparse.Namespace, repo_root: pathlib.Path) -> None:
    skill: str = args.skill
    dep: str = args.dependency
    parent: str | None = args.parent
    dry_run: bool = args.dry_run

    # resolve skill file
    skill_file = _resolve_skill_file(repo_root, skill, parent)
    if skill_file is None:
        # try subskill location explicitly
        if parent:
            cand = repo_root / "skills" / parent / "subskills" / skill / "SKILL.md"
            if cand.exists():
                skill_file = cand
        if skill_file is None:
            print(
                f"error: skill not found: {skill}" + (f" (parent {parent})" if parent else ""),
                file=sys.stderr,
            )
            sys.exit(2)
    print(f"depend: {skill} relies on {dep}" + (f" (parent {parent})" if parent else ""))
    if dry_run:
        print("dry-run: no writes")
    changed = _update_list_in_meta(skill_file, "metadata.depends-on", add=dep, dry_run=dry_run)
    if changed:
        print(
            f"  {'[dry-run] would update' if dry_run else 'updated'} {skill_file} depends-on += {dep}"
        )
    else:
        print(f"  already depends on {dep}")
    print("done: depend")


def cmd_undepend(args: argparse.Namespace, repo_root: pathlib.Path) -> None:
    skill: str = args.skill
    dep: str = args.dependency
    parent: str | None = args.parent
    dry_run: bool = args.dry_run
    skill_file = _resolve_skill_file(repo_root, skill, parent)
    if skill_file is None:
        if parent:
            cand = repo_root / "skills" / parent / "subskills" / skill / "SKILL.md"
            if cand.exists():
                skill_file = cand
        if skill_file is None:
            print(f"error: skill not found: {skill}", file=sys.stderr)
            sys.exit(2)
    print(f"undepend: {skill} no longer relies on {dep}")
    if dry_run:
        print("dry-run: no writes")
    changed = _update_list_in_meta(skill_file, "metadata.depends-on", remove=dep, dry_run=dry_run)
    if changed:
        print(
            f"  {'[dry-run] would update' if dry_run else 'updated'} {skill_file} depends-on -= {dep}"
        )
    else:
        print(f"  was not depending on {dep}")
    print("done: undepend")


def cmd_manage(args: argparse.Namespace, repo_root: pathlib.Path) -> None:
    parent: str = args.parent
    child: str = args.child
    dry_run: bool = args.dry_run
    # locate parent
    parent_file = repo_root / "skills" / parent / "SKILL.md"
    if not parent_file.exists():
        print(f"error: parent skill not found: {parent}", file=sys.stderr)
        sys.exit(2)
    # locate child: could be top-level or subskill
    child_top_dir = repo_root / "skills" / child
    child_top_file = child_top_dir / "SKILL.md"
    child_sub_dir = repo_root / "skills" / parent / "subskills" / child
    child_sub_file = child_sub_dir / "SKILL.md"

    child_file: pathlib.Path | None = None
    needs_move = False

    if child_sub_dir.is_dir():
        child_file = child_sub_file
        print(f"manage: {child} is already subskill of {parent} — ensuring wiring")
    elif child_top_dir.is_dir():
        child_file = child_top_file
        needs_move = True
        print(
            f"manage: {child} is top-level skill — will move to {parent}/subskills/{child} and wire"
        )
    else:
        print(
            f"error: child skill not found: {child} (checked {child_top_dir} and {child_sub_dir})",
            file=sys.stderr,
        )
        sys.exit(2)

    if dry_run:
        print("dry-run: no writes")

    # 1. update parent manage list
    changed_parent = _update_list_in_meta(
        parent_file, "metadata.manage", add=child, dry_run=dry_run
    )
    if changed_parent:
        print(
            f"  {'[dry-run] would update' if dry_run else 'updated'} {parent_file} manage += {child}"
        )
    else:
        print(f"  parent {parent} already manages {child}")

    # 2. update child managed-by
    if child_file is not None and child_file.exists():
        # if needs_move, we will update after move; else update in place
        # For dry-run, just show intent
        if needs_move:
            # after move, file will be at child_sub_file
            # we can update the original file's managed-by then move, or move then update dest
            # Do: update original then move (so dest has correct)
            if not dry_run:
                _update_list_in_meta(
                    child_file, "metadata.managed-by", set_value=parent, dry_run=False
                )
                # now move directory
                child_top_dir.rename(child_sub_dir)
                print(
                    f"  moved {child_top_dir.relative_to(repo_root)} -> {child_sub_dir.relative_to(repo_root)}"
                )
                print(f"  updated {child_sub_file} managed-by = {parent}")
            else:
                print(f"  [dry-run] would update {child_file} managed-by = {parent}")
                print(
                    f"  [dry-run] would move {child_top_dir.relative_to(repo_root)} -> {child_sub_dir.relative_to(repo_root)}"
                )
        else:
            changed_child = _update_list_in_meta(
                child_file, "metadata.managed-by", set_value=parent, dry_run=dry_run
            )
            if changed_child:
                print(
                    f"  {'[dry-run] would update' if dry_run else 'updated'} {child_file} managed-by = {parent}"
                )
            else:
                print(f"  child {child} already managed-by {parent}")
    print("done: manage")


def cmd_unmanage(args: argparse.Namespace, repo_root: pathlib.Path) -> None:
    parent: str = args.parent
    child: str = args.child
    dry_run: bool = args.dry_run
    parent_file = repo_root / "skills" / parent / "SKILL.md"
    if not parent_file.exists():
        print(f"error: parent skill not found: {parent}", file=sys.stderr)
        sys.exit(2)
    child_sub_dir = repo_root / "skills" / parent / "subskills" / child
    child_sub_file = child_sub_dir / "SKILL.md"
    child_top_dir = repo_root / "skills" / child
    # determine where child currently lives
    if child_sub_dir.is_dir():
        # remove from parent manage, clear child's managed-by, optionally move back to top-level?
        print(f"unmanage: {child} from {parent} (currently subskill)")
        if dry_run:
            print("dry-run: no writes")
        changed_parent = _update_list_in_meta(
            parent_file, "metadata.manage", remove=child, dry_run=dry_run
        )
        if changed_parent:
            print(
                f"  {'[dry-run] would update' if dry_run else 'updated'} {parent_file} manage -= {child}"
            )
        changed_child = _update_list_in_meta(
            child_sub_file, "metadata.managed-by", set_value=None, dry_run=dry_run
        )
        if changed_child:
            print(
                f"  {'[dry-run] would update' if dry_run else 'updated'} {child_sub_file} managed-by cleared"
            )
        # optionally move back to top-level? For now keep as subskill directory but unwired; user can move manually or we move if top doesn't exist
        # If child_top_dir doesn't exist, we move subskill to top-level for cleanliness
        if not child_top_dir.exists():
            if dry_run:
                print(
                    f"  [dry-run] would move {child_sub_dir.relative_to(repo_root)} -> {child_top_dir.relative_to(repo_root)}"
                )
            else:
                child_sub_dir.rename(child_top_dir)
                print(
                    f"  moved {child_sub_dir.relative_to(repo_root)} -> {child_top_dir.relative_to(repo_root)} (now top-level)"
                )
        else:
            print(
                f"  note: {child_top_dir} already exists, leaving subskill directory in place (now unwired)"
            )
    elif (repo_root / "skills" / child).is_dir():
        # child is top-level but parent claims to manage it? just remove from manage and clear managed-by if present
        child_top_file = repo_root / "skills" / child / "SKILL.md"
        print(f"unmanage: {child} from {parent} (currently top-level, just unwiring)")
        if dry_run:
            print("dry-run: no writes")
        changed_parent = _update_list_in_meta(
            parent_file, "metadata.manage", remove=child, dry_run=dry_run
        )
        if changed_parent:
            print(
                f"  {'[dry-run] would update' if dry_run else 'updated'} {parent_file} manage -= {child}"
            )
        if child_top_file.exists():
            changed_child = _update_list_in_meta(
                child_top_file, "metadata.managed-by", set_value=None, dry_run=dry_run
            )
            if changed_child:
                print(
                    f"  {'[dry-run] would update' if dry_run else 'updated'} {child_top_file} managed-by cleared"
                )
    else:
        print(f"error: child not found as subskill or top-level: {child}", file=sys.stderr)
        sys.exit(2)
    print("done: unmanage")


# original rename logic wrappers
def do_rename_skill(old: str, new: str, repo_root: pathlib.Path, dry_run: bool) -> None:
    skills_dir = repo_root / "skills"
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
    if dry_run:
        print("dry-run: no writes")
    if not dry_run:
        old_dir.rename(new_dir)
        print(f"moved {old_dir.relative_to(repo_root)} -> {new_dir.relative_to(repo_root)}")
    else:
        print(
            f"  [dry-run] would move {old_dir.relative_to(repo_root)} -> {new_dir.relative_to(repo_root)}"
        )
    pairs = build_skill_pairs(old, new)
    dst = new_dir if not dry_run else old_dir
    files_to_patch: list[pathlib.Path] = []
    files_to_patch.append(dst / "SKILL.md")
    subskills_dir = dst / "subskills"
    if subskills_dir.exists() or (old_dir / "subskills").exists():
        sd = subskills_dir if not dry_run else old_dir / "subskills"
        if sd.is_dir():
            for sub in sd.iterdir():
                if sub.is_dir():
                    files_to_patch.append(sub / "SKILL.md")
        for sub in ["oxc", "typecheck", "worktree"]:
            p = dst / "subskills" / sub / "SKILL.md"
            if p not in files_to_patch:
                files_to_patch.append(p)
            p2 = (old_dir if dry_run else dst) / "subskills" / sub / "SKILL.md"
            if p2 not in files_to_patch:
                files_to_patch.append(p2)
    for f in skills_dir.rglob("SKILL.md"):
        if f not in files_to_patch:
            files_to_patch.append(f)
    for f in skills_dir.rglob("README.md"):
        if f not in files_to_patch:
            files_to_patch.append(f)
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
    files_to_patch.append(dst / "subskills" / "oxc" / "references" / "README.md")
    files_to_patch.append(
        skills_dir / new / "subskills" / "oxc" / "references" / "README.md"
        if not dry_run
        else skills_dir / old / "subskills" / "oxc" / "references" / "README.md"
    )
    seen_p: set[pathlib.Path] = set()
    uniq_patch: list[pathlib.Path] = []
    for f in files_to_patch:
        rf = f.resolve() if f.exists() else f
        if rf not in seen_p:
            seen_p.add(rf)
            uniq_patch.append(f)
    files_to_patch = uniq_patch
    for f in files_to_patch:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        orig = text
        text = _apply_pairs_single_pass(text, pairs)
        if text != orig:
            if dry_run:
                print(f"  [dry-run] would patch {f.relative_to(repo_root)}")
            else:
                f.write_text(text, encoding="utf-8")
                print(f"  patched {f.relative_to(repo_root)}")
    print(f"done: {old} -> {new}")


def do_rename_subskill(
    parent: str, old_sub: str, new_sub: str, repo_root: pathlib.Path, dry_run: bool
) -> None:
    skills_dir = repo_root / "skills"
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
    if dry_run:
        print("dry-run: no writes")
    if not dry_run:
        old_dir.rename(new_dir)
        print(f"moved {old_dir.relative_to(repo_root)} -> {new_dir.relative_to(repo_root)}")
    else:
        print(
            f"  [dry-run] would move {old_dir.relative_to(repo_root)} -> {new_dir.relative_to(repo_root)}"
        )
    pairs = build_subskill_pairs(parent, old_sub, new_sub)
    files_to_patch: list[pathlib.Path] = []
    files_to_patch.append(new_dir / "SKILL.md" if not dry_run else old_dir / "SKILL.md")
    files_to_patch.append(skills_dir / parent / "SKILL.md")
    parent_subskills = skills_dir / parent / "subskills"
    if parent_subskills.is_dir():
        for sub in parent_subskills.iterdir():
            if sub.is_dir():
                files_to_patch.append(sub / "SKILL.md")
    for f in skills_dir.rglob("SKILL.md"):
        if f not in files_to_patch:
            files_to_patch.append(f)
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
    files_to_patch.append(
        skills_dir / parent / "subskills" / new_sub / "references" / "README.md"
        if not dry_run
        else skills_dir / parent / "subskills" / old_sub / "references" / "README.md"
    )
    for f in skills_dir.rglob("README.md"):
        if f not in files_to_patch:
            files_to_patch.append(f)
    seen_p: set[pathlib.Path] = set()
    uniq_patch: list[pathlib.Path] = []
    for f in files_to_patch:
        rf = f.resolve() if f.exists() else f
        if rf not in seen_p:
            seen_p.add(rf)
            uniq_patch.append(f)
    files_to_patch = uniq_patch
    for f in files_to_patch:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        orig = text
        text = _apply_pairs_single_pass(text, pairs)
        if text != orig:
            if dry_run:
                print(f"  [dry-run] would patch {f.relative_to(repo_root)}")
            else:
                f.write_text(text, encoding="utf-8")
                print(f"  patched {f.relative_to(repo_root)}")
    print(f"done: {old_sub} -> {new_sub} (parent {parent})")


def main() -> None:
    # Detect legacy positional rename without subcommand: `rename.py old new` or `rename.py --parent P old new`
    # We handle this by inspecting argv before argparse subparsers
    raw = sys.argv[1:]
    subcmds = {"rename", "add", "remove", "depend", "undepend", "manage", "unmanage"}
    _flags_with_val = {"--cwd", "--parent", "--description", "--depends-on"}
    has_subcmd = False
    _i = 0
    while _i < len(raw):
        _tok = raw[_i]
        if _tok.startswith("--") and "=" in _tok:
            _flag = _tok.split("=", 1)[0]
            if _flag in _flags_with_val:
                _i += 1
                continue
            _i += 1
            continue
        if _tok in _flags_with_val:
            _i += 2
            continue
        if _tok in ("--dry-run", "-h", "--help"):
            _i += 1
            continue
        if _tok.startswith("-"):
            _i += 1
            continue
        if _tok in subcmds:
            has_subcmd = True
        break
    if not has_subcmd:
        _positionals: list[str] = []
        _j = 0
        while _j < len(raw):
            _t = raw[_j]
            if _t.startswith("--") and "=" in _t:
                _j += 1
                continue
            if _t in _flags_with_val:
                _j += 2
                continue
            if _t in ("--dry-run", "-h", "--help"):
                _j += 1
                continue
            if _t.startswith("-"):
                _j += 1
                continue
            _positionals.append(_t)
            _j += 1
        if len(_positionals) >= 2:
            # Legacy rename path: use original parser
            ap = argparse.ArgumentParser(
                description="Skill lifecycle manager — legacy rename compat"
            )
            ap.add_argument(
                "old_name", help="Current skill name (or old subskill name when --parent is used)"
            )
            ap.add_argument("new_name", help="New skill/subskill name")
            ap.add_argument(
                "--parent", dest="parent", default=None, help="Parent skill for subskill rename"
            )
            ap.add_argument("--dry-run", action="store_true", help="preview without writing")
            ap.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")
            args = ap.parse_args()
            script_path = pathlib.Path(__file__)
            repo_root = args.cwd.resolve() if args.cwd else repo_root_from_script(script_path)
            if not (repo_root / "skills").is_dir():
                print(
                    f"error: cannot locate repo root from {script_path} (guessed {repo_root})",
                    file=sys.stderr,
                )
                sys.exit(2)
            if args.parent:
                do_rename_subskill(
                    args.parent, args.old_name, args.new_name, repo_root, args.dry_run
                )
            else:
                do_rename_skill(args.old_name, args.new_name, repo_root, args.dry_run)
            return
        # else no positional -> fall through to subcommand help

    # Subcommand mode
    ap = argparse.ArgumentParser(
        description="Skill lifecycle manager — add/remove/rename + dependency & hierarchy wiring"
    )
    ap.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")
    ap.add_argument("--dry-run", action="store_true", help="preview without writing (global)")
    sub = ap.add_subparsers(dest="command", required=True)

    p_rename = sub.add_parser("rename", help="Rename a skill or subskill and cascade references")
    p_rename.add_argument("old_name", help="Current skill/subskill name")
    p_rename.add_argument("new_name", help="New name")
    p_rename.add_argument(
        "--parent", dest="parent", default=None, help="Parent skill for subskill rename"
    )
    p_rename.add_argument("--dry-run", action="store_true", help="preview without writing")
    p_rename.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")

    p_add = sub.add_parser("add", help="Add a new skill or subskill")
    p_add.add_argument("name", help="New skill/subskill name")
    p_add.add_argument(
        "--parent", dest="parent", default=None, help="Parent skill if creating a subskill"
    )
    p_add.add_argument(
        "--description",
        dest="description",
        default=None,
        help="Frontmatter description (uses block scalar)",
    )
    p_add.add_argument(
        "--depends-on",
        dest="depends_on",
        action="append",
        default=None,
        help="Initial dependency (repeatable)",
    )
    p_add.add_argument("--dry-run", action="store_true", help="preview without writing")
    p_add.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")

    p_remove = sub.add_parser("remove", help="Remove a skill or subskill")
    p_remove.add_argument("name", help="Skill/subskill name to remove")
    p_remove.add_argument(
        "--parent", dest="parent", default=None, help="Parent skill if removing a subskill"
    )
    p_remove.add_argument("--dry-run", action="store_true", help="preview without writing")
    p_remove.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")

    p_depend = sub.add_parser(
        "depend", help="Declare that <skill> relies on <dependency> (A relies on B)"
    )
    p_depend.add_argument("skill", help="Skill that will depend on another (A)")
    p_depend.add_argument("dependency", help="Dependency skill (B)")
    p_depend.add_argument(
        "--parent", dest="parent", default=None, help="Parent if skill is a subskill"
    )
    p_depend.add_argument("--dry-run", action="store_true", help="preview without writing")
    p_depend.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")

    p_undepend = sub.add_parser("undepend", help="Remove a depends-on relationship")
    p_undepend.add_argument("skill", help="Skill to modify")
    p_undepend.add_argument("dependency", help="Dependency to remove")
    p_undepend.add_argument(
        "--parent", dest="parent", default=None, help="Parent if skill is a subskill"
    )
    p_undepend.add_argument("--dry-run", action="store_true", help="preview without writing")
    p_undepend.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")

    p_manage = sub.add_parser(
        "manage", help="Make <child> a subskill of <parent> (parent manages child)"
    )
    p_manage.add_argument("parent", help="Parent skill (B)")
    p_manage.add_argument("child", help="Child skill/subskill (A)")
    p_manage.add_argument("--dry-run", action="store_true", help="preview without writing")
    p_manage.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")

    p_unmanage = sub.add_parser("unmanage", help="Remove parent-child manage relationship")
    p_unmanage.add_argument("parent", help="Parent skill")
    p_unmanage.add_argument("child", help="Child skill/subskill")
    p_unmanage.add_argument("--dry-run", action="store_true", help="preview without writing")
    p_unmanage.add_argument("--cwd", type=pathlib.Path, default=None, help="repo root override")
    args = ap.parse_args()
    script_path = pathlib.Path(__file__)
    # effective cwd/dry_run: support --dry-run / --cwd either before or after subcommand
    _eff_cwd = getattr(args, "cwd", None)
    if _eff_cwd is None:
        for _i, _tok in enumerate(sys.argv):
            if _tok == "--cwd" and _i + 1 < len(sys.argv):
                _eff_cwd = pathlib.Path(sys.argv[_i + 1])
                break
            if _tok.startswith("--cwd="):
                _eff_cwd = pathlib.Path(_tok.split("=", 1)[1])
                break
    _eff_dry = bool(getattr(args, "dry_run", False) or ("--dry-run" in sys.argv))
    # stash effective values back onto args for downstream commands
    args.cwd = _eff_cwd  # type: ignore[attr-defined]
    args.dry_run = _eff_dry  # type: ignore[attr-defined]
    repo_root = _eff_cwd.resolve() if _eff_cwd else repo_root_from_script(script_path)
    if not (repo_root / "skills").is_dir():
        print(
            f"error: cannot locate repo root from {script_path} (guessed {repo_root})",
            file=sys.stderr,
        )
        sys.exit(2)
    # propagate global dry-run to command-specific if needed (argparse already global)
    # but subparsers don't inherit; we set it as global attribute
    # args.dry_run is global, ensure each command sees it
    if args.command == "rename":
        if args.parent:
            do_rename_subskill(args.parent, args.old_name, args.new_name, repo_root, args.dry_run)
        else:
            do_rename_skill(args.old_name, args.new_name, repo_root, args.dry_run)
    elif args.command == "add":
        cmd_add(args, repo_root)
    elif args.command == "remove":
        cmd_remove(args, repo_root)
    elif args.command == "depend":
        cmd_depend(args, repo_root)
    elif args.command == "undepend":
        cmd_undepend(args, repo_root)
    elif args.command == "manage":
        cmd_manage(args, repo_root)
    elif args.command == "unmanage":
        cmd_unmanage(args, repo_root)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
