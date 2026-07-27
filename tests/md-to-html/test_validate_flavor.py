"""Tests for the flavor validation script."""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = (
    Path(__file__).parent.parent.parent / "skills" / "md-to-html" / "scripts"
).resolve()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from validate_flavor import check_flavor, parse_required_classes

CONTRACT_PATH = (
    Path(__file__).parent.parent.parent
    / "skills"
    / "md-to-html"
    / "references"
    / "flavors"
    / "RENDERING-CONTRACT.md"
)


class TestParseRequiredClasses:
    """Manifest parsing from RENDERING-CONTRACT.md."""

    def test_parses_all_items(self):
        """Manifest contains expected number of items."""
        items = parse_required_classes(CONTRACT_PATH)
        assert len(items) > 100  # known floor

    def test_includes_typography_classes(self):
        """Typography classes are in the manifest."""
        items = parse_required_classes(CONTRACT_PATH)
        assert ".md-heading-level-1" in items
        assert ".md-paragraph" in items

    def test_includes_design_tokens(self):
        """CSS custom properties are in the manifest."""
        items = parse_required_classes(CONTRACT_PATH)
        assert "--fg" in items
        assert "--surface" in items

    def test_includes_attribute_selectors(self):
        """Attribute/pseudo selectors are in the manifest."""
        items = parse_required_classes(CONTRACT_PATH)
        assert "[data-tooltip]" in items
        assert "[data-tooltip]::after" in items


class TestCheckFlavor:
    """Flavor CSS validation."""

    @pytest.fixture
    def kami_dir(self):
        return str(
            Path(__file__).parent.parent.parent / "skills" / "md-to-html" / "references" / "flavors" / "kami"
        )

    def test_kami_passes_all_checks(self, kami_dir):
        """Kami flavor should pass all 110 checks."""
        required = parse_required_classes(CONTRACT_PATH)
        missing, _ = check_flavor(kami_dir, required)
        assert missing == [], f"Kami flavor missing: {missing}"

    def test_finds_missing_class(self, tmp_path):
        """Validator reports classes missing from style.css."""
        css = tmp_path / "style.css"
        css.write_text(".md-paragraph { color: red; }")
        required = [".md-paragraph", ".md-nonexistent"]
        missing, _ = check_flavor(str(tmp_path), required)
        assert ".md-nonexistent" in missing
        assert ".md-paragraph" not in missing

    def test_finds_missing_token(self, tmp_path):
        """Validator reports CSS custom properties missing from :root."""
        css = tmp_path / "style.css"
        css.write_text(
            ":root { --fg: black; }\n.md-paragraph { color: var(--fg); }"
        )
        required = ["--fg", "--nonexistent"]
        missing, _ = check_flavor(str(tmp_path), required)
        assert "--nonexistent" in missing
        assert "--fg" not in missing

    def test_handles_empty_css(self, tmp_path):
        """Empty CSS should report everything as missing."""
        css = tmp_path / "style.css"
        css.write_text("")
        required = parse_required_classes(CONTRACT_PATH)
        missing, _ = check_flavor(str(tmp_path), required)
        assert len(missing) == len(required)
