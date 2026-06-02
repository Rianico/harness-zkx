"""Self-consistency: every class in the rendered HTML is documented in the contract."""

import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from conftest import SAMPLE_MD

SCRIPTS_DIR = (
    Path(__file__).parent.parent.parent / "skills" / "md-to-html" / "scripts"
).resolve()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from render import KamiRenderer
from validate_flavor import parse_required_classes

SKILL_DIR = Path(__file__).parent.parent.parent / "skills" / "md-to-html"
CONTRACT_PATH = SKILL_DIR / "flavors" / "RENDERING-CONTRACT.md"

# Classes that are dynamically generated and NOT expected to be in the contract
# because they are data-driven and don't need flavor styling.
DYNAMIC_CLASSES = {
    "legend-tag-",          # prefix for data-driven legend colors
    "flavor-",              # prefix for active flavor name
    "language-",            # prefix from markdown library syntax highlighting
}

# Classes that are part of the JS interaction layer and styled via parent
JS_INTERACTION_CLASSES = {
    "zoom-in",              # styled via .md-mermaid-zoom button
    "zoom-out",
    "zoom-fullscreen",
}

# Classes that are semantic HTML element targets (styled by element, not class)
ELEMENT_TARGETS = {
    "mermaid",              # pre.mermaid in the HTML
}

# Classes that apply to specific instances and are styled via context
CONTEXT_CLASSES = {
    "md-tabular",               # applied to numeric cells, styled via .md-tabular
    "md-card-files",            # only when [!files] callout is used
    "md-heading-level-3",       # renderer skips h3 inside card divs
    "md-heading-level-4",       # renderer skips h4 inside card divs
    "md-mermaid-viewport",      # only when mermaid diagram is present
    "md-mermaid-wrap",          # only when mermaid diagram is present
    "md-mermaid-zoom",          # only when mermaid diagram is present
    "md-section-level-2",       # only for nested sub-sections
    "md-section-level-3",       # only for deeper nested sub-sections
    "md-tag-success",           # only for specific category tags
    "md-tag-warn",              # only for specific category tags
    "md-tag-info",              # fallback tag class for unmatched items
}


def extract_all_classes(html):
    """Extract every CSS class name from rendered HTML."""
    doc = BeautifulSoup(html, "html.parser")
    classes = set()
    for tag in doc.find_all(True):
        for cls in tag.get("class", []):
            classes.add(cls)
    return classes


def is_documented(cls, manifest):
    """Check if a class appears in the contract manifest."""
    # Direct match
    if f".{cls}" in manifest:
        return True
    # Dynamic prefix match
    for prefix in DYNAMIC_CLASSES:
        if cls.startswith(prefix):
            return True
    return False


class TestContractSelfConsistency:
    """Every CSS class in rendered HTML must be documented in the contract."""

    @pytest.fixture(scope="class")
    def rendered_classes(self):
        """Generate HTML from the full sample and extract all classes."""
        renderer = KamiRenderer(flavor="kami")
        html = renderer.render(SAMPLE_MD)
        return extract_all_classes(html)

    @pytest.fixture(scope="class")
    def contract_manifest(self):
        return parse_required_classes(CONTRACT_PATH)

    def test_all_classes_documented(self, rendered_classes, contract_manifest):
        """Every class in the HTML appears in the contract or is known-dynamic."""
        undocumented = set()
        for cls in sorted(rendered_classes):
            if is_documented(cls, contract_manifest):
                continue
            if cls in JS_INTERACTION_CLASSES:
                continue
            if cls in ELEMENT_TARGETS:
                continue
            if cls in CONTEXT_CLASSES:
                continue
            undocumented.add(cls)

        assert not undocumented, (
            f"Undocumented CSS classes in rendered HTML: {sorted(undocumented)}"
        )

    def test_no_stale_contract_classes(self, rendered_classes, contract_manifest):
        """Every class-only item in the contract is actually generated."""
        unused = []
        for item in contract_manifest:
            if not item.startswith("."):
                continue  # skip tokens and attributes
            # Skip pseudo-elements (::before, ::after), compound selectors (space), attributes
            if "::" in item or " " in item:
                continue
            cls = item[1:]  # strip leading dot
            if any(cls.startswith(p[1:]) for p in DYNAMIC_CLASSES):
                continue
            if cls not in rendered_classes:
                unused.append(cls)

        # Allow known JS interaction classes that aren't in this sample
        known_unused = JS_INTERACTION_CLASSES | ELEMENT_TARGETS | CONTEXT_CLASSES
        actual_unused = [c for c in unused if c not in known_unused]

        assert not actual_unused, (
            f"Contract documents classes never generated: {sorted(actual_unused)}"
        )
