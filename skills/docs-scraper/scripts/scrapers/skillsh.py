#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "beautifulsoup4",
#   "requests",
# ]
# ///
"""Skill.sh scraper — fetch complementary agent skills from skill.sh / GitHub.

skill.sh is a *catalog*; the actual SKILL.md content lives in GitHub repos.
This scraper therefore treats skill.sh as the mapping + metadata source and
fetches real skill files (SKILL.md + references/ + scripts/) from GitHub.
It is deterministic about fetching and staging; ALL composition/merging is
left to the LLM (see references/skillsh-compose.md, guided by the
ai-engineering-expert methodology).

Workflow
--------
Phase A (this module, deterministic):
    parse inputs -> resolve each to a GitHub repo -> fetch the skill's files
    -> stage them under <staging_root>/<run>/stage/<repo>/<skill>/ and write a
    SOURCES.md index (verbatim frontmatter only — no composition).

Phases B+C (LLM, NOT this module):
    read the staged sources + ai-engineering-expert, then compose/reorganize
    them into ONE new skill written to <staging_root>/<run>/out/<new_skill>/.

Input forms
-----------
    scrape.py skills https://www.skills.sh/<owner>/<collection>/<skill> ...
    scrape.py skills <owner>/<collection>/<skill> ...
    scrape.py skills https://github.com/<org>/<repo> ...
    (one or many inputs — for composing complementary skills across repos)

Fetch methods
-------------
    raw   (default for explicit skills)  contents API walk + raw.githubusercontent
    clone (default for whole collections) git clone --depth 1
    npx   (opt-in)  delegate to `npx skills` inside a temp project, then harvest
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from .base import DocumentationScraper

# Repos whose links appear on every skill.sh page but are NOT the target
# collection repo (skills.sh's own product repo, etc.).
NOISE_REPOS = {"vercel-labs/skills", "vercel/skills", "skillsdotsh/skills"}

DEFAULT_STAGING_ROOT = ".lsz/tmp/skill-compose"


class SkillResolveError(Exception):
    """Raised when a skill.sh input cannot be resolved to a GitHub skill."""


def _strip_scheme(source: str) -> tuple[str, str | None]:
    """Return (path_without_scheme, host) for an http(s) or bare source."""
    m = re.match(r"^https?://([^/]+)(/.*)?$", source.strip())
    if m:
        host = m.group(1).lower().rstrip(".")
        rest = (m.group(2) or "").strip("/")
        return rest, host
    return source.strip().strip("/"), None


def parse_skill_source(source: str) -> dict[str, Any]:
    """Parse a skill input into structured parts.

    Handles:
        https://www.skills.sh/<owner>/<collection>/<skill>
        https://github.com/<org>/<repo>[/tree/<branch>/<path>]
        <owner>/<collection>[/<skill>]           (bare)
        <org>/<repo>                             (bare repo)
    """
    s = source.strip()
    rest, host = _strip_scheme(s)
    parts = [p for p in rest.split("/") if p]
    out: dict[str, Any] = {"original": source, "host": host, "kind": "bare"}

    if host and ("skills.sh" in host or skillsh_suffix(host)):
        # skills.sh/<owner>/<collection>[/<skill>]
        out["kind"] = "skillsh"
        out["owner"] = parts[0] if parts else None
        out["collection"] = parts[1] if len(parts) >= 2 else None
        out["skill"] = parts[2] if len(parts) >= 3 else None
        if out["owner"] and out["collection"]:
            out["repo_url"] = (
                f"https://github.com/{out['owner']}/{out['collection']}"
            )
            out["repo_hint"] = f"{out['owner']}/{out['collection']}"
    elif host and "github.com" in host:
        out["kind"] = "github"
        out["owner"] = parts[0] if parts else None
        out["collection"] = parts[1] if len(parts) >= 2 else None
        out["skill"] = parts[2] if len(parts) >= 3 else None
        out["repo_path"] = "/".join(parts[3:]) if len(parts) > 3 else None
        if out["owner"] and out["collection"]:
            out["repo_url"] = f"https://github.com/{out['owner']}/{out['collection']}"
            out["repo_hint"] = f"{out['owner']}/{out['collection']}"
    else:
        out["kind"] = "bare"
        if len(parts) >= 2:
            out["owner"], out["collection"] = parts[0], parts[1]
            out["repo_url"] = f"https://github.com/{parts[0]}/{parts[1]}"
            out["repo_hint"] = f"{parts[0]}/{parts[1]}"
        out["skill"] = parts[2] if len(parts) >= 3 else None
    return out


def skillsh_suffix(host: str | None) -> bool:
    """True if host is a skills.sh-style domain (www.skills.sh, skills.sh)."""
    if not host:
        return False
    return host == "skills.sh" or host.endswith(".skills.sh")


def extract_github_repo_from_html(html: str) -> str | None:
    """Extract the target collection's GitHub repo URL from a skill.sh page.

    Returns the first absolute github.com/<org>/<repo> link that is not a
    known skills.sh product/noise repo (the skill.sh page links its own
    product repo, e.g. vercel-labs/skills, in the footer).
    """
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.match(r"^https?://github\.com/([^/]+/[^/]+)", href)
        if m and m.group(1).lower() not in {r.lower() for r in NOISE_REPOS}:
            candidates.append(m.group(1))
    if candidates:
        return f"https://github.com/{candidates[0]}"
    return None

def _parse_frontmatter_block(markdown: str) -> dict[str, str]:
    """Extract the leading YAML frontmatter block as raw key: value lines."""
    stripped = markdown.lstrip("\ufeff")
    if not stripped.startswith("---"):
        return {}
    end = stripped.find("\n---", 3)
    if end == -1:
        return {}
    block = stripped[3:end]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        line = line.rstrip("\r")
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip()
    return fields


class SkillshScraper(DocumentationScraper):
    """Fetch and stage complementary agent skills from skill.sh / GitHub."""

    name: str = "skills"
    description: str = """Fetch complementary agent skills from skill.sh/GitHub and stage them for
LLM composition into a single new skill (guided by ai-engineering-expert).

scrape.py skills <url-or-owner/collection/skill>... [--run R] [--method auto|raw|clone|npx]

Fetching/staging is deterministic; composition is an LLM step (see
references/skillsh-compose.md)."""

    def __init__(
        self,
        sources: list[str] | None = None,
        output_dir: Path | None = None,
        run: str | None = None,
        method: str = "auto",
        force: bool = False,
        **kwargs: Any,
    ) -> None:
        self.sources = [s for s in (sources or []) if s and s.strip()]
        self.method = (method or "auto").lower()
        self.run_arg = run
        if output_dir is None:
            output_dir = Path(DEFAULT_STAGING_ROOT)
        self.staging_root = Path(output_dir)
        # GitHub/raw fetches are not site crawls; skip robots.txt handling.
        kwargs.setdefault("respect_robots_txt", False)
        kwargs.setdefault("delay", 0.3)
        super().__init__(
            base_url="", output_dir=self.staging_root, force=force, **kwargs
        )

    # -- orchestration ------------------------------------------------------

    def run(self) -> None:
        if not self.sources:
            raise SkillResolveError("No skill sources provided.")
        run_dir = self._resolve_run_dir()
        stage_dir = run_dir / "stage"
        out_dir = run_dir / "out"
        stage_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        inventory: list[dict[str, Any]] = []
        for src in self.sources:
            parsed = parse_skill_source(src)
            print(f"\n[{src}]")
            repo = self._resolve_repo(parsed, src)
            skill = parsed.get("skill")
            method = self._choose_method(parsed)
            try:
                result = self._fetch(method, repo, skill, stage_dir)
                result.update({"source": src, "repo": repo, "skill": skill})
                inventory.append(result)
            except SkillResolveError as e:
                print(f"  SKIP {src}: {e}")

        self._write_sources_index(stage_dir, inventory)
        print(f"\nStaged to: {stage_dir}")
        print(f"Compose target (LLM): {out_dir}")
        print("Next: read references/skillsh-compose.md and compose.")

    # -- run + path helpers ------------------------------------------------

    def _resolve_run_dir(self) -> Path:
        root = self.staging_root
        root.mkdir(parents=True, exist_ok=True)
        if self.run_arg:
            base = self.sanitize_filename(self.run_arg) or "run"
            d = root / base
            d.mkdir(parents=True, exist_ok=True)
            return d
        hint = self._auto_slug() or "run"
        d = root / hint
        n = 1
        while d.exists():
            d = root / f"{hint}-{n}"
            n += 1
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _auto_slug(self) -> str | None:
        if not self.sources:
            return None
        parsed = parse_skill_source(self.sources[0])
        name = parsed.get("skill") or parsed.get("collection") or parsed.get("repo_hint")
        if not name:
            return None
        slug = name.replace("/", "-")
        return self.sanitize_filename(slug) or "run"

    def _choose_method(self, parsed: dict[str, Any]) -> str:
        if self.method in ("raw", "clone", "npx"):
            return self.method
        # auto: whole collections (no explicit skill) -> clone; else raw.
        return "clone" if not parsed.get("skill") else "raw"

    # -- repos --------------------------------------------------------------

    def _split_repo(self, repo: str) -> tuple[str, str]:
        path = repo.replace("https://github.com/", "").replace("github.com/", "").strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            raise SkillResolveError(f"Not a repo: {repo}")
        return parts[0], parts[1]

    def _resolve_repo(self, parsed: dict[str, Any], src: str) -> str:
        # skill.sh URLs: the page's GitHub link is authoritative (skills.sh
        # owner need not equal the GitHub org). Fetch it, fall back to the
        # conventional github.com/<owner>/<collection> on any failure.
        if parsed.get("kind") == "skillsh" and parsed.get("owner") and parsed.get("collection"):
            page_url = f"https://www.skills.sh/{parsed['owner']}/{parsed['collection']}"
            soup = self.fetch_page(page_url, cache_file="skillsh-collection.html")
            if soup is not None:
                repo = extract_github_repo_from_html(str(soup))
                if repo:
                    return repo
            if parsed.get("repo_url"):
                return parsed["repo_url"]
        if parsed.get("repo_url"):
            return parsed["repo_url"]
        raise SkillResolveError(f"Cannot resolve GitHub repo for {src}")

    def _api_json(self, url: str) -> Any:
        resp = self._rate_limited_get(url)
        if resp is None:
            return None
        try:
            return resp.json()
        except ValueError:
            return None

    def _default_branch(self, org: str, repo: str) -> str:
        info = self._api_json(
            f"https://api.github.com/repos/{org}/{repo}"
        )
        if isinstance(info, dict) and info.get("default_branch"):
            return info["default_branch"]
        return "main"

    def _contents(self, org: str, repo: str, branch: str, path: str) -> list[dict[str, Any]] | None:
        data = self._api_json(
            f"https://api.github.com/repos/{org}/{repo}/contents/{path}?ref={branch}"
        )
        if isinstance(data, list):
            return data
        return None

    # -- fetch --------------------------------------------------------------

    def _fetch(self, method: str, repo: str, skill: str | None, stage_dir: Path) -> dict[str, Any]:
        if method == "clone":
            return self._fetch_by_clone(repo, skill, stage_dir)
        if method == "npx":
            return self._fetch_by_npx(repo, skill, stage_dir)
        return self._fetch_by_raw(repo, skill, stage_dir)

    def _fetch_by_raw(
        self, repo: str, skill: str | None, stage_dir: Path
    ) -> dict[str, Any]:
        org, repo_name = self._split_repo(repo)
        branch = self._default_branch(org, repo_name)
        skill_path = self._find_skill_path(org, repo_name, branch, skill)

        if skill is None:
            # Fetch every skill in the repo's skills/ dir.
            return self._fetch_all_raw(org, repo_name, branch, stage_dir)

        if not skill_path:
            raise SkillResolveError(
                f"Skill dir not found for '{skill}' in {org}/{repo_name}"
            )

        files = self._collect_files(org, repo_name, branch, skill_path)
        dest = stage_dir / self._repo_slug(org, repo_name) / skill
        dest.mkdir(parents=True, exist_ok=True)
        n = 0
        for rel, download_url in files:
            content = self._fetch_text(download_url)
            if content is None:
                continue
            out_file = dest / rel[len(skill_path):].lstrip("/")
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding="utf-8")
            n += 1
        print(f"  staged {org}/{repo_name}/{skill}: {n} files -> {dest}")
        return {"staged": str(dest), "methods": ["raw"], "files": n, "skill": skill}

    def _find_skill_path(self, org: str, repo: str, branch: str, skill: str) -> str | None:
        candidates = [f"skills/{skill}", skill]
        for cand in candidates:
            if self._contents(org, repo, branch, cand) is not None:
                return cand
        # Root SKILL.md when skill matches the repo id (single-skill repos).
        root = self._contents(org, repo, branch, "")
        if isinstance(root, list) and skill:
            for e in root:
                if e.get("type") == "file" and e.get("name") == "SKILL.md":
                    if skill in (repo, self._repo_slug(org, repo).replace("_", "-")):
                        return ""
        return None

    def _collect_files(
        self, org: str, repo: str, branch: str, path: str
    ) -> list[tuple[str, str]]:
        files: list[tuple[str, str]] = []
        stack = [path] if path else [""]
        visited: set[str] = set()
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            entries = self._contents(org, repo, branch, cur) or []
            for e in entries:
                if e.get("type") == "dir":
                    stack.append(e["path"])
                elif e.get("type") == "file":
                    download = e.get("download_url") or e.get("path", "")
                    files.append((e["path"], download))
        return files

    def _fetch_all_raw(
        self, org: str, repo: str, branch: str, stage_dir: Path
    ) -> dict[str, Any]:
        skills_root = self._contents(org, repo, branch, "skills")
        names = [
            e["name"]
            for e in (skills_root or [])
            if e.get("type") == "dir"
        ] or [repo]
        staged = 0
        methods: list[str] = ["raw"]
        for skill in names:
            skill_path = self._find_skill_path(org, repo, branch, skill)
            if not skill_path:
                continue
            files = self._collect_files(org, repo, branch, skill_path)
            dest = stage_dir / self._repo_slug(org, repo) / skill
            dest.mkdir(parents=True, exist_ok=True)
            for rel, download_url in files:
                content = self._fetch_text(download_url)
                if content is None:
                    continue
                out_file = dest / rel[len(skill_path):].lstrip("/")
                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_text(content, encoding="utf-8")
            staged += 1
            print(f"  staged {org}/{repo}/{skill} -> {dest}")
        return {"staged": str(stage_dir), "methods": methods, "files": staged, "skill": None}

    def _fetch_by_clone(
        self, repo: str, skill: str | None, stage_dir: Path
    ) -> dict[str, Any]:
        tmp = tempfile.mkdtemp(prefix="skillsh-clone-")
        clone = Path(tmp) / "repo"
        try:
            proc = subprocess.run(
                ["git", "clone", "--depth", "1", repo, str(clone)],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                raise SkillResolveError(f"git clone failed: {proc.stderr.strip()[:200]}")
            org, repo_name = self._split_repo(repo)
            bucket = self._repo_slug(org, repo_name)
            skill_dirs = self._locate_skill_dirs(clone, skill)
            staged = 0
            for src_dir in skill_dirs:
                skill_name = src_dir.name
                dest = stage_dir / bucket / skill_name
                shutil.copytree(src_dir, dest, dirs_exist_ok=True)
                staged += 1
                print(f"  cloned {bucket}/{skill_name} -> {dest}")
            return {"staged": str(stage_dir), "methods": ["clone"], "files": staged, "skill": skill}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _locate_skill_dirs(self, clone: Path, skill: str | None) -> list[Path]:
        """Find skill dirs (containing SKILL.md) in a cloned repo."""
        roots = [clone / "skills"] if (clone / "skills").exists() else [clone]
        matches: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            if skill:
                for cand in (root / skill, root / f"{skill}/SKILL.md"):
                    if cand.is_dir():
                        matches.append(cand)
                        break
                    if cand.is_file() and cand.name == "SKILL.md":
                        matches.append(cand.parent)
                        break
                # fall back to search
                if not matches:
                    matches = _search_skill_dirs(root, skill)
            else:
                matches = _search_skill_dirs(root, None)
        return matches

    def _fetch_by_npx(
        self, repo: str, skill: str | None, stage_dir: Path
    ) -> dict[str, Any]:
        pkg = repo.replace("https://github.com/", "")
        tmp = tempfile.mkdtemp(prefix="skillsh-npx-")
        try:
            cmd = ["npx", "-y", "skills", "add", pkg]
            if skill:
                cmd += ["-s", skill]
            cmd += ["-y", "--project"]
            proc = subprocess.run(
                cmd, cwd=tmp, capture_output=True, text=True, timeout=300
            )
            if proc.returncode != 0:
                raise SkillResolveError(
                    f"npx skills failed: {proc.stderr.strip()[:200] or proc.stdout.strip()[:200]}"
                )
            org, repo_name = self._split_repo(repo)
            bucket = self._repo_slug(org, repo_name)
            skill_dirs = self._locate_skill_dirs(Path(tmp), skill)
            staged = 0
            for src_dir in skill_dirs:
                dest = stage_dir / bucket / src_dir.name
                shutil.copytree(src_dir, dest, dirs_exist_ok=True)
                staged += 1
            return {"staged": str(stage_dir), "methods": ["npx"], "files": staged, "skill": skill}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- low-level ----------------------------------------------------------

    def _fetch_text(self, url: str) -> str | None:
        resp = self._rate_limited_get(url)
        if resp is None:
            return None
        return resp.text

    def _repo_slug(self, org: str, repo_name: str) -> str:
        return self.sanitize_filename(f"{org}-{repo_name}")

    def _write_sources_index(
        self, stage_dir: Path, inventory: list[dict[str, Any]]
    ) -> None:
        if not inventory:
            return
        lines = [
            "# Staged Skill Sources",
            "",
            "Deterministic index of fetched sources. The LLM composes from the",
            "actual staged `SKILL.md` files (see references/skillsh-compose.md);",
            "this index lists where each source lives and its verbatim frontmatter.",
            "",
        ]
        for inv in inventory:
            lines.append(f"## {inv.get('skill') or inv.get('repo')}")
            lines.append("")
            lines.append(f"- **Source:** {inv.get('source')}")
            lines.append(f"- **Repo:** {inv.get('repo')}")
            lines.append(f"- **Staged at:** `{inv.get('staged')}`")
            lines.append("")
            staged = inv.get("staged")
            if staged:
                md = Path(str(staged)) / "SKILL.md"
                if md.exists():
                    fm = _parse_frontmatter_block(md.read_text(encoding="utf-8"))
                    if fm:
                        lines.append("Frontmatter (verbatim):")
                        lines.append("")
                        lines.append("```yaml")
                        for k, v in fm.items():
                            lines.append(f"{k}: {v}")
                        lines.append("```")
                        lines.append("")
        (stage_dir / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote index: {stage_dir / 'SOURCES.md'}")


def _search_skill_dirs(root: Path, skill: str | None) -> list[Path]:
    """Recursively find dirs containing SKILL.md (optionally matching skill)."""
    out: list[Path] = []
    for p in root.rglob("SKILL.md"):
        parent = p.parent
        if skill and parent.name != skill:
            continue
        if skill is not None:
            out.append(parent)
        elif (
            parent.parent == root
            or (root / "skills") == parent.parent
            or parent.parent.name == root.name
        ):
            out.append(parent)
    return out
