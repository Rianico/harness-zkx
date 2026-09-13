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
    """Template files, minus build litter git already ignores.

    A tool that imports a template `.py` (pytest's assertion cache, ruff check) leaves a
    `__pycache__` inside the tree; it is not a template, and it must not read as one.
    """
    return sorted(
        p.relative_to(TEMPLATES).as_posix()
        for p in TEMPLATES.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )


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
        "python/src/_pkg/__init__.py (project_name=demo)": scaffold.render_template(
            "python/src/_pkg/__init__.py.j2", project_name="demo"
        ),
        "python/tests/test_smoke.py (module=demo)": scaffold.render_template(
            "python/tests/test_smoke.py.j2", module="demo"
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
    "git/.github/ISSUE_TEMPLATE/01-bug_report.yml": "042c8a9647b165ef3c354cfd60e1a1b619b81b86f60bdc5fec65e324e061d676",
    "git/.github/ISSUE_TEMPLATE/02-feature_request.yml": "087a54cf8324469c1a1e06f7776419c5dad072781bb76245e42037fc0440c3ac",
    "git/.github/ISSUE_TEMPLATE/config.yml": "27539305684d7673d88e80ec149c4ec9714da05a054b09fee67d56b8a7e5a820",
    "git/.github/pull_request_template.md": "a6c4a5a99295d803693760bf33246e995c22c16b2c282caa1e52eb4fd667b603",
    "git/.github/workflows/changelog-check.yml": "bcc24d5a39359a2e2bac26039d172568bbd7c47f5dd6f9ad497d7d2a29419c7d",
    "git/.husky/pre-push": "4c08b6fe2b024a878970f2a74f22426460474d34d5d6a4f9115d1c2f3b62559f",
    "git/.releaserc.json": "380cd48c0082fdbbad3fb439c6378840d5412a9d93368fee929a55672bc8225c",
    "git/CHANGELOG.md": "eb242175379339814c7a91a1881f32f311970c549cfb01b468d99af7c04e67de",
    "git/commitlint.config.js": "9c46dd6e2258b8783f57255cbcdd09fd13c0283069b281568806ba147df85340",
    "rust/rust-toolchain.toml": "a6a0bbd29ffaa8182dc22d1d9149709f1091e47df40ed96eb8a78a711c66a4ce",
    "rust/src/lib.rs": "7ee751810675dd67935f48c90a0ff696035fd0b47d7520a00bc0772d3eff1813",
    "typescript/.oxfmtrc.json": "de9ec5a4f748493a84113f6f9881a3db585cc4e8a8bea2c83e3ba65c204e8fb3",
    "typescript/.oxlintrc.json": "af18217668580c6e3df7ede6481eb29df644a4f8929d5a9a15faec6a476a6d71",
    "typescript/scripts/oxlint-plugin-comment-gate.js": "9cbf8af3366f0e71f743c518c8ba31d5aed0144c7705ae76144a639673dd7484",
    "typescript/src/cli.ts": "3dd9148df21a5c186761c242b7f49ef8a3c4f6041535707ee5bc09879ceeeb85",
    "typescript/tests/index.test.ts": "4b91f6158817cf7dd1b57a41472772e961106bdf34430690e17386b53e0df80f",
}

# Re-pin only when the byte change is intended — the failure message prints the new digests.
RENDERED_SHA256: dict[str, str] = {
    "CONTRIBUTING.default (project_name=demo)": "dcf7372501cad68db54342a8e8f2e0e2dc2911485f38dc2bf2e09e51a14c91ea",
    "CONTRIBUTING.python (project_name=demo)": "587df36cc0f73f107fdbc34b9bbb634b0cdf121656517798a17685a30bea178a",
    "CONTRIBUTING.typescript (project_name=demo)": "31dafc569c65f1dbca8137fce61b5ef168c83226cd271a6d74e2c73d0aa0417f",
    "ci/release.yml[node+coverage]": "30d4d7d031c9e48380bf66c62f60f506f393edc25caae96f2c6bc080f1883240",
    "ci/release.yml[node]": "56f1151ed60761d7e8364e151ddced3757b487c643a66b01e9e71a920d466296",
    "ci/release.yml[python+coverage]": "122b942be6922bf559c992435a9a52f2ab3f1dea299d66175717967a6b49f8ab",
    "ci/release.yml[python]": "aebbf9b89021bf9a64c4bc5bbdb9605efce3bb08504dfb63a521002cb1e33189",
    "ci/release.yml[rust+coverage]": "263338d0df619d5fc45d91cb2a4425e26d4ce92b553e29231d4588a265d4eda5",
    "python/src/_pkg/__init__.py (project_name=demo)": "9907974c0023c1fb987d828ec2de408840a3cc8fd753b3573adb976ae4a83cd1",
    "python/tests/test_smoke.py (module=demo)": "f5de38a8b16e5e306a3a8f2306055eee929119537933e4c9c6a3c24a44991466",
    "ci/release.yml[rust]": "2a58947cf96f500ec8f8e26c4bc6562e1654a0f05fefd741bf1ddabfe37b9028",
    "rust/Cargo.toml (project_name=demo-cli)": "506eabda9eef1b9f5bf528259059d3d866aa0dc3bd538d83174602f9e9f0d047",
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


# --- action pins ----------------------------------------------------------------

# Which SHA_TABLE entry each action must use. The table is the single source, but the raw git
# template and this repo's own workflows are hand-maintained, so nothing else stops them from
# drifting behind it — and they did: four of six pins sat two majors back before this test.
ACTION_TO_TABLE_KEY = {
    "actions/checkout": "checkout",
    "actions/setup-node": "setup-node",
    "actions/setup-python": "setup-python",
    "actions/github-script": "github-script",
    "pnpm/action-setup": "pnpm-setup",
    "Swatinem/rust-cache": "rust-cache",
    "astral-sh/setup-uv": "setup-uv",
    "taiki-e/install-action": "install-action",
}

REPO_ROOT = Path(__file__).resolve().parents[2]


def _pinned_actions(text: str) -> dict[str, str]:
    """`uses: owner/action@<40-hex>` pairs; a floating ref (`@stable`) is not a pin."""
    return dict(re.findall(r"uses:\s*(\S+?)@([0-9a-f]{40})\b", text))


def test_action_pins_match_the_sha_table():
    sources = [TEMPLATES / "git/.github/workflows/changelog-check.yml"]
    sources += sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    seen: set[str] = set()
    for path in sources:
        for action, sha in _pinned_actions(path.read_text(encoding="utf-8")).items():
            key = ACTION_TO_TABLE_KEY.get(action)
            assert key, f"{path.name}: {action} is pinned but has no SHA_TABLE entry"
            assert sha == scaffold.SHA_TABLE[key], (
                f"{path.name}: {action} pinned to {sha}, yet SHA_TABLE[{key!r}] is "
                f"{scaffold.SHA_TABLE[key]} — bump the table, never the caller"
            )
            seen.add(key)
    assert seen, "expected at least one SHA-pinned action"
    assert {"checkout", "setup-uv"} <= seen, f"workflows stopped pinning: {sorted(seen)}"


# --- hygiene: what the scaffold ships names no other project ---------------------------

# The `git` flavor's issue and PR templates were first lifted out of a sibling repo, and every
# generated project inherits their issue links and internals verbatim — a URL into someone
# else's tracker is worse than no link. The check spans the templates *and* the docs that
# describe them, because the next copy-paste is what reintroduces the leak. `dsh-better-edit`
# is the sibling; `harness-zkx` is this repo, so its slug is legitimate wherever it appears.
FOREIGN_PROJECT_SLUGS = ("dsh-better-edit",)


def test_shipped_bytes_name_no_foreign_project():
    shipped = [TEMPLATES / rel for rel in _template_files()]
    shipped += sorted(SKILL_DIR.rglob("*.md"))

    offenders = sorted(
        f"{path.relative_to(SKILL_DIR).as_posix()}: {slug}"
        for path in shipped
        for slug in FOREIGN_PROJECT_SLUGS
        if slug in path.read_text(encoding="utf-8")
    )
    assert not offenders, (
        "what the scaffold ships names the author's own project, and every generated repo "
        "inherits it verbatim:\n" + "\n".join(offenders)
    )
