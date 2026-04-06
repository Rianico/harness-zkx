---
name: perl-expert
description: Deep expertise in Perl 5.36+ patterns, security, testing, and modern idioms. Invoke this skill when instructed by the Perl rules.
argument-hint: "[patterns|security|testing]"
---

# Perl Expert Skill

You have invoked the Perl Expert Skill. This skill contains actionable checklists and constraints for Perl software engineering tasks.

## Quick Actions & Checklists

### Idiomatic Perl (Modern Patterns)
- **Signatures:** Use subroutine signatures (`sub foo($bar, $baz)`) available in 5.36+.
- **Object Orientation:** Prefer `Object::Pad`, `Corinna`, or `Moo`/`Moose` over raw blessed hashrefs.
- **Data Structures:** Pass by reference (hashrefs `\%hash`, arrayrefs `\@array`) to subroutines instead of flattening lists.
> **Need Deep Knowledge?** Read `skills/perl-expert/references/perl-patterns.md`.

### Security
- **Taint Mode:** Understand that `-T` prevents using unvalidated input in system commands or file operations.
- **Input Validation:** Always untaint data using regex matches before using it.
- **Safe Execution:** Use multi-argument `system LIST` or `IPC::Run` instead of `system "string"` to prevent shell injection.
> **Need Deep Knowledge?** Read `skills/perl-expert/references/perl-security.md`.

### Testing & Verification
- **Framework:** Default to `Test2::V0` (modern) or `Test::More`.
- **Structure:** Put tests in the `t/` directory. Use `prove -l` or `prove -lv` to run them.
- **Mocking:** Use `Test::MockModule` or `Test2::Mock`.
> **Need Deep Knowledge?** Read `skills/perl-expert/references/perl-testing.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "patterns", "security", "testing"), apply the relevant checklist above.
2. If the task is architectural or requires deep security knowledge, use the `Read` tool to fetch the relevant reference document from `skills/perl-expert/references/`.
