"""Tests for the `templates/` byte contract.

Static artifacts live in `skills/scaffold/templates/<flavor>/<target path>`; the
generator ships their bytes verbatim. These tests pin the layout, the registry
coherence (no orphan file, no dangling reference), the fail-loud loader, and the
bytes themselves — a formatter or editor rewrite of a template is a silent change
to every generated project, so it must fail here first.
"""

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"
TEMPLATES = SKILL_DIR / "templates"

# flavors own their projection; `shared/` holds cross-flavor artifacts (CONTRIBUTING)
FLAVORS = {"git", "shared", "ci", "python", "rust", "typescript"}

# Re-pin (`sha256sum skills/scaffold/templates/**`) only when the byte change is intended.
SHA256 = {
    "git/.githooks/pre-push": "de8caa1a501942aa208b50db1eabec5ecd54adb92272e131cd658ca3d05867dd",
    "git/.github/ISSUE_TEMPLATE/01-bug_report.yml": (
        "3fbe634b22982b9df5466b26e6bcebcc86a7c9560616275a3335e6a2f819f279"
    ),
    "git/.github/ISSUE_TEMPLATE/02-feature_request.yml": (
        "087a54cf8324469c1a1e06f7776419c5dad072781bb76245e42037fc0440c3ac"
    ),
    "git/.github/ISSUE_TEMPLATE/config.yml": (
        "c1af6fc67ffa59cb4c87561165267bbd7e7b8d7a1763a61c7a4ff065e5cff59e"
    ),
    "git/.github/pull_request_template.md": (
        "d3d2216b8fd2e58f6e8de255ca9f20050916d2eb93c808989b3716e24e320c85"
    ),
    "git/.github/workflows/changelog-check.yml": (
        "36bc35ccb97a5f95a698e3ca0a12afbc3a0ad2c466a01e224d4dcc2b5647dbd3"
    ),
    "git/.husky/pre-push": "4c08b6fe2b024a878970f2a74f22426460474d34d5d6a4f9115d1c2f3b62559f",
    "git/.releaserc.json": "8e4a562913c3c8276f6689046d5b92c862ffa79d5b08c04b284eea75e0c3570f",
    "git/CHANGELOG.md": "bdaecdeebf458639f8ab199e8bd8d9452b5091276e435f8271029e65d5a0ca16",
    "git/commitlint.config.js": (
        "9c46dd6e2258b8783f57255cbcdd09fd13c0283069b281568806ba147df85340"
    ),
    "shared/CONTRIBUTING.default.md": (
        "227e8644ccb587f197dc7d89d45bb80e876167b7bdc53af9d741f8cdb16c9907"
    ),
    "shared/CONTRIBUTING.python.md": (
        "a145f6a75022026d35948a5c831236a6138454f1d1d6720b72e3cd66dc6db72c"
    ),
    "shared/CONTRIBUTING.typescript.md": (
        "b9ddaeba798b2a69007eece82a59190ddb915432703fd619810cb6356bb75148"
    ),
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_templates", SCRIPT)
SRC = SCRIPT.read_text(encoding="utf-8")


def _template_files() -> list[str]:
    return sorted(p.relative_to(TEMPLATES).as_posix() for p in TEMPLATES.rglob("*") if p.is_file())


# --- layout + registry ---------------------------------------------------------


def test_template_layout_is_flavor_then_target_path():
    for rel in _template_files():
        assert rel.split("/")[0] in FLAVORS, f"{rel} is not under a known flavor directory"


def test_every_referenced_template_exists():
    for rel in re.findall(r'load_template\("([^"]+)"\)', SRC):
        assert (TEMPLATES / rel).is_file(), f"load_template({rel!r}) points at nothing"


def test_no_orphan_template_files():
    referenced = set(re.findall(r'load_template\("([^"]+)"\)', SRC))
    assert set(_template_files()) == referenced


def test_missing_template_fails_loud():
    try:
        scaffold.load_template("git/does-not-exist.yml")
    except FileNotFoundError as exc:
        assert "templates/ ships with scripts/" in str(exc)
    else:
        raise AssertionError("missing template must raise, never fall back to embedded bytes")


# --- bytes ---------------------------------------------------------------------


def test_template_bytes_are_pinned():
    changed = [
        rel
        for rel, digest in SHA256.items()
        if hashlib.sha256((TEMPLATES / rel).read_bytes()).hexdigest() != digest
    ]
    assert not changed, f"template bytes changed: {changed} — re-pin only if intended"


def test_generator_ships_template_bytes_verbatim(tmp_path):
    scaffold.do_git(tmp_path, "demo", dry_run=False)

    shipped = {
        ".releaserc.json": "git/.releaserc.json",
        ".github/workflows/changelog-check.yml": "git/.github/workflows/changelog-check.yml",
        ".github/ISSUE_TEMPLATE/01-bug_report.yml": "git/.github/ISSUE_TEMPLATE/01-bug_report.yml",
        ".github/ISSUE_TEMPLATE/02-feature_request.yml": (
            "git/.github/ISSUE_TEMPLATE/02-feature_request.yml"
        ),
        ".github/ISSUE_TEMPLATE/config.yml": "git/.github/ISSUE_TEMPLATE/config.yml",
        ".github/pull_request_template.md": "git/.github/pull_request_template.md",
        ".githooks/pre-push": "git/.githooks/pre-push",
        ".husky/pre-push": "git/.husky/pre-push",
        "commitlint.config.js": "git/commitlint.config.js",
        "CHANGELOG.md": "git/CHANGELOG.md",
    }
    for written, rel in shipped.items():
        assert (tmp_path / written).read_bytes() == (TEMPLATES / rel).read_bytes(), written


def test_contributing_variants_render_from_shared(tmp_path):
    scaffold.do_git(tmp_path, "demo", dry_run=False)
    default = (TEMPLATES / "shared/CONTRIBUTING.default.md").read_text(encoding="utf-8")
    assert (tmp_path / "CONTRIBUTING.md").read_text(encoding="utf-8") == default.format(
        project_name="demo"
    )

    py = tmp_path / "pyrepo"
    py.mkdir()
    scaffold.do_python(py, "demo", dry_run=False, with_coverage=False, threshold=80)
    python_tmpl = (TEMPLATES / "shared/CONTRIBUTING.python.md").read_text(encoding="utf-8")
    assert (py / "CONTRIBUTING.md").read_text(encoding="utf-8") == python_tmpl.format(
        project_name="demo"
    )
