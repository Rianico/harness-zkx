"""Regression checks for the md-to-html Mermaid interaction asset."""

from pathlib import Path


ZOOM_JS = (
    Path(__file__).parent.parent.parent
    / "skills"
    / "md-to-html"
    / "assets"
    / "zoom.js"
)


def test_zoom_asset_supports_cursor_zoom_and_drag_pan():
    script = ZOOM_JS.read_text()

    assert "addEventListener('wheel'" in script
    assert "getBoundingClientRect()" in script
    assert "zoomAtPoint" in script
    assert "addEventListener('pointerdown'" in script
    assert "addEventListener('pointermove'" in script
    assert "translate(' + translateX" in script
    assert "scale(' + scale" in script


def test_zoom_asset_does_not_rerender_mermaid():
    script = ZOOM_JS.read_text()

    assert "mermaid.init" not in script
    assert "mermaid.initialize" not in script
    assert "mermaid.run" not in script
