# Tooling & CI — ShellCheck, shfmt, Bats, Pre-commit

> Companion to `SKILL.md` §9. Configuration recipes for the Bash toolchain. Sources: `wshobson/agents/shellcheck-configuration`, `wshobson/agents/bats-testing-patterns`, `rmyndharis/antigravity-skills/bash-pro` (CI/CD), `sickn33/agentic-awesome-skills/bash-scripting` Phase 6.

## ShellCheck

```bash
# Install
sudo apt install shellcheck        # Debian/Ubuntu
brew install shellcheck            # macOS
# Or via pip: pipx install shellcheck-py

# Run
shellcheck --enable=all --external-sources script.sh
shellcheck --enable=all --external-sources --shell=bash script.sh
shellcheck -f gcc script.sh        # gcc format for CI annotations
shellcheck -f json script.sh | jq  # JSON for tooling

# Config file .shellcheckrc (project root)
# enable=all
# external-sources=true
# shell=bash
# disable=SC2148   # only with justification

# Severity levels: error, warning, info, style — gate on error+warning in CI
shellcheck --severity=warning **/*.sh
```

Suppress narrowly with reason:

```bash
# shellcheck disable=SC2086  # Reason: intentional word splitting for glob
for f in $patterns; do echo "$f"; done
```

Common codes to know: `SC2086` unquoted var, `SC2046` unquoted `$( )`, `SC2164` unchecked `cd`, `SC2181` check `[[ $? == 0 ]]` directly, `SC2143` use `grep -q` not `grep | wc`.

## shfmt

```bash
# Install
go install mvdan.cc/sh/v3/cmd/shfmt@latest
brew install shfmt

# Format check (CI) vs write
shfmt -i 2 -ci -bn -sr -kp -d .     # diff, exit 1 if not formatted
shfmt -i 2 -ci -bn -sr -kp -w .     # write

# Standard flags: -i 2 (indent 2), -ci (case indent), -bn (binary ops newline),
# -sr (space redirect), -kp (keep padding)
# Config file .editorconfig or .shfmt.toml

# Pre-commit hook: shfmt -d exits non-zero when diff found
```

## Bats (bats-core)

```bash
# Install
npm install -g bats                     # via npm
brew install bats-core                  # macOS
git clone https://github.com/bats-core/bats-core && ./install.sh /usr/local

# Run
bats tests/                             # all
bats tests/*.bats --tap                 # TAP output
bats --filter "handles spaces" tests/   # filter

# Fixtures & helpers — test_helper.bash
# setup() / teardown() per test, setup_file() / teardown_file() per file (bats-core v1.7+)
# Use run -- "$SCRIPT" args; check [ "$status" -eq 0 ] and [[ "$output" == *pattern* ]]

# Coverage patterns
# - happy path, missing args, invalid input, permissions, spaces-in-filename
# - error messages contain Usage:/ERROR:
# - idempotency: run twice, second should succeed or report exists
```

Minimal `Makefile` integration:

```makefile
.PHONY: lint fmt test test-verbose
lint: ; shellcheck --enable=all --external-sources **/*.sh
fmt-check: ; shfmt -i 2 -ci -bn -sr -kp -d .
fmt: ; shfmt -i 2 -ci -bn -sr -kp -w .
test: ; bats tests/ --tap
test-verbose: ; bats tests/ --verbose-run
```

## Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.10.0
    hooks: [{ id: shellcheck, args: [--enable=all, --external-sources] }]
  - repo: https://github.com/shellcheck-py/shfmt-py
    rev: v3.8.0
    hooks:
      - id: shfmt
        args: [-i, '2', -ci, -bn, -sr, -kp, -d]
  - repo: https://github.com/shellspec/shellspec
    rev: master
    hooks: [{ id: shellspec }]
  - repo: https://github.com/jazzco/checkbashisms
    rev: master
    hooks: [{ id: checkbashisms, args: [--force] }]

# Install: pre-commit install && pre-commit run --all-files
```

## GitHub Actions Matrix

```yaml
name: Shell CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: shellcheck --enable=all --external-sources **/*.sh
      - run: shfmt -i 2 -ci -bn -sr -kp -d .
      - run: checkbashisms **/*.sh # if POSIX target
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        bash: ['4.4', '5.1', '5.2']
    runs-on: ${{ matrix.os }}
    container: ${{ matrix.os == 'ubuntu-latest' && 'bash:5.2' || '' }}
    steps:
      - uses: actions/checkout@v4
      - uses: bats-core/bats-action@3.0.0
        with: { bats-install: true }
      - run: bats tests/ --tap
```

## Additional Hardening

- **Shdoc** — documentation from comments: `shdoc < script.sh > docs.md`
- **Semgrep** — custom shell rules for `eval`, `curl|bash`, secrets
- **Gitleaks/Trufflehog** — secrets scanning before commit
- **Actionlint** — validates workflow files that embed shell

## References

- ShellCheck wiki: `https://www.shellcheck.net/wiki/SCXXXX` per code
- Google Shell Style Guide: `https://google.github.io/styleguide/shellguide.html`
- Bash Pitfalls: `https://mywiki.wooledge.org/BashPitfalls`
- Bash Hackers Wiki: `https://wiki.bash-hackers.org/`
