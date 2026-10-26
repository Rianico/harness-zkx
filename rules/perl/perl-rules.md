---
paths:
  - "Makefile.PL"
  - "Build.PL"
  - "**/*.pl"
  - "**/*.pm"
  - "**/*.t"
  - "cpanfile"
---

# Perl Rules

You are operating in a Perl codebase.

## Core Perl Standards (80% Base)

- **Strict & warnings:** every file must carry `use strict;` and `use warnings;`, or `use v5.36;` (which implies both).
- **Modern dialect:** assume Perl 5.36+ features are available unless specified otherwise.
- **Lexical scope:** declare variables with `my`. Avoid global `our` or package variables unless explicitly required.

## Expertise Routing (Use `Read` tool)

`perl-expert` is a managed subskill of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`) — do not invoke them through the `Skill` tool. Read the file directly:

- `skills/programming-expert/subskills/perl-expert/SKILL.md` — modern patterns (signatures, Moo), security (taint, safe execution), testing (Test2, prove)
- `skills/programming-expert/subskills/perl-expert/references/` — Perl patterns, security deep dive, testing workflow

**CRITICAL:** Do not write legacy Perl 4 style code. Read the expert methodology for modern Perl 5 idioms first.
