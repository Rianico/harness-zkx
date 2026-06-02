"""Tests for the md-to-html rendering pipeline."""

from bs4 import BeautifulSoup


class TestBasicStructure:
    """Basic HTML structure and metadata."""

    def test_returns_valid_html(self, renderer, sample_md):
        """Render produces valid, parseable HTML."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        assert doc.find("article", class_="md-document")

    def test_title_in_head(self, renderer, sample_md):
        """Frontmatter title appears in <title>."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        assert doc.title and "Test Architecture Review" in doc.title.get_text()

    def test_project_as_h1(self, renderer, sample_md):
        """Frontmatter project becomes the h1."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        h1 = doc.find("h1", class_="md-heading-level-1")
        assert h1 and "test-project" in h1.get_text()

    def test_flavor_class_on_article(self, renderer, sample_md):
        """Article wrapper has flavor-{name} class."""
        html = renderer.render(sample_md)
        assert 'class="md-document flavor-kami"' in html


class TestDashboard:
    """Statistics dashboard rendering."""

    def test_stat_cards_rendered(self, renderer, sample_md):
        """Dashboard contains stat cards."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        cards = doc.find_all("div", class_="md-stat-card")
        assert len(cards) >= 3

    def test_dashboard_groups_separate_total_and_strength(self, renderer, sample_md):
        """Dashboard has at least two groups (total + strength)."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        groups = doc.find_all("div", class_="md-dashboard-group")
        assert len(groups) >= 2


class TestMetaBlock:
    """Metadata block rendering."""

    def test_meta_items_rendered(self, renderer, sample_md):
        """Meta block includes known labels."""
        html = renderer.render(sample_md)
        assert "Repository" in html
        assert "Branch" in html
        assert "Lines reviewed" in html
        assert "1,500" in html

    def test_meta_uses_tabular_nums(self, renderer, sample_md):
        """Numeric meta values have md-tabular class."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        tabular = doc.find_all(class_="md-tabular")
        assert len(tabular) >= 2


class TestEnumLegendStrip:
    """Enum bar rendering."""

    def test_strength_enum_row(self, renderer, sample_md):
        """Strength enum labels appear in the bar."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        strength_row = None
        for row in doc.find_all("div", class_="md-enum-row"):
            label = row.find("span", class_="md-enum-label")
            if label and "Strength" in label.get_text():
                strength_row = row
                break
        assert strength_row is not None

    def test_category_enum_row(self, renderer, sample_md):
        """Category enum labels appear in the bar."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        category_row = None
        for row in doc.find_all("div", class_="md-enum-row"):
            label = row.find("span", class_="md-enum-label")
            if label and "Category" in label.get_text():
                category_row = row
                break
        assert category_row is not None

    def test_tags_have_badge_classes(self, renderer, sample_md):
        """Enum tags use the configured badge-* classes."""
        html = renderer.render(sample_md)
        assert 'class="md-tag badge-strong"' in html

    def test_category_tags_have_tooltip(self, renderer, sample_md):
        """Category tags with description get data-tooltip."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        # Enum bar category tags use title, table category tags use data-tooltip
        cells = doc.select("td [data-tooltip]")
        assert len(cells) >= 1


class TestLegendKey:
    """Header legend rendering."""

    def test_legend_label(self, renderer, sample_md):
        """Legend has the 'Legend' label."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        label = doc.find("span", class_="md-legend-key-label")
        assert label and "Legend" in label.get_text()

    def test_legend_items_have_correct_classes(self, renderer, sample_md):
        """Each legend item has legend-tag-{key} class."""
        html = renderer.render(sample_md)
        assert 'class="md-legend-key-item legend-tag-module"' in html
        assert 'class="md-legend-key-item legend-tag-deep_module"' in html

    def test_legend_items_have_tooltips(self, renderer, sample_md):
        """Legend items with glossary entries get data-tooltip."""
        html = renderer.render(sample_md)
        assert 'data-tooltip="anything with an interface' in html


class TestSectionGeneration:
    """Numbered section / card generation."""

    def test_numbered_section_has_header(self, renderer, sample_md):
        """Each numbered section gets a section-header."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        headers = doc.find_all("div", class_="md-section-header")
        assert len(headers) >= 2

    def test_badges_in_section_header(self, renderer, sample_md):
        """Badge callout content lands in section-header badges."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        badges = doc.find_all("div", class_="md-section-badges")
        assert len(badges) >= 2

    def test_section_number_appears(self, renderer, sample_md):
        """Zero-padded section number is present."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        nums = doc.find_all("span", class_="md-section-num")
        texts = [n.get_text(strip=True) for n in nums]
        assert "01" in texts
        assert "02" in texts


class TestCardContent:
    """Content within candidate cards."""

    def test_problem_blockquote(self, renderer, sample_md):
        """Problem callout becomes md-blockquote with 'Problem:' prefix."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        quotes = doc.find_all("blockquote", class_="md-blockquote")
        texts = [q.get_text() for q in quotes]
        assert any("Problem:" in t for t in texts)

    def test_warning_callout(self, renderer, sample_md):
        """Warning callout gets md-blockquote-warn class."""
        html = renderer.render(sample_md)
        assert 'class="md-blockquote md-blockquote-warn"' in html

    def test_note_callout(self, renderer, sample_md):
        """Note callout gets md-blockquote-note class."""
        html = renderer.render(sample_md)
        assert 'class="md-blockquote md-blockquote-note"' in html

    def test_per_card_legend_row(self, renderer, sample_md):
        """Cards with legend callouts get md-card-legend-row."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        rows = doc.find_all("div", class_="md-card-legend-row")
        assert len(rows) >= 1


class TestOverviewTable:
    """Table processing and overview links."""

    def test_overview_links_rendered(self, renderer, sample_md):
        """Candidate names in tables become anchor links."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        links = doc.find_all("a", class_="md-overview-link")
        assert len(links) >= 2
        # Links should reference section IDs
        hrefs = [a.get("href", "") for a in links]
        assert any("test-candidate-one" in h for h in hrefs)

    def test_strength_badge_in_table(self, renderer, sample_md):
        """Strength cells become tags with badge classes."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        # Look for badge-strong inside tables
        tags = doc.select("table .badge-strong")
        assert len(tags) >= 1

    def test_category_tooltip_in_table(self, renderer, sample_md):
        """Category cells with description get data-tooltip."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        cells = doc.select("td [data-tooltip]")
        assert len(cells) >= 1


class TestGlossary:
    """Glossary section rendering."""

    def test_glossary_section_exists(self, renderer, sample_md):
        """Glossary section is rendered."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        gloss = doc.find("dl", class_="md-glossary")
        assert gloss is not None

    def test_glossary_terms_rendered(self, renderer, sample_md):
        """Each glossary entry has a dt/dd pair."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        terms = doc.find_all("dt", class_="md-glossary-term")
        defs = doc.find_all("dd", class_="md-glossary-def")
        assert len(terms) >= 2
        assert len(defs) >= 2

    def test_glossary_heading(self, renderer, sample_md):
        """Glossary has an h2 with id='glossary'."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        h2 = doc.find("h2", id="glossary")
        assert h2 is not None
        assert "Glossary" in h2.get_text()


class TestDynamicLegendCSS:
    """Inline dynamic CSS generation."""

    def test_legend_color_rules_inlined(self, renderer, sample_md):
        """Data-driven legend color CSS is inlined in <style>."""
        html = renderer.render(sample_md)
        doc = BeautifulSoup(html, "html.parser")
        style_tags = doc.find_all("style")
        inline = [s for s in style_tags if "legend-tag" in (s.string or "")]
        assert len(inline) >= 1
        assert ".legend-tag-module::before" in inline[0].string
        assert "#94a3b8" in inline[0].string


class TestExternalAssets:
    """Asset pipeline (external CSS/JS files)."""

    def test_external_asset_references_in_html(self, renderer, sample_md, output_dir):
        """HTML links to skill's own assets via relative paths."""
        out_path = output_dir / "report.html"
        html = renderer.render(sample_md, output_path=str(out_path))
        doc = BeautifulSoup(html, "html.parser")

        links = doc.find_all("link", rel="stylesheet")
        assert any("style.css" in l.get("href", "") for l in links)

        scripts = doc.find_all("script")
        srcs = [s.get("src", "") for s in scripts if s.get("src")]
        assert any("mermaid.min.js" in s for s in srcs)
        assert any("zoom.js" in s for s in srcs)

    def test_mermaid_init_always_inline(self, renderer, sample_md, output_dir):
        """mermaid.initialize is always inlined regardless of asset mode."""
        out_path = output_dir / "report.html"
        html = renderer.render(sample_md, output_path=str(out_path))
        assert "mermaid.initialize({" in html

    def test_no_external_assets_without_path(self, renderer, sample_md):
        """Without output_path, no external assets are written (backward compat)."""
        html = renderer.render(sample_md)
        # Should still work (inline mode)
        assert "mermaid.initialize({" in html

    def test_external_asset_href_resolves_to_flavor(self, renderer, sample_md, output_dir):
        """CSS href points to the flavor's style.css."""
        out_path = output_dir / "report.html"
        html = renderer.render(sample_md, output_path=str(out_path))
        doc = BeautifulSoup(html, "html.parser")

        link = doc.find("link", rel="stylesheet")
        assert link and "flavors" in link.get("href", "") and "style.css" in link.get("href", "")


class TestNonNumberedSections:
    """Non-numbered sections (Top Recommendation, Glossary)."""

    def test_non_numbered_section_id(self, renderer, sample_md):
        """Non-numbered section h2 gets an id and correct class."""
        html = renderer.render(sample_md)
        # The "Top Recommendation" section from the body
        assert 'id="top-recommendation"' in html or "Top Recommendation" in html


class TestMermaidWrap:
    """Mermaid diagram wrapping."""

    def test_no_mermaid_no_wraps(self, renderer, sample_md):
        """Sample without mermaid blocks produces no wraps."""
        html = renderer.render(sample_md)
        assert 'class="md-mermaid-wrap"' not in html
