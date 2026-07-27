---
title: Architecture Review
project: file-processor
date: 2026-07-27
repository: acme/file-processor
branch: feat/refactor-pipeline
reviewed: 2026-07-27T14:32:00+08:00
files_scanned: 24
model: Claude Opus 4
strength_enum:
  Strong: { css: "badge-strong" }
  Worth exploring: { css: "badge-worth" }
  Speculative: { css: "badge-speculative" }
category_enum:
  in_process: { label: "in-process", description: "pure computation, no I/O" }
  local_substitutable: { label: "local-substitutable", description: "local test stand-ins exist" }
  ports_and_adapters: { label: "ports & adapters", description: "remote but owned services" }
  mock: { label: "mock", description: "true external, third-party" }
legend:
  module: { symbol: "solid box", css: "border-slate-400" }
  shallow_module: { symbol: "thin box", css: "border-red-500" }
  deep_module: { symbol: "thick dark box", css: "border-emerald-600" }
  leakage: { symbol: "red arrow", css: "border-red-500" }
  seam: { symbol: "dashed line", css: "border-slate-400" }
glossary:
  module: anything with an interface and an implementation
  shallow_module: interface nearly as complex as the implementation
  deep_module: interface dramatically simpler than its implementation
  leakage: dependency that crosses a seam
  seam: where an interface lives
statistics:
  candidates: 3
  strong: 2
  worth_exploring: 1
  speculative: 0
  total_lines_reviewed: 1906
  files_involved: 8
---

## Overview

| # | Strength | Candidate | Files | Lines | Category |
|---|----------|-----------|-------|-------|----------|
| 1 | **Strong** | Pipeline Normalization | 5 | 1,206 | in-process |
| 2 | **Strong** | Config Unification | 3 | 500 | ports & adapters |
| 3 | **Worth exploring** | Output Formatter Extraction | 3 | 200 | local-substitutable |

## 1. Pipeline Normalization

> [!badge]
> Strong · in-process

> [!files]
> - `domain/pipeline/normalizer.py`
> - `domain/pipeline/validator.py`
> - `domain/pipeline/transformer.py`
> - `domain/models.py`
> - `output/renderer.py`

> [!legend]
> deep_module · seam · leakage

> [!problem]
> Pipeline stages each duplicate normalization logic. Three independent code paths for input validation, type coercion, and field mapping produce inconsistent results when processing the same input through different stages.

> [!warning]
> Contradicts ADR-0019 which specified per-stage validation. Must update ADR before merging.

> [!note]
> First phase of a larger pipeline refactor. This candidate is the highest-leverage because it fixes the root cause rather than patching symptoms.

### Before / After

```mermaid
graph TD
    subgraph "BEFORE"
        A["Input"] --> B["Stage 1: normalize"]
        B --> C["Stage 2: normalize"]
        C --> D["Stage 3: normalize"]
        D --> E["Output"]
    end
    subgraph "AFTER"
        F["Input"] --> G["Normalizer"]
        G --> H["Stage 1"]
        G --> I["Stage 2"]
        G --> J["Stage 3"]
        H --> K["Output"]
        I --> K
        J --> K
    end
```

**Solution:** Extract a single `Normalizer` class that all pipeline stages delegate to. Each stage calls `normalizer.process(data)` instead of maintaining its own validation and coercion.

**Wins:**
- locality: normalization lives in one module, not three
- leverage: every pipeline stage benefits from the fix
- seam: Normalizer becomes the interface between input and processing
- deep_module: Normalizer is substantially simpler than the sum of three per-stage implementations

### Details

The `Normalizer` class handles three concerns currently duplicated across stages:

1. **Type coercion** — string-to-int, date parsing, enum mapping
2. **Field validation** — required field presence, range checks, format validation
3. **Default application** — config-driven defaults for optional fields

Each stage currently imports `domain.models` and applies these checks independently. The Normalizer consolidates all three into a single call site with consistent error reporting.

```python
class Normalizer:
    """Single authority for input normalization."""
    def process(self, data: dict) -> NormalizedInput:
        coerced = self._coerce_types(data)
        self._validate(coerced)
        return NormalizedInput(**coerced)
```

## 2. Config Unification

> [!badge]
> Strong · ports & adapters

> [!files]
> - `config/loader.py`
> - `config/remote_fetcher.py`
> - `domain/services/config_service.py`

> [!legend]
> seam · shallow_module

> [!problem]
> Configuration is loaded from three sources (env vars, YAML files, remote API) with no unified interface. The remote fetcher has its own caching layer that duplicates logic from the local YAML loader.

> [!note]
> The remote config API is an owned service — not third-party. Use the ports & adapters pattern rather than mocking.

### Before / After

```mermaid
graph LR
    subgraph "BEFORE"
        EV["env vars"] --> A["App"]
        YF["YAML files"] --> A
        RA["remote API"] --> A
    end
    subgraph "AFTER"
        EV2["env vars"] --> U["ConfigHub"]
        YF2["YAML files"] --> U
        RA2["remote API"] --> U
        U --> B["App"]
    end
```

**Solution:** Create a `ConfigHub` class that implements the ports & adapters pattern. Each config source becomes an adapter behind a shared interface. The app queries `ConfigHub` and never touches individual loaders.

**Wins:**
- seam: ConfigHub is the single interface for all config
- locality: caching lives in one place, not duplicated per source
- leverage: adding a new config source requires one new adapter, zero app changes

## 3. Output Formatter Extraction

> [!badge]
> Worth exploring · local-substitutable

> [!files]
> - `output/formatter.py`
> - `output/renderer.py`
> - `domain/services/export_service.py`

> [!legend]
> shallow_module · leakage

> [!problem]
> The output formatter is tangled with the renderer — changing output format (JSON, CSV, table) requires modifying renderer internals. The export service directly imports formatter internals.

### Before / After

```mermaid
graph TD
    subgraph "BEFORE"
        R["Renderer"] --- F["Formatter"]
        E["ExportService"] --> F
    end
    subgraph "AFTER"
        R2["Renderer"] --> |"uses"| FR["FormatRegistry"]
        E2["ExportService"] --> |"uses"| FR
        FR --> J2["JSONFormatter"]
        FR --> C2["CSVFormatter"]
        FR --> T2["TableFormatter"]
    end
```

**Solution:** Extract formatters behind a `FormatRegistry` interface. The renderer and export service both query the registry by format name. Each formatter is a separate module implementing the same protocol.

**Wins:**
- seam: FormatRegistry is the interface between consumers and formatters
- locality: each formatter is a self-contained module
- deep_module: FormatRegistry interface is a single `format(data, fmt)` call

> [!warning]
> Worth exploring rather than Strong because the current formatter/renderer coupling affects only the export path, not the main pipeline. Weigh this against the Pipeline Normalization candidate which affects every input.

## Top Recommendation

Primary choice is candidate 1 (Pipeline Normalization). Candidate 2 (Config Unification) should follow in the same sprint since it shares no code with candidate 1 and can run in parallel. Candidate 3 (Output Formatter Extraction) should wait — it is lower leverage and its `[!warning]` note should be addressed in planning before scheduling.
