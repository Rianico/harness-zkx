---
name: perl-expert
description: >-
  Perl 5.36+ domain expertise for CPAN modules, modern signatures, Object::Pad, Moo/Moose, taint mode, input validation, safe command execution, Test2, Test::More, prove, security review, and legacy modernization. Use for Perl implementation, debugging, testing, security hardening, and refactoring.
argument-hint: |-
  [patterns|security|testing]
metadata:
  managed-by: programming-expert
---

# Perl Expert Skill

Checklists and constraints for Perl engineering tasks.

## Quick Actions & Checklists

### Idiomatic Perl (Modern Patterns)

- **Signatures:** use subroutine signatures (`sub foo($bar, $baz)`), available in 5.36+.
- **Object orientation:** prefer `Object::Pad`, `Corinna`, or `Moo`/`Moose` over raw blessed hashrefs.
- **Data structures:** pass by reference (hashrefs `\%hash`, arrayrefs `\@array`) instead of flattening lists.

> Deep dive: [perl-patterns.md](references/perl-patterns.md) — core principles, error handling, modern OO with Moo, regular expressions.

### Security

- **Taint mode:** `-T` blocks unvalidated input from system commands and file operations.
- **Input validation:** untaint data with regex matches before use.
- **Safe execution:** use multi-argument `system LIST` or `IPC::Run` instead of `system "string"` to prevent shell injection.

> Deep dive: [perl-security.md](references/perl-security.md) — taint mode, input validation, safe regexes, safe file operations.

### Testing & Verification

- **Framework:** default to `Test2::V0` (modern) or `Test::More`.
- **Structure:** put tests in the `t/` directory. Run them with `prove -l` or `prove -lv`.
- **Mocking:** use `Test::MockModule` or `Test2::Mock`.

> Deep dive: [perl-testing.md](references/perl-testing.md) — TDD workflow, Test::More fundamentals, Test2::V0, test organization with prove.
