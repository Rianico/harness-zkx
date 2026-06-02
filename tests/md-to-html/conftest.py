"""Pytest configuration and shared fixtures for md-to-html tests."""

import sys
from pathlib import Path

import pytest

# Add the scripts directory to the import path
scripts_path = (
    Path(__file__).parent.parent.parent / "skills" / "md-to-html" / "scripts"
).resolve()
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from render import KamiRenderer


SAMPLE_MD = """---
title: Test Architecture Review
project: test-project
date: 2026-06-01
repository: test/repo
branch: main
strength_enum:
  Strong: { color: emerald, css: "badge-strong" }
  Worth exploring: { color: amber, css: "badge-worth" }
  Speculative: { color: slate, css: "badge-speculative" }
category_enum:
  in_process: { label: "in-process", description: "pure computation, no I/O" }
  mock: { label: "mock", description: "true external, third-party" }
legend:
  module: { symbol: "solid box", css: "border-slate-400" }
  deep_module: { symbol: "thick dark box", css: "border-emerald-600 bg-emerald-50" }
glossary:
  module: anything with an interface and an implementation
  seam: where an interface lives
statistics:
  candidates: 3
  strong: [1, 2]
  worth_exploring: [3]
  speculative: []
  total_lines_reviewed: 1500
  files_involved: 8
candidates:
  - id: 1
    title: Test Candidate One
    strength: Strong
    category: in_process
    diagram_type: boxes_arrows
    files:
      - path: src/module1.py
        lines: 500
    total_lines: 500
    problem: "Duplicated logic across two modules"
    solution: "Extract shared logic into a single authority"
    wins:
      - "locality: logic in one module"
      - "leverage: one handler for all callers"
  - id: 2
    title: Test Candidate Two
    strength: Strong
    category: in_process
    diagram_type: boxes_arrows
    problem: "Overlapping responsibilities"
    solution: "Merge into single service"
    wins:
      - "locality: fewer files to touch"
  - id: 3
    title: Speculative Candidate
    strength: Speculative
    category: mock
    diagram_type: boxes_arrows
    problem: "Thin wrapper"
    solution: "Delegate directly to underlying library"
    wins:
      - "leverage: delete wrapper"
top_recommendation:
  primary: 1
  secondary: 2
  rationale: "Highest leverage-to-risk ratio"
---

## 1. Test Candidate One

> [!badge]
> Strong · in-process

> [!legend]
> module · deep_module

> [!problem]
> Duplicated logic across two modules

> [!warning]
> This candidate conflicts with ADR-0019

### Before / After

Test prose content.

### Wins

- locality: logic in one module
- leverage: one handler for all callers

## 2. Test Candidate Two

> [!badge]
> Strong · in-process

> [!note]
> This follows the established pattern

> [!legend]
> deep_module

### Details

More test content here.

```python
def hello():
    pass
```

## Overview

| Candidate | Strength | Category |
|-----------|----------|----------|
| Test Candidate One | Strong | in-process |
| Test Candidate Two | Strong | in-process |

## Additional Analysis

Some extra content with a note.

> [!note]
> Here is a note callout

## Top Recommendation

Primary choice is candidate 1.
"""


@pytest.fixture
def renderer():
    """KamiRenderer instance pointed at the skill's actual directories."""
    return KamiRenderer(flavor="kami")


@pytest.fixture
def sample_md():
    """Full-featured sample markdown exercising all render paths."""
    return SAMPLE_MD


@pytest.fixture
def output_dir(tmp_path):
    """Temporary directory used as the output target for asset generation."""
    return tmp_path
