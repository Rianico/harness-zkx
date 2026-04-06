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

You are operating in a Perl codebase. Before proceeding with your task, review and apply these rules.

## Core Perl Standards (80% Base)
- **Strict & Warnings:** EVERY file must have `use strict;` and `use warnings;` or `use v5.36;` (which implies both).
- **Modern Dialect:** Assume Perl 5.36+ features are available unless specified otherwise.
- **Lexical Scope:** Always use `my` to declare variables. Avoid global `our` or package variables unless explicitly required.

## Expertise Routing (Use `Skill` tool)
If your task requires modern object orientation, secure system interactions, or testing, you MUST pause and invoke the `Skill` tool for `perl-expert` to retrieve the deep methodology:

- **Code Review & Patterns:** Invoke `Skill(skill="perl-expert", args="patterns")`.
- **Security & Taint:** Invoke `Skill(skill="perl-expert", args="security")`.
- **Testing:** Invoke `Skill(skill="perl-expert", args="testing")`.

**CRITICAL INSTRUCTION:** Do not write legacy Perl 4 style code. Retrieve the expert skill methodology to use modern Perl 5 idioms.
