# Crate `ratatui_widgets`

**ratatui-widgets** contains all the widgets that were previously part of the [Ratatui] crate.
It is meant to be used in conjunction with `ratatui`, which provides the core functionality for
building terminal user interfaces.

Most applications shouldn't need to depend directly on `ratatui-widgets`, `ratatui` crate
re-exports all the widgets from this crate. However, if you are building a widget library that
internally uses these widgets, or if you prefer finer grained dependencies, you may want to
depend on this crate rather than transitively through the `ratatui` crate.

Previously, a crate named `ratatui-widgets` was published with some formative ideas about an
eventual Ratatui framework. That crate has now moved to [tui-framework-experiment], pending a
new name.

# Installation

Run the following command to add this crate to your project:

```sh
cargo add ratatui-widgets
```

# Available Widgets

- [`BarChart`](barchart.md): displays multiple datasets as bars with optional grouping.
- [`Block`](block.md): a basic widget that draws a block with optional borders, titles, and styles.
- `calendar::Monthly`: displays a single month.
- [`Canvas`](canvas.md): draws arbitrary shapes using drawing characters.
- [`Chart`](chart.md): displays multiple datasets as lines or scatter graphs.
- [`Clear`](clear.md): clears the area it occupies. Useful to render over previously drawn widgets.
- [`Fill`](fill.md): paints every cell in its area with a single repeated symbol and style.
- [`Gauge`](gauge.md): displays progress percentage using block characters.
- [`LineGauge`](gauge.md): displays progress as a line.
- [`List`](list.md): displays a list of items and allows selection.
- [`RatatuiLogo`](logo.md): displays the Ratatui logo.
- [`RatatuiMascot`](mascot.md): displays the Ratatui mascot.
- [`Paragraph`](paragraph.md): displays a paragraph of optionally styled and wrapped text.
- [`Scrollbar`](scrollbar.md): displays a scrollbar.
- [`Sparkline`](sparkline.md): displays a single dataset as a sparkline.
- [`Table`](table.md): displays multiple rows and columns in a grid and allows selection.
- [`Tabs`](tabs.md): displays a tab bar and allows selection.

All these widgets are re-exported directly under `ratatui::widgets` in the `ratatui` crate.

# Crate Organization

`ratatui-widgets` is part of the Ratatui workspace that was modularized in version 0.30.0.
This crate contains all the built-in widget implementations that were previously part of the
main `ratatui` crate.

**When to use `ratatui-widgets`:**

- Building widget libraries that need to compose with built-in widgets
- You want finer-grained dependencies and only need specific widgets
- Creating custom widgets that extend or wrap the built-in ones

**When to use the main `ratatui` crate:**

- Building applications (recommended - includes everything you need)
- You want the convenience of having all widgets available

For detailed information about the workspace organization, see [ARCHITECTURE.md].

# Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub. For more
details on contributing, please see the [CONTRIBUTING](CONTRIBUTING.md) document.

# License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## Contents

- [Modules](#modules)
  - [`barchart`](#barchart)
  - [`block`](#block)
  - [`borders`](#borders)
  - [`canvas`](#canvas)
  - [`chart`](#chart)
  - [`clear`](#clear)
  - [`fill`](#fill)
  - [`gauge`](#gauge)
  - [`list`](#list)
  - [`logo`](#logo)
  - [`mascot`](#mascot)
  - [`paragraph`](#paragraph)
  - [`scrollbar`](#scrollbar)
  - [`sparkline`](#sparkline)
  - [`table`](#table)
  - [`tabs`](#tabs)
  - [`calendar`](#calendar)
- [Macros](#macros)
  - [`border!`](#border)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`barchart`](#barchart) | mod | The [`BarChart`] widget and its related types (e.g. [`Bar`], [`BarGroup`]). |
| [`block`](#block) | mod | Elements related to the `Block` base widget. |
| [`borders`](#borders) | mod | Border related types ([`Borders`], [`BorderType`]) and a macro to create borders ([`border`]). |
| [`canvas`](#canvas) | mod | A [`Canvas`] and a collection of [`Shape`]s. |
| [`chart`](#chart) | mod | The [`Chart`] widget is used to plot one or more [`Dataset`] in a cartesian coordinate system. |
| [`clear`](#clear) | mod | The [`Clear`] widget allows you to clear a certain area to allow overdrawing (e.g. for popups). |
| [`fill`](#fill) | mod | The [`Fill`] widget paints every cell in its area with a single symbol and style. |
| [`gauge`](#gauge) | mod | The [`Gauge`] widget is used to display a horizontal progress bar. |
| [`list`](#list) | mod | The [`List`] widget is used to display a list of items and allows selecting one or multiple items. |
| [`logo`](#logo) | mod | The [`RatatuiLogo`] widget renders the Ratatui logo. |
| [`mascot`](#mascot) | mod | A Ratatui mascot widget |
| [`paragraph`](#paragraph) | mod | The [`Paragraph`] widget and related types allows displaying a block of text with optional wrapping, alignment, and block styling. |
| [`scrollbar`](#scrollbar) | mod | The [`Scrollbar`] widget is used to display a scrollbar alongside other widgets. |
| [`sparkline`](#sparkline) | mod | The [`Sparkline`] widget is used to display a sparkline over one or more lines. |
| [`table`](#table) | mod | The [`Table`] widget is used to display multiple rows and columns in a grid and allows selecting one or multiple cells. |
| [`tabs`](#tabs) | mod | The [`Tabs`] widget displays a horizontal set of tabs with a single tab selected. |
| [`calendar`](#calendar) | mod | A simple calendar widget. |
| [`border!`](#border) | macro | Macro that constructs and returns a combination of the [`Borders`] object from TOP, BOTTOM, LEFT and RIGHT. |

## Modules

- [`barchart`](barchart.md) — The [`BarChart`] widget and its related types (e.g. [`Bar`], [`BarGroup`]).
- [`block`](block.md) — Elements related to the `Block` base widget.
- [`borders`](borders.md) — Border related types ([`Borders`], [`BorderType`]) and a macro to create borders ([`border`]).
- [`canvas`](canvas.md) — A [`Canvas`] and a collection of [`Shape`]s.
- [`chart`](chart.md) — The [`Chart`] widget is used to plot one or more [`Dataset`] in a cartesian coordinate system.
- [`clear`](clear.md) — The [`Clear`] widget allows you to clear a certain area to allow overdrawing (e.g. for popups).
- [`fill`](fill.md) — The [`Fill`] widget paints every cell in its area with a single symbol and style.
- [`gauge`](gauge.md) — The [`Gauge`] widget is used to display a horizontal progress bar.
- [`list`](list.md) — The [`List`] widget is used to display a list of items and allows selecting one or multiple
- [`logo`](logo.md) — The [`RatatuiLogo`] widget renders the Ratatui logo.
- [`mascot`](mascot.md) — A Ratatui mascot widget
- [`paragraph`](paragraph.md) — The [`Paragraph`] widget and related types allows displaying a block of text with optional
- [`scrollbar`](scrollbar.md) — The [`Scrollbar`] widget is used to display a scrollbar alongside other widgets.
- [`sparkline`](sparkline.md) — The [`Sparkline`] widget is used to display a sparkline over one or more lines.
- [`table`](table.md) — The [`Table`] widget is used to display multiple rows and columns in a grid and allows selecting
- [`tabs`](tabs.md) — The [`Tabs`] widget displays a horizontal set of tabs with a single tab selected.
- [`calendar`](calendar.md) — A simple calendar widget. `(feature: widget-calendar)`

## Macros

### `border!`

Macro that constructs and returns a combination of the [`Borders`](borders.md) object from TOP, BOTTOM, LEFT
and RIGHT.

When used with NONE you should consider omitting this completely. For ALL you should consider
[`Block::bordered()`](crate::block::Block::bordered) instead.

## Examples

```rust
use ratatui::border;
use ratatui::widgets::Block;

Block::new()
    .title("Construct Borders and use them in place")
    .borders(border!(TOP, BOTTOM));
```

`border!` can be called with any number of individual sides:

```rust
use ratatui::border;
use ratatui::widgets::Borders;
let right_open = border!(TOP, LEFT, BOTTOM);
assert_eq!(right_open, Borders::TOP | Borders::LEFT | Borders::BOTTOM);
```

Single borders work but using `Borders::` directly would be simpler.

```rust
use ratatui::border;
use ratatui::widgets::Borders;

assert_eq!(border!(TOP), Borders::TOP);
assert_eq!(border!(ALL), Borders::ALL);
assert_eq!(border!(), Borders::NONE);
```

