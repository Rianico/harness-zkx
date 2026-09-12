"""Tests for the `templates/` byte contract.

Templates live in `skills/scaffold/templates/<flavor>/<target path>`; a `.j2` suffix marks a
file that Jinja renders, every other template ships verbatim. These tests pin the layout, the
registry coherence (no orphan file, no dangling reference), the fail-loud loader, and the
output bytes — a formatter or template edit that changes a rendered byte silently changes
every generated project, so it must fail here first.

Pins are per *rendered cell*, not per template file: adding a runtime to `CI_RUNTIMES` adds
cells that fail until pinned, while existing cells keep their hash and cannot drift unnoticed.
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


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_templates", SCRIPT)
SRC = SCRIPT.read_text(encoding="utf-8")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _as_source(pins: dict[str, str]) -> str:
    """Format a pin dict for copy-paste into this file (failure messages carry it)."""
    return "\n".join(f'    "{k}": "{v}",' for k, v in sorted(pins.items()))


def _template_files() -> list[str]:
    return sorted(p.relative_to(TEMPLATES).as_posix() for p in TEMPLATES.rglob("*") if p.is_file())


def _raw_files() -> list[str]:
    return [rel for rel in _template_files() if not rel.endswith(".j2")]


def _referenced_templates() -> set[str]:
    """Every template the generator can read: literal loader calls, the CI registry, extends."""
    refs = set(re.findall(r'(?:load_template|render_template)\(\s*"([^"]+)"', SRC))
    refs |= set(scaffold.CI_RUNTIMES.values())
    for rel in _template_files():
        refs |= set(re.findall(r'{%\s*extends\s+"([^"]+)"', (TEMPLATES / rel).read_text("utf-8")))
    return refs


def _render_cases() -> dict[str, str]:
    """Every cell the generator can ship, labelled — the unit of the byte contract."""
    cases = {
        "CONTRIBUTING.default (project_name=demo)": scaffold.render_template(
            "shared/CONTRIBUTING.default.md.j2", project_name="demo"
        ),
        "CONTRIBUTING.python (project_name=demo)": scaffold.render_template(
            "shared/CONTRIBUTING.python.md.j2", project_name="demo"
        ),
        "CONTRIBUTING.typescript (project_name=demo)": scaffold.render_template(
            "shared/CONTRIBUTING.typescript.md.j2", project_name="demo"
        ),
        "rust/Cargo.toml (project_name=demo-cli)": scaffold.render_template(
            "rust/Cargo.toml.j2", project_name="demo-cli"
        ),
        "typescript/src/index.ts (project_name=demo)": scaffold.render_template(
            "typescript/src/index.ts.j2", project_name="demo"
        ),
        "typescript/vitest.config.ts (threshold=75)": scaffold.render_template(
            "typescript/vitest.config.ts.j2", threshold=75
        ),
    }
    for variant in scaffold.CI_RUNTIMES:
        for coverage in (False, True):
            suffix = "+coverage" if coverage else ""
            cases[f"ci/release.yml[{variant}{suffix}]"] = scaffold.render_ci_release(
                variant, with_coverage=coverage, threshold=scaffold.DEFAULT_COVERAGE_THRESHOLD
            )
    return cases


# Re-pin only when the byte change is intended — the failure message prints the new digests.
RAW_SHA256: dict[str, str] = {
    "git/.githooks/pre-push": "de8caa1a501942aa208b50db1eabec5ecd54adb92272e131cd658ca3d05867dd",
    "git/.github/ISSUE_TEMPLATE/01-bug_report.yml": "3fbe634b22982b9df5466b26e6bcebcc86a7c9560616275a3335e6a2f819f279",
    "git/.github/ISSUE_TEMPLATE/02-feature_request.yml": "087a54cf8324469c1a1e06f7776419c5dad072781bb76245e42037fc0440c3ac",
    "git/.github/ISSUE_TEMPLATE/config.yml": "c1af6fc67ffa59cb4c87561165267bbd7e7b8d7a1763a61c7a4ff065e5cff59e",
    "git/.github/pull_request_template.md": "d3d2216b8fd2e58f6e8de255ca9f20050916d2eb93c808989b3716e24e320c85",
    "git/.github/workflows/changelog-check.yml": "36bc35ccb97a5f95a698e3ca0a12afbc3a0ad2c466a01e224d4dcc2b5647dbd3",
    "git/.husky/pre-push": "4c08b6fe2b024a878970f2a74f22426460474d34d5d6a4f9115d1c2f3b62559f",
    "git/.releaserc.json": "8e4a562913c3c8276f6689046d5b92c862ffa79d5b08c04b284eea75e0c3570f",
    "git/CHANGELOG.md": "bdaecdeebf458639f8ab199e8bd8d9452b5091276e435f8271029e65d5a0ca16",
    "git/commitlint.config.js": "9c46dd6e2258b8783f57255cbcdd09fd13c0283069b281568806ba147df85340",
    "rust/rust-toolchain.toml": "a6a0bbd29ffaa8182dc22d1d9149709f1091e47df40ed96eb8a78a711c66a4ce",
    "typescript/.oxfmtrc.json": "c0dae20afb1d2ab41fcddb3dad2a1334bb114e6906aa62b3b955a270486c2ac8",
    "typescript/.oxlintrc.json": "af18217668580c6e3df7ede6481eb29df644a4f8929d5a9a15faec6a476a6d71",
    "typescript/scripts/oxlint-plugin-comment-gate.js": "9cbf8af3366f0e71f743c518c8ba31d5aed0144c7705ae76144a639673dd7484",
    "typescript/src/cli.ts": "3dd9148df21a5c186761c242b7f49ef8a3c4f6041535707ee5bc09879ceeeb85",
    "typescript/tests/index.test.ts": "4b91f6158817cf7dd1b57a41472772e961106bdf34430690e17386b53e0df80f",
}

RENDERED_SHA256: dict[str, str] = {
    "CONTRIBUTING.default (project_name=demo)": "3af4b4bbb29406a678a01bfc8cceadf576577db747680a7c4b0f8451451c2357",
    "CONTRIBUTING.python (project_name=demo)": "cc3105b590d9b9e6ee644bc72cf849d219f368effa4124f3ab8e526bce029a16",
    "CONTRIBUTING.typescript (project_name=demo)": "31dafc569c65f1dbca8137fce61b5ef168c83226cd271a6d74e2c73d0aa0417f",
    "ci/release.yml[node+coverage]": "e3b1190fae6ccade3d0f35bc3ed3cbf79e6ba8cba90907fc8f23c9080f38bb97",
    "ci/release.yml[node]": "efbb1c3028b8776dcf76d9e1f6a68a8d834ad7dc4a82b8469b3c63f0b8590aa7",
    "ci/release.yml[python+coverage]": "ae174f49d7559869c9e340074e722740c94ff3c13d4480cef52dba82b6c39bb1",
    "ci/release.yml[python]": "76776943ebe6ae4de1da0961f2cd39907893f39296041fe78e1d3349db87e473",
    "ci/release.yml[rust+coverage]": "77d010a336e07dd4a32d668d088303367677852b985a17c3d39c6b6eed09bb39",
    "ci/release.yml[rust]": "f6cb0109fbc1ee9229eaa2ea9db8e9260f18ca6428998d65be791a3ba867f6f9",
    "rust/Cargo.toml (project_name=demo-cli)": "68e139adfc750f33851fe0778d8bdf199b37c23a8d2aee147c39d63d4fc4cc0c",
    "typescript/src/index.ts (project_name=demo)": "dd66d9df929a39c2e17a8b6609c030e03b6d247d7dee0b22649654633708410f",
    "typescript/vitest.config.ts (threshold=75)": "a175e6b0d7402032010f980086249c89968a5b393575f084126fd1645911b586",
}


# --- layout + registry ---------------------------------------------------------


def test_template_layout_is_flavor_then_target_path():
    for rel in _template_files():
        assert rel.split("/")[0] in FLAVORS, f"{rel} is not under a known flavor directory"


def test_every_referenced_template_exists():
    for rel in _referenced_templates():
        assert (TEMPLATES / rel).is_file(), f"template reference {rel!r} points at nothing"


def test_no_orphan_template_files():
    assert set(_template_files()) == _referenced_templates()


def test_j2_suffix_marks_exactly_the_rendered_templates():
    render_calls = set(re.findall(r'render_template\(\s*"([^"]+)"', SRC))
    raw_calls = set(re.findall(r'load_template\(\s*"([^"]+)"', SRC))
    assert render_calls, "expected literal render_template() calls"
    assert all(rel.endswith(".j2") for rel in render_calls)
    assert all(not rel.endswith(".j2") for rel in raw_calls)
    # registry templates render through render_ci_release and are reached by name, not by a
    # literal call; the base is only ever reached through {% extends %}
    assert all(rel.endswith(".j2") for rel in scaffold.CI_RUNTIMES.values())
    assert set(scaffold.CI_RUNTIMES.values()) <= _referenced_templates()
    assert "ci/release.yml.j2" not in render_calls
    assert "ci/release.yml.j2" in _referenced_templates()


def test_missing_template_fails_loud():
    for call in (
        lambda: scaffold.load_template("git/does-not-exist.yml"),
        lambda: scaffold.render_template("ci/runtimes/does-not-exist.yml.j2"),
    ):
        try:
            call()
        except FileNotFoundError as exc:
            assert "templates/ ships with scripts/" in str(exc)
        else:
            raise AssertionError("missing template must raise, never fall back to embedded bytes")


def test_base_template_needs_a_runtime_block():
    """`{% block verify required %}` — a base render without a runtime must raise, not ship."""
    try:
        scaffold.render_template(
            "ci/release.yml.j2",
            shas=scaffold.SHA_TABLE,
            node_version=scaffold.NODE_VERSION_NUM,
            gh_actions_token=scaffold.GH_ACTIONS_TOKEN,
            with_coverage=False,
            threshold=scaffold.DEFAULT_COVERAGE_THRESHOLD,
        )
    except Exception as exc:  # jinja2.TemplateRuntimeError: Required block 'verify' not found
        assert "verify" in str(exc)
    else:
        raise AssertionError("ci/release.yml.j2 must not render without a runtime fragment")


# --- bytes ---------------------------------------------------------------------


def test_raw_template_bytes_are_pinned():
    actual = {rel: _digest((TEMPLATES / rel).read_bytes().decode("utf-8")) for rel in _raw_files()}
    assert actual == RAW_SHA256, (
        "raw template bytes changed — re-pin only if intended:\n" + _as_source(actual)
    )


def test_rendered_bytes_are_pinned():
    cases = _render_cases()
    missing = sorted(set(cases) - set(RENDERED_SHA256))
    assert not missing, "new rendered cell(s) — pin them:\n" + _as_source(
        {k: _digest(cases[k]) for k in missing}
    )
    drifted = sorted(k for k, v in cases.items() if _digest(v) != RENDERED_SHA256[k])
    assert not drifted, "rendered bytes changed — re-pin only if intended:\n" + _as_source(
        {k: _digest(cases[k]) for k in drifted}
    )


def test_rendered_output_has_no_template_leftovers():
    for label, out in _render_cases().items():
        assert "{%" not in out, f"{label} shipped a Jinja tag"
        # the one legitimate `{{` is the Actions expression the context supplies
        stripped = out.replace(scaffold.GH_ACTIONS_TOKEN, "")
        assert "{{" not in stripped and "}}" not in stripped, (
            f"{label} shipped an unrendered variable"
        )


def test_generator_ships_raw_template_bytes_verbatim(tmp_path):
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


def test_flavor_raw_artifacts_ship_verbatim(tmp_path):
    rust = tmp_path / "rustrepo"
    rust.mkdir()
    scaffold.do_rust(rust, "demo", dry_run=False, with_coverage=True, threshold=80)
    assert (rust / "rust-toolchain.toml").read_bytes() == (
        TEMPLATES / "rust/rust-toolchain.toml"
    ).read_bytes()

    ts = tmp_path / "tsrepo"
    ts.mkdir()
    scaffold.do_typescript(
        ts, "demo", dry_run=False, ts_variant="cli", with_coverage=True, threshold=80
    )
    for written, rel in {
        ".oxlintrc.json": "typescript/.oxlintrc.json",
        ".oxfmtrc.json": "typescript/.oxfmtrc.json",
        "scripts/oxlint-plugin-comment-gate.js": "typescript/scripts/oxlint-plugin-comment-gate.js",
        "tests/index.test.ts": "typescript/tests/index.test.ts",
        "src/cli.ts": "typescript/src/cli.ts",
    }.items():
        assert (ts / written).read_bytes() == (TEMPLATES / rel).read_bytes(), written


def test_contributing_variants_render_from_shared(tmp_path):
    scaffold.do_git(tmp_path, "demo", dry_run=False)
    expected = scaffold.render_template("shared/CONTRIBUTING.default.md.j2", project_name="demo")
    assert (tmp_path / "CONTRIBUTING.md").read_text(encoding="utf-8") == expected

    py = tmp_path / "pyrepo"
    py.mkdir()
    scaffold.do_python(py, "demo", dry_run=False, with_coverage=False, threshold=80)
    python_render = scaffold.render_template(
        "shared/CONTRIBUTING.python.md.j2", project_name="demo"
    )
    assert (py / "CONTRIBUTING.md").read_text(encoding="utf-8") == python_render


def test_ci_runtime_registry_drives_the_cli_choices():
    parser_choices = re.search(r'"--ci-variant",\s*\n\s*choices=([^,]+),', SRC)
    assert parser_choices is not None
    assert parser_choices.group(1).strip() == "list(CI_RUNTIMES)"
    for variant in scaffold.CI_RUNTIMES:
        assert (TEMPLATES / scaffold.CI_RUNTIMES[variant]).is_file(), variant
