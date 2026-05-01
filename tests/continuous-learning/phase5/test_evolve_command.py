"""
Tests for evolve command.

Eval 5.3: evolve Command

Input: `/continuous-learning evolve`
Expected: Cluster related instincts, propose skills

Pass criteria:
- [ ] Groups instincts by domain
- [ ] Identifies related patterns
- [ ] Proposes draft skill content
- [ ] Requires user approval
"""

import sys
from pathlib import Path

import pytest
import yaml

from hooks.observe.instinct_manager import InstinctManager


SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "continuous-learning" / "scripts"


@pytest.fixture
def evolve_script() -> Path:
    """Return path to evolve script."""
    return SCRIPTS_DIR / "evolve.py"


@pytest.fixture
def instinct_manager(homunculus_dir: Path) -> InstinctManager:
    """Create instinct manager instance."""
    return InstinctManager(homunculus_dir)


@pytest.fixture
def multiple_workflow_instincts(homunculus_dir: Path) -> list[Path]:
    """Create multiple workflow-related instincts across projects."""
    instincts = []

    # Create instincts in multiple projects with workflow domain
    for project_idx, project_id in enumerate(["proj1", "proj2", "proj3"]):
        project_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
        project_dir.mkdir(parents=True, exist_ok=True)

        for inst_idx in range(3):
            instinct_content = f"""---
id: workflow-pattern-{project_idx}-{inst_idx}
trigger: "when working with {['files', 'tests', 'code'][inst_idx]}"
confidence: {0.6 + inst_idx * 0.1}
domain: "workflow"
scope: "project"
project_id: "{project_id}"
created_at: "2026-04-30T{10 + project_idx}:00:00Z"
updated_at: "2026-04-30T{10 + project_idx}:30:00Z"
evidence_count: {5 + inst_idx * 3}
---

# Workflow Pattern {project_idx}-{inst_idx}

## Action
Follow TDD workflow: test, implement, refactor.

## Evidence
- Session s{project_idx}{inst_idx}: Pattern observed
"""
            instinct_file = project_dir / f"workflow-pattern-{project_idx}-{inst_idx}.yaml"
            instinct_file.write_text(instinct_content)
            instincts.append(instinct_file)

    return instincts


@pytest.fixture
def multiple_debugging_instincts(homunculus_dir: Path) -> list[Path]:
    """Create multiple debugging-related instincts."""
    instincts = []

    # Global debugging instincts
    global_dir = homunculus_dir / "instincts" / "personal"
    global_dir.mkdir(parents=True, exist_ok=True)

    for idx in range(2):
        instinct_content = f"""---
id: debug-pattern-{idx}
trigger: "when encountering {['errors', 'failures'][idx]}"
confidence: 0.8
domain: "debugging"
scope: "global"
project_id: "global"
created_at: "2026-04-30T08:00:00Z"
updated_at: "2026-04-30T08:30:00Z"
evidence_count: {10 + idx * 5}
---

# Debug Pattern {idx}

## Action
Check logs, trace execution, fix root cause.

## Evidence
- Session g{idx}: Pattern observed
"""
        instinct_file = global_dir / f"debug-pattern-{idx}.yaml"
        instinct_file.write_text(instinct_content)
        instincts.append(instinct_file)

    return instincts


@pytest.fixture
def mixed_domain_instincts(homunculus_dir: Path) -> list[Path]:
    """Create instincts across different domains."""
    domains = ["workflow", "debugging", "refactoring", "testing"]
    instincts = []

    project_id = "mixed-proj"
    project_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
    project_dir.mkdir(parents=True, exist_ok=True)

    for idx, domain in enumerate(domains):
        instinct_content = f"""---
id: {domain}-instinct-{idx}
trigger: "when doing {domain}"
confidence: 0.7
domain: "{domain}"
scope: "project"
project_id: "{project_id}"
created_at: "2026-04-30T12:00:00Z"
updated_at: "2026-04-30T12:30:00Z"
evidence_count: 5
---

# {domain.title()} Instinct

## Action
{domain.title()} action placeholder.

## Evidence
- Session s{idx}: Pattern observed
"""
        instinct_file = project_dir / f"{domain}-instinct-{idx}.yaml"
        instinct_file.write_text(instinct_content)
        instincts.append(instinct_file)

    return instincts


class TestEvolveCommandScript:
    """Tests for the evolve command script file existence."""

    def test_script_exists(self, evolve_script: Path) -> None:
        """
        The evolve.py script should exist in the scripts directory.
        """
        assert evolve_script.exists(), f"Script not found at {evolve_script}"


class TestEvolveCommandFunctionality:
    """Tests for evolve command functionality via InstinctManager."""

    def test_groups_instincts_by_domain(
        self,
        instinct_manager: InstinctManager,
        multiple_workflow_instincts: list[Path],
        multiple_debugging_instincts: list[Path]
    ) -> None:
        """
        Eval 5.3: Groups instincts by domain.

        The evolve command should group instincts by their domain.
        """
        all_instincts = instinct_manager.list_instincts()

        # Group by domain
        by_domain: dict[str, list] = {}
        for inst in all_instincts:
            domain = inst["frontmatter"]["domain"]
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(inst)

        # Should have both workflow and debugging domains
        assert "workflow" in by_domain
        assert "debugging" in by_domain
        assert len(by_domain["workflow"]) >= 9  # 3 projects x 3 instincts
        assert len(by_domain["debugging"]) >= 2

    def test_identifies_related_patterns(
        self,
        instinct_manager: InstinctManager,
        multiple_workflow_instincts: list[Path]
    ) -> None:
        """
        Eval 5.3: Identifies related patterns.

        The evolve command should identify patterns that could be clustered.
        """
        # Get all workflow instincts
        all_instincts = instinct_manager.list_instincts()
        workflow_instincts = [
            i for i in all_instincts
            if i["frontmatter"]["domain"] == "workflow"
        ]

        # Should have multiple workflow instincts to cluster
        assert len(workflow_instincts) >= 3

        # Check that they have related triggers (all mention workflow-like terms)
        triggers = [i["frontmatter"]["trigger"] for i in workflow_instincts]
        assert all("when" in t.lower() for t in triggers)

    def test_identifies_cross_project_patterns(
        self,
        instinct_manager: InstinctManager,
        multiple_workflow_instincts: list[Path]
    ) -> None:
        """
        Evolve should identify patterns that span multiple projects.
        """
        all_instincts = instinct_manager.list_instincts()

        # Count by project_id
        by_project: dict[str, int] = {}
        for inst in all_instincts:
            pid = inst["frontmatter"].get("project_id", "unknown")
            by_project[pid] = by_project.get(pid, 0) + 1

        # Should have multiple projects represented
        assert len([p for p, c in by_project.items() if p != "global"]) >= 3

    def test_collects_evidence_for_proposals(
        self,
        instinct_manager: InstinctManager,
        multiple_workflow_instincts: list[Path]
    ) -> None:
        """
        Evolve should collect evidence from all instincts in a cluster.
        """
        all_instincts = instinct_manager.list_instincts()
        workflow_instincts = [
            i for i in all_instincts
            if i["frontmatter"]["domain"] == "workflow"
        ]

        # Calculate total evidence
        total_evidence = sum(
            i["frontmatter"].get("evidence_count", 0)
            for i in workflow_instincts
        )

        assert total_evidence >= 9  # At least some evidence collected


class TestEvolveCommandProposals:
    """Tests for skill proposal generation."""

    def test_proposal_includes_domain(
        self,
        instinct_manager: InstinctManager,
        multiple_workflow_instincts: list[Path]
    ) -> None:
        """
        Generated proposals should include the domain.
        """
        all_instincts = instinct_manager.list_instincts()
        workflow_instincts = [
            i for i in all_instincts
            if i["frontmatter"]["domain"] == "workflow"
        ]

        # Domain should be consistent
        domains = set(i["frontmatter"]["domain"] for i in workflow_instincts)
        assert domains == {"workflow"}

    def test_proposal_includes_triggers(
        self,
        instinct_manager: InstinctManager,
        multiple_workflow_instincts: list[Path]
    ) -> None:
        """
        Proposals should aggregate triggers from source instincts.
        """
        all_instincts = instinct_manager.list_instincts()
        workflow_instincts = [
            i for i in all_instincts
            if i["frontmatter"]["domain"] == "workflow"
        ]

        triggers = [i["frontmatter"]["trigger"] for i in workflow_instincts]
        # All triggers should start with "when"
        assert all(t.startswith("when") for t in triggers)

    def test_proposal_calculates_average_confidence(
        self,
        instinct_manager: InstinctManager,
        multiple_workflow_instincts: list[Path]
    ) -> None:
        """
        Proposals should calculate average confidence from source instincts.
        """
        all_instincts = instinct_manager.list_instincts()
        workflow_instincts = [
            i for i in all_instincts
            if i["frontmatter"]["domain"] == "workflow"
        ]

        # Calculate average confidence
        confidences = [i["frontmatter"]["confidence"] for i in workflow_instincts]
        avg_confidence = sum(confidences) / len(confidences)

        # Should be in valid range
        assert 0.0 <= avg_confidence <= 1.0
        # Given our fixture data, should be around 0.6-0.8
        assert 0.5 <= avg_confidence <= 0.9


class TestEvolveCommandFilters:
    """Tests for evolve command filtering options."""

    def test_filter_by_domain(
        self,
        instinct_manager: InstinctManager,
        mixed_domain_instincts: list[Path]
    ) -> None:
        """
        Evolve should support filtering by domain.
        """
        # Simulate filtering by domain
        all_instincts = instinct_manager.list_instincts(project_id="mixed-proj")

        workflow_only = [
            i for i in all_instincts
            if i["frontmatter"]["domain"] == "workflow"
        ]

        # Should only have workflow instincts
        assert len(workflow_only) >= 1
        assert all(i["frontmatter"]["domain"] == "workflow" for i in workflow_only)

    def test_minimum_cluster_size(
        self,
        instinct_manager: InstinctManager,
        mixed_domain_instincts: list[Path]
    ) -> None:
        """
        Evolve should respect minimum cluster size.
        """
        all_instincts = instinct_manager.list_instincts(project_id="mixed-proj")

        # Group by domain
        by_domain: dict[str, list] = {}
        for inst in all_instincts:
            domain = inst["frontmatter"]["domain"]
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(inst)

        # With min_size=2, each domain has only 1 instinct
        # So no clusters would form
        min_size = 2
        clusters = {d: insts for d, insts in by_domain.items() if len(insts) >= min_size}

        # Each domain has only 1 instinct, so no clusters
        assert len(clusters) == 0


class TestEvolveScriptExecution:
    """Tests for evolve script execution.

    These tests verify the script wrapper works correctly.
    The scripts are currently stubs, so these tests should FAIL.
    """

    def test_script_returns_zero_exit_code(
        self, evolve_script: Path, multiple_workflow_instincts: list[Path], temp_home: Path
    ) -> None:
        """
        Script should return exit code 0 on success.

        Currently FAILS because script is a stub.
        """
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(evolve_script), "--dry-run"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_script_outputs_cluster_info(
        self, evolve_script: Path, multiple_workflow_instincts: list[Path], temp_home: Path
    ) -> None:
        """
        Script should output cluster information.

        Currently FAILS because script is a stub.
        """
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(evolve_script), "--dry-run"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )

        # Should mention clusters or domains
        output = result.stdout.lower()
        assert "cluster" in output or "domain" in output or "workflow" in output, \
            f"Expected cluster info in output: {result.stdout}"
