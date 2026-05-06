*[ratatui_widgets](../index.md) / [gauge](index.md)*

---

# Module `gauge`

The [`Gauge`](#gauge) widget is used to display a horizontal progress bar.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Gauge`](#gauge) | struct | A widget to display a progress bar. |
| [`LineGauge`](#linegauge) | struct | A compact widget to display a progress bar over a single thin line. |

## Structs

### `Gauge<'a>`

```rust
struct Gauge<'a> {
    // [REDACTED: Private Fields]
}
```

A widget to display a progress bar.

A `Gauge` renders a bar filled according to the value given to `Gauge::percent` or
`Gauge::ratio`. The bar width and height are defined by the [`Rect`](../../ratatui_core/index.md) it is
[rendered](Widget::render) in.

The associated label is always centered horizontally and vertically. If not set with
`Gauge::label`, the label is the percentage of the bar filled.

You might want to have a higher precision bar using `Gauge::use_unicode`.

This can be useful to indicate the progression of a task, like a download.

# Example

```rust
use ratatui::style::{Style, Stylize};
use ratatui::widgets::{Block, Gauge};

Gauge::default()
    .block(Block::bordered().title("Progress"))
    .gauge_style(Style::new().white().on_black().italic())
    .percent(20);
```

# See also

- [`LineGauge`](#linegauge) for a thin progress bar

#### Implementations

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](../block/index.md#block)

  Surrounds the `Gauge` with a [`Block`](../block/index.md).

  

  The gauge is rendered in the inner portion of the block once space for borders and padding

  is reserved. Styles set on the block do **not** affect the bar itself.

- `fn percent(self, percent: u16) -> Self`

  Sets the bar progression from a percentage.

  

  # Panics

  

  This method panics if `percent` is **not** between 0 and 100 inclusively.

  

  # See also

  

  See `Gauge::ratio` to set from a float.

- `fn ratio(self, ratio: f64) -> Self`

  Sets the bar progression from a ratio (float).

  

  `ratio` is the ratio between filled bar over empty bar (i.e. `3/4` completion is `0.75`).

  This is more easily seen as a floating point percentage (e.g. 42% = `0.42`).

  

  # Panics

  

  This method panics if `ratio` is **not** between 0 and 1 inclusively.

  

  # See also

  

  See `Gauge::percent` to set from a percentage.

- `fn label<T>(self, label: T) -> Self`

  Sets the label to display in the center of the bar.

  

  For a left-aligned label, see [`LineGauge`](#linegauge).

  If the label is not defined, it is the percentage filled.

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the widget style.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](../../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

  

  This will style the block (if any non-styled) and background of the widget (everything

  except the bar itself). [`Block`](../block/index.md) style set with `Gauge::block` takes precedence.

- `fn gauge_style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of the bar.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](../../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

- `const fn use_unicode(self, unicode: bool) -> Self`

  Sets whether to use unicode characters to display the progress bar.

  

  This enables the use of

  [unicode block characters](https://en.wikipedia.org/wiki/Block_Elements).

  This is useful to display a higher precision bar (8 extra fractional parts per cell).

#### Trait Implementations

##### `impl AsRef for crate::gauge::Gauge<'a>`

- `fn as_ref(&self) -> &crate::gauge::Gauge<'a>` — [`Gauge`](#gauge)

##### `impl Clone for Gauge<'a>`

- `fn clone(&self) -> Gauge<'a>` — [`Gauge`](#gauge)

##### `impl Debug for Gauge<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Gauge<'a>`

- `fn default() -> Gauge<'a>` — [`Gauge`](#gauge)

##### `impl IntoEither for Gauge<'a>`

##### `impl PartialEq for Gauge<'a>`

- `fn eq(&self, other: &Gauge<'a>) -> bool` — [`Gauge`](#gauge)

##### `impl StructuralPartialEq for Gauge<'a>`

##### `impl Styled for Gauge<'_>`

- `type Item = Gauge<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Gauge<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for Gauge<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

### `LineGauge<'a>`

```rust
struct LineGauge<'a> {
    // [REDACTED: Private Fields]
}
```

A compact widget to display a progress bar over a single thin line.

This can be useful to indicate the progression of a task, like a download.

A `LineGauge` renders a line filled with symbols defined by `LineGauge::filled_symbol` and
`LineGauge::unfilled_symbol` according to the value given to `LineGauge::ratio`.
Unlike [`Gauge`](#gauge), only the width can be defined by the [rendering](Widget::render) [`Rect`](../../ratatui_core/index.md). The
height is always 1.

The associated label is always left-aligned. If not set with `LineGauge::label`, the label is
the percentage of the bar filled.

You can also set the symbols used to draw the bar with `LineGauge::line_set`.

To style the gauge line use `LineGauge::filled_style` and `LineGauge::unfilled_style` which
let you pick a color for foreground (i.e. line) and background of the filled and unfilled part
of gauge respectively.

# Examples:

```rust
use ratatui::style::{Style, Stylize};
use ratatui::symbols;
use ratatui::widgets::{Block, LineGauge};

LineGauge::default()
    .block(Block::bordered().title("Progress"))
    .filled_style(Style::new().white().on_black().bold())
    .filled_symbol(symbols::line::THICK_HORIZONTAL)
    .ratio(0.4);
```

# See also

- [`Gauge`](#gauge) for bigger, higher precision and more configurable progress bar

#### Implementations

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](../block/index.md#block)

  Surrounds the `LineGauge` with a [`Block`](../block/index.md).

- `fn ratio(self, ratio: f64) -> Self`

  Sets the bar progression from a ratio (float).

  

  `ratio` is the ratio between filled bar over empty bar (i.e. `3/4` completion is `0.75`).

  This is more easily seen as a floating point percentage (e.g. 42% = `0.42`).

  

  # Panics

  

  This method panics if `ratio` is **not** between 0 and 1 inclusively.

- `const fn line_set(self, set: symbols::line::Set<'a>) -> Self`

  Sets the characters to use for the line.

  

  # See also

  

  See [`symbols::line::Set`](../../ratatui_core/symbols/block/index.md) for more information. Predefined sets are also available, see

  [`NORMAL`](symbols::line::NORMAL), [`DOUBLE`](symbols::line::DOUBLE) and

  [`THICK`](symbols::line::THICK).

- `const fn filled_symbol(self, symbol: &'a str) -> Self`

  Sets the symbol for the filled part of the gauge.

- `const fn unfilled_symbol(self, symbol: &'a str) -> Self`

  Sets the symbol for the unfilled part of the gauge.

- `fn label<T>(self, label: T) -> Self`

  Sets the label to display.

  

  With `LineGauge`, labels are only on the left, see [`Gauge`](#gauge) for a centered label.

  If the label is not defined, it is the percentage filled.

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the widget style.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](../../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

  

  This will style everything except the bar itself, so basically the block (if any) and

  background.

- `fn gauge_style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of the bar.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](../../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

- `fn filled_style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of filled part of the bar.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](../../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

- `fn unfilled_style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of the unfilled part of the bar.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](../../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

#### Trait Implementations

##### `impl AsRef for crate::gauge::LineGauge<'a>`

- `fn as_ref(&self) -> &crate::gauge::LineGauge<'a>` — [`LineGauge`](#linegauge)

##### `impl Clone for LineGauge<'a>`

- `fn clone(&self) -> LineGauge<'a>` — [`LineGauge`](#linegauge)

##### `impl Debug for LineGauge<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for LineGauge<'_>`

- `fn default() -> Self`

##### `impl IntoEither for LineGauge<'a>`

##### `impl PartialEq for LineGauge<'a>`

- `fn eq(&self, other: &LineGauge<'a>) -> bool` — [`LineGauge`](#linegauge)

##### `impl StructuralPartialEq for LineGauge<'a>`

##### `impl Styled for LineGauge<'_>`

- `type Item = LineGauge<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for LineGauge<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for LineGauge<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

