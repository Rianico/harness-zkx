"""Metadata-Driven Markdown to HTML Renderer.

Refactored into 3 composable stages (FrontmatterParser, BodyRenderer,
AssetBundler) with a thin KamiRenderer orchestrator maintaining the
original public API.
"""

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

import markdown
import yaml
from bs4 import BeautifulSoup

# ─── Module-Level Helpers ─────────────────────────────────────────────


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    return re.sub(r"[\W_]+", "-", text.lower()).strip("-")


# ─── Stage 1: FrontmatterParser ───────────────────────────────────────


@dataclass(frozen=True)
class ParsedDocument:
    """Result of parsing frontmatter from raw markdown.

    Holds only the extracted frontmatter dict and the remaining body.
    Downstream stages (BodyRenderer, AssetBundler) extract additional
    fields (strength_map, category_map, glossary) from *frontmatter*.
    """

    frontmatter: dict
    body: str


class FrontmatterParser:
    """Parse YAML frontmatter from markdown content and normalize the body."""

    def parse(self, md_content: str) -> ParsedDocument:
        """Split frontmatter from body and apply input normalization."""
        frontmatter: dict = {}
        if md_content.startswith("---"):
            parts = re.split(r"^---$", md_content, maxsplit=2, flags=re.MULTILINE)
            if len(parts) >= 3:
                try:
                    parsed = yaml.safe_load(parts[1])
                    if isinstance(parsed, dict):
                        frontmatter = parsed
                    md_content = parts[2]
                except yaml.YAMLError:
                    pass

        # Pre-process MD to fix list rendering bugs
        md_content = re.sub(r"([^\n])\n\s*([-*+]\s+)", r"\1\n\n\2", md_content)
        md_content = re.sub(r"([^\n])\n\s*(\d+\.\s+)", r"\1\n\n\2", md_content)
        md_content = re.sub(r"(\*\*Wins:\*\*)\n-", r"\1\n\n-", md_content)
        md_content = re.sub(r"(\*\*Details:\*\*)\n-", r"\1\n\n-", md_content)

        return ParsedDocument(frontmatter=frontmatter, body=md_content)


# ─── Stage 2: BodyRenderer ────────────────────────────────────────────


class BodyRenderer:
    """Convert parsed markdown body into a structured BeautifulSoup tree.

    Responsible for: markdown -> HTML conversion, section structure, callout
    processing, mermaid embedding, CSS class mapping, and table enrichment.
    """

    _DEFAULT_MAPPINGS: dict[str, str] = {
        "h1": "md-heading-level-1",
        "h2": "md-heading-level-2",
        "h3": "md-heading-level-3",
        "h4": "md-heading-level-4",
        "p": "md-paragraph",
        "ul": "md-list",
        "ol": "md-list-ordered",
        "li": "md-list-item",
        "blockquote": "md-blockquote",
        "table": "md-table",
        "hr": "md-hr",
        "code": "md-code",
    }

    def __init__(self, mappings: dict[str, str] | None = None) -> None:
        """*mappings* maps HTML tag names to CSS classes.

        When *mappings* is None the standard default set is used.
        """
        self.mappings: dict[str, str] = (
            mappings if mappings is not None else dict(self._DEFAULT_MAPPINGS)
        )

    def render(self, doc: ParsedDocument) -> BeautifulSoup:
        """Convert *doc* body into a structured BeautifulSoup element tree."""
        frontmatter = doc.frontmatter
        md_content = doc.body

        strength_map: dict = frontmatter.get("strength_enum", {})
        category_map: dict = frontmatter.get("category_enum", {})
        glossary: dict = frontmatter.get("glossary", frontmatter.get("vocabulary", {}))
        title: str = frontmatter.get("title", "").strip()

        # MD -> HTML
        html_output = markdown.markdown(md_content, extensions=["extra", "toc", "admonition"])
        soup = BeautifulSoup(html_output, "html.parser")
        new_soup = BeautifulSoup("", "html.parser")

        # Main element loop
        all_elements = list(soup.contents)
        current_section = None
        current_card = None

        for _i, el in enumerate(all_elements):
            if isinstance(el, str) and not el.strip():
                continue
            if isinstance(el, str):
                (current_card or new_soup).append(el)
                continue

            if el.name == "h1" and el.get_text().strip() == title:
                continue

            text = el.get_text().strip()

            # H2 -> Section Header
            if el.name == "h2":
                m = re.match(r"^(\d+)\.\s+(.*)", text)
                if m:
                    num, t_text = m.groups()
                    current_section = new_soup.new_tag(
                        "section",
                        attrs={"class": "md-section md-section-level-1", "id": slugify(t_text)},
                    )
                    hdr = new_soup.new_tag("div", attrs={"class": "md-section-header"})
                    span = new_soup.new_tag("span", attrs={"class": "md-section-num"})
                    span.string = num.zfill(2)
                    hdr.append(span)
                    h2 = new_soup.new_tag("h2", attrs={"class": "md-heading-level-2"})
                    h2.string = t_text
                    hdr.append(h2)
                    badges_div = new_soup.new_tag("div", attrs={"class": "md-section-badges"})
                    hdr.append(badges_div)
                    current_section.append(hdr)
                    new_soup.append(current_section)
                    current_card = new_soup.new_tag("div", attrs={"class": "md-card"})
                    current_section.append(current_card)
                    continue

                # Non-numbered H2 — wrap in section + card for consistent styling
                current_section = new_soup.new_tag("section", attrs={"class": "md-section"})
                current_section.append(el)
                new_soup.append(current_section)
                current_card = new_soup.new_tag("div", attrs={"class": "md-card"})
                current_section.append(current_card)
                continue

            if el.name == "hr":
                current_section = None
                current_card = None
                new_soup.append(el)
                continue

            if current_section:
                # 3a. Callout Support
                if el.name == "blockquote" and "[!" in text:
                    current_card = self._process_callouts(
                        new_soup,
                        el,
                        current_section,
                        current_card,
                        strength_map,
                        category_map,
                        glossary,
                    )
                    continue

                # Problem inline detection
                if "Problem:" in text:
                    if not current_card:
                        current_card = new_soup.new_tag("div", attrs={"class": "md-card"})
                        current_section.append(current_card)
                    bq = new_soup.new_tag("blockquote", attrs={"class": "md-blockquote"})
                    p = new_soup.new_tag("p", attrs={"class": "md-paragraph"})
                    p.string = text.strip()
                    bq.append(p)
                    current_card.append(bq)
                    continue

                # Mermaid
                if (
                    el.name == "pre"
                    and el.find("code")
                    and "language-mermaid" in el.find("code").get("class", [])
                ):
                    self._process_mermaid(new_soup, el, current_section, current_card)
                    continue

                (current_card or current_section).append(el)
            else:
                new_soup.append(el)

        # 4. Standard Classes & Table Processing
        self._apply_standard_classes(new_soup)
        self._color_enums_and_link_tables(new_soup, strength_map, category_map)

        return new_soup

    # ── Private helpers ───────────────────────────────────────────────

    def _process_callouts(
        self,
        new_soup: BeautifulSoup,
        el,
        current_section,
        current_card,
        strength_map: dict,
        category_map: dict,
        glossary: dict,
    ):
        """Handle [!badge], [!legend], [!files], [!problem], [!warning], [!note].

        Returns the (possibly updated) *current_card* so the caller can
        pick up any card created during callout processing.
        """
        full_text = el.get_text(separator="\n")
        markers = re.findall(r"\[!(badge|files|legend|problem|warning|note)\]", full_text)
        segments = re.split(r"\[!(?:badge|files|legend|problem|warning|note)\]", full_text)

        for idx, kind in enumerate(markers):
            content = segments[idx + 1].strip()
            if kind == "badge":
                b_container = current_section.find("div", class_="md-section-badges")
                if b_container:
                    parts = [p.strip().replace("**", "") for p in content.split("·")]
                    for p_val in parts:
                        if not p_val:
                            continue
                        cls = "md-tag-info"
                        if p_val in strength_map:
                            cls = strength_map[p_val].get("css", "md-tag-success")
                        elif p_val in category_map:
                            cls = category_map[p_val].get("css", "md-tag-muted")
                        else:
                            for _, v in category_map.items():
                                if v.get("label") == p_val:
                                    cls = v.get("css", "md-tag-muted")
                                    break
                        badge = new_soup.new_tag("span", attrs={"class": f"md-tag {cls}"})
                        badge.string = p_val
                        b_container.append(badge)

            elif kind == "legend":
                if not current_card:
                    current_card = new_soup.new_tag("div", attrs={"class": "md-card"})
                    current_section.append(current_card)
                lr = current_card.find("div", class_="md-card-legend-row")
                if not lr:
                    lr = new_soup.new_tag("div", attrs={"class": "md-card-legend-row"})
                    current_card.append(lr)
                tags_inner = [t.strip() for t in content.split("·")]
                for t in tags_inner:
                    if not t:
                        continue
                    t_key = t.replace(" ", "_").lower()
                    item = new_soup.new_tag(
                        "span",
                        attrs={"class": f"md-legend-key-item legend-tag-{t_key}"},
                    )
                    item.string = t.replace("_", " ")
                    if glossary.get(t_key):
                        item["data-tooltip"] = glossary[t_key]
                    lr.append(item)

            elif kind == "files":
                if not current_card:
                    current_card = new_soup.new_tag("div", attrs={"class": "md-card"})
                    current_section.append(current_card)
                files_div = new_soup.new_tag("div", attrs={"class": "md-card-files"})
                files = []
                for line in content.split("\n"):
                    clean = line.strip().lstrip("-").strip(" `")
                    if clean and not clean.startswith("[!"):
                        files.append(clean)
                if files:
                    files_div.string = " · ".join(files)
                    current_card.append(files_div)

            elif kind == "problem":
                if not current_card:
                    current_card = new_soup.new_tag("div", attrs={"class": "md-card"})
                    current_section.append(current_card)
                bq = new_soup.new_tag("blockquote", attrs={"class": "md-blockquote"})
                p = new_soup.new_tag("p", attrs={"class": "md-paragraph"})
                p.string = f"Problem: {content}"
                bq.append(p)
                current_card.append(bq)

            elif kind == "warning":
                if not current_card:
                    current_card = new_soup.new_tag("div", attrs={"class": "md-card"})
                    current_section.append(current_card)
                bq = new_soup.new_tag(
                    "blockquote", attrs={"class": "md-blockquote md-blockquote-warn"}
                )
                p = new_soup.new_tag("p", attrs={"class": "md-paragraph"})
                p.string = content
                bq.append(p)
                current_card.append(bq)

            elif kind == "note":
                if not current_card:
                    current_card = new_soup.new_tag("div", attrs={"class": "md-card"})
                    current_section.append(current_card)
                bq = new_soup.new_tag(
                    "blockquote", attrs={"class": "md-blockquote md-blockquote-note"}
                )
                p = new_soup.new_tag("p", attrs={"class": "md-paragraph"})
                p.string = content
                bq.append(p)
                current_card.append(bq)

        return current_card

    def _process_mermaid(self, new_soup: BeautifulSoup, el, current_section, current_card) -> None:
        """Embed a mermaid diagram with zoom controls."""
        dw = new_soup.new_tag("div", attrs={"class": "md-mermaid-wrap"})
        mp = new_soup.new_tag("pre", attrs={"class": "mermaid"})
        mp.string = el.find("code").string
        vp = new_soup.new_tag("div", attrs={"class": "md-mermaid-viewport"})
        vp.append(mp)
        dw.append(vp)
        zoom = new_soup.new_tag("div", attrs={"class": "md-mermaid-zoom"})
        for btn_text, btn_class in [("+", "zoom-in"), ("−", "zoom-out"), ("⛶", "zoom-fullscreen")]:
            btn = new_soup.new_tag("button", attrs={"class": btn_class})
            btn.string = btn_text
            zoom.append(btn)
        dw.append(zoom)
        (current_card or current_section).append(dw)

    def _apply_standard_classes(self, new_soup: BeautifulSoup) -> None:
        """Apply standard CSS classes to all HTML elements."""
        for tag, cls in self.mappings.items():
            for el in new_soup.find_all(tag):
                if tag.startswith("h") and el.parent and el.parent.name in ["header", "div"]:
                    continue
                if cls not in el.get("class", []):
                    el["class"] = el.get("class", []) + [cls]
        for td in new_soup.find_all("td"):
            if re.match(r"^[\d,\.%\s]+$", td.get_text().strip()):
                td["class"] = td.get("class", []) + ["md-tabular"]
        for c in new_soup.find_all("code"):
            if not c.parent or c.parent.name != "pre":
                c["class"] = c.get("class", []) + ["md-code"]

    def _color_enums_and_link_tables(
        self, new_soup: BeautifulSoup, strength_map: dict, category_map: dict
    ) -> None:
        """Color-code enum values in tables and link candidate names."""
        if not strength_map and not category_map:
            return
        for table in new_soup.find_all("table"):
            thead = table.find("thead")
            if not thead:
                continue
            headers = [th.get_text().strip() for th in thead.find_all("th")]
            strength_idx = next((i for i, h in enumerate(headers) if h.lower() == "strength"), None)
            category_idx = next((i for i, h in enumerate(headers) if h.lower() == "category"), None)
            candidate_idx = next(
                (i for i, h in enumerate(headers) if h.lower() == "candidate"), None
            )
            if strength_idx is None and category_idx is None and candidate_idx is None:
                continue
            for tr in table.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if candidate_idx is not None and candidate_idx < len(tds):
                    td = tds[candidate_idx]
                    name = td.get_text().strip()
                    if name:
                        td.clear()
                        a = new_soup.new_tag(
                            "a", attrs={"href": f"#{slugify(name)}", "class": "md-overview-link"}
                        )
                        a.string = name
                        td.append(a)
                if strength_idx is not None and strength_idx < len(tds):
                    td = tds[strength_idx]
                    text = td.get_text().strip()
                    if text in strength_map:
                        td.clear()
                        span = new_soup.new_tag(
                            "span", attrs={"class": f"md-tag {strength_map[text]['css']}"}
                        )
                        span.string = text
                        td.append(span)
                if category_idx is not None and category_idx < len(tds):
                    td = tds[category_idx]
                    text = td.get_text().strip()
                    css_cls = ""
                    desc = ""
                    if text in category_map:
                        css_cls = category_map[text].get("css", "md-tag-muted")
                        desc = category_map[text].get("description", "")
                    else:
                        for _ek, ev in category_map.items():
                            if ev.get("label") == text:
                                css_cls = ev.get("css", "md-tag-muted")
                                desc = ev.get("description", "")
                                break
                    if css_cls:
                        td.clear()
                        span = new_soup.new_tag("span", attrs={"class": f"md-tag {css_cls}"})
                        span.string = text
                        if desc:
                            span["data-tooltip"] = desc
                        td.append(span)


# ─── Stage 3: AssetBundler ────────────────────────────────────────────


class AssetBundler:
    """Bundle a parsed soup tree into a complete HTML document with assets."""

    def __init__(self, flavor: str, flavors_dir: Path, asset_dir: Path) -> None:
        self.flavor = flavor
        self.flavors_dir = flavors_dir
        self.asset_dir = asset_dir

    def get_dynamic_legend_css(self, legend_data: dict | None = None) -> str:
        """Return only the data-driven legend color CSS that must be inline."""
        css = ""
        if legend_data:
            for key, entry in legend_data.items():
                if "css" in entry:
                    cls_str = entry["css"]
                    color = None
                    if "border-slate-400" in cls_str:
                        color = "#94a3b8"
                    elif "border-red-500" in cls_str:
                        color = "#ef4444"
                    elif "border-emerald-600" in cls_str:
                        color = "#059669"
                    if color:
                        css += f".legend-tag-{key}::before {{ background: {color}; }}\n"
        return css

    def bundle(self, soup: BeautifulSoup, doc: ParsedDocument, output_path: str | None) -> str:
        """Wrap *soup* in a complete HTML document with head, assets, header, and glossary."""
        frontmatter = doc.frontmatter
        legend_data: dict = frontmatter.get("legend", {})
        glossary: dict = frontmatter.get("glossary", frontmatter.get("vocabulary", {}))
        strength_map: dict = frontmatter.get("strength_enum", {})
        category_map: dict = frontmatter.get("category_enum", {})

        result = BeautifulSoup(
            '<!doctype html><html lang="en"><head></head><body></body></html>',
            "html.parser",
        )
        head = result.head
        body_tag = result.body

        # ── Meta / Title ──
        head.append(result.new_tag("meta", charset="utf-8"))
        head.append(
            result.new_tag(
                "meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1"}
            )
        )
        title_tag = result.new_tag("title")
        title_tag.string = frontmatter.get("title", "Report")
        head.append(title_tag)

        # ── Dynamic legend colors (data-driven, always inline) ──
        legend_css = self.get_dynamic_legend_css(legend_data)
        if legend_css:
            style = result.new_tag("style")
            style.string = legend_css
            head.append(style)

        # ── External assets (skill's own files, referenced in-place) ──
        # When the output file sits inside the repo tree we write relative
        # <link>/<script> references so the browser resolves them from the
        # repo-local asset files.  If the output lives *outside* the repo
        # tree the relative path would traverse through the filesystem root
        # (e.g. ../../Users/…) which browsers block for file:// pages, so
        # we fall back to inlining the assets instead.
        if output_path:
            out_parent = Path(output_path).parent
            flavor_css = self.flavors_dir / self.flavor / "style.css"
            css_rel = os.path.relpath(str(flavor_css), str(out_parent))
            # Check that the relative path resolves to the actual CSS file.
            # If not (e.g. output is outside the repo tree, producing a
            # root-traversing path like ../../Users/…), fall back to inlining.
            if not (out_parent / css_rel).resolve().exists():
                if flavor_css.exists():
                    style = result.new_tag("style")
                    style.string = flavor_css.read_text()
                    head.append(style)
                for js_file in ["mermaid.min.js", "zoom.js"]:
                    js_path = self.asset_dir / js_file
                    if js_path.exists():
                        script = result.new_tag("script")
                        script.string = js_path.read_text()
                        head.append(script)
            else:
                # Inside repo tree — relative references work
                head.append(
                    result.new_tag(
                        "link",
                        attrs={
                            "rel": "stylesheet",
                            "href": css_rel,
                        },
                    )
                )
                for js_file in ["mermaid.min.js", "zoom.js"]:
                    js_path = self.asset_dir / js_file
                    if js_path.exists():
                        head.append(
                            result.new_tag(
                                "script",
                                attrs={
                                    "src": os.path.relpath(str(js_path), str(out_parent)),
                                },
                            )
                        )
        else:
            # Fallback: inline everything (backward compat)
            base_css_path = self.flavors_dir / self.flavor / "style.css"
            if base_css_path.exists():
                style = result.new_tag("style")
                style.string = base_css_path.read_text()
                head.append(style)
            mermaid_js_path = self.asset_dir / "mermaid.min.js"
            if mermaid_js_path.exists():
                script = result.new_tag("script")
                script.string = mermaid_js_path.read_text()
                head.append(script)

        # ── Mermaid init (tiny, always inline) ──
        head.append(
            result.new_tag(
                "script",
                string="mermaid.initialize({startOnLoad:true, theme:'base', securityLevel:'loose', flowchart:{useMaxWidth:true, htmlLabels:true}});",
            )
        )

        # ── Article wrapper ──
        art = result.new_tag("article", attrs={"class": f"md-document flavor-{self.flavor}"})
        body_tag.append(art)

        # ── Header ──
        header = self._build_header(
            result,
            frontmatter,
            strength_map,
            category_map,
            legend_data,
            glossary,
        )
        if header is not None:
            art.append(header)

        # ── Body content ──
        for e in list(soup.contents):
            art.append(e)

        # ── Glossary ──
        if glossary:
            g_section = result.new_tag("section", attrs={"class": "md-section"})
            g_hr = result.new_tag("hr", attrs={"class": "md-hr"})
            g_section.append(g_hr)
            g_h2 = result.new_tag("h2", attrs={"class": "md-heading-level-2", "id": "glossary"})
            g_h2.string = "Glossary"
            g_section.append(g_h2)
            g_card = result.new_tag("div", attrs={"class": "md-card"})
            dl = result.new_tag("dl", attrs={"class": "md-glossary"})
            for term, defn in glossary.items():
                dt = result.new_tag("dt", attrs={"class": "md-glossary-term"})
                dt.string = term.replace("_", " ").capitalize()
                dd = result.new_tag("dd", attrs={"class": "md-glossary-def"})
                dd.string = defn
                dl.append(dt)
                dl.append(dd)
            g_card.append(dl)
            g_section.append(g_card)
            art.append(g_section)

        return result.prettify()

    # ── Header helpers ────────────────────────────────────────────────

    def _make_stat_card(self, doc, label: str, value, extra_class: str = ""):
        """Build a single stat card element."""
        card = doc.new_tag("div", attrs={"class": f"md-stat-card {extra_class}".strip()})
        lbl = doc.new_tag("span", attrs={"class": "md-stat-label"})
        lbl.string = label
        card.append(lbl)
        if isinstance(value, (list, tuple)):
            value = len(value)
        val_tag = doc.new_tag(
            "span",
            attrs={"class": "md-stat-value" + (" md-tabular" if isinstance(value, int) else "")},
        )
        val_tag.string = f"{value:,}" if isinstance(value, int) else str(value)
        card.append(val_tag)
        return card

    def _build_header(
        self,
        doc,
        frontmatter: dict,
        strength_map: dict,
        category_map: dict,
        legend_data: dict,
        glossary: dict,
    ):
        """Build the <header> with title, stats dashboard, meta, enum strip, and legend key."""
        if not frontmatter:
            return None

        h = doc.new_tag("header", attrs={"class": "md-header"})

        # Eyebrow
        eb = doc.new_tag("span", attrs={"class": "md-eyebrow"})
        eb.string = frontmatter.get("title", "Architecture Review")
        h.append(eb)

        # H1
        h1 = doc.new_tag("h1", attrs={"class": "md-heading-level-1"})
        h1.string = frontmatter.get("project", "Report")
        h.append(h1)

        # Subtitle
        stats: dict = frontmatter.get("statistics", {})
        subtitle = doc.new_tag("p", attrs={"class": "md-subtitle"})
        subtitle.string = f"{stats.get('candidates', 0)} refactoring candidates ranked by leverage, locality, and risk"
        h.append(subtitle)

        # --- Statistics Dashboard ---
        if stats:
            dash = doc.new_tag("div", attrs={"class": "md-dashboard"})
            # Total group
            if "candidates" in stats:
                tg = doc.new_tag("div", attrs={"class": "md-dashboard-group"})
                tg.append(self._make_stat_card(doc, "Candidates", stats["candidates"]))
                dash.append(tg)
            # Strength group
            strength_keys = [
                ("strong", "Strong"),
                ("worth_exploring", "Worth exploring"),
                ("speculative", "Speculative"),
            ]
            sg = doc.new_tag("div", attrs={"class": "md-dashboard-group"})
            has_sg = False
            for sk, sl in strength_keys:
                if sk in stats:
                    has_sg = True
                    css_cls = strength_map.get(sl, {}).get("css", "")
                    sg.append(self._make_stat_card(doc, sl, stats[sk], css_cls))
            if has_sg:
                dash.append(sg)
            h.append(dash)

        # --- Meta Block ---
        mc = doc.new_tag("div", attrs={"class": "md-meta"})
        meta_defs = [
            ("repository", "Repository"),
            ("branch", "Branch"),
            ("reviewed", "Reviewed"),
            ("files_scanned", "Files scanned"),
            ("model", "Model"),
        ]
        for key, label in meta_defs:
            if key == "reviewed":
                val = frontmatter.get("reviewed", frontmatter.get("date"))
            else:
                val = frontmatter.get(key)
            if val:
                item = doc.new_tag("div", attrs={"class": "md-meta-item"})
                css_extra = ""
                if isinstance(val, dict) and "value" in val:
                    css_extra = val.get("css", "")
                    val = val["value"]
                lbl = doc.new_tag("span", attrs={"class": "md-meta-label"})
                lbl.string = label
                item.append(lbl)
                cls_val = "md-meta-value" + (" md-tabular" if isinstance(val, int) else "")
                if css_extra:
                    cls_val += f" {css_extra}"
                val_tag = doc.new_tag("span", attrs={"class": cls_val})
                if isinstance(val, int):
                    val_tag.string = f"{val:,}"
                else:
                    val_tag.string = str(val)
                item.append(val_tag)
                mc.append(item)
        # Stats-derived meta items
        if stats:
            if "total_lines_reviewed" in stats:
                item = doc.new_tag("div", attrs={"class": "md-meta-item"})
                lbl = doc.new_tag("span", attrs={"class": "md-meta-label"})
                lbl.string = "Lines reviewed"
                item.append(lbl)
                val_tag = doc.new_tag("span", attrs={"class": "md-meta-value md-tabular"})
                val_tag.string = f"{stats['total_lines_reviewed']:,}"
                item.append(val_tag)
                mc.append(item)
            if "files_involved" in stats:
                item = doc.new_tag("div", attrs={"class": "md-meta-item"})
                lbl = doc.new_tag("span", attrs={"class": "md-meta-label"})
                lbl.string = "Files involved"
                item.append(lbl)
                val_tag = doc.new_tag("span", attrs={"class": "md-meta-value md-tabular"})
                val_tag.string = f"{stats['files_involved']:,}"
                item.append(val_tag)
                mc.append(item)
        h.append(mc)

        # --- Enum Legend Strip ---
        if strength_map or category_map:
            enum_bar = doc.new_tag("div", attrs={"class": "md-enum-bar"})
            if strength_map:
                row = doc.new_tag("div", attrs={"class": "md-enum-row"})
                lbl = doc.new_tag("span", attrs={"class": "md-enum-label"})
                lbl.string = "Strength:"
                row.append(lbl)
                for ek, ev in strength_map.items():
                    tag = doc.new_tag(
                        "span", attrs={"class": f"md-tag {ev.get('css', 'md-tag-info')}"}
                    )
                    tag.string = ek
                    row.append(tag)
                enum_bar.append(row)
            if category_map:
                row = doc.new_tag("div", attrs={"class": "md-enum-row"})
                lbl = doc.new_tag("span", attrs={"class": "md-enum-label"})
                lbl.string = "Category:"
                row.append(lbl)
                for ek, ev in category_map.items():
                    tag = doc.new_tag(
                        "span", attrs={"class": f"md-tag {ev.get('css', 'md-tag-muted')}"}
                    )
                    tag.string = ev.get("label", ek)
                    if ev.get("description"):
                        tag["title"] = ev["description"]
                    row.append(tag)
                enum_bar.append(row)
            h.append(enum_bar)

        # --- Legend Key ---
        if legend_data:
            lk = doc.new_tag("div", attrs={"class": "md-legend-key"})
            lbl = doc.new_tag("span", attrs={"class": "md-legend-key-label"})
            lbl.string = "Legend"
            lk.append(lbl)
            for label, _ in legend_data.items():
                item = doc.new_tag(
                    "span", attrs={"class": f"md-legend-key-item legend-tag-{label}"}
                )
                item.string = label.replace("_", " ")
                if glossary.get(label):
                    item["data-tooltip"] = glossary[label]
                lk.append(item)
            h.append(lk)

        return h


# ─── Thin Orchestrator ────────────────────────────────────────────────


class KamiRenderer:
    """Thin orchestrator over the 3-stage rendering pipeline.

    Public API is unchanged: ``render(md_content, output_path=None)`` and
    ``get_dynamic_legend_css(legend_data=None)``.
    """

    def __init__(self, asset_dir: str | None = None, flavor: str = "kami") -> None:
        script_dir = Path(__file__).parent.parent.absolute()
        if asset_dir is None:
            self.asset_dir = script_dir / "assets"
        else:
            self.asset_dir = Path(asset_dir).absolute()

        self.flavors_dir = script_dir / "references" / "flavors"
        self.flavor = flavor

        self._parser = FrontmatterParser()
        self._body_renderer = BodyRenderer()
        self._asset_bundler = AssetBundler(flavor, self.flavors_dir, self.asset_dir)

    def get_dynamic_legend_css(self, legend_data: dict | None = None) -> str:
        """Delegate to AssetBundler."""
        return self._asset_bundler.get_dynamic_legend_css(legend_data)

    def render(self, md_content: str, output_path: str | None = None) -> str:
        """Full pipeline: parse frontmatter, render body, bundle assets."""
        doc = self._parser.parse(md_content)
        soup = self._body_renderer.render(doc)
        return self._asset_bundler.bundle(soup, doc, output_path)


# ─── CLI ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Metadata-Driven Markdown to HTML")
    parser.add_argument("source", help="Source Markdown file")
    parser.add_argument("-o", "--output", help="Output HTML file")
    parser.add_argument("-f", "--flavor", default="kami", help="Flavor (kami, minimal)")
    args = parser.parse_args()
    renderer = KamiRenderer(flavor=args.flavor)
    output_path = args.output or args.source.replace(".md", ".html")
    with open(args.source) as f:
        md_content = f.read()
    html = renderer.render(md_content, output_path=output_path)
    with open(output_path, "w") as f:
        f.write(html)
    print(f"Rendered: {output_path}")
