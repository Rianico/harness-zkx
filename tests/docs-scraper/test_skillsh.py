"""Tests for skills scraper (skill.sh composition)."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest  # pyright: ignore[reportMissingImports]

_scraper_path = (
    Path(__file__).parent.parent.parent / "skills" / "docs-scraper" / "scripts" / "scrapers"
).resolve()
if str(_scraper_path) not in sys.path:
    sys.path.insert(0, str(_scraper_path))

_scripts_path = (
    Path(__file__).parent.parent.parent / "skills" / "docs-scraper" / "scripts"
).resolve()
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))

_tests_path = Path(__file__).parent.resolve()
if str(_tests_path) not in sys.path:
    sys.path.insert(0, str(_tests_path))

from scrapers.skillsh import (  # type: ignore[import-not-found]  # noqa: E402  # pyright: ignore[reportMissingImports]
    _cache_key,  # pyright: ignore[reportMissingImports]
    _repo_slug,  # pyright: ignore[reportMissingImports]
    parse_skillsh_input,  # pyright: ignore[reportMissingImports]
)  # pyright: ignore[reportMissingImports]


class TestParseSkillshInput:
    def test_sk_01_skillsh_url_full(self):
        p = parse_skillsh_input(
            "https://www.skills.sh/sickn33/agentic-awesome-skills/typescript-expert"
        )
        assert p.kind == "skill"
        assert p.owner == "sickn33"
        assert p.collection == "agentic-awesome-skills"
        assert p.skill == "typescript-expert"
        assert p.repo == "sickn33/agentic-awesome-skills"

    def test_sk_02_skillsh_url_second_skill(self):
        p = parse_skillsh_input("https://www.skills.sh/sickn33/agentic-awesome-skills/clean-code")
        assert p.kind == "skill"
        assert p.skill == "clean-code"
        assert p.repo == "sickn33/agentic-awesome-skills"

    def test_sk_03_bare_triple(self):
        p = parse_skillsh_input("sickn33/agentic-awesome-skills/typescript-expert")
        assert p.kind == "skill"
        assert p.owner == "sickn33"
        assert p.collection == "agentic-awesome-skills"
        assert p.skill == "typescript-expert"
        assert p.repo == "sickn33/agentic-awesome-skills"
        assert (
            p.skillsh_url
            == "https://www.skills.sh/sickn33/agentic-awesome-skills/typescript-expert"
        )

    def test_sk_04_bare_collection(self):
        p = parse_skillsh_input("sickn33/agentic-awesome-skills")
        assert p.kind == "collection"
        assert p.owner == "sickn33"
        assert p.collection == "agentic-awesome-skills"
        assert p.repo == "sickn33/agentic-awesome-skills"

    def test_sk_05_github_repo(self):
        p = parse_skillsh_input("https://github.com/sickn33/agentic-awesome-skills")
        assert p.kind == "repo"
        assert p.repo == "sickn33/agentic-awesome-skills"
        assert p.skill is None

    def test_sk_06_github_with_skill_path(self):
        p = parse_skillsh_input(
            "https://github.com/sickn33/agentic-awesome-skills/tree/main/skills/typescript-expert"
        )
        assert p.kind == "repo"
        assert p.repo == "sickn33/agentic-awesome-skills"

    def test_sk_07_non_www_host(self):
        p = parse_skillsh_input(
            "https://skills.sh/sickn33/agentic-awesome-skills/typescript-expert"
        )
        assert p.kind == "skill"
        assert p.skill == "typescript-expert"

    def test_sk_08_skills_collection_variant(self):
        p = parse_skillsh_input("https://www.skills.sh/anthropics/skills/retrieval-expert")
        assert p.kind == "skill"
        assert p.owner == "anthropics"
        assert p.collection == "skills"
        assert p.skill == "retrieval-expert"
        assert p.repo == "anthropics/skills"

    def test_sk_09_invalid_empty(self):
        with pytest.raises(ValueError):
            parse_skillsh_input("")

    def test_sk_10_invalid_single_segment(self):
        with pytest.raises(ValueError):
            parse_skillsh_input("onlyone")

    def test_sk_11_invalid_host(self):
        with pytest.raises(ValueError):
            parse_skillsh_input("https://example.com/foo/bar/baz")

    def test_sk_12_github_direct_skill_heuristic(self):
        p = parse_skillsh_input("https://github.com/sickn33/agentic-awesome-skills/my-skill")
        assert p.kind == "skill"
        assert p.skill == "my-skill"

    def test_sk_13_idempotence(self):
        raw = "https://www.skills.sh/sickn33/agentic-awesome-skills/typescript-expert"
        a = parse_skillsh_input(raw)
        b = parse_skillsh_input(raw)
        assert a == b


class TestHelpers:
    def test_repo_slug(self):
        assert _repo_slug("a/b") == Path("a/b")

    def test_cache_key_sanitizes(self):
        k = _cache_key("a/b", "c:d")
        assert "/" not in k
        assert ":" not in k
        assert k == "a_b__c_d"

    def test_cache_key_join(self):
        assert _cache_key("x", "y", "z") == "x__y__z"


class TestSkillsScraperInit:
    def test_empty_inputs_error(self, temp_output_dir):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        with pytest.raises(ValueError):
            SkillsScraper(inputs=[], staging=temp_output_dir)
        with pytest.raises(ValueError):
            SkillsScraper(inputs=None, staging=temp_output_dir)  # type: ignore[arg-type]

    def test_layout_with_run(self, tmp_path):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        staging = tmp_path / "compose"
        s = SkillsScraper(
            inputs=["sickn33/agentic-awesome-skills/typescript-expert"],
            staging=staging,
            run="my-run",
            respect_robots_txt=False,
        )
        assert s.staging_base == staging
        assert s.run_slug == "my-run"
        assert s.run_dir == staging / "my-run"
        assert s.stage_dir == staging / "my-run" / "stage"
        assert s.out_dir == staging / "my-run" / "out"
        assert s.cache_dir == Path(".cache") / "skills"
        assert s.cache_dir.parts[-2:] == (".cache", "skills")

    def test_layout_without_run(self, tmp_path):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        staging = tmp_path / "compose"
        s = SkillsScraper(
            inputs=["sickn33/agentic-awesome-skills/typescript-expert"],
            staging=staging,
            respect_robots_txt=False,
        )
        assert s.run_slug is None
        assert s.run_dir == staging
        assert s.stage_dir == staging / "stage"
        assert s.out_dir == staging / "out"
        assert s.cache_dir == Path(".cache") / "skills"

    def test_method_validation(self, tmp_path):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        with pytest.raises(ValueError):
            SkillsScraper(
                inputs=["sickn33/agentic-awesome-skills/typescript-expert"],
                staging=tmp_path / "compose",
                method="bad",
                respect_robots_txt=False,
            )

    def test_run_slug_sanitization(self, tmp_path):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        s = SkillsScraper(
            inputs=["sickn33/agentic-awesome-skills/typescript-expert"],
            staging=tmp_path / "compose",
            run="  hello world!  ",
            respect_robots_txt=False,
        )
        assert s.run_dir.name == "hello-world"

    def test_run_slug_invalid(self, tmp_path):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        with pytest.raises(ValueError):
            SkillsScraper(
                inputs=["sickn33/agentic-awesome-skills/typescript-expert"],
                staging=tmp_path / "compose",
                run="---",
                respect_robots_txt=False,
            )


class TestSkillsScraperNpx:
    """Npx-based fetch tests (mocked subprocess)."""

    def test_list_via_npx_parses(self, tmp_path):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        staging = tmp_path / "compose"
        s = SkillsScraper(
            inputs=["sickn33/agentic-awesome-skills/typescript-expert"],
            staging=staging,
            respect_robots_txt=False,
        )
        fake_stdout = (
            "Available Skills\n"
            "    a-skill\n\n"
            "    description\n"
            "    b-skill\n"
            "    other\n"
            "    vercel-react-best-practices\n"
        )
        mock_result = MagicMock(stdout=fake_stdout, stderr="", returncode=0)
        s._run_npx = MagicMock(return_value=mock_result)  # type: ignore[method-assign]
        names = s._list_skills_via_npx("sickn33/agentic-awesome-skills")
        assert "a-skill" in names
        assert "b-skill" in names
        assert "vercel-react-best-practices" in names

    def test_fetch_via_npx_success(self, tmp_path):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        staging = tmp_path / "compose"
        s = SkillsScraper(
            inputs=["vercel-labs/agent-skills/vercel-react-best-practices"],
            staging=staging,
            respect_robots_txt=False,
        )

        def fake_run_npx(_args, cwd, timeout=300):
            _ = timeout
            # Simulate npx installing skill into .agents/skills
            dest = cwd / ".agents" / "skills" / "vercel-react-best-practices"
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "SKILL.md").write_text("# skill")
            return MagicMock(stdout="installed", stderr="", returncode=0)

        s._run_npx = fake_run_npx  # type: ignore[method-assign]
        work = tmp_path / "work"
        staged = s._fetch_via_npx("vercel-labs/agent-skills", ["vercel-react-best-practices"], work)
        assert "vercel-react-best-practices" in staged
        dest = s.stage_dir / "vercel-labs" / "agent-skills" / "vercel-react-best-practices"
        assert dest.exists()
        assert (dest / "SKILL.md").read_text().strip() == "# skill"

    def test_run_stages_via_mocked_npx(self, tmp_path):
        from scrapers.skillsh import SkillsScraper  # pyright: ignore[reportMissingImports]

        staging = tmp_path / "compose"
        s = SkillsScraper(
            inputs=["vercel-labs/agent-skills/vercel-react-best-practices"],
            staging=staging,
            respect_robots_txt=False,
        )

        def fake_run_npx2(args, cwd, timeout=300):
            _ = timeout
            # For any add, create .agents/skills entry
            if "--list" in args:
                return MagicMock(
                    stdout="Available Skills\n    vercel-react-best-practices\n",
                    stderr="",
                    returncode=0,
                )
            # fetch
            skill = "vercel-react-best-practices"
            # extract skill from args if present
            if "--skill" in args:
                idx = args.index("--skill")
                skill = args[idx + 1].split(",")[0]
            d = cwd / ".agents" / "skills" / skill
            d.mkdir(parents=True, exist_ok=True)
            (d / "SKILL.md").write_text("# skill")
            return MagicMock(stdout="ok", stderr="", returncode=0)

        s._run_npx = fake_run_npx2  # type: ignore[method-assign]
        # Avoid skill.sh page fetch: patch resolve
        with patch.object(s, "_resolve_github_repo", return_value="vercel-labs/agent-skills"):
            s.run()
        assert (s.run_dir / "README.md").exists()
        assert (s.run_dir / "manifest.json").exists()
        manifest = json.loads((s.run_dir / "manifest.json").read_text())
        assert manifest["staged"][0]["status"] == "ok"
        assert manifest["staged"][0]["skill"] == "vercel-react-best-practices"
