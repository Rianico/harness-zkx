"""
Instinct Manager for the Continuous Learning System.

This module provides:
- Creating instinct YAML files from agent results
- Updating existing instincts with new evidence
- Promoting project-scoped instincts to global scope

Phase 4 GREEN: Implementation for TDD.
"""

# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "pydantic"]
# ///

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from hooks.observe.agent_runner import AgentResult, InstinctCreated, InstinctUpdated, Promotion


class InstinctManager:
    """
    Manager for instinct lifecycle operations.

    This class handles:
    1. Creating new instinct YAML files
    2. Updating existing instincts with new evidence
    3. Promoting project instincts to global scope
    """

    def __init__(self, base_dir: Path) -> None:
        """
        Initialize the instinct manager.

        Args:
            base_dir: The base directory for data storage (homunculus dir)
        """
        self.base_dir = base_dir

    def create_instinct(
        self,
        instinct: InstinctCreated,
        project_id: str | None = None,
        scope: str = "project"
    ) -> Path | None:
        """
        Create a new instinct YAML file.

        Args:
            instinct: The instinct data to create
            project_id: The project ID for project-scoped instincts
            scope: "project" or "global"

        Returns:
            Path to created file, or None if creation failed
        """
        # Determine target directory
        if scope == "global":
            target_dir = self.base_dir / "instincts" / "personal"
            effective_project_id = "global"
        else:
            if not project_id:
                return None
            target_dir = self.base_dir / "projects" / project_id / "instincts" / "personal"
            effective_project_id = project_id

        # Check if instinct already exists
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{instinct.id}.yaml"

        if file_path.exists():
            # Don't overwrite existing instincts
            return None

        # Build frontmatter
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        evidence_list = instinct.evidence or []

        frontmatter = {
            "id": instinct.id,
            "trigger": instinct.trigger,
            "confidence": min(instinct.confidence, 1.0),  # Cap at 1.0
            "domain": instinct.domain,
            "scope": scope,
            "project_id": effective_project_id,
            "created_at": now,
            "updated_at": now,
            "evidence_count": len(evidence_list)
        }

        # Build content
        lines = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip(),
            "---",
            "",
            f"# {self._title_from_id(instinct.id)}",
            "",
            "## Action",
            instinct.action or "No action specified.",
            "",
            "## Evidence",
        ]

        for ev in evidence_list:
            lines.append(f"- Session {ev.session_id}: {ev.description}")

        if not evidence_list:
            lines.append("- No evidence recorded yet.")

        file_path.write_text("\n".join(lines) + "\n")
        return file_path

    def _title_from_id(self, instinct_id: str) -> str:
        """Convert an instinct ID to a title."""
        return instinct_id.replace("-", " ").title()

    def update_instinct(
        self,
        update: InstinctUpdated,
        project_id: str
    ) -> Path | None:
        """
        Update an existing instinct with new evidence and confidence.

        Args:
            update: The update data
            project_id: The project ID for the instinct

        Returns:
            Path to updated file, or None if instinct not found
        """
        # Find the instinct file
        file_path = self._find_instinct_path(update.id, project_id)
        if not file_path or not file_path.exists():
            return None

        # Parse existing content
        content = file_path.read_text()
        parts = content.split("---")
        if len(parts) < 3:
            return None

        frontmatter = yaml.safe_load(parts[1])
        body = "---".join(parts[2:])

        # Update frontmatter
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        frontmatter["confidence"] = min(update.new_confidence, 1.0)  # Cap at 1.0
        frontmatter["updated_at"] = now

        # Get existing evidence count
        existing_count = frontmatter.get("evidence_count", 0)

        # Append new evidence (no duplicates by session_id)
        existing_sessions = set()
        for line in body.split("\n"):
            if line.startswith("- Session "):
                # Extract session ID from line like "- Session s1: description"
                try:
                    session_part = line.split("Session ")[1].split(":")[0].strip()
                    existing_sessions.add(session_part)
                except (IndexError, ValueError):
                    pass

        new_evidence = update.evidence_appended or []
        unique_new_evidence = [
            ev for ev in new_evidence
            if ev.session_id not in existing_sessions
        ]

        # Update evidence count
        frontmatter["evidence_count"] = existing_count + len(unique_new_evidence)

        # Rebuild content
        lines = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip(),
            "---",
            body.rstrip()
        ]

        # Append new evidence
        if unique_new_evidence:
            lines.append("")
            for ev in unique_new_evidence:
                lines.append(f"- Session {ev.session_id}: {ev.description}")

        file_path.write_text("\n".join(lines) + "\n")
        return file_path

    def _find_instinct_path(self, instinct_id: str, project_id: str) -> Path | None:
        """Find the path to an instinct file."""
        # Check project-specific location
        project_path = self.base_dir / "projects" / project_id / "instincts" / "personal" / f"{instinct_id}.yaml"
        if project_path.exists():
            return project_path

        # Check global location
        global_path = self.base_dir / "instincts" / "personal" / f"{instinct_id}.yaml"
        if global_path.exists():
            return global_path

        return None

    def promote_instinct(
        self,
        promotion: Promotion,
        force: bool = False
    ) -> Path | None:
        """
        Promote a project-scoped instinct to global scope.

        Args:
            promotion: The promotion data
            force: If True, bypass multi-project requirement

        Returns:
            Path to global instinct file, or None if promotion failed
        """
        # Check promotion eligibility
        if not force:
            is_eligible, _ = self.check_promotion_eligibility(promotion.id)
            if not is_eligible:
                return None

        # Find all instances of this instinct across projects
        instances = self._find_all_instinct_instances(promotion.id)

        if not instances:
            return None

        # Create global instinct
        global_dir = self.base_dir / "instincts" / "personal"
        global_dir.mkdir(parents=True, exist_ok=True)
        global_path = global_dir / f"{promotion.id}.yaml"

        # Use the first instance as the base
        first_project_id, first_path = instances[0]
        content = first_path.read_text()
        parts = content.split("---")
        if len(parts) < 3:
            return None

        frontmatter = yaml.safe_load(parts[1])
        body = "---".join(parts[2:])

        # Update frontmatter for global scope
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        frontmatter["scope"] = "global"
        frontmatter["project_id"] = "global"
        frontmatter["promoted_at"] = now

        # Calculate average confidence and total evidence
        total_confidence = frontmatter.get("confidence", 0)
        total_evidence = frontmatter.get("evidence_count", 0)
        source_projects = [first_project_id]

        for project_id, inst_path in instances[1:]:
            inst_content = inst_path.read_text()
            inst_parts = inst_content.split("---")
            if len(inst_parts) >= 3:
                inst_fm = yaml.safe_load(inst_parts[1])
                total_confidence += inst_fm.get("confidence", 0)
                total_evidence += inst_fm.get("evidence_count", 0)
                source_projects.append(project_id)

        avg_confidence = total_confidence / len(instances) if instances else 0
        frontmatter["confidence"] = round(avg_confidence, 2)
        frontmatter["evidence_count"] = total_evidence
        frontmatter["source_projects"] = source_projects

        # Build new content
        lines = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip(),
            "---",
            body.rstrip(),
            "",
            "## Promotion",
            f"- Reason: {promotion.reason}",
            f"- Promoted at: {now}",
            f"- Source projects: {', '.join(source_projects)}"
        ]

        global_path.write_text("\n".join(lines) + "\n")

        # Remove project-specific copies
        for project_id, inst_path in instances:
            if inst_path.exists():
                inst_path.unlink()

        return global_path

    def _find_all_instinct_instances(self, instinct_id: str) -> list[tuple[str, Path]]:
        """Find all instances of an instinct across all projects."""
        instances = []

        projects_dir = self.base_dir / "projects"
        if not projects_dir.exists():
            return instances

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            instinct_path = project_dir / "instincts" / "personal" / f"{instinct_id}.yaml"
            if instinct_path.exists():
                instances.append((project_dir.name, instinct_path))

        return instances

    def process_result(
        self,
        result: AgentResult,
        project_id: str
    ) -> list[Path]:
        """
        Process an AgentResult, creating/updating/promoting instincts.

        Args:
            result: The agent result to process
            project_id: The project ID for project-scoped operations

        Returns:
            List of paths to affected files
        """
        affected_paths: list[Path] = []

        # Create new instincts
        for instinct in result.instincts_created:
            path = self.create_instinct(instinct, project_id)
            if path:
                affected_paths.append(path)

        # Update existing instincts
        for update in result.instincts_updated:
            path = self.update_instinct(update, project_id)
            if path:
                affected_paths.append(path)

        # Process promotions
        for promotion in result.promotions:
            path = self.promote_instinct(promotion)
            if path:
                affected_paths.append(path)

        return affected_paths

    def load_instinct(
        self,
        instinct_id: str,
        project_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        Load an instinct file and parse its content.

        Args:
            instinct_id: The instinct ID
            project_id: The project ID (for project-scoped instincts)

        Returns:
            Parsed instinct data, or None if not found
        """
        file_path = None

        if project_id:
            file_path = self._find_instinct_path(instinct_id, project_id)

        if not file_path:
            # Try global
            global_path = self.base_dir / "instincts" / "personal" / f"{instinct_id}.yaml"
            if global_path.exists():
                file_path = global_path

        if not file_path or not file_path.exists():
            return None

        content = file_path.read_text()
        parts = content.split("---")
        if len(parts) < 3:
            return None

        frontmatter = yaml.safe_load(parts[1])
        body = "---".join(parts[2:])

        return {
            "frontmatter": frontmatter,
            "body": body.strip(),
            "path": str(file_path)
        }

    def list_instincts(
        self,
        project_id: str | None = None,
        scope: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List all instincts, optionally filtered by project and scope.

        Args:
            project_id: Filter by project ID
            scope: Filter by scope ("project" or "global")

        Returns:
            List of instinct data dictionaries
        """
        instincts: list[dict[str, Any]] = []

        # List global instincts
        if scope is None or scope == "global":
            global_dir = self.base_dir / "instincts" / "personal"
            if global_dir.exists():
                for yaml_file in global_dir.glob("*.yaml"):
                    data = self.load_instinct(yaml_file.stem)
                    if data:
                        instincts.append(data)

        # List project-specific instincts
        if scope is None or scope == "project":
            if project_id:
                project_dir = self.base_dir / "projects" / project_id / "instincts" / "personal"
                if project_dir.exists():
                    for yaml_file in project_dir.glob("*.yaml"):
                        data = self.load_instinct(yaml_file.stem, project_id)
                        if data:
                            instincts.append(data)
            else:
                # List from all projects
                projects_dir = self.base_dir / "projects"
                if projects_dir.exists():
                    for proj_dir in projects_dir.iterdir():
                        if not proj_dir.is_dir():
                            continue
                        proj_instincts_dir = proj_dir / "instincts" / "personal"
                        if proj_instincts_dir.exists():
                            for yaml_file in proj_instincts_dir.glob("*.yaml"):
                                data = self.load_instinct(yaml_file.stem, proj_dir.name)
                                if data:
                                    instincts.append(data)

        return instincts

    def check_promotion_eligibility(
        self,
        instinct_id: str
    ) -> tuple[bool, str]:
        """
        Check if an instinct qualifies for promotion.

        Criteria:
        - Exists in at least 2 projects
        - Average confidence >= 0.8

        Args:
            instinct_id: The instinct ID to check

        Returns:
            Tuple of (is_eligible, reason)
        """
        instances = self._find_all_instinct_instances(instinct_id)

        if len(instances) < 2:
            return (False, f"Instinct exists in only {len(instances)} project(s), need at least 2")

        # Calculate average confidence
        total_confidence = 0.0
        for _, inst_path in instances:
            content = inst_path.read_text()
            parts = content.split("---")
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                total_confidence += frontmatter.get("confidence", 0)

        avg_confidence = total_confidence / len(instances)

        if avg_confidence < 0.8:
            return (False, f"Average confidence {avg_confidence:.2f} is below 0.8 threshold")

        return (True, f"Eligible: found in {len(instances)} projects with average confidence {avg_confidence:.2f}")
