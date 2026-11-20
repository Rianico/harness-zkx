---
name: tauri
description: >-
  Tauri 2.0 app guide: setup, IPC commands, Rust traits, windowing, capabilities, and plugins. Use when scaffolding Tauri apps, writing #[tauri::command] handlers, or configuring permissions.
metadata:
  managed-by: toolchain-wiki
argument-hint: |-
  '[topic]'
---

# Tauri

> **2.0.0** (Tauri v2) — <https://v2.tauri.app/> — package `@tauri-apps/api`, crate `tauri`

Tauri 2.0 builds cross-platform desktop and mobile applications with native webview rendering and a Rust core process.

Pair web frontend tooling (`pnpm`, `Vite`, `TypeScript`) with Rust backend systems.

## Quick Start

Create a new application or initialize Tauri in an existing web project:

```bash
# Initialize a new Tauri project
pnpm create tauri-app

# Run development server with live reload
pnpm tauri dev

# Build production bundle
pnpm tauri build
```

The application directory separates frontend assets from native backend code:

```
├── src/                # Frontend application code (TypeScript, HTML, CSS)
├── src-tauri/          # Native Rust backend project
│   ├── Cargo.toml      # Rust crate dependencies and plugins
│   ├── capabilities/   # Window permission ACL configuration files
│   ├── tauri.conf.json # Build configuration, bundle settings, and windows
│   └── src/
│       ├── lib.rs      # Application setup, plugin registration, and command routing
│       └── main.rs     # Binary entry point
└── package.json        # Frontend scripts and @tauri-apps dependencies
```

## Core Concepts

1. **Process Model**: A privileged Rust core process coordinates one or more sandboxed webview processes.
2. **Commands**: Annotated Rust functions (`#[tauri::command]`) called from JavaScript via `invoke`.
3. **Managed State**: Shared data structures managed via `app.manage()` and accessed in commands using `tauri::State`.
4. **Rust Traits**: Core functionality relies on `tauri::Manager`, `tauri::Emitter`, and `tauri::Listener`.
5. **Capabilities ACL**: JSON files map explicit permissions to target windows and webviews.
6. **Plugin Ecosystem**: Official modular plugins (`@tauri-apps/plugin-*`) expose native device capabilities.

## Trait Import Invariant

In Rust, methods defined on traits require the trait in lexical scope.

Calling methods such as `app.get_webview_window()` or `app.emit()` without their traits causes compile errors:

```rust
// Required trait imports for core application operations
use tauri::{Emitter, Listener, Manager};
```

Import `Manager` for state and window lookup. Import `Emitter` and `Listener` for event communication.

## Dispatch

Read the reference module that matches your task:

| Domain | Reference File | Scope |
| ------ | -------------- | ----- |
| Architecture & Lifecycle | [architecture-lifecycle](references/architecture-lifecycle.md) | Process isolation, `tauri::Builder`, setup hook, `AppHandle`, and Tokio runtime |
| IPC & Commands | [ipc-commands](references/ipc-commands.md) | `#[tauri::command]`, arguments, return types, error handling, `State`, and `invoke()` |
| Rust Traits & APIs | [rust-traits-apis](references/rust-traits-apis.md) | `Manager`, `Emitter`, `Listener`, window management, native menus, and tray |
| Security & Capabilities | [security-capabilities](references/security-capabilities.md) | Capabilities JSON, permission identifiers, file scopes, and CSP configuration |
| Configuration & CLI | [configuration-cli](references/configuration-cli.md) | `tauri.conf.json` v2 schema, `tauri dev`, `tauri build`, and `tauri icon` |
| Plugins | [plugins](references/plugins.md) | Official plugin catalog, registration patterns, and custom plugin development |
| Cheatsheet | [cheatsheet](cheatsheet.md) | Quick lookup tables, commands, code patterns, and trait matrices |
| Raw Documentation | [tauri-raw](references/tauri-raw/) | Full uncurated upstream documentation snapshot |

## Deterministic Gates

Verify application contracts and builds using deterministic commands:

```bash
# Check Rust backend syntax and types
cargo check --manifest-path src-tauri/Cargo.toml

# Validate system environment and dependencies
pnpm tauri info

# Validate frontend types
pnpm run typecheck

# Build application in debug mode
pnpm tauri build --debug
```

## Trade-offs

- **System Webview vs Bundled Engine**: Tauri uses OS webviews to achieve tiny binary sizes. Developers must test rendering across Windows WebView2, macOS WKWebView, and Linux WebKitGTK.
- **Granular ACL vs Fast Prototyping**: App commands registered via `invoke_handler` are permitted by default. Core and plugin commands require explicit ACL permissions unless configured otherwise. Unauthorized commands reject the frontend invoke Promise with a permission error.
- **Rust Backend vs Node Runtime**: Rust provides memory safety and concurrency. Backend features require Rust familiarity or existing Tauri plugins.
