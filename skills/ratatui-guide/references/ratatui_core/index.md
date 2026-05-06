# Crate `ratatui_core`

**ratatui-core** is the core library of the [`ratatui`](../ratatui/index.md) project,
providing the essential building blocks for creating rich terminal user interfaces in Rust.

# Why `ratatui-core`?

The `ratatui-core` crate is split from the main [`ratatui`](https://crates.io/crates/ratatui)
crate to offer better stability for widget library authors and advanced integrations. Widget
libraries should generally depend on `ratatui-core`, benefiting from a stable API and reducing
the need for frequent updates.

Most applications, on the other hand, should depend on the main `ratatui` crate, which
includes built-in widgets, backend re-exports, and higher-level setup helpers.

In practice:

- Use `ratatui` to build applications.
- Use `ratatui-core` to implement widgets, backend integrations, or other code that needs the
  core rendering and layout contracts directly.

# Installation

Add `ratatui-core` to your `Cargo.toml`:

```shell
cargo add ratatui-core
```

# Crate Organization

`ratatui-core` is part of the Ratatui workspace that was modularized in version 0.30.0 to
improve compilation times, API stability, and dependency management. This crate provides the
foundational types and traits that other crates in the workspace depend on.

**When to use `ratatui-core`:**

- Building widget libraries that implement [`Widget`](#widget) or [`StatefulWidget`](#statefulwidget)
- Building custom integrations on top of Ratatui's core rendering contracts
- You want minimal dependencies and faster compilation times
- You need maximum API stability (core types change less frequently)

**When to use the main `ratatui` crate:**

- Building applications
- You want built-in widgets, backend re-exports, and setup helpers such as `ratatui::run`

For detailed information about the workspace organization, see [ARCHITECTURE.md].

# Contributing

We welcome contributions from the community! Please see our [CONTRIBUTING](../CONTRIBUTING.md)
guide for more details on how to get involved.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## Contents

- [Modules](#modules)
  - [`backend`](#backend)
  - [`buffer`](#buffer)
  - [`layout`](#layout)
  - [`style`](#style)
  - [`symbols`](#symbols)
  - [`terminal`](#terminal)
  - [`text`](#text)
  - [`widgets`](#widgets)
- [Macros](#macros)
  - [`assert_buffer_eq!`](#assert-buffer-eq)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`backend`](#backend) | mod | This module provides the backend implementations for different terminal libraries. |
| [`buffer`](#buffer) | mod | A module for the [`Buffer`] and [`Cell`] types. |
| [`layout`](#layout) | mod | Layout and positioning in terminal user interfaces. |
| [`style`](#style) | mod | `style` contains the primitives used to control how your user interface will look. |
| [`symbols`](#symbols) | mod | Symbols and markers for drawing various widgets. |
| [`terminal`](#terminal) | mod | Provides the [`Terminal`], [`Frame`], [`CompletedFrame`], and [`Viewport`] types. |
| [`text`](#text) | mod | Primitives for styled text. |
| [`widgets`](#widgets) | mod | The `widgets` module contains the `Widget` and `StatefulWidget` traits, which are used to render UI elements on the screen. |
| [`assert_buffer_eq!`](#assert-buffer-eq) | macro | Assert that two buffers are equal by comparing their areas and content. |

## Modules

- [`backend`](backend/index.md) — This module provides the backend implementations for different terminal libraries.
- [`buffer`](buffer/index.md) — A module for the [`Buffer`] and [`Cell`] types.
- [`layout`](layout/index.md) — Layout and positioning in terminal user interfaces.
- [`style`](style/index.md) — `style` contains the primitives used to control how your user interface will look.
- [`symbols`](symbols/index.md) — Symbols and markers for drawing various widgets.
- [`terminal`](terminal/index.md) — Provides the [`Terminal`], [`Frame`], [`CompletedFrame`], and [`Viewport`] types.
- [`text`](text/index.md) — Primitives for styled text.
- [`widgets`](widgets/index.md) — The `widgets` module contains the `Widget` and `StatefulWidget` traits, which are used to

## Macros

### `assert_buffer_eq!`

Assert that two buffers are equal by comparing their areas and content.

# Panics
When the buffers differ this method panics and displays the differences similar to
`assert_eq!()`.

