"""Declared py-dep input surface: N1, N2, and out-of-contract pin.

N1: multiline array without a trailing comma accepts the append.
N2: quoted [project] header and quoted dependencies key are supported.
Pin: out-of-contract inputs refuse without mutating and name what was found.
"""

import importlib.util
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_py_dep_surface", SCRIPT)


def test_n1_multiline_without_trailing_comma_appends(tmp_path: Path):
    body = '[project]\nname = "demo"\nversion = "0.1.0"\ndependencies = [\n    "httpx>=0.27"\n]\n'
    _ = (tmp_path / "pyproject.toml").write_text(body, encoding="utf-8")
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "py-dep", "--req", "pydantic>=2"])
    assert rc == 0
    out = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert '"httpx>=0.27",' in out
    assert '"pydantic>=2",' in out
    import tomllib as _toml

    data = _toml.loads(out)
    assert "pydantic>=2" in data["project"]["dependencies"]


def test_n2_quoted_header_and_quoted_key_supported(tmp_path: Path, capsys):
    for body in (
        '["project"]\nname = "demo"\ndependencies = []\n',
        '[project]\nname = "demo"\n"dependencies" = []\n',
    ):
        p = tmp_path / "pyproject.toml"
        _ = p.write_text(body, encoding="utf-8")
        capsys.readouterr()
        rc = scaffold.ensure_main(["--cwd", str(tmp_path), "py-dep", "--req", "httpx>=0.27"])
        assert rc == 0
        out = p.read_text(encoding="utf-8")
        assert "httpx>=0.27" in out
        import tomllib as _toml

        assert "httpx>=0.27" in _toml.loads(out)["project"]["dependencies"]


def test_declaration_out_of_contract_refuses_naming_found(tmp_path: Path, capsys):
    body = '[project]\nname = "demo"\nversion = "0.1.0"\n'
    p = tmp_path / "pyproject.toml"
    _ = p.write_text(body, encoding="utf-8")
    before = p.read_bytes()
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "py-dep", "--req", "httpx>=0.27"])
    assert rc != 0
    assert p.read_bytes() == before
    err = capsys.readouterr().err
    assert "dependencies" in err
    assert "run --flavor python first" not in err
