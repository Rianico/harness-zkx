*[ratatui_widgets](../index.md) / [barchart](index.md)*

---

# Module `barchart`

The [`BarChart`](#barchart) widget and its related types (e.g. [`Bar`](../index.md), [`BarGroup`](../index.md)).

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Bar`](#bar) | struct |  |
| [`BarGroup`](#bargroup) | struct |  |
| [`BarChart`](#barchart) | struct | A chart showing values as [bars](Bar). |

## Structs

### `Bar<'a>`

```rust
struct Bar<'a> {
    // [REDACTED: Private Fields]
}
```

A bar to be shown by the [`BarChart`](super::BarChart) widget.

Here is an explanation of a `Bar`'s components.
```plain
███                          ┐
█2█  <- text_value or value  │ bar
foo  <- label                ┘
```
Note that every element can be styled individually.

# Example

The following example creates a bar with the label "Bar 1", a value "10",
red background and a white value foreground.
```rust
use ratatui::style::{Style, Stylize};
use ratatui::widgets::Bar;

Bar::with_label("Bar 1", 10)
    .red()
    .value_style(Style::new().red().on_white())
    .text_value("10°C");
```

#### Implementations

- `const fn new(value: u64) -> Self`

  Creates a new `Bar` with the given value.

  

  # Examples

  

  ```rust

  use ratatui::widgets::Bar;

  

  let bar = Bar::new(42);

  ```

- `fn with_label<T: Into<Line<'a>>>(label: T, value: u64) -> Self`

  Creates a new `Bar` with the given `label` and value.

  

  a `label` can be a `&str`, `String` or anything that can be converted into [`Line`](../../ratatui_core/index.md).

  

  # Examples

  

  ```rust

  use ratatui::widgets::Bar;

  

  let bar = Bar::with_label("Label", 42);

  ```

- `const fn value(self, value: u64) -> Self`

  Set the value of this bar.

  

  The value will be displayed inside the bar.

  

  # See also

  

  - `Bar::value_style` to style the value.

  - `Bar::text_value` to set the displayed value.

- `fn label<T: Into<Line<'a>>>(self, label: T) -> Self`

  Set the label of the bar.

  

  `label` can be a `&str`, `String` or anything that can be converted into [`Line`](../../ratatui_core/index.md).

  

  # Examples

  

  From `&str` and `String`:

  

  ```rust

  use ratatui::widgets::Bar;

  

  Bar::default().label("label");

  Bar::default().label(String::from("label"));

  ```

  

  From a [`Line`](../../ratatui_core/index.md) with red foreground color:

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::text::Line;

  use ratatui::widgets::Bar;

  

  Bar::default().label(Line::from("Line").red());

  ```

  

  For [`Vertical`](ratatui_core::layout::Direction::Vertical) bars,

  display the label **under** the bar.

  For [`Horizontal`](ratatui_core::layout::Direction::Horizontal) bars,

  display the label **in** the bar.

  See [`BarChart::direction`](crate::barchart::BarChart::direction) to set the direction.

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Set the style of the bar.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This will apply to every non-styled element. It can be seen and used as a default value.

- `fn value_style<S: Into<Style>>(self, style: S) -> Self`

  Set the style of the value.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  # See also

  

  `Bar::value` to set the value.

- `fn text_value<T: Into<String>>(self, text_value: T) -> Self`

  Set the text value printed in the bar.

  

  `text_value` can be a `&str`, `Number` or anything that can be converted into `String`.

  

  If `text_value` is not set, then the `ToString` representation of `value` will be shown on

  the bar.

  

  # Examples

  

  From `&str` and `String`:

  

  ```rust

  use ratatui::widgets::Bar;

  

  Bar::default().text_value("label");

  Bar::default().text_value(String::from("label"));

  ```

  

  # See also

  

  `Bar::value` to set the value.

#### Trait Implementations

##### `impl Clone for Bar<'a>`

- `fn clone(&self) -> Bar<'a>` — [`Bar`](../index.md#bar)

##### `impl Debug for Bar<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Bar<'a>`

- `fn default() -> Bar<'a>` — [`Bar`](../index.md#bar)

##### `impl Eq for Bar<'a>`

##### `impl<K> Equivalent for Bar<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Bar<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Bar<'a>`

##### `impl PartialEq for Bar<'a>`

- `fn eq(&self, other: &Bar<'a>) -> bool` — [`Bar`](../index.md#bar)

##### `impl StructuralPartialEq for Bar<'a>`

##### `impl Styled for Bar<'_>`

- `type Item = Bar<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Bar<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

### `BarGroup<'a>`

```rust
struct BarGroup<'a> {
    // [REDACTED: Private Fields]
}
```

A group of bars to be shown by the Barchart.

# Examples

```rust
use ratatui::widgets::{Bar, BarGroup};

let group = BarGroup::new([Bar::with_label("Red", 20), Bar::with_label("Blue", 15)]);
```

#### Implementations

- `fn new<T: Into<Vec<Bar<'a>>>>(bars: T) -> Self`

  Creates a new `BarGroup` with the given bars.

  

  # Examples

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::{Bar, BarGroup};

  

  let group = BarGroup::new(vec![Bar::with_label("A", 10), Bar::with_label("B", 20)]);

  ```

- `fn with_label<T: Into<Line<'a>>, B: Into<Vec<Bar<'a>>>>(label: T, bars: B) -> Self`

  Creates a new `BarGroup` with the given bars and label.

  

  # Examples

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::{Bar, BarGroup};

  

  let group = BarGroup::with_label(

      "Group1",

      vec![Bar::with_label("A", 10), Bar::with_label("B", 20)],

  );

  ```

- `fn label<T: Into<Line<'a>>>(self, label: T) -> Self`

  Set the group label

  

  `label` can be a `&str`, `String` or anything that can be converted into [`Line`](../../ratatui_core/index.md).

  

  # Examples

  

  From `&str` and `String`.

  

  ```rust

  use ratatui::widgets::BarGroup;

  

  BarGroup::default().label("label");

  BarGroup::default().label(String::from("label"));

  ```

  

  From a [`Line`](../../ratatui_core/index.md) with red foreground color:

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::text::Line;

  use ratatui::widgets::BarGroup;

  

  BarGroup::default().label(Line::from("Line").red());

  ```

- `fn bars(self, bars: &[Bar<'a>]) -> Self` — [`Bar`](../index.md#bar)

  Set the bars of the group to be shown

#### Trait Implementations

##### `impl Clone for BarGroup<'a>`

- `fn clone(&self) -> BarGroup<'a>` — [`BarGroup`](../index.md#bargroup)

##### `impl Debug for BarGroup<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for BarGroup<'a>`

- `fn default() -> BarGroup<'a>` — [`BarGroup`](../index.md#bargroup)

##### `impl Eq for BarGroup<'a>`

##### `impl<K> Equivalent for BarGroup<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for BarGroup<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for BarGroup<'a>`

##### `impl PartialEq for BarGroup<'a>`

- `fn eq(&self, other: &BarGroup<'a>) -> bool` — [`BarGroup`](../index.md#bargroup)

##### `impl StructuralPartialEq for BarGroup<'a>`

### `BarChart<'a>`

```rust
struct BarChart<'a> {
    // [REDACTED: Private Fields]
}
```

A chart showing values as [bars](Bar).

Here is a possible `BarChart` output.
```plain
┌─────────────────────────────────┐
│                             ████│
│                        ▅▅▅▅ ████│
│            ▇▇▇▇        ████ ████│
│     ▄▄▄▄   ████ ████   ████ ████│
│▆10▆ █20█   █50█ █40█   █60█ █90█│
│ B1   B2     B1   B2     B1   B2 │
│ Group1      Group2      Group3  │
└─────────────────────────────────┘
```

A `BarChart` is composed of a set of [`Bar`](../index.md) which can be set via `BarChart::data`.
Bars can be styled globally (`BarChart::bar_style`) or individually (`Bar::style`).
There are other methods available to style even more precisely. See [`Bar`](../index.md) to find out about
each bar component.

The `BarChart` widget can also show groups of bars via [`BarGroup`](../index.md).
A [`BarGroup`](../index.md) is a set of [`Bar`](../index.md), multiple can be added to a `BarChart` using
`BarChart::data` multiple time as demonstrated in the example below.

The chart can have a [`Direction`](../../ratatui_core/index.md) (by default the bars are [`Vertical`](Direction::Vertical)).
This is set using `BarChart::direction`.

Note: this is the only widget that doesn't implement `Widget` for `&T` because the current
implementation modifies the internal state of self. This will be fixed in the future.

# Examples

The following example creates a `BarChart` with two groups of bars.
The first group is added by an array slice (`&[(&str, u64)]`).
The second group is added by a [`BarGroup`](../index.md) instance.
```rust
use ratatui::style::{Style, Stylize};
use ratatui::widgets::{Bar, BarChart, BarGroup, Block};

BarChart::default()
    .block(Block::bordered().title("BarChart"))
    .bar_width(3)
    .bar_gap(1)
    .group_gap(3)
    .bar_style(Style::new().yellow().on_red())
    .value_style(Style::new().red().bold())
    .label_style(Style::new().white())
    .data(&[("A0", 0), ("A1", 2), ("A2", 4), ("A3", 3)])
    .data(BarGroup::new([
        Bar::with_label("B0", 10),
        Bar::with_label("B2", 20),
    ]))
    .max(4);
```

For simpler usages, you can also create a `BarChart` simply by

```rust
use ratatui::widgets::{Bar, BarChart};

BarChart::new([Bar::with_label("A", 10), Bar::with_label("B", 20)]);
```

#### Implementations

- `fn new<T: Into<Vec<Bar<'a>>>>(bars: T) -> Self`

  Creates a new vertical `BarChart` widget with the given bars.

  

  The `bars` parameter accepts any type that can be converted into a `Vec<Bar>`.

  

  # Examples

  

  ```rust

  use ratatui::layout::Direction;

  use ratatui::widgets::{Bar, BarChart};

  

  BarChart::new(vec![Bar::with_label("A", 10), Bar::with_label("B", 10)]);

  ```

- `fn vertical(bars: impl Into<Vec<Bar<'a>>>) -> Self` — [`Bar`](../index.md#bar)

  Creates a new `BarChart` widget with a vertical direction.

  

  This function is equivalent to `BarChart::new()`.

- `fn horizontal(bars: impl Into<Vec<Bar<'a>>>) -> Self` — [`Bar`](../index.md#bar)

  Creates a new `BarChart` widget with a horizontal direction.

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Bar, BarChart};

  

  BarChart::horizontal(vec![Bar::with_label("A", 10), Bar::with_label("B", 20)]);

  ```

- `fn grouped<T: Into<Vec<BarGroup<'a>>>>(groups: T) -> Self`

  Creates a new `BarChart` widget with a group of bars.

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Bar, BarChart, BarGroup};

  

  BarChart::grouped(vec![

      BarGroup::with_label(

          "Group 1",

          vec![Bar::with_label("A", 10), Bar::with_label("B", 20)],

      ),

      BarGroup::with_label(

          "Group 2",

          [Bar::with_label("C", 30), Bar::with_label("D", 40)],

      ),

  ]);

  ```

- `fn data(self, data: impl Into<BarGroup<'a>>) -> Self` — [`BarGroup`](../index.md#bargroup)

  Add group of bars to the `BarChart`

  

  # Examples

  

  The following example creates a `BarChart` with two groups of bars.

  The first group is added by an array slice (`&[(&str, u64)]`).

  The second group is added by a [`BarGroup`](../index.md) instance.

  ```rust

  use ratatui::widgets::{Bar, BarChart, BarGroup};

  

  BarChart::default()

      .data(&[("B0", 0), ("B1", 2), ("B2", 4), ("B3", 3)])

      .data(BarGroup::new([

          Bar::with_label("A", 10),

          Bar::with_label("B", 20),

      ]));

  ```

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](../block/index.md#block)

  Surround the [`BarChart`](#barchart) with a [`Block`](../block/index.md).

- `const fn max(self, max: u64) -> Self`

  Set the value necessary for a [`Bar`](../index.md) to reach the maximum height.

  

  If not set, the maximum value in the data is taken as reference.

  

  # Examples

  

  This example shows the default behavior when `max` is not set.

  The maximum value in the dataset is taken (here, `100`).

  ```rust

  use ratatui::widgets::BarChart;

  BarChart::default().data(&[("foo", 1), ("bar", 2), ("baz", 100)]);

  // Renders

  //     █

  //     █

  // f b b

  ```

  

  This example shows a custom max value.

  The maximum height being `2`, `bar` & `baz` render as the max.

  ```rust

  use ratatui::widgets::BarChart;

  

  BarChart::default()

      .data(&[("foo", 1), ("bar", 2), ("baz", 100)])

      .max(2);

  // Renders

  //   █ █

  // █ █ █

  // f b b

  ```

- `fn bar_style<S: Into<Style>>(self, style: S) -> Self`

  Set the default style of the bar.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  It is also possible to set individually the style of each [`Bar`](../index.md).

  In this case the default style will be patched by the individual style

- `const fn bar_width(self, width: u16) -> Self`

  Set the width of the displayed bars.

  

  For [`Horizontal`](ratatui_core::layout::Direction::Horizontal) bars this becomes the height

  of the bar.

  

  If not set, this defaults to `1`.

  The bar label also uses this value as its width.

- `const fn bar_gap(self, gap: u16) -> Self`

  Set the gap between each bar.

  

  If not set, this defaults to `1`.

  The bar label will never be larger than the bar itself, even if the gap is sufficient.

  

  # Example

  

  This shows two bars with a gap of `3`. Notice the labels will always stay under the bar.

  ```rust

  use ratatui::widgets::BarChart;

  

  BarChart::default()

      .data(&[("foo", 1), ("bar", 2)])

      .bar_gap(3);

  // Renders

  //     █

  // █   █

  // f   b

  ```

- `const fn bar_set(self, bar_set: symbols::bar::Set<'a>) -> Self`

  The [`bar::Set`](ratatui_core::symbols::bar::Set) to use for displaying the bars.

  

  If not set, the default is [`bar::NINE_LEVELS`](ratatui_core::symbols::bar::NINE_LEVELS).

- `fn value_style<S: Into<Style>>(self, style: S) -> Self`

  Set the default value style of the bar.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  It is also possible to set individually the value style of each [`Bar`](../index.md).

  In this case the default value style will be patched by the individual value style

  

  # See also

  

  `Bar::value_style` to set the value style individually.

- `fn label_style<S: Into<Style>>(self, style: S) -> Self`

  Set the default label style of the groups and bars.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  It is also possible to set individually the label style of each [`Bar`](../index.md) or [`BarGroup`](../index.md).

  In this case the default label style will be patched by the individual label style

  

  # See also

  

  `Bar::label` to set the label style individually.

- `const fn group_gap(self, gap: u16) -> Self`

  Set the gap between [`BarGroup`](../index.md).

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Set the style of the entire chart.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  The style will be applied to everything that isn't styled (borders, bars, labels, ...).

- `const fn direction(self, direction: Direction) -> Self`

  Set the direction of the bars.

  

  [`Vertical`](ratatui_core::layout::Direction::Vertical) bars are the default.

  

  # Examples

  

  Vertical bars

  ```plain

    █

  █ █

  f b

  ```

  

  Horizontal bars

  ```plain

  █foo██

  

  █bar██

  ```

#### Trait Implementations

##### `impl AsRef for crate::barchart::BarChart<'a>`

- `fn as_ref(&self) -> &crate::barchart::BarChart<'a>` — [`BarChart`](#barchart)

##### `impl Clone for BarChart<'a>`

- `fn clone(&self) -> BarChart<'a>` — [`BarChart`](#barchart)

##### `impl Debug for BarChart<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for BarChart<'_>`

- `fn default() -> Self`

##### `impl Eq for BarChart<'a>`

##### `impl<K> Equivalent for BarChart<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for BarChart<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for BarChart<'a>`

##### `impl PartialEq for BarChart<'a>`

- `fn eq(&self, other: &BarChart<'a>) -> bool` — [`BarChart`](#barchart)

##### `impl StructuralPartialEq for BarChart<'a>`

##### `impl Styled for BarChart<'_>`

- `type Item = BarChart<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for BarChart<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for BarChart<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

