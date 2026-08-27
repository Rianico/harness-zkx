"""Tests for the skill.sh / GitHub skill fetcher (skillsh.py).

Covers: source parsing, GitHub-link extraction, frontmatter parsing, raw
fetch-and-stage (single + whole collection), multi-run isolation, and the
deterministic source index. Network is fully mocked.
"""

import sys
from pathlib import Path

# Expose the scrapers package (parent of scrapers/) so the module's relative
# `.base` import resolves. The package's own base/base.py helpers are pinned by
# conftest's scraper_path insert; this adds the enclosing scripts/ dir.
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "skills" / "docs-scraper" / "scripts"),
)

from scrapers.skillsh import (
    SkillshScraper,
    _parse_frontmatter_block,
    extract_github_repo_from_html,
    parse_skill_source,
)

SKILLSH_URL = "https://www.skills.sh/sickn33/agentic-awesome-skills/typescript-expert"

RAW = "https://raw.githubusercontent.com/sickn33/agentic-awesome-skills/main" + "/skills"


class FakeResponse:
    """Minimal stand-in for requests.Response used by _rate_limited_get."""

    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200
        self.text = payload

    def json(self):
        # contents API returns a JSON list; default_branch returns an object.
        return self._payload


def make_scraper(tmp_path, run="test-run", method="auto"):
    staging = tmp_path / "skill-compose"
    inst = SkillshScraper(sources=[], output_dir=staging, run=run, method=method, force=True)
    return inst, staging


# ----------------------------------------------------------------------
# Pure parsing helpers
# ----------------------------------------------------------------------


class TestParseSkillSource:
    def test_skillsh_url_full(self):
        p = parse_skill_source(SKILLSH_URL)
        assert p["kind"] == "skillsh"
        assert p["owner"] == "sickn33"
        assert p["collection"] == "agentic-awesome-skills"
        assert p["skill"] == "typescript-expert"
        assert p["repo_url"] == "https://github.com/sickn33/agentic-awesome-skills"

    def test_skillsh_url_collection_only(self):
        p = parse_skill_source("https://www.skills.sh/sickn33/agentic-awesome-skills")
        assert p["skill"] is None
        assert p["repo_hint"] == "sickn33/agentic-awesome-skills"

    def test_bare_triple(self):
        p = parse_skill_source("sickn33/agentic-awesome-skills/typescript-expert")
        assert p["kind"] == "bare"
        assert p["skill"] == "typescript-expert"
        assert p["repo_url"] == "https://github.com/sickn33/agentic-awesome-skills"

    def test_github_repo(self):
        p = parse_skill_source("https://github.com/sickn33/agentic-awesome-skills")
        assert p["kind"] == "github"
        assert p["skill"] is None

    def test_bare_repo(self):
        p = parse_skill_source("sickn33/agentic-awesome-skills")
        assert p["repo_url"] == "https://github.com/sickn33/agentic-awesome-skills"

    def test_trailing_slash_stripped(self):
        p = parse_skill_source("sickn33/agentic-awesome-skills/typescript-expert/")
        assert p["skill"] == "typescript-expert"


class TestExtractGithubRepo:
    def test_filters_noise_and_returns_target(self):
        html = (
            '<a href="https://github.com/vercel-labs/skills">GitHub</a>'
            '<a href="https://github.com/sickn33/agentic-awesome-skills">Repo</a>'
        )
        assert extract_github_repo_from_html(html) == "https://github.com/sickn33/agentic-awesome-skills"

    def test_no_github_links(self):
        assert extract_github_repo_from_html("<html><body>nope</body></html>") is None


class TestFrontmatterBlock:
    def test_parses_key_values(self):
        md = "---\nname: typescript-expert\ndescription: expert\ncategory: framework\n---\n# Body"
        fm = _parse_frontmatter_block(md)
        assert fm["name"] == "typescript-expert"
        assert fm["description"] == "expert"
        assert fm["category"] == "framework"

    def test_no_frontmatter(self):
        assert _parse_frontmatter_block("# Just a heading") == {}


# ----------------------------------------------------------------------
# Fetch + stage (raw method, mocked network)
# ----------------------------------------------------------------------


class TestFetchByRaw:
    def _raw_fake(self):
        """fake_get for the single-skill fetch: repo info, dir walk, raw files."""
        main = RAW

        def fake_get(url, **kwargs):
            if ("repos/sickn33/agentic-awesome-skills" in url) and ("contents" not in url):
                return FakeResponse({"default_branch": "main"})
            if "contents" in url and "skills/typescript-expert/references" in url:
                return FakeResponse(
                    [
                        {
                            "type": "file",
                            "path": "skills/typescript-expert/references/cheatsheet.md",
                            "download_url": f"{main}/typescript-expert/references/cheatsheet.md",
                        }
                    ]
                )
            if "contents" in url and "skills/typescript-expert/scripts" in url:
                return FakeResponse(
                    [
                        {
                            "type": "file",
                            "path": "skills/typescript-expert/scripts/check.py",
                            "download_url": f"{main}/typescript-expert/scripts/check.py",
                        }
                    ]
                )
            if "contents" in url and "skills/typescript-expert" in url:
                return FakeResponse(
                    [
                        {
                            "type": "file",
                            "path": "skills/typescript-expert/SKILL.md",
                            "download_url": f"{main}/typescript-expert/SKILL.md",
                        },
                        {"type": "dir", "path": "skills/typescript-expert/references"},
                        {"type": "dir", "path": "skills/typescript-expert/scripts"},
                    ]
                )
            if "contents" in url and "skills" in url:
                return FakeResponse(
                    [
                        {
                            "type": "dir",
                            "name": "typescript-expert",
                            "path": "skills/typescript-expert",
                        }
                    ]
                )
            return FakeResponse("---\nname: typescript-expert\n---\n# Body")

        return fake_get

    def test_stages_single_skill_files(self, tmp_path):
        inst, _ = make_scraper(tmp_path)
        inst._rate_limited_get = self._raw_fake()
        stage_dir = tmp_path / "skill-compose" / "test-run" / "stage"
        stage_dir.mkdir(parents=True, exist_ok=True)

        result = inst._fetch_by_raw(
            "https://github.com/sickn33/agentic-awesome-skills",
            "typescript-expert",
            stage_dir,
        )

        skill_dir = stage_dir / "sickn33-agentic-awesome-skills" / "typescript-expert"
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "references" / "cheatsheet.md").exists()
        assert (skill_dir / "scripts" / "check.py").exists()
        assert result["files"] == 3

    def test_fetch_all_raw(self, tmp_path):
        inst, _ = make_scraper(tmp_path)

        def fake_get(url, **kwargs):
            if "contents/skills?ref" in url:
                return FakeResponse(
                    [
                        {"type": "dir", "name": "a", "path": "skills/a"},
                        {"type": "dir", "name": "b", "path": "skills/b"},
                    ]
                )
            if "contents/skills/a" in url and "?ref" in url:
                return FakeResponse(
                    [
                        {
                            "type": "file",
                            "path": "skills/a/SKILL.md",
                            "download_url": "https://raw.githubusercontent.com/x/main/skills/a/SKILL.md",
                        }
                    ]
                )
            if "contents/skills/b" in url and "?ref" in url:
                return FakeResponse(
                    [
                        {
                            "type": "file",
                            "path": "skills/b/SKILL.md",
                            "download_url": "https://raw.githubusercontent.com/x/main/skills/b/SKILL.md",
                        }
                    ]
                )
            return FakeResponse("content")

        inst._rate_limited_get = fake_get
        stage_dir = tmp_path / "skill-compose" / "test-run" / "stage"
        stage_dir.mkdir(parents=True, exist_ok=True)

        result = inst._fetch_by_raw(
            "https://github.com/sickn33/agentic-awesome-skills", None, stage_dir
        )
        assert result["files"] == 2
        assert (stage_dir / "sickn33-agentic-awesome-skills" / "a" / "SKILL.md").exists()
        assert (stage_dir / "sickn33-agentic-awesome-skills" / "b" / "SKILL.md").exists()


class TestResolveAndChooseMethod:
    def test_auto_clone_for_collection(self, tmp_path):
        inst, _ = make_scraper(tmp_path)
        assert inst._choose_method(parse_skill_source("sickn33/agentic-awesome-skills")) == "clone"

    def test_auto_raw_for_explicit_skill(self, tmp_path):
        inst, _ = make_scraper(tmp_path)
        assert (
            inst._choose_method(parse_skill_source("sickn33/agentic-awesome-skills/tsc"))
        ) == "raw"

    def test_explicit_method_overrides(self, tmp_path):
        inst, _ = make_scraper(tmp_path, method="npx")
        assert inst._choose_method(parse_skill_source("a/b")) == "npx"


# ----------------------------------------------------------------------
# Multi-run isolation + index
# ----------------------------------------------------------------------


class TestRunIsolation:
    def test_auto_run_increments(self, tmp_path):
        inst = SkillshScraper(sources=["sickn33/agentic-awesome-skills/tsc"], output_dir=tmp_path)
        r1 = inst._resolve_run_dir()
        r2 = inst._resolve_run_dir()
        assert r1 != r2
        assert "tsc" in r1.name
        assert r2.name == f"{r1.name}-1"

    def test_explicit_run_stable(self, tmp_path):
        inst, staging = make_scraper(tmp_path, run="stable")
        r1 = inst._resolve_run_dir()
        r2 = inst._resolve_run_dir()
        assert r1 == r2
        assert r1.parent == staging
        assert r1.name == "stable"

    def test_multi_run_coexist(self, tmp_path):
        a = make_scraper(tmp_path, run="alpha")[0]
        b = make_scraper(tmp_path, run="beta")[0]
        da = a._resolve_run_dir()
        db = b._resolve_run_dir()
        (da / "out").mkdir(parents=True, exist_ok=True)
        (db / "out").mkdir(parents=True, exist_ok=True)
        assert da != db
        assert da.exists() and db.exists()


class TestSourcesIndex:
    def test_writes_index_with_frontmatter(self, tmp_path):
        inst, staging = make_scraper(tmp_path)
        stage_dir = staging / "test-run" / "stage"
        skill_dir = stage_dir / "repo" / "tsc"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: tsc\ndescription: an expert\n---\n# TSC", encoding="utf-8"
        )
        inventory = [
            {
                "source": "sickn33/x/tsc",
                "repo": "https://github.com/sickn33/x",
                "skill": "tsc",
                "staged": str(skill_dir),
            }
        ]
        inst._write_sources_index(stage_dir, inventory)
        index = (stage_dir / "SOURCES.md").read_text(encoding="utf-8")
        assert "## tsc" in index
        assert "name: tsc" in index
        assert "description: an expert" in index
