from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).parent.parent
    / "skills"
    / "ai-engineering-expert"
    / "subskills"
    / "skill-authoring"
    / "scripts"
    / "validate-deps.py"
)


def run_validate_deps(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", str(SCRIPT_PATH), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def write_skill(root: Path, name: str, depends_on: str | None = None) -> None:
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True)
    metadata = f"metadata:\n  depends-on: [{depends_on}]\n" if depends_on else ""
    (skill_dir / "SKILL.md").write_text(
        (
            f"---\nname: {name}\n"
            "description: Test skill for dependency validation.\n"
            f"{metadata}---\n\n# {name}\n"
        ),
        encoding="utf-8",
    )


def test_callers_lists_inbound_depends_on(tmp_path: Path) -> None:
    write_skill(tmp_path, "target")
    write_skill(tmp_path, "caller-a", "target")
    write_skill(tmp_path, "caller-b", "other")

    result = run_validate_deps("callers", "target", "--project-root", str(tmp_path))

    assert result.returncode == 0
    assert "Skills declaring metadata.depends-on for 'target':" in result.stdout
    assert "caller-a: skills/caller-a/SKILL.md" in result.stdout
    assert "caller-b" not in result.stdout


def test_callers_reports_no_dependents(tmp_path: Path) -> None:
    write_skill(tmp_path, "target")

    result = run_validate_deps("callers", "target", "--project-root", str(tmp_path))

    assert result.returncode == 0
    assert "No skills declare metadata.depends-on for 'target'." in result.stdout
