import os
import re
import argparse
import markdown
import yaml
from bs4 import BeautifulSoup
from pathlib import Path

class KamiRenderer:
    def __init__(self, asset_dir=None, flavor="kami"):
        script_dir = Path(__file__).parent.parent.absolute()
        if asset_dir is None:
            self.asset_dir = script_dir / "assets"
        else:
            self.asset_dir = Path(asset_dir).absolute()
        
        self.flavors_dir = script_dir / "flavors"
        self.flavor = flavor
        
        self.mappings = {
            'h1': 'md-heading-level-1', 'h2': 'md-heading-level-2', 'h3': 'md-heading-level-3',
            'h4': 'md-heading-level-4', 'p': 'md-paragraph', 'ul': 'md-list',
            'ol': 'md-list-ordered', 'li': 'md-list-item', 'blockquote': 'md-blockquote',
            'table': 'md-table', 'hr': 'md-hr', 'code': 'md-code'
        }

    def slugify(self, text):
        return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

    def get_style_content(self, legend_data=None):
        """Loads and synthesizes CSS."""
        base_style_path = self.flavors_dir / "kami" / "style.css"
        base_css = base_style_path.read_text() if base_style_path.exists() else ""
        
        flavor_tokens_path = self.flavors_dir / self.flavor / "reference" / "tokens.css"
        if self.flavor != "kami" and flavor_tokens_path.exists():
            tokens = flavor_tokens_path.read_text()
            root_match = re.search(r':root\s*\{(.*?)\}', tokens, re.DOTALL)
            flavor_root = root_match.group(0) if root_match else ""
            base_css = re.sub(r':root\s*\{.*?\}', flavor_root, base_css, count=1, flags=re.DOTALL)
        
        helpers = """
/* ── global ui helpers ────────────────────────────────────────── */
.md-tag-success { background: #e4ecf5 !important; color: var(--success) !important; }
.md-tag-warn { background: #f0e8d0 !important; color: var(--warn) !important; }
.md-tag-muted { background: var(--surface-warm) !important; color: var(--meta) !important; }
.md-tag-info { background: var(--tag-bg-soft) !important; color: var(--accent) !important; }
.badge-strong { background: #e4ecf5 !important; color: var(--success) !important; }
.badge-worth { background: #f0e8d0 !important; color: var(--warn) !important; }
.badge-speculative { background: var(--surface-warm) !important; color: var(--meta) !important; }

/* ── layout overrides ────────────────────────────────────────── */
.mermaid svg { max-width: 100% !important; height: auto !important; width: 100% !important; }
.md-mermaid-wrap { width: 100% !important; overflow: hidden; margin-bottom: 24px; }
.md-section-header { display: flex !important; align-items: baseline !important; gap: 16px !important; }
.md-section-badges { display: flex; gap: 8px; align-self: baseline; }

/* ── list fix (prevent premature wrap) ────────────────────────── */
.md-list-item .md-paragraph { max-width: none !important; }

/* ── legend styling ─────────────────────────────────────────── */
.md-legend { display: flex; flex-wrap: wrap; gap: 24px; margin-bottom: 32px; border-bottom: 1px solid var(--border-soft); padding-bottom: 16px; }
.md-legend-item { display: flex; align-items: center; gap: 10px; font: 500 var(--text-xs) var(--font-display); color: var(--meta); text-transform: uppercase; letter-spacing: 0.05em; }
.md-legend-symbol { color: var(--muted); font-weight: 400; text-transform: none; font-style: italic; }
"""
        if legend_data:
            for key, entry in legend_data.items():
                if 'css' in entry:
                    cls_str = entry['css']
                    styles = []
                    if 'border-slate-400' in cls_str: styles.append("border: 1px solid #94a3b8;")
                    if 'border-dashed' in cls_str: styles.append("border-style: dashed;")
                    if 'border-red-500' in cls_str: styles.append("border: 2px solid #ef4444;")
                    if 'border-emerald-600' in cls_str: styles.append("border: 2px solid #059669;")
                    if 'bg-emerald-50' in cls_str: styles.append("background: #ecfdf5;")
                    if styles:
                        helpers += f".swatch-{key} {{ {' '.join(styles)} }}\n"
        return base_css + helpers

    def render(self, md_content, output_path, inline=False):
        # 1. Parse Frontmatter
        frontmatter = {}
        if md_content.startswith('---'):
            parts = re.split(r'^---$', md_content, maxsplit=2, flags=re.MULTILINE)
            if len(parts) >= 3:
                try: 
                    frontmatter = yaml.safe_load(parts[1])
                    md_content = parts[2]
                except: pass

        strength_map = frontmatter.get('strength_enum', {})
        category_map = frontmatter.get('category_enum', {})
        legend_data = frontmatter.get('legend', {})
        glossary = frontmatter.get('glossary', frontmatter.get('vocabulary', {}))
        title = frontmatter.get('title', '').strip()

        # Pre-process MD to fix list rendering bugs
        md_content = re.sub(r'([^\n])\n\s*([-*+]\s+)', r'\1\n\n\2', md_content)
        md_content = re.sub(r'([^\n])\n\s*(\d+\.\s+)', r'\1\n\n\2', md_content)
        md_content = re.sub(r'(\*\*Wins:\*\*)\n-', r'\1\n\n-', md_content)
        md_content = re.sub(r'(\*\*Details:\*\*)\n-', r'\1\n\n-', md_content)
        
        # 2. MD -> HTML
        html_output = markdown.markdown(md_content, extensions=['extra', 'toc', 'admonition'])
        soup = BeautifulSoup(html_output, 'html.parser')
        new_soup = BeautifulSoup("", 'html.parser')
        
        # 3. Advanced Synthesis
        all_elements = list(soup.contents)
        skip = set()
        current_section = None
        current_card = None
        
        for i, el in enumerate(all_elements):
            if i in skip or (isinstance(el, str) and not el.strip()): continue
            if isinstance(el, str):
                (current_card or new_soup).append(el)
                continue
            
            if el.name == 'h1' and el.get_text().strip() == title: continue
            
            text = el.get_text().strip()
            
            # H2 -> Section Header
            if el.name == 'h2':
                m = re.match(r'^(\d+)\.\s+(.*)', text)
                if m:
                    num, t_text = m.groups()
                    current_section = new_soup.new_tag('section', attrs={'class': 'md-section md-section-level-1', 'id': self.slugify(t_text)})
                    hdr = new_soup.new_tag('div', attrs={'class': 'md-section-header'})
                    span = new_soup.new_tag('span', attrs={'class': 'md-section-num'}); span.string = num.zfill(2); hdr.append(span)
                    h2 = new_soup.new_tag('h2', attrs={'class': 'md-heading-level-2'}); h2.string = t_text; hdr.append(h2)
                    badges_div = new_soup.new_tag('div', attrs={'class': 'md-section-badges'})
                    hdr.append(badges_div)
                    current_section.append(hdr)
                    new_soup.append(current_section)
                    current_card = None
                    continue
                current_section = None
                new_soup.append(el); continue

            if el.name == 'hr':
                current_section = current_card = None
                new_soup.append(el); continue

            if current_section:
                # 3a. Callout Support
                if el.name == 'blockquote' and '[!' in text:
                    full_text = el.get_text(separator='\n')
                    markers = re.findall(r'\[!(badge|files|legend|problem)\]', full_text)
                    segments = re.split(r'\[!(?:badge|files|legend|problem)\]', full_text)
                    
                    for idx, kind in enumerate(markers):
                        content = segments[idx+1].strip()
                        if kind == 'badge':
                            b_container = current_section.find('div', class_='md-section-badges')
                            if b_container:
                                parts = [p.strip().replace('**', '') for p in content.split('·')]
                                for p_val in parts:
                                    if not p_val: continue
                                    cls = "md-tag-info"
                                    if p_val in strength_map: cls = strength_map[p_val].get('css', 'md-tag-success')
                                    elif p_val in category_map: cls = category_map[p_val].get('css', 'md-tag-muted')
                                    else:
                                        for k, v in category_map.items():
                                            if v.get('label') == p_val: cls = v.get('css', 'md-tag-muted'); break
                                    badge = new_soup.new_tag('span', attrs={'class': f'md-tag {cls}'}); badge.string = p_val; b_container.append(badge)

                        elif kind == 'legend':
                            if not current_card:
                                current_card = new_soup.new_tag('div', attrs={'class': 'md-card'})
                                current_section.append(current_card)
                            r1 = current_card.find('div', class_='md-card-header-row')
                            if not r1:
                                r1 = new_soup.new_tag('div', attrs={'class': 'md-card-header-row'})
                                h3 = new_soup.new_tag('h3', attrs={'class': 'md-heading-level-3'})
                                h3.string = current_section.find('h2').get_text() if current_section.find('h2') else "Candidate"
                                r1.append(h3); current_card.append(r1)
                            
                            tags = [t.strip() for t in content.split('·')]
                            for t in tags:
                                if not t: continue
                                t_key = t.replace(' ', '_').lower()
                                tag = new_soup.new_tag('span', attrs={'class': f'md-tag md-tag-info swatch-{t_key}'})
                                tag.string = t.replace('_', ' ')
                                r1.append(tag)

                        elif kind == 'files':
                            if not current_card:
                                current_card = new_soup.new_tag('div', attrs={'class': 'md-card'})
                                current_section.append(current_card)
                            files_div = new_soup.new_tag('div', attrs={'class': 'md-card-files'})
                            files = []
                            for line in content.split('\n'):
                                clean = line.strip().lstrip('-').strip(' `')
                                if clean and not clean.startswith('[!'): files.append(clean)
                            if files:
                                files_div.string = " · ".join(files)
                                current_card.append(files_div)

                        elif kind == 'problem':
                            if not current_card:
                                current_card = new_soup.new_tag('div', attrs={'class': 'md-card'})
                                current_section.append(current_card)
                            bq = new_soup.new_tag('blockquote', attrs={'class': 'md-blockquote'})
                            p = new_soup.new_tag('p', attrs={'class': 'md-paragraph'}); p.string = f"Problem: {content}"; bq.append(p)
                            current_card.append(bq)
                    continue

                if 'Problem:' in text:
                    if not current_card:
                        current_card = new_soup.new_tag('div', attrs={'class': 'md-card'})
                        current_section.append(current_card)
                    bq = new_soup.new_tag('blockquote', attrs={'class': 'md-blockquote'})
                    p = new_soup.new_tag('p', attrs={'class': 'md-paragraph'}); p.string = text.strip(); bq.append(p)
                    current_card.append(bq)
                    continue

                if el.name == 'pre' and el.find('code') and 'language-mermaid' in el.find('code').get('class', []):
                    dw = new_soup.new_tag('div', attrs={'class': 'md-mermaid-wrap'})
                    mp = new_soup.new_tag('pre', attrs={'class': 'mermaid'}); mp.string = el.find('code').string
                    dw.append(mp)
                    (current_card or current_section).append(dw)
                    continue

                (current_card or current_section).append(el)
            else:
                new_soup.append(el)

        # 4. Standard Classes & Table Processing
        for tag, cls in self.mappings.items():
            for el in new_soup.find_all(tag):
                if tag.startswith('h') and el.parent and el.parent.name in ['header', 'div']: continue
                if cls not in el.get('class', []): el['class'] = el.get('class', []) + [cls]
        for td in new_soup.find_all('td'):
            if re.match(r'^[\d,\.%s]+$', td.get_text().strip()): td['class'] = td.get('class', []) + ['md-tabular']
        for c in new_soup.find_all('code'):
            if not c.parent or c.parent.name != 'pre': c['class'] = c.get('class', []) + ['md-code']

        # 5. Build Result
        doc = BeautifulSoup('<!doctype html><html lang="en"><head></head><body></body></html>', 'html.parser')
        head = doc.head; body = doc.body
        head.append(doc.new_tag('meta', charset='utf-8'))
        head.append(doc.new_tag('meta', attrs={'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}))
        title_tag = doc.new_tag('title'); title_tag.string = frontmatter.get('title', 'Report'); head.append(title_tag)
        style = doc.new_tag('style'); style.string = self.get_style_content(legend_data); head.append(style)
        
        output_dir = Path(output_path).parent.absolute()
        mermaid_js_path = self.asset_dir / "mermaid.min.js"
        if inline and mermaid_js_path.exists():
            script = doc.new_tag('script'); script.string = mermaid_js_path.read_text(); head.append(script)
        else:
            try: js_ref = os.path.relpath(mermaid_js_path, output_dir)
            except: js_ref = str(mermaid_js_path)
            head.append(doc.new_tag('script', src=js_ref))
        
        m_init = doc.new_tag('script')
        m_init.string = "mermaid.initialize({startOnLoad:true, theme:'base', securityLevel:'loose', flowchart:{useMaxWidth:true, htmlLabels:true}});"
        head.append(m_init)
        art = doc.new_tag('article', attrs={'class': f'md-document flavor-{self.flavor}'}); body.append(art)
        
        if frontmatter:
            h = doc.new_tag('header', attrs={'class': 'md-header'})
            eb = doc.new_tag('span', attrs={'class': 'md-eyebrow'}); eb.string = frontmatter.get('title', 'Architecture Review'); h.append(eb)
            h1 = doc.new_tag('h1', attrs={'class': 'md-heading-level-1'}); h1.string = frontmatter.get('project', 'Report'); h.append(h1)
            stats = frontmatter.get('statistics', {})
            subtitle = doc.new_tag('p', attrs={'class': 'md-subtitle'}); subtitle.string = f"{stats.get('candidates', 0)} refactoring candidates ranked by leverage, locality, and risk"; h.append(subtitle)
            mc = doc.new_tag('div', attrs={'class': 'md-meta'})
            meta_items = [("Repository", frontmatter.get('repository')), ("Branch", frontmatter.get('branch')), ("Date", frontmatter.get('date')), ("Lines reviewed", stats.get('total_lines_reviewed')), ("Files involved", stats.get('files_involved'))]
            for k, v in meta_items:
                if v:
                    item = doc.new_tag('div', attrs={'class': 'md-meta-item'})
                    lbl = doc.new_tag('span', attrs={'class': 'md-meta-label'}); lbl.string = k; item.append(lbl)
                    val = doc.new_tag('span', attrs={'class': 'md-meta-value' + (' md-tabular' if isinstance(v, int) else '')})
                    val.string = f"{v:,}" if isinstance(v, int) else str(v); item.append(val); mc.append(item)
            h.append(mc)
            if legend_data:
                leg = doc.new_tag('div', attrs={'class': 'md-legend'})
                for label, entry in legend_data.items():
                    item = doc.new_tag('div', attrs={'class': 'md-legend-item'})
                    item.append(doc.new_tag('span', attrs={'class': f"md-legend-swatch swatch-{label}"}))
                    lbl_span = doc.new_tag('span'); lbl_span.string = label.replace('_', ' ')
                    sym_span = doc.new_tag('span', attrs={'class': 'md-legend-symbol'}); sym_span.string = f" ({entry.get('symbol', '')})"
                    item.append(lbl_span); item.append(sym_span); leg.append(item)
                h.append(leg)
            art.append(h)
        
        for e in list(new_soup.contents): art.append(e)
        if glossary:
            hr = doc.new_tag('hr', attrs={'class': 'md-hr'}); art.append(hr)
            g_h2 = doc.new_tag('h2', attrs={'class': 'md-heading-level-2', 'id': 'glossary'}); g_h2.string = "Glossary"; art.append(g_h2)
            dl = doc.new_tag('dl', attrs={'class': 'md-glossary'})
            for term, defn in glossary.items():
                dt = doc.new_tag('dt', attrs={'class': 'md-glossary-term'}); dt.string = term.replace('_', ' ').capitalize()
                dd = doc.new_tag('dd', attrs={'class': 'md-glossary-def'}); dd.string = defn
                dl.append(dt); dl.append(dd)
            art.append(dl)
        return doc.prettify()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Metadata-Driven Markdown to HTML")
    parser.add_argument("source", help="Source Markdown file")
    parser.add_argument("-o", "--output", help="Output HTML file")
    parser.add_argument("-f", "--flavor", default="executive-report", help="Flavor (kami, minimal)")
    parser.add_argument("--inline", action="store_true", help="Inline JS assets")
    args = parser.parse_args()
    renderer = KamiRenderer(flavor="kami")
    html = renderer.render(open(args.source).read(), args.output or args.source.replace('.md', '.html'), inline=args.inline)
    open(args.output or args.source.replace('.md', '.html'), 'w').write(html)
    print(f"Rendered: {args.output or args.source.replace('.md', '.html')}")
