*[ratatui_widgets](./index.md) / [sparkline](#)*

---

# Module `sparkline`

The [`Sparkline`](#sparkline) widget is used to display a sparkline over one or more lines.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Sparkline`](#sparkline) | struct | Widget to render a sparkline over one or more lines. |
| [`SparklineBar`](#sparklinebar) | struct | An bar in a `Sparkline`. |
| [`RenderDirection`](#renderdirection) | enum | Defines the direction in which sparkline will be rendered. |

## Structs

### `Sparkline<'a>`

```rust
struct Sparkline<'a> {
    // [REDACTED: Private Fields]
}
```

Widget to render a sparkline over one or more lines.

Each bar in a `Sparkline` represents a value from the provided dataset. The height of the bar
is determined by the value in the dataset.

You can create a `Sparkline` using `Sparkline::default`.

The data is set using `Sparkline::data`. The data can be a slice of `u64`, `Option<u64>`, or a
[`SparklineBar`](#sparklinebar).  For the `Option<u64>` and [`SparklineBar`](#sparklinebar) cases, a data point with a value
of `None` is interpreted an as the _absence_ of a value.

`Sparkline` can be styled either using `Sparkline::style` or preferably using the methods
provided by the [`Stylize`](ratatui_core::style::Stylize) trait.  The style may be set for the
entire widget or for individual bars by setting individual `SparklineBar::style`.

The bars are rendered using a set of symbols. The default set is [`symbols::bar::NINE_LEVELS`](../ratatui_core/symbols/bar.md).
You can change the set using `Sparkline::bar_set`.

If the data provided is a slice of `u64` or `Option<u64>`, the bars will be styled with the
style of the sparkline. If the data is a slice of [`SparklineBar`](#sparklinebar), the bars will be
styled with the style of the sparkline combined with the style provided in the [`SparklineBar`](#sparklinebar)
if it is set, otherwise the sparkline style will be used.

Absent values and will be rendered with the style set by `Sparkline::absent_value_style` and
the symbol set by `Sparkline::absent_value_symbol`.

# Setter methods

- `Sparkline::block` wraps the sparkline in a [`Block`](./block.md)
- `Sparkline::data` defines the dataset, you'll almost always want to use it
- `Sparkline::max` sets the maximum value of bars
- `Sparkline::direction` sets the render direction

# Examples

```rust
use ratatui::style::{Color, Style, Stylize};
use ratatui::symbols;
use ratatui::widgets::{Block, RenderDirection, Sparkline};

Sparkline::default()
    .block(Block::bordered().title("Sparkline"))
    .data(&[0, 2, 3, 4, 1, 4, 10])
    .max(5)
    .direction(RenderDirection::RightToLeft)
    .style(Style::default().red().on_white())
    .absent_value_style(Style::default().fg(Color::Red))
    .absent_value_symbol(symbols::shade::FULL);
```

#### Implementations

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](./block.md#block)

  Wraps the sparkline with the given `block`.

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of the entire widget.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  The foreground corresponds to the bars while the background is everything else.

- `fn absent_value_style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style to use for absent values.

  

  Absent values are values in the dataset that are `None`.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  The foreground corresponds to the bars while the background is everything else.

- `fn absent_value_symbol(self, symbol: impl Into<String>) -> Self`

  Sets the symbol to use for absent values.

  

  Absent values are values in the dataset that are `None`.

  

  The default is [`symbols::shade::EMPTY`](../ratatui_core/symbols/border.md).

- `fn data<T>(self, data: T) -> Self`

  Sets the dataset for the sparkline.

  

  Each item in the dataset is a bar in the sparkline. The height of the bar is determined by

  the value in the dataset.

  

  The data can be a slice of `u64`, `Option<u64>`, or a [`SparklineBar`](#sparklinebar).  For the

  `Option<u64>` and [`SparklineBar`](#sparklinebar) cases, a data point with a value of `None` is

  interpreted an as the _absence_ of a value.

  

  If the data provided is a slice of `u64` or `Option<u64>`, the bars will be styled with the

  style of the sparkline. If the data is a slice of [`SparklineBar`](#sparklinebar), the bars will be

  styled with the style of the sparkline combined with the style provided in the

  [`SparklineBar`](#sparklinebar) if it is set, otherwise the sparkline style will be used.

  

  Absent values and will be rendered with the style set by `Sparkline::absent_value_style`

  and the symbol set by `Sparkline::absent_value_symbol`.

  

  # Examples

  

  Create a `Sparkline` from a slice of `u64`:

  

  ```rust

  use ratatui::Frame;

  use ratatui::layout::Rect;

  use ratatui::widgets::Sparkline;

  

  fn ui(frame: &mut Frame) {

  let area = Rect::default();

  let sparkline = Sparkline::default().data(&[1, 2, 3]);

  frame.render_widget(sparkline, area);

  }

  ```

  

  Create a `Sparkline` from a slice of `Option<u64>` such that some bars are absent:

  

  ```rust

  use ratatui::{prelude::*, widgets::*};

  fn ui(frame: &mut Frame) {

  let area = Rect::default();

  let data = vec![Some(1), None, Some(3)];

  let sparkline = Sparkline::default().data(data);

  frame.render_widget(sparkline, area);

  }

  ```

  

  Create a [`Sparkline`](#sparkline) from a a Vec of [`SparklineBar`](#sparklinebar) such that some bars are styled:

  

  ```rust

  use ratatui::{prelude::*, widgets::*};

  fn ui(frame: &mut Frame) {

  let area = Rect::default();

  let data = vec![

      SparklineBar::from(1).style(Some(Style::default().fg(Color::Red))),

      SparklineBar::from(2),

      SparklineBar::from(3).style(Some(Style::default().fg(Color::Blue))),

  ];

  let sparkline = Sparkline::default().data(data);

  frame.render_widget(sparkline, area);

  }

  ```

- `const fn max(self, max: u64) -> Self`

  Sets the maximum value of bars.

  

  Every bar will be scaled accordingly. If no max is given, this will be the max in the

  dataset.

- `const fn bar_set(self, bar_set: symbols::bar::Set<'a>) -> Self`

  Sets the characters used to display the bars.

  

  Can be [`symbols::bar::THREE_LEVELS`](../ratatui_core/symbols/block.md), [`symbols::bar::NINE_LEVELS`](../ratatui_core/symbols/bar.md) (default) or a custom

  [`Set`](symbols::bar::Set).

- `const fn direction(self, direction: RenderDirection) -> Self` — [`RenderDirection`](#renderdirection)

  Sets the direction of the sparkline.

  

  [`RenderDirection::LeftToRight`](./index.md) by default.

#### Trait Implementations

##### `impl AsRef for crate::sparkline::Sparkline<'a>`

- `fn as_ref(&self) -> &crate::sparkline::Sparkline<'a>` — [`Sparkline`](#sparkline)

##### `impl Clone for Sparkline<'a>`

- `fn clone(&self) -> Sparkline<'a>` — [`Sparkline`](#sparkline)

##### `impl Debug for Sparkline<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Sparkline<'a>`

- `fn default() -> Sparkline<'a>` — [`Sparkline`](#sparkline)

##### `impl Eq for Sparkline<'a>`

##### `impl<K> Equivalent for Sparkline<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl IntoEither for Sparkline<'a>`

##### `impl PartialEq for Sparkline<'a>`

- `fn eq(&self, other: &Sparkline<'a>) -> bool` — [`Sparkline`](#sparkline)

##### `impl StructuralPartialEq for Sparkline<'a>`

##### `impl Styled for Sparkline<'_>`

- `type Item = Sparkline<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Sparkline<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for Sparkline<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

### `SparklineBar`

```rust
struct SparklineBar {
    // [REDACTED: Private Fields]
}
```

An bar in a `Sparkline`.

The height of the bar is determined by the value and a value of `None` is interpreted as the
_absence_ of a value, as distinct from a value of `Some(0)`.

#### Implementations

- `fn style<S: Into<Option<Style>>>(self, style: S) -> Self`

  Sets the style of the bar.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  If not set, the default style of the sparkline will be used.

  

  As well as the style of the sparkline, each [`SparklineBar`](#sparklinebar) may optionally set its own

  style.  If set, the style of the bar will be the style of the sparkline combined with

  the style of the bar.

#### Trait Implementations

##### `impl Clone for SparklineBar`

- `fn clone(&self) -> SparklineBar` — [`SparklineBar`](#sparklinebar)

##### `impl Copy for SparklineBar`

##### `impl Debug for SparklineBar`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for SparklineBar`

- `fn default() -> SparklineBar` — [`SparklineBar`](#sparklinebar)

##### `impl Eq for SparklineBar`

##### `impl<K> Equivalent for SparklineBar`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl IntoEither for SparklineBar`

##### `impl PartialEq for SparklineBar`

- `fn eq(&self, other: &SparklineBar) -> bool` — [`SparklineBar`](#sparklinebar)

##### `impl StructuralPartialEq for SparklineBar`

## Enums

### `RenderDirection`

```rust
enum RenderDirection {
    LeftToRight,
    RightToLeft,
}
```

Defines the direction in which sparkline will be rendered.

See `Sparkline::direction`.

#### Variants

- **`LeftToRight`**

  The first value is on the left, going to the right

- **`RightToLeft`**

  The first value is on the right, going to the left

#### Trait Implementations

##### `impl Clone for RenderDirection`

- `fn clone(&self) -> RenderDirection` — [`RenderDirection`](#renderdirection)

##### `impl Copy for RenderDirection`

##### `impl Debug for RenderDirection`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for RenderDirection`

- `fn default() -> RenderDirection` — [`RenderDirection`](#renderdirection)

##### `impl Display for RenderDirection`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for RenderDirection`

##### `impl<K> Equivalent for RenderDirection`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for RenderDirection`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<RenderDirection, <Self as ::core::str::FromStr>::Err>` — [`RenderDirection`](#renderdirection)

##### `impl Hash for RenderDirection`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for RenderDirection`

##### `impl PartialEq for RenderDirection`

- `fn eq(&self, other: &RenderDirection) -> bool` — [`RenderDirection`](#renderdirection)

##### `impl StructuralPartialEq for RenderDirection`

##### `impl ToCompactString for RenderDirection`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for RenderDirection`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for RenderDirection`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for RenderDirection`

- `fn to_string(&self) -> String`

##### `impl ToText for RenderDirection`

- `fn to_text(&self) -> Text<'_>`

