#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "beautifulsoup4",
#   "requests",
# ]
# ///
"""Skills scraper for skill.sh composition via npx skills mature client.

Phase A (deterministic): parse inputs -> resolve skill.sh -> GitHub -> fetch
via `npx -y skills add` and stage to per-run dir.

Phases B/C are LLM responsibilities under ai-engineering-expert guidance.
This module only does fetch+stage and writes a staging README.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from bs4 import BeautifulSoup  # pyright: ignore[reportMissingImports]

from .base import DocumentationScraper

# ---------------------------------------------------------------------------
# Parsed input model
# ---------------------------------------------------------------------------

Kind = Literal["skill", "collection", "repo"]


@dataclass(frozen=True)
class ParsedInput:
    kind: Kind
    raw: str
    owner: str | None = None
    collection: str | None = None
    skill: str | None = None
    repo: str | None = None  # owner/repo for GitHub
    skillsh_url: str | None = None  # normalized skill.sh URL if applicable


_SKILLSH_HOSTS = {"www.skills.sh", "skills.sh"}


def _strip_scheme(s: str) -> str:
    return s.strip()


def parse_skillsh_input(raw: str) -> ParsedInput:
    """Parse a single skill input string.

    Accepted forms:
    - https://www.skills.sh/<owner>/<collection>/<skill>
    - https://www.skills.sh/<owner>/<collection>  (collection)
    - https://www.skills.sh/<owner>/skills/<skill> variant
    - bare triple: <owner>/<collection>/<skill>
    - bare collection: <owner>/<collection>
    - https://github.com/<owner>/<repo>  (repo)
    - https://github.com/<owner>/<repo>/tree/...  (repo, extra path ignored)
    """
    s = _strip_scheme(raw)
    if not s:
        raise ValueError("empty skill input")

    # URL inputs
    if s.startswith("http://") or s.startswith("https://"):
        parsed = urlparse(s)
        host = parsed.netloc.lower()
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p]

        if "github.com" in host:
            if len(parts) < 2:
                raise ValueError(f"GitHub URL needs owner/repo: {s}")
            repo = f"{parts[0]}/{parts[1]}"
            # If path has more than 2 segments and looks like skills/<name>, capture skill
            skill: str | None = None
            if len(parts) >= 4 and parts[2] == "skills":
                skill = parts[3]
            elif len(parts) >= 3 and parts[2] != "tree" and parts[2] != "blob":
                # Heuristic: owner/repo/<skill> direct? treat as skill if 3 parts
                # but not tree/blob branches
                if len(parts) == 3:
                    skill = parts[2]
            if skill:
                return ParsedInput(kind="skill", raw=s, repo=repo, skill=skill, skillsh_url=None)
            return ParsedInput(kind="repo", raw=s, repo=repo, skillsh_url=None)

        if host in _SKILLSH_HOSTS:
            # skill.sh
            if len(parts) == 2:
                # owner/collection
                return ParsedInput(
                    kind="collection",
                    raw=s,
                    owner=parts[0],
                    collection=parts[1],
                    repo=f"{parts[0]}/{parts[1]}",
                    skillsh_url=f"https://www.skills.sh/{parts[0]}/{parts[1]}",
                )
            if len(parts) == 3:
                # owner/collection/skill  (collection may be "skills")
                return ParsedInput(
                    kind="skill",
                    raw=s,
                    owner=parts[0],
                    collection=parts[1],
                    skill=parts[2],
                    repo=f"{parts[0]}/{parts[1]}",
                    skillsh_url=s if s.startswith("https://") else f"https://{s}",
                )
            if len(parts) == 1:
                # owner page -> treat as collection listing? but we treat as repo-like
                return ParsedInput(
                    kind="collection",
                    raw=s,
                    owner=parts[0],
                    collection=None,
                    repo=None,
                    skillsh_url=s,
                )
            raise ValueError(f"Unexpected skill.sh path: {s}")

        raise ValueError(f"Unsupported host for skill input: {s}")

    # Bare inputs (no scheme)
    parts = [p for p in s.strip("/").split("/") if p]
    if len(parts) == 2:
        # Could be owner/collection (skill.sh collection) or owner/repo (github repo)
        # Default to collection; it will be resolved as repo later.
        return ParsedInput(
            kind="collection",
            raw=s,
            owner=parts[0],
            collection=parts[1],
            repo=f"{parts[0]}/{parts[1]}",
            skillsh_url=f"https://www.skills.sh/{parts[0]}/{parts[1]}",
        )
    if len(parts) == 3:
        return ParsedInput(
            kind="skill",
            raw=s,
            owner=parts[0],
            collection=parts[1],
            skill=parts[2],
            repo=f"{parts[0]}/{parts[1]}",
            skillsh_url=f"https://www.skills.sh/{parts[0]}/{parts[1]}/{parts[2]}",
        )
    raise ValueError(
        f"Cannot parse skill input (expected owner/collection or owner/collection/skill): {s}"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _repo_slug(repo: str) -> Path:
    """Repo string owner/repo -> Path owner/repo (keeps hierarchy)."""
    return Path(repo)


def _cache_key(*parts: str) -> str:
    raw = "__".join(parts)
    return re.sub(r"[^A-Za-z0-9_.-]", "_", raw)


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------


class SkillsScraper(DocumentationScraper):
    """Fetch complementary skills from skill.sh via npx skills mature client."""

    name: str = "skills"
    description: str = (
        "Fetch skills from skill.sh catalog via npx skills CLI (mature client) "
        "and stage them for LLM composition under ai-engineering-expert. "
        "Handles skill.sh URLs, bare owner/collection/skill triples, and GitHub "
        "repo URLs. Multi-run via --run. TRIGGER: skill.sh, skills.sh, compose skills, fetch skill"
    )

    def __init__(
        self,
        inputs: list[str] | None = None,
        staging: Path | None = None,
        run: str | None = None,
        output_dir: Path | None = None,
        method: str = "auto",
        force: bool = False,
        **kwargs: Any,
    ) -> None:
        if not inputs:
            raise ValueError(
                "SkillsScraper requires at least one input (skill.sh URL or owner/collection/skill)"
            )

        # Resolve staging vs output_dir (alias). staging wins.
        staging_base: Path
        if staging is not None:
            staging_base = Path(staging)
        elif output_dir is not None:
            staging_base = Path(output_dir)
        else:
            staging_base = Path(".lsz/tmp/skill-compose")

        # Normalize method: raw/clone are deprecated aliases for npx
        normalized = method
        if method in ("raw", "clone"):
            print(f"  Warning: --method {method!r} is deprecated, using 'npx' (mature client)")
            normalized = "npx"
        if normalized not in ("auto", "npx"):
            raise ValueError(f"Unknown method {method!r}, expected auto|npx (raw/clone deprecated)")

        # auto maps to npx
        effective_method = "npx" if normalized == "auto" else normalized

        # Determine run dir
        self.staging_base: Path = staging_base
        self.run_slug: str | None = run
        self.method: str = effective_method
        self.inputs_raw: list[str] = list(inputs)

        # Parse inputs eagerly to fail fast
        self.parsed: list[ParsedInput] = [parse_skillsh_input(x) for x in inputs]

        if run:
            # Basic slug sanitization
            safe_run = re.sub(r"[^A-Za-z0-9_.-]", "-", run).strip("-")
            if not safe_run:
                raise ValueError(f"Invalid --run slug: {run!r}")
            run_dir = staging_base / safe_run
        else:
            run_dir = staging_base

        self.run_dir: Path = run_dir
        self.stage_dir: Path = run_dir / "stage"
        self.out_dir: Path = run_dir / "out"

        # DocumentationScraper expects base_url + output_dir
        # output_dir for base class is stage_dir (where we stage sources)
        base_url = "https://www.skills.sh"
        # Try to use first skillsh URL as base_url for robots if present
        for p in self.parsed:
            if p.skillsh_url:
                try:
                    u = urlparse(p.skillsh_url)
                    base_url = f"{u.scheme}://{u.netloc}"
                    break
                except Exception:
                    pass

        super().__init__(
            base_url=base_url,
            output_dir=self.stage_dir,
            force=force,
            cache_base=Path(".cache"),
            **kwargs,
        )

        # For npx fetches, cache is handled by npx/XDG; our cache_dir still used for manifest

    # -- npx helpers ---------------------------------------------------------

    def _run_npx(
        self, args: list[str], cwd: Path, timeout: int = 300
    ) -> subprocess.CompletedProcess[str]:
        """Run npx skills with args in cwd."""
        cmd = ["npx", "-y", "skills", *args]
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _list_skills_via_npx(self, repo: str) -> list[str]:
        """List skill names via `npx skills add <repo> --list`.

        Parses skill names from stdout. Robust regex: skill names are
        indented lines with hyphens/underscores under Available Skills.
        """
        # Use a temporary directory for listing to avoid polluting project
        tmp = self.run_dir / "_npx_list" / _cache_key(repo)
        _ = tmp.mkdir(parents=True, exist_ok=True)
        try:
            result = self._run_npx(["add", repo, "--list"], cwd=tmp, timeout=180)
        except subprocess.TimeoutExpired:
            print(f"  Warning: npx list timed out for {repo}")
            return []
        except Exception as e:
            print(f"  Warning: npx list failed for {repo}: {e}")
            return []

        output = (result.stdout or "") + "\n" + (result.stderr or "")
        # Extract skill names: lines indented 2-4 spaces, alphanumeric + - _
        # Filter out headings and descriptions
        candidates: list[str] = []
        # Pattern for skill names (indented, e.g. vercel-react-best-practices)
        pattern = re.compile(r"^\s{2,4}([a-z0-9][a-z0-9\-_]+)\s*$", re.MULTILINE)
        for m in pattern.finditer(output):
            name = m.group(1).strip()
            # Heuristic: skill names are kebab-case, not common words like "Source" or "Available"
            if name.lower() in {"available", "skills", "source", "installing", "found"}:
                continue
            # Length and shape filter
            if 2 <= len(name) <= 64 and re.match(r"^[a-z0-9][a-z0-9\-_]*$", name):
                candidates.append(name)

        # Deduplicate preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                deduped.append(c)
        return deduped

    def _fetch_via_npx(self, repo: str, skills: list[str], work_dir: Path) -> dict[str, Path]:
        """Fetch skills via npx into work_dir and return mapping skill->installed path.

        Uses `npx -y skills add <repo> [--skill <comma>] -y` with cwd=work_dir.
        After install, locates installed dirs under .agents/skills, skills, .claude/skills.
        Copies each to stage_dir and returns mapping.
        """
        # Ensure clean work_dir
        if work_dir.exists():
            try:
                _ = shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

        cmd: list[str] = ["add", repo, "-y"]
        if skills:
            cmd.extend(["--skill", ",".join(skills)])

        try:
            result = self._run_npx(cmd, cwd=work_dir, timeout=300)
        except subprocess.TimeoutExpired as e:
            print(f"  npx fetch timed out for {repo} {skills}: {e}")
            return {}
        except Exception as e:
            print(f"  npx fetch failed for {repo} {skills}: {e}")
            return {}

        if result.returncode != 0:
            # Include stderr for diagnostics but don't fail hard
            err = (result.stderr or result.stdout or "")[:800]
            print(f"  npx fetch failed for {repo} (code {result.returncode}): {err[:400]}")
            # Still try to locate any partially installed skills

        # Locate installed skills: check .agents/skills, skills, .claude/skills
        possible_roots = [
            work_dir / ".agents" / "skills",
            work_dir / "skills",
            work_dir / ".claude" / "skills",
        ]
        found: dict[str, Path] = {}
        for root in possible_roots:
            if not root.exists():
                continue
            for child in root.iterdir():
                if child.is_dir() and child.name not in found:
                    found[child.name] = child

        # Also check skills-lock.json for source mapping as fallback
        lock = work_dir / "skills-lock.json"
        if lock.exists():
            try:
                data = json.loads(lock.read_text(encoding="utf-8"))
                skills_map = data.get("skills", {})
                if isinstance(skills_map, dict):
                    for name, _meta in skills_map.items():
                        if name not in found:
                            # meta has skillPath but path is .agents/skills/<name>
                            # try to resolve via .agents/skills
                            cand = work_dir / ".agents" / "skills" / name
                            if cand.exists():
                                found[name] = cand
            except Exception:
                pass

        # Copy found skills to stage_dir
        staged: dict[str, Path] = {}
        for skill_name, src_path in found.items():
            # If specific skills requested, filter
            if skills and skill_name not in skills:
                continue
            dest = self.stage_dir / _repo_slug(repo) / skill_name
            if dest.exists():
                try:
                    _ = shutil.rmtree(dest, ignore_errors=True)
                except Exception:
                    pass
            try:
                _ = shutil.copytree(src_path, dest)
                staged[skill_name] = dest
                print(f"  Staged {skill_name} -> {dest}")
            except Exception as e:
                print(f"  Warning: copy failed for {skill_name}: {e}")

        # For requested skills not found, warn
        for s in skills:
            if s not in staged:
                print(f"  Warning: skill not staged (not found after npx): {s} in {repo}")

        return staged

    # -- GitHub resolve ------------------------------------------------------

    def _resolve_github_repo(self, parsed: ParsedInput) -> str:
        """Resolve skill.sh input to GitHub repo string owner/repo.

        For github inputs, return repo directly.
        For skill.sh inputs, try to fetch the skill.sh page and extract the GitHub link.
        Fallback to parsed.repo (owner/collection).
        """
        if parsed.repo and parsed.kind == "repo":
            return parsed.repo

        # If we have a skillsh_url, try to fetch it
        if parsed.skillsh_url:
            try:
                resp = self._rate_limited_get(parsed.skillsh_url)
                if resp is not None and resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.find_all("a", href=True):
                        href = str(a.get("href", ""))
                        if href.startswith("https://github.com/"):
                            pu = urlparse(href)
                            parts = [p for p in pu.path.strip("/").split("/") if p]
                            if len(parts) >= 2:
                                return f"{parts[0]}/{parts[1]}"
            except Exception as e:
                print(f"  Warning: could not resolve GitHub repo from {parsed.skillsh_url}: {e}")

        if parsed.repo:
            return parsed.repo
        raise ValueError(f"Cannot resolve GitHub repo for input: {parsed.raw}")

    # -- Staging README ------------------------------------------------------

    def _generate_staging_readme(self, results: list[dict[str, Any]]) -> None:
        _ = self.run_dir.mkdir(parents=True, exist_ok=True)
        _ = self.stage_dir.mkdir(parents=True, exist_ok=True)
        _ = self.out_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(UTC)
        date_str = now.strftime("%Y-%m-%d %H:%M UTC")

        lines: list[str] = [
            f"# Staged Skills — {self.run_slug or 'default'}",
            "",
            f"**Staged:** {date_str}",
            f"**Staging root:** `{self.staging_base}`",
            f"**Run dir:** `{self.run_dir}`",
            f"**Stage dir:** `{self.stage_dir}`",
            f"**Out dir (LLM target):** `{self.out_dir}`",
            f"**Method:** {self.method} (via npx skills mature client)",
            "",
            "## Inputs",
            "",
        ]
        for p in self.parsed:
            repo_label = p.repo if p.kind == "repo" else self._resolve_github_repo(p)
            lines.append(f"- `{p.raw}` — {p.kind} — repo `{repo_label}`")

        lines.extend(["", "## Staged Skills", ""])
        if not results:
            lines.append("_No skills staged._")
        for r in results:
            status = r.get("status", "unknown")
            skill = r.get("skill", "?")
            repo = r.get("repo", "?")
            path = r.get("path", "")
            if status == "ok":
                lines.append(f"- **{skill}** ({repo}) — `{path}` — {r.get('source', '')}")
            else:
                lines.append(f"- **{skill}** ({repo}) — **{status}**: {r.get('error', '')}")

        lines.extend(
            [
                "",
                "## Next step — Compose with LLM (ai-engineering-expert)",
                "",
                "This staging is **Phase A (deterministic)**. Phases B/C are",
                "**LLM** responsibilities:",
                "",
                "- Load `ai-engineering-expert` skill (domains `skill-authoring` + `writing`).",
                "- Read each `stage/<repo>/<skill>/SKILL.md` + `references/` + `scripts/`.",
                "- Decide composition: single skill → reorganize; multiple → merge & dedup.",
                "- Write the new skill to `out/<new-skill>/SKILL.md` "
                "(+ `references/`, `scripts/`) per skill conventions "
                "(description ≤300 chars, trigger vocab, "
                "progressive disclosure) and include `meta: sources:` in frontmatter "
                "(list of skill.sh URLs from `manifest.json` `skillsh_url`/`source`) "
                "as authoritative attribution.",
                "",
                "See `references/skillsh-compose.md` for the full workflow.",
                "",
                "```bash",
                "# Example: after staging, invoke LLM to compose into out/my-new-skill",
                f"# LLM reads {self.stage_dir}/<repo>/<skill>/SKILL.md "
                f"and writes {self.out_dir}/<new-skill>/SKILL.md",
                "```",
                "---",
                f"*Generated by skills scraper (npx) on {date_str}*",
            ]
        )

        readme_path = self.run_dir / "README.md"
        _ = readme_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Generated staging README: {readme_path}")

        # Also write machine-readable manifest
        manifest_path = self.run_dir / "manifest.json"
        manifest = {
            "run": self.run_slug or "default",
            "staging_base": str(self.staging_base),
            "run_dir": str(self.run_dir),
            "stage_dir": str(self.stage_dir),
            "out_dir": str(self.out_dir),
            "method": self.method,
            "generated": date_str,
            "inputs": [
                {
                    "raw": p.raw,
                    "kind": p.kind,
                    "owner": p.owner,
                    "collection": p.collection,
                    "skill": p.skill,
                    "repo": p.repo,
                    "skillsh_url": p.skillsh_url,
                }
                for p in self.parsed
            ],
            "staged": results,
        }
        try:
            _ = manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            print(f"Generated manifest: {manifest_path}")
        except Exception as e:
            print(f"Warning: could not write manifest: {e}")

    def run(self) -> None:
        """Fetch and stage skills via npx."""
        run_name = self.run_slug or "default"
        print(
            f"SkillsScraper (npx): {len(self.parsed)} input(s), "
            f"staging={self.staging_base}, run={run_name}, "
            f"method={self.method}"
        )

        # Prepare dirs
        _ = self.stage_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Expand inputs -> list of (repo, skill) targets, handling collections
        # First pass: gather explicit skills and collections
        explicit: list[tuple[str, str]] = []
        collection_repos: list[str] = []
        for p in self.parsed:
            if p.kind == "skill":
                repo = self._resolve_github_repo(p)
                assert p.skill is not None
                explicit.append((repo, p.skill))
            elif p.kind == "collection":
                repo = self._resolve_github_repo(p)
                collection_repos.append(repo)
            elif p.kind == "repo":
                assert p.repo is not None
                collection_repos.append(p.repo)

        # For collections, discover skills via npx --list
        for repo in collection_repos:
            names = self._list_skills_via_npx(repo)
            if not names:
                print(f"  Warning: no skills discovered via npx for {repo} (--list empty)")
                # Fallback: will fetch all via npx without --skill (install all)
                # For composition we prefer explicit list; leave empty to install all
                # Represent as single target with empty skill to indicate "all"
                # But for now warn and skip unless user expects all
                continue
            print(f"  Collection {repo}: {len(names)} skills discovered via npx")
            for name in names:
                explicit.append((repo, name))

        # Deduplicate targets
        seen: set[tuple[str, str]] = set()
        deduped: list[tuple[str, str]] = []
        for t in explicit:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        targets = deduped

        if not targets:
            # Handle case where collection meant "install all" without discovery
            if collection_repos and not explicit:
                # Try npx install all directly
                for repo in collection_repos:
                    work = self.run_dir / "_npx" / _cache_key(repo, "all")
                    staged_map = self._fetch_via_npx(repo, [], work)
                    # staged_map contains all installed
                    for skill, _path in staged_map.items():
                        targets.append((repo, skill))
                # Re-dedup after
                seen2: set[tuple[str, str]] = set()
                tmp: list[tuple[str, str]] = []
                for t in targets:
                    if t not in seen2:
                        seen2.add(t)
                        tmp.append(t)
                targets = tmp
            if not targets:
                print("No skill targets to fetch.")
                self._generate_staging_readme([])
                return

        # Group by repo for npx batch fetch
        from collections import defaultdict

        by_repo: dict[str, list[str]] = defaultdict(list)
        for repo, skill in targets:
            by_repo[repo].append(skill)

        results: list[dict[str, Any]] = []

        for repo, skills in by_repo.items():
            work = self.run_dir / "_npx" / _cache_key(repo, ",".join(sorted(skills))[:60])
            staged_map = self._fetch_via_npx(repo, skills, work)
            for skill in skills:
                if skill in staged_map:
                    dest = self.stage_dir / _repo_slug(repo) / skill
                    # staged_map already copied to dest inside _fetch_via_npx
                    # Ensure dest exists (copy may have placed it)
                    results.append(
                        {
                            "repo": repo,
                            "skill": skill,
                            "status": "ok",
                            "path": str(dest) if dest.exists() else str(staged_map[skill]),
                            "source": f"https://github.com/{repo}",
                            "error": "",
                        }
                    )
                else:
                    results.append(
                        {
                            "repo": repo,
                            "skill": skill,
                            "status": "error",
                            "path": "",
                            "source": f"https://github.com/{repo}",
                            "error": "npx fetch did not stage skill",
                        }
                    )

        self._generate_staging_readme(results)

        ok_count = sum(1 for r in results if r.get("status") == "ok")
        print(f"Staging complete: {ok_count}/{len(results)} skills staged to {self.stage_dir}")
        print(
            f"Next: LLM composes into {self.out_dir}/<new-skill>/ per references/skillsh-compose.md"
        )
