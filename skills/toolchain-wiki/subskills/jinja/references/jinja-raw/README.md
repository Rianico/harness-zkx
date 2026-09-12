# Jinja raw docs — 3.1.x snapshot

Verbatim upstream documentation text, fetched 2026-09-12 from <https://jinja.palletsprojects.com/en/stable/>.

- Rendered HTML was retrieved through the Jina reader proxy (the docs host challenges direct requests), reduced to the article body, and converted to GFM with `pandoc -f html -t gfm --wrap=none`.
- Sphinx definition lists were flattened to `code signature` + body paragraphs; Sphinx permalink anchors, viewcode links and link-only index tables were dropped.
- Content is otherwise unedited: these files are authoritative for signatures, defaults and edge-case wording. When a curated `references/<module>.md` conflicts with these files, these win.

| File | Upstream page | Covers |
| --- | --- | --- |
| `001-stable.md` | `/en/stable/` | Project overview, links, feature summary |
| `002-intro.md` | `/en/stable/intro/` | Installation, dependencies, optional dependencies |
| `003-api.md` | `/en/stable/api/` | `Environment`, loaders, undefined types, context, bytecode cache, async, policies, utilities, exceptions, custom filters/tests, low-level and meta API |
| `004-sandbox.md` | `/en/stable/sandbox/` | `SandboxedEnvironment`, security considerations, policy API, operator intercepting |
| `005-nativetypes.md` | `/en/stable/nativetypes/` | `NativeEnvironment`, native-type rendering examples |
| `006-templates.md` | `/en/stable/templates/` | Template language: syntax, inheritance, control structures, expressions, builtin filters/tests/globals |
| `007-extensions.md` | `/en/stable/extensions/` | Bundled extensions, writing extensions, `Extension`/`Parser`/AST APIs |
| `008-integration.md` | `/en/stable/integration/` | Flask, Django, Babel, Pylons |
| `009-switching.md` | `/en/stable/switching/` | Django and Mako template translation tables |
| `010-tricks.md` | `/en/stable/tricks/` | Null-default fallback, alternating rows, menu highlighting, parent loop |
| `011-faq.md` | `/en/stable/faq/` | Name, speed, logic-in-templates, HTML-escaping rationale |
| `013-changes.md` | `/en/stable/changes/` | Release-by-release changelog (3.1.6 back to 2.x) |

Not captured: `/en/stable/license/` (BSD-3-Clause, boilerplate) and `/en/stable/genindex/` + `/en/stable/py-modindex/` (generated indexes).
