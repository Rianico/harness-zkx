---
name: sketchybar
description: >-
  SketchyBar macOS status bar guide: bar layout, items, components, events, popups, animations, and querying. Use when configuring sketchybarrc, writing plugin scripts, or debugging bar items and events.
metadata:
  managed-by: toolchain-wiki
argument-hint: |-
  '[topic]'
disable-model-invocation: true
---

# SketchyBar

> **v2.24.1** (2026-10-09) — <https://felixkratz.github.io/SketchyBar/> — macOS `sketchybar` CLI

SketchyBar is a dynamic, command-driven macOS status bar daemon.
An executable startup script at `~/.config/sketchybar/sketchybarrc` builds the bar, sets item defaults, registers items, and binds event-driven shell or Mach plugins.
Every bar element can be queried, mutated, animated, or removed at runtime through `sketchybar` CLI calls.

## Quick Start

Install SketchyBar and Nerd Font icons, copy the starter files, and mark plugins executable:

```bash
brew tap FelixKratz/formulae
brew install sketchybar
brew install --cask font-hack-nerd-font

mkdir -p ~/.config/sketchybar/plugins
cp "$(brew --prefix)/share/sketchybar/examples/sketchybarrc" ~/.config/sketchybar/sketchybarrc
cp -r "$(brew --prefix)/share/sketchybar/examples/plugins/" ~/.config/sketchybar/plugins/
chmod +x ~/.config/sketchybar/sketchybarrc ~/.config/sketchybar/plugins/*.sh
```

Start as a login service, or run directly in the foreground (never run both at once):

```bash
brew services start sketchybar   # Option 1: background login service
sketchybar                       # Option 2: foreground debug output
```

## Core Concepts

1. **Bar & Defaults:** `--bar` sets global geometry and blur, while `--default` sets inherited defaults for items added afterward.
2. **Items & Positions:** `--add item <name> <pos>` places items at `left`, `right`, `center`, `q` (left of notch), or `e` (right of notch).
3. **Special Components & Popups:** `space`, `bracket`, `alias`, `slider`, and `graph` extend items with specialized behavior. Every item also owns a `popup.<name>` dropdown namespace.
4. **Event-Driven Scripting:** `--subscribe <name> <event>` runs `script` with `$NAME`, `$SENDER`, `$CONFIG_DIR`, and `$BAR_NAME` (plus event-specific `$INFO`) on state transitions.
5. **Batching & Animations:** Combining flags in bash arrays avoids intermediate redraws, while `--animate <curve> <frames>` interpolates integer and ARGB properties at 60Hz.

## Key Invariants

- Enable **Displays have separate Spaces** in macOS **System Settings -> Desktop & Dock** before launching SketchyBar.
- Set executable permissions (`chmod +x`) on `sketchybarrc` and every plugin script, and reference scripts by absolute path (`$CONFIG_DIR/plugins/...`).
- Never call `sketchybar --update` inside an item plugin script because it triggers recursive script execution.
- Remove trailing spaces after `\` line continuations in `sketchybarrc` so Bash parses batched flags intact.
- Use 8-digit ARGB hex colors (`0xAARRGGBB`) rather than 6-digit RGB values.

## Common Patterns

### Batched Bar and Defaults Array

```bash
PLUGIN_DIR="$CONFIG_DIR/plugins"

bar=(
  position=top
  height=36
  blur_radius=30
  color=0x40000000
)
sketchybar --bar "${bar[@]}"

default=(
  padding_left=5
  padding_right=5
  icon.font="Hack Nerd Font:Bold:17.0"
  label.font="Hack Nerd Font:Bold:14.0"
  icon.color=0xffffffff
  label.color=0xffffffff
)
sketchybar --default "${default[@]}"
```

### Event-Subscribed Item and Plugin

```bash
sketchybar --add item front_app left \
           --set front_app icon.drawing=off script="$PLUGIN_DIR/front_app.sh" \
           --subscribe front_app front_app_switched
```

```sh
#!/bin/sh
# ~/.config/sketchybar/plugins/front_app.sh
if [ "$SENDER" = "front_app_switched" ]; then
  sketchybar --set "$NAME" label="$INFO"
fi
```

### Popup Toggle and Animated Property Update

```bash
sketchybar --add item menu left \
           --set menu icon= popup.align=left \
                      click_script="sketchybar --set \$NAME popup.drawing=toggle" \
           --add item menu.prefs popup.menu \
           --set menu.prefs label="Settings"

sketchybar --animate sin 15 --set menu background.color=0x88334455
```

## Dispatch

Read the reference module that matches the task.
Prose guidance uses `$SKILL_DIR/references/<module>.md`, and links below resolve directly:

| Domain | Reference File | Scope |
| :--- | :--- | :--- |
| Bar & Setup | [bar-setup](references/bar-setup.md) | Homebrew setup, macOS prerequisites, fonts, `--bar` options, `--reload`, `--hotload`, and multi-bar symlinks |
| Items & Properties | [items-properties](references/items-properties.md) | `--add`, `--set`, `--default`, `--clone`, `--move`, `--reorder`, regex targets, text/background/image/shadow properties, and types |
| Components & Popups | [components-popups](references/components-popups.md) | `space`, `bracket`, `alias`, `slider`, `graph`, and `popup.<name>` menus |
| Events & Scripting | [events-scripting](references/events-scripting.md) | Built-in events, `$SENDER`, `$INFO`, custom `NSDistributedNotificationCenter` events, and starter plugins |
| Animations, Querying & Tricks | [animations-querying-tricks](references/animations-querying-tricks.md) | `--animate` curves and chaining, `--query` JSON commands, array batching, performance, and debugging |
| Cheatsheet | [cheatsheet](cheatsheet.md) | Decision rules, CLI command quick lookup, and event environment matrix |
| Raw Documentation | [sketchybar-raw](references/sketchybar-raw/) | Uncurated upstream docs and starter examples snapshot |

## When to Use Raw Docs

Read `$SKILL_DIR/references/sketchybar-raw/` when:

- Curated references omit an exact flag, default value, or component edge case.
- You need the full starter `sketchybarrc` or plugin scripts in `_supplementary/supplementary/default-examples.md`.
- Curated text conflicts with observed CLI behavior, because raw upstream docs are authoritative.

## Deterministic Gates

Verify configuration syntax, executable bits, and live state with deterministic commands:

```bash
# 1. Check bash syntax of sketchybarrc and every plugin script
bash -n ~/.config/sketchybar/sketchybarrc && \
(for f in ~/.config/sketchybar/plugins/*.sh; do [ -e "$f" ] || break; bash -n "$f" || exit 1; done)

# 2. Verify executable permissions on config and every plugin script
test -x ~/.config/sketchybar/sketchybarrc && \
(for f in ~/.config/sketchybar/plugins/*.sh; do [ -e "$f" ] || break; test -x "$f" || exit 1; done)

# 3. Inspect live bar and event state
sketchybar --query bar >/dev/null && sketchybar --query events >/dev/null
```

For manual foreground debugging, the operator may stop the login service (`brew services stop sketchybar`) and run `sketchybar` interactively.

## Trade-offs

- **Event Subscriptions vs `update_freq` Polling:** Subscribing to macOS events runs scripts only when values change. Polling with `update_freq` wastes CPU on idle desktops.
- **Shell Plugins vs `mach_helper`:** Shell scripts are simple to edit and reload. Compiled `mach_helper` binaries cut process-spawn latency for high-frequency items.
- **Native Menu Bar Coexistence vs `alias` Mirroring:** Auto-hiding the macOS bar while adding `alias` items preserves tray applets without losing custom bar aesthetics. Each alias needs Screen Recording permission and polls continuously if its app exits.
