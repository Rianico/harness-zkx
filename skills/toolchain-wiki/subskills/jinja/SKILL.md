---
name: jinja
description: >-
  Jinja 3.1 templating reference for Python — template language, filters/tests, Environment API, extensions, sandboxing, native types. Use when writing or debugging Jinja templates, configuring an Environment or loader, fixing autoescaping or whitespace output, or sandboxing untrusted templates.
metadata:
  managed-by: toolchain-wiki
argument-hint: |-
  '[topic]'
---

# Jinja

> **3.1.6** (docs 3.1.x) — <https://jinja.palletsprojects.com/en/stable/> — package `jinja2`, Python only

Fast, expressive, extensible Python templating engine. A template is text plus `{{ expressions }}`, `{% statements %}` and `{# comments #}`; the application owns all configuration through one `Environment`.

Templates compile to Python and are cached by the loader (400 entries, `auto_reload` on). Undefined names render as empty string by default and raise on any other operation.

## Quick Start

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader("templates"),          # resolves "page.html" under templates/
    autoescape=select_autoescape(),                # escape .html/.xml/.xhtml only
    autoescape=select_autoescape(),                # escapes .html/.htm/.xml by default
)
print(env.get_template("page.html").render(users=users))
```

```jinja
{# templates/page.html #}
{% extends "base.html" %}
{% block content %}
  {% for u in users if u.active %}
    <li>{{ u.name|title }} — {{ u.email }}</li>
  {% else %}
    <li>none</li>
  {% endfor %}
{% endblock %}
```

**Done when:** `render()` returns the expected `str` and `env.get_template()` resolved the file from the loader directory — if either fails, the fault is in `Environment` configuration, not the template.

## Authoring Rules

1. Build the `Environment` once at application start; never per request or per render.
2. Set `autoescape=select_autoescape()` for markup. Never add `|safe` or `Markup` around user input.
3. Reuse a loader (`FileSystemLoader`, `PackageLoader`, `DictLoader`) instead of `Template("…")` strings — only loaders enable inheritance, caching and bytecode caching.
4. Control whitespace at `Environment` level (`trim_blocks`, `lstrip_blocks`) before sprinkling `{%- -%}` markers through templates.
5. Use `StrictUndefined` while developing so typos fail loudly; the default `Undefined` silently prints nothing.
6. Treat templates as untrusted input only through [sandbox](references/sandbox.md); a plain `Environment` executes arbitrary Python.

## Verification Gates

Run from the project that owns the templates — compiler output beats eyeballing rendered markup.

```bash
# 1. Syntax only (fast, no context needed) — raises TemplateSyntaxError on failure
uv run python -c "from jinja2 import Environment; Environment().parse(open('templates/page.html').read())"

# 2. Render smoke test with a minimal context
uv run python -c "
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(loader=FileSystemLoader('templates'), autoescape=select_autoescape())
print(env.get_template('page.html').render(users=[]))"
```

**Done when:** both commands exit 0 and the rendered output contains no literal `{{` or `{%`. In Flask/Django, the same template fails through the framework's own loader first — check the framework wiring.

## The 80% Surface

### Delimiters

| Syntax      | Meaning                                                            |
| ----------- | ------------------------------------------------------------------ |
| `{{ … }}`   | Expression printed to output                                       |
| `{% … %}`   | Statement: control flow, inheritance, macros                       |
| `{# … #}`   | Comment, not in output                                             |
| line prefix | `line_statement_prefix` / `line_comment_prefix` (unset by default) |

### Composition skeleton

```jinja
{# base.html #}
<title>{% block title %}Site{% endblock %}</title>
<body>{% block body %}{% endblock %}</body>

{# child.html #}
{% extends "base.html" %}
{% import "forms.html" as forms %}          {# without context by default #}
{% from "macros.html" import field with context %}
{% block title %}{{ super() }} — Child{% endblock %}
{% include "footer.html" ignore missing %}
```

`{% macro field(name, value='') %}…{% endmacro %}` defines reusable markup; call blocks via `{% call render_thing() %}`. Details: [inheritance](references/inheritance.md).

### Most-used filters

| Filter                                                                                                                                                  | Effect                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `default(value, '', boolean=False)`                                                                                                                     | Fallback when undefined (or falsy with `boolean=True`) |
| `join(sep='')`, `length`, `first`, `last`                                                                                                               | Sequence shaping                                       |
| `map(attribute=…)`, `select('odd')`, `rejectattr('x')`, `selectattr('x', 'eq', v)`                                                                      | Lazy filtering/transforming                            |
| `sort(reverse=False, case_sensitive=False, attribute=None)`, `groupby('attr')`, `unique`, `dictsort`                                                    | Ordering                                               |
| `title`, `capitalize`, `lower`, `upper`, `trim`, `replace(old, new, count)`, `truncate(length, …)`, `wordwrap(width)`, `center(width)`, `indent(width)` | Text                                                   |
| `tojson(indent=None)`, `urlencode`, `urlize`, `striptags`, `xmlattr`, `filesizeformat`, `pprint`                                                        | Output shaping                                         |
| `int(default=0)`, `float(default=0.0)`, `round(precision, method)`, `abs`, `sum(attribute=None)`                                                        | Numbers                                                |
| `escape`, `forceescape`, `safe`                                                                                                                         | Escaping — `safe` only on trusted content              |
| `batch(linecount, fill_with)`, `slice(slices, fill_with)`, `items`, `attr(name)`                                                                        | Grouping / access                                      |

Full list with signatures and examples: [filters](references/filters.md).

### Most-used tests and globals

```jinja
{% if user is defined and user.email is not none %}   {# defined, none #}
{% if items is iterable and items is not string %}    {# iterable, string #}
{% if n is divisibleby 3 and n is odd %}              {# divisibleby, odd, even #}
{% if a is sameas b and c is escaped %}               {# sameas, escaped #}
```

Tests: `boolean callable defined divisibleby eq escaped even false filter float ge gt in integer iterable le lower lt mapping ne none number odd sameas sequence string test true undefined upper`.
Globals: `range()`, `dict()`, `lipsum(n, html, min, max)`, `cycler(*items)` (`.next()`, `.reset()`, `.current`), `joiner(sep=', ')`, `namespace(...)` for mutable loop state. Custom registration: [tests](references/tests.md).

### Environment options worth knowing

| Option                                      | Default                | Use it for                               |
| ------------------------------------------- | ---------------------- | ---------------------------------------- |
| `loader`, `optimized`, `auto_reload`        | `None`, `True`, `True` | Template resolution and reload behaviour |
| `autoescape`                                | `False`                | `select_autoescape()` for markup         |
| `undefined`                                 | `Undefined`            | `StrictUndefined` / `ChainableUndefined` |
| `trim_blocks`, `lstrip_blocks`              | `False`                | Removing tag-only line whitespace        |
| `keep_trailing_newline`, `newline_sequence` | `False`, `'\n'`        | Exact output bytes                       |
| `extensions` / `add_extension()`            | `[]`                   | i18n, `do`, loop controls, debug         |
| `cache_size`                                | `400`                  | `-1` never clear, `0` recompile always   |
| `finalize`, `enable_async`                  | `None`, `False`        | Pre-output coercion, async templates     |

Loaders, undefined types, policies, `Template`/`Context` objects, exceptions and the Meta API: [api](references/api.md).

### Bundled extensions

| Extension                 | Adds                                    | Status                       |
| ------------------------- | --------------------------------------- | ---------------------------- |
| `jinja2.ext.i18n`         | `{% trans %}` + `gettext`/Babel filters | Requires `install_gettext_*` |
| `jinja2.ext.do`           | `{% do %}` expression statement         | Active                       |
| `jinja2.ext.loopcontrols` | `{% break %}`, `{% continue %}`         | Active                       |
| `jinja2.ext.debug`        | `{% debug %}` context dump              | Active                       |
| `jinja2.ext.with_`        | `{% with %}`                            | Built-in since 2.9 (no-op)   |
| `jinja2.ext.autoescape`   | `{% autoescape %}`                      | Removed in 2.9 (built-in)    |

Writing your own extension (Extension, Parser, AST APIs): [extensions](references/extensions.md).

### Sandboxing

`SandboxedEnvironment` swaps the compiler for a safe runtime and raises `SecurityError` on insecure attribute access; `SandboxedEnvironment(SecurityPolicy, …)` and `intercepted_binops` / `call_binop()` tune the surface.

> [!WARNING]
> The sandbox is not a security sandbox for untrusted _template authors_ by default: `is_safe_callable`, `is_safe_attribute` and the operator tables must be audited for your threat model. Details: [sandbox](references/sandbox.md).

`NativeEnvironment` renders to native Python types (`int`, `list`, arbitrary objects) instead of strings — for templates that define values, not text.

## Reference Map

| Need                                                                                 | Leading word  | Pointer                                  |
| ------------------------------------------------------------------------------------ | ------------- | ---------------------------------------- |
| delimiters, variables, whitespace, escaping, control structures, expressions         | `syntax`      | [language](references/language.md)       |
| `extends`/`block`/`super`, macros, `call`, `include`, `import`                       | `inheritance` | [inheritance](references/inheritance.md) |
| every builtin filter, custom filter registration                                     | `filters`     | [filters](references/filters.md)         |
| builtin tests, global functions, custom test registration                            | `tests`       | [tests](references/tests.md)             |
| `Environment`, loaders, undefined types, context, cache, exceptions, Meta API        | `environment` | [api](references/api.md)                 |
| i18n/`do`/`loopcontrols`/`debug`, writing an extension, Extension API                | `extensions`  | [extensions](references/extensions.md)   |
| `SandboxedEnvironment`, `SecurityPolicy`, operator intercepting, `NativeEnvironment` | `sandbox`     | [sandbox](references/sandbox.md)         |
| Flask, Django, Babel, Pylons; Django/Mako → Jinja translation                        | `integration` | [integration](references/integration.md) |
| null-default fallback, alternating rows, active menu, parent loop, FAQ               | `recipes`     | [recipes](references/recipes.md)         |
| release-by-release removals, default changes, 2.x → 3.1 upgrade                      | `migration`   | [migration](references/migration.md)     |

Raw upstream docs (authoritative for flag-level and edge-case detail): `$SKILL_DIR/references/jinja-raw/` — `001-stable`, `002-intro`, `003-api`, `004-sandbox`, `005-nativetypes`, `006-templates`, `007-extensions`, `008-integration`, `009-switching`, `010-tricks`, `011-faq`, `013-changes`.

- Prose pointer: `$SKILL_DIR/references/jinja-raw/006-templates.md` (cwd unknown)
- Markdown link: from this file `[for](references/jinja-raw/006-templates.md)`; from `references/<module>.md` the same target is the bare path `jinja-raw/006-templates.md`
- If a curated file conflicts with observation, raw wins

## When Answering Questions

1. Answer from the tables and snippets above first.
2. For module depth, read `$SKILL_DIR/references/<module>.md` per the reference map.
3. For exact signatures, defaults and version behaviour, read `$SKILL_DIR/references/jinja-raw/<file>.md` (and [migration](references/migration.md) for "why did this change").
4. Confirm version-sensitive answers against the installed package: `uv run python -c "import jinja2; print(jinja2.__version__)"`.

**Done when:** every cited filter, test, option or tag is traced to a curated reference or raw doc — not to memory.

## Triggers

- `jinja`, `jinja2`, `Jinja template`, `Environment`, `FileSystemLoader`, `PackageLoader`, `select_autoescape`
- `{{ }}`, `{% for %}`, `{% if %}`, `{% block %}`, `{% extends %}`, `super()`, `{% include %}`, `{% import %}`, `{% macro %}`
- `filter` (`map`, `select`, `groupby`, `default`), `test` (`is defined`, `divisibleby`), `tojson`, `|safe`
- `whitespace control`, `trim_blocks`, `lstrip_blocks`, `keep_trailing_newline`, `Undefined` / `StrictUndefined`
- `SandboxedEnvironment`, `SecurityError`, `NativeEnvironment`, `jinja2.ext.i18n`, `{% trans %}`, custom extension
- Flask `render_template` internals, Django→Jinja migration, Mako→Jinja migration, `TemplateNotFound`, `TemplateSyntaxError`
