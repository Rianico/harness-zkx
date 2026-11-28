---
name: aerospace
description: >-
  AeroSpace macOS tiling window manager guide: TOML config, tree layouts, bindings, callbacks, CLI, and socket IPC. Use when configuring aerospace.toml, scripting CLI commands, or fixing macOS workspaces.
metadata:
  managed-by: toolchain-wiki
argument-hint: |-
  '[topic]'
disable-model-invocation: true
---

# AeroSpace

> **v0.21.3-Beta** — <https://nikitabobko.github.io/AeroSpace/> — CLI `aerospace`, config `~/.aerospace.toml`

AeroSpace is an i3-inspired tiling window manager for macOS. It organizes windows in per-workspace trees and emulates virtual workspaces outside native macOS Spaces.

## Quick Start

Install via Homebrew Cask, seed `~/.aerospace.toml`, and verify the config without GUI popups:

```bash
# Install app and aerospace CLI
brew install --cask nikitabobko/tap/aerospace

# Bootstrap config from app bundle
cp /Applications/AeroSpace.app/Contents/Resources/default-config.toml ~/.aerospace.toml

# Print loaded config path, then validate TOML without GUI popups
aerospace config --config-path
aerospace reload-config --dry-run --no-gui
```

Minimal `~/.aerospace.toml` skeleton:

```toml
config-version = 2
after-startup-command = []
default-root-container-layout = 'tiles'
default-root-container-orientation = 'auto'
on-focused-monitor-changed = ['move-mouse monitor-lazy-center']

on-window-detected = [
    { if = 'test %{app-bundle-id} = com.apple.systempreferences', run = 'layout floating' },
]

[mode.main.binding]
    alt-h = 'focus left'
    alt-j = 'focus down'
    alt-k = 'focus up'
    alt-l = 'focus right'
    alt-shift-1 = 'move-node-to-workspace 1; workspace 1'
```

## Core Concepts

1. **Tree & Containers**: Each workspace holds one root container. Non-leaf nodes define `layout` (`tiles` or `accordion`) and `orientation` (`horizontal` or `vertical`).
2. **Normalizations**: AeroSpace flattens single-child non-root containers and enforces alternating orientations on nested containers by default.
3. **Virtual Workspaces**: Inactive windows park in a bottom screen corner with 1 pixel visible, avoiding native macOS Spaces limits.
4. **Binding Modes**: Keys inside `[mode.main.binding]` stay active until a binding invokes `mode <name>` to enter a sub-mode.
5. **Callbacks**: `on-window-detected`, `on-focus-changed`, `on-focused-monitor-changed`, and `exec-on-workspace-change` automate rules and status bars.
6. **Socket IPC**: `AeroSpace.app` listens on `/tmp/bobko.aerospace-${USER}.sock` using 4-byte LE length-prefixed JSON frames.

## Common CLI & Config Patterns

Focus, move, and switch workspaces safely:

```bash
# Focus across monitor frames without stopping at workspace edge
aerospace focus --boundaries all-monitors-outer-frame right

# Group two tiled windows under a new container (works with normalization on)
aerospace join-with right

# Switch to next non-empty workspace on the focused monitor (shell form)
# Inside aerospace.toml bindings or `aerospace eval`, omit `aerospace`:
#   list-workspaces --monitor focused --empty no | workspace --stdin next
aerospace list-workspaces --monitor focused --empty no | aerospace workspace --stdin next
```

Query windows or apps in JSON and apply new `on-window-detected` rules retroactively:

```bash
# Inspect windows on the focused monitor as JSON
aerospace list-windows --monitor focused --json

# Find app bundle IDs for on-window-detected matchers
aerospace list-apps

# Re-evaluate on-window-detected rules for existing windows (v0.21+)
aerospace run-callback --for-every-window on-window-detected
```

## API / CLI Quick Reference

| Command | Arguments / Key Flags | Purpose |
| --- | --- | --- |
| `focus` | `(left\|down\|up\|right\|dfs-next\|dfs-prev)`, `--window-id`, `--ignore-floating`, `--wrap-around` | Move focus across windows or monitors |
| `move` | `(left\|down\|up\|right)`, `--boundaries`, `--boundaries-action` | Move window within or across containers |
| `swap` | `(left\|down\|up\|right\|dfs-next\|dfs-prev)`, `--swap-focus`, `--wrap-around` | Swap positions of two windows |
| `join-with` | `(left\|down\|up\|right)` | Wrap focused window and neighbor in container |
| `layout` | `<target-layout>...`, `--root`, `--fail-if-noop` | Change container or window layout |
| `resize` | `(smart\|smart-opposite\|width\|height) [+|-]<n>` | Resize window relative or absolute |
| `workspace` | `<name> \| (next\|prev)`, `--auto-back-and-forth`, `--stdin` | Focus workspace or cycle workspace list |
| `move-node-to-workspace` | `<name> \| (next\|prev)`, `--focus-follows-window` | Move window to target workspace |
| `summon-workspace` | `<workspace>`, `--fail-if-noop` | Pull workspace to focused monitor |
| `focus-monitor` | `(left\|down\|up\|right\|next\|prev \| <pattern>...)` | Focus target display |
| `move-workspace-to-monitor` | `(left\|down\|up\|right\|next\|prev \| <pattern>...)` | Move workspace unless force-assigned |
| `list-windows` | `--monitor <m> \| --workspace <w> \| --all \| --focused`, `--format`, `--json` | Query windows and metadata |
| `list-workspaces` | `--monitor <m> \| --all \| --focused`, `--visible`, `--empty`, `--json` | Query workspaces and state |
| `list-apps` | `--macos-native-hidden [no]`, `--format`, `--json` | List Dock-visible apps and bundle IDs |
| `config` | `--get <name> [--json\|--keys] \| --major-keys \| --all-keys \| --config-path` | Inspect active config path, keys, and modes |
| `reload-config` | `--dry-run`, `--no-gui`, `--warnings-as-errors` | Validate and reload `~/.aerospace.toml` |
| `run-callback` | `on-window-detected [--for-every-window\|--window-id <id>] \| on-focus-changed \| on-focused-monitor-changed` `(v0.21+)` | Re-run config callbacks on demand |
| `subscribe` | `[--all] [--no-send-initial] [<event>...]` `(v0.21+)` | Stream JSON events over socket |
| `eval` | `[--stdin] <aerospace-shell-expr>` `(v0.21+)` | Execute AeroSpace shell pipeline |

## References

Read the curated module matching your task, or use `$SKILL_DIR/references/<module>.md`:

| Module | File | Source | Topics |
| --- | --- | --- | --- |
| Configuration | [configuration](references/configuration.md) | `references/aerospace-raw/001-guide.md` | Install, config discovery, TOML keys, key mapping, modes, shell syntax |
| Tree & Monitors | [tree-workspaces-monitors](references/tree-workspaces-monitors.md) | `references/aerospace-raw/001-guide.md` | Tree containers, layouts, normalizations, virtual workspaces, monitor force assignment |
| CLI Commands | [cli-commands](references/cli-commands.md) | `references/aerospace-raw/002-commands.md` | All 45 subcommands, global options, context flags, interpolation vars |
| Callbacks & IPC | [callbacks-scripting](references/callbacks-scripting.md) | `references/aerospace-raw/001-guide.md` | `on-window-detected`, focus callbacks, env forwarding, `subscribe`, socket protocol |
| Goodies & Tweaks | [goodies-integrations](references/goodies-integrations.md) | `references/aerospace-raw/003-goodies.md` | SketchyBar (`subscribe` & monitor mapping), simple-bar, JankyBorders, macOS defaults, AppleScript, bundle IDs |
| Cheatsheet | [cheatsheet](references/cheatsheet.md) | `references/aerospace-raw/` | Decision rules, CLI quick lookup, minimal TOML snippet, macOS checklist |
| Raw Docs | [aerospace-raw](references/aerospace-raw/) | Converted Markdown & TOML | Complete uncurated guide, commands, goodies, and example configs |

## When to Use Raw Docs

Read `$SKILL_DIR/references/aerospace-raw/` when:

- Curated references omit an obscure flag, interpolation variable, or Apple bundle ID
- You need exact comment wording from `default-config.toml` or `i3-like-config-example.toml`
- A curated table conflicts with CLI behavior — raw docs win

## Deterministic Gates

Verify configuration and runtime state from the command line:

```bash
# Confirm loaded config path and dry-run parse without GUI alerts
aerospace config --config-path && aerospace reload-config --dry-run --no-gui

# Inspect live workspaces and Accessibility window metadata
aerospace list-workspaces --all
aerospace debug-windows
```

## Trade-offs

- **Virtual Workspaces vs Native Spaces**: Emulated workspaces switch with zero animation and bypass the 16-Space cap. Every monitor needs an exposed bottom corner so hidden windows do not bleed onto adjacent screens.
- **Normalizations vs Raw i3 Trees**: Default flattening and orientation flipping keep trees predictable. Disable both flags if you rely on `split` or manual single-child containers.
- **Accessibility API Quirks**: Apps that omit fullscreen buttons or delay window titles can trigger false dialog floats. Pin stubborn apps explicitly with `on-window-detected`.
