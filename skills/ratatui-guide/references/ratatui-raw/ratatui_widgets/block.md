*[ratatui_widgets](./index.md) / [block](#)*

---

# Module `block`

Elements related to the `Block` base widget.

This holds everything needed to display and configure a [`Block`](#block).

In its simplest form, a `Block` is a [border](Borders) around another widget. It can have a
[title](Block::title) and [padding](Block::padding).

## Contents

- [Structs](#structs)
  - [`Padding`](#padding)
  - [`Dimmed`](#dimmed)
  - [`Shadow`](#shadow)
  - [`Block`](#block)
- [Enums](#enums)
  - [`TitlePosition`](#titleposition)
- [Traits](#traits)
  - [`CellEffect`](#celleffect)
  - [`BlockExt`](#blockext)
- [Functions](#functions)
  - [`dimmed`](#dimmed)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Padding`](#padding) | struct |  |
| [`Dimmed`](#dimmed) | struct |  |
| [`Shadow`](#shadow) | struct |  |
| [`Block`](#block) | struct | A widget that renders borders, titles, and padding around other widgets. |
| [`TitlePosition`](#titleposition) | enum | Defines the position of the title. |
| [`CellEffect`](#celleffect) | trait |  |
| [`BlockExt`](#blockext) | trait | An extension trait for [`Block`] that provides some convenience methods. |
| [`dimmed`](#dimmed) | fn |  |

## Structs

### `Padding`

```rust
struct Padding {
    pub left: u16,
    pub right: u16,
    pub top: u16,
    pub bottom: u16,
}
```

Defines the padding for a [`Block`](#block).

See the `padding` method of [`Block`](#block) to configure its padding.

This concept is similar to [CSS padding].

**NOTE**: Terminal cells are often taller than they are wide, so to make horizontal and vertical
padding seem equal, doubling the horizontal padding is usually pretty good.

# Example

```rust
use ratatui::widgets::Padding;

Padding::uniform(1);
Padding::horizontal(2);
Padding::left(3);
Padding::proportional(4);
Padding::symmetric(5, 6);
```

#### Fields

- **`left`**: `u16`

  Left padding

- **`right`**: `u16`

  Right padding

- **`top`**: `u16`

  Top padding

- **`bottom`**: `u16`

  Bottom padding

#### Implementations

- `const ZERO: Self`

- `const fn new(left: u16, right: u16, top: u16, bottom: u16) -> Self`

  Creates a new `Padding` by specifying every field individually.

  

  Note: the order of the fields does not match the order of the CSS properties.

- `const fn zero() -> Self`

  Creates a `Padding` with all fields set to `0`.

- `const fn horizontal(value: u16) -> Self`

  Creates a `Padding` with the same value for `left` and `right`.

- `const fn vertical(value: u16) -> Self`

  Creates a `Padding` with the same value for `top` and `bottom`.

- `const fn uniform(value: u16) -> Self`

  Creates a `Padding` with the same value for all fields.

- `const fn proportional(value: u16) -> Self`

  Creates a `Padding` that is visually proportional to the terminal.

  

  This represents a padding of 2x the value for `left` and `right` and 1x the value for

  `top` and `bottom`.

- `const fn symmetric(x: u16, y: u16) -> Self`

  Creates a `Padding` that is symmetric.

  

  The `x` value is used for `left` and `right` and the `y` value is used for `top` and

  `bottom`.

- `const fn left(value: u16) -> Self`

  Creates a `Padding` that only sets the `left` padding.

- `const fn right(value: u16) -> Self`

  Creates a `Padding` that only sets the `right` padding.

- `const fn top(value: u16) -> Self`

  Creates a `Padding` that only sets the `top` padding.

- `const fn bottom(value: u16) -> Self`

  Creates a `Padding` that only sets the `bottom` padding.

#### Trait Implementations

##### `impl Clone for Padding`

- `fn clone(&self) -> Padding` — [`Padding`](./index.md#padding)

##### `impl<K> Comparable for Padding`

- `fn compare(&self, key: &K) -> Ordering`

##### `impl Copy for Padding`

##### `impl Debug for Padding`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Padding`

- `fn default() -> Padding` — [`Padding`](./index.md#padding)

##### `impl Eq for Padding`

##### `impl<K> Equivalent for Padding`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Padding`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Padding`

##### `impl Ord for Padding`

- `fn cmp(&self, other: &Padding) -> cmp::Ordering` — [`Padding`](./index.md#padding)

##### `impl PartialEq for Padding`

- `fn eq(&self, other: &Padding) -> bool` — [`Padding`](./index.md#padding)

##### `impl PartialOrd for Padding`

- `fn partial_cmp(&self, other: &Padding) -> option::Option<cmp::Ordering>` — [`Padding`](./index.md#padding)

##### `impl StructuralPartialEq for Padding`

### `Dimmed`

```rust
struct Dimmed;
```

A [`CellEffect`](./index.md) that dims the shadow cells by setting the [`DIM`](Modifier::DIM) modifier.

If the cell background is RGB, each channel is halved. Otherwise the background is replaced
with `Color::Black`.

#### Trait Implementations

##### `impl CellEffect for Dimmed`

- `fn apply(&self, shadow_area: Rect, base_area: Rect, buf: &mut Buffer)`

##### `impl Clone for Dimmed`

- `fn clone(&self) -> Dimmed` — [`Dimmed`](./index.md#dimmed)

##### `impl Copy for Dimmed`

##### `impl Debug for Dimmed`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Dimmed`

- `fn default() -> Dimmed` — [`Dimmed`](./index.md#dimmed)

##### `impl Eq for Dimmed`

##### `impl<K> Equivalent for Dimmed`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Dimmed`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Dimmed`

##### `impl PartialEq for Dimmed`

- `fn eq(&self, other: &Dimmed) -> bool` — [`Dimmed`](./index.md#dimmed)

##### `impl StructuralPartialEq for Dimmed`

### `Shadow`

```rust
struct Shadow {
    // [REDACTED: Private Fields]
}
```

A configurable shadow that can be rendered behind a [`Block`](crate::block::Block).

A [`Shadow`](./index.md) is rendered in an offset area relative to the block. Its [`Style`](../ratatui_core/style.md) is applied
first, then an optional cell effect can modify the affected cells, for example by filling them
with a shading symbol or dimming the existing background.

Built-in presets:

- `Shadow::overlay` applies only style
- `Shadow::block` fills with full block symbols
- `Shadow::light_shade`, `Shadow::medium_shade`, and `Shadow::dark_shade` fill with shade
  symbols

```plain
┌Popup─────┐
│content   │▒
└──────────┘▒
  ▒▒▒▒▒▒▒▒▒▒▒
```

# Custom effects

```rust
use ratatui::buffer::Buffer;
use ratatui::layout::{Position, Rect};
use ratatui::widgets::{Block, CellEffect, Shadow};

#[derive(Debug)]
struct Checker;

impl CellEffect for Checker {
    fn apply(&self, shadow_area: Rect, base_area: Rect, buf: &mut Buffer) {
        for y in shadow_area.top()..shadow_area.bottom() {
            for x in shadow_area.left()..shadow_area.right() {
                if base_area.contains(Position { x, y }) {
                    continue;
                }
                if (x + y) % 2 == 0 {
                    buf[(x, y)].set_symbol("░");
                }
            }
        }
    }
}

let shadow = Shadow::custom(Checker);
let block = Block::bordered().shadow(shadow);
```

#### Implementations

- `fn overlay() -> Self`

  Creates a shadow that only applies style to the offset area.

  

  This leaves the existing cell symbols unchanged.

  

  # Example

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::{Block, Shadow};

  

  let shadow = Shadow::overlay().black().on_white();

  let block = Block::bordered().shadow(shadow);

  ```

- `fn block() -> Self`

  Creates a shadow filled with full block symbols.

  

  # Example

  

  ```rust

  use ratatui::widgets::{Block, Shadow};

  

  let block = Block::bordered().shadow(Shadow::block());

  ```

- `fn light_shade() -> Self`

  Creates a shadow filled with light shade symbols.

  

  # Example

  

  ```rust

  use ratatui::widgets::{Block, Shadow};

  

  let block = Block::bordered().shadow(Shadow::light_shade());

  ```

- `fn medium_shade() -> Self`

  Creates a shadow filled with medium shade symbols.

  

  # Example

  

  ```rust

  use ratatui::widgets::{Block, Shadow};

  

  let block = Block::bordered().shadow(Shadow::medium_shade());

  ```

- `fn dark_shade() -> Self`

  Creates a shadow filled with dark shade symbols.

  

  # Example

  

  ```rust

  use ratatui::layout::Offset;

  use ratatui::style::Stylize;

  use ratatui::widgets::{Block, Shadow};

  

  let block = Block::bordered().shadow(

      Shadow::dark_shade()

          .black()

          .on_white()

          .offset(Offset::new(2, 1)),

  );

  ```

- `fn symbol(symbol: &'static str) -> Self`

  Creates a shadow filled with the given symbol.

  

  # Example

  

  ```rust

  use ratatui::widgets::{Block, Shadow};

  

  let shadow = Shadow::symbol("░");

  let block = Block::bordered().shadow(shadow);

  ```

- `fn custom<F: CellEffect + 'static>(effect: F) -> Self`

  Creates a new shadow from a custom cell effect.

  

  The effect receives the shadow area, the original block area, and the target buffer. It is

  called after the shadow style has been applied.

- `fn new<F: CellEffect + 'static>(effect: F) -> Self`

  Creates a new shadow from a custom cell effect.

  

  Alias for `Shadow::custom`.

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style applied to the shadow area.

- `const fn offset(self, offset: Offset) -> Self`

  Sets the shadow offset relative to the original area.

  

  Positive horizontal values move the shadow to the right and positive vertical values move it

  downward.

#### Trait Implementations

##### `impl Clone for Shadow`

- `fn clone(&self) -> Shadow` — [`Shadow`](./index.md#shadow)

##### `impl Debug for Shadow`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Shadow`

- `fn default() -> Self`

##### `impl Eq for Shadow`

##### `impl<K> Equivalent for Shadow`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Shadow`

- `fn hash<H: Hasher>(&self, state: &mut H)`

##### `impl IntoEither for Shadow`

##### `impl PartialEq for Shadow`

- `fn eq(&self, other: &Self) -> bool`

##### `impl Styled for Shadow`

- `type Item = Shadow`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Shadow`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for &Shadow`

- `fn render(self, area: Rect, buf: &mut Buffer)`

### `Block<'a>`

```rust
struct Block<'a> {
    // [REDACTED: Private Fields]
}
```

A widget that renders borders, titles, and padding around other widgets.

A `Block` is a foundational widget that creates visual containers by drawing borders around an
area. It serves as a wrapper or frame for other widgets, providing structure and visual
separation in terminal UIs. Most built-in widgets in Ratatui use a pattern where they accept an
optional `Block` parameter that wraps the widget's content.

When a widget renders with a block, the widget's style is applied first, then the block's style,
and finally the widget's content is rendered within the inner area calculated by the block. This
layered approach allows for flexible styling where the block can provide background colors,
borders, and padding while the inner widget handles its own content styling.

Multiple blocks can be nested within each other. The `Block::inner` method calculates the area
available for content after accounting for borders, titles, and padding, making it easy to nest
blocks or position widgets within a block's boundaries.

# Constructor Methods

- `Block::new` - Creates a block with no borders or padding
- `Block::bordered` - Creates a block with all borders enabled

# Border Configuration

- `Block::borders` - Specifies which borders to display
- `Block::border_style` - Sets the style of the borders
- `Block::border_type` - Sets border symbols (single, double, thick, rounded, etc.)
- `Block::border_set` - Sets custom border symbols as a [`border::Set`](../ratatui_core/symbols/block.md)
- `Block::merge_borders` - Controls how borders merge with adjacent blocks

# Title Configuration

- `Block::title` - Adds a title to the block
- `Block::title_top` - Adds a title to the top of the block
- `Block::title_bottom` - Adds a title to the bottom of the block
- `Block::title_alignment` - Sets default alignment for all titles
- `Block::title_style` - Sets the style for all titles
- `Block::title_position` - Sets default position for titles

# Styling and Layout

- `Block::style` - Sets the base style of the block
- `Block::shadow` - Adds a shadow rendered behind the block
- `Block::padding` - Adds internal padding within the borders
- `Block::inner` - Calculates the inner area available for content

# Title Behavior

You can add multiple titles to a block, and they will be rendered with spaces separating titles
that share the same position or alignment. When both centered and non-centered titles exist, the
centered space is calculated based on the full width of the block.

Titles are set using the `.title`, `.title_top`, and `.title_bottom` methods. These methods
accept a string or any type that can be converted into a [`Line`](../ratatui_core/index.md), such as a string slice,
`String`, or a vector of `Span`s. To control the alignment of a title (left, center, right),
pass a `Line` with the desired alignment, e.g. `Line::from("Title").centered()`.

By default, `.title` places the title at the top of the block, but you can use `.title_top` or
`.title_bottom` to explicitly set the position. The default alignment for all titles can be set
with `Block::title_alignment`, and the default position for all titles can be set with
`Block::title_position`.

Note that prior to `v0.30.0`, the `block::Title` struct was used to create titles. This struct
has been removed. The new recommended approach is to use [`Line`](../ratatui_core/index.md) with a specific alignment for
the title's content and the `Block::title_top` and `Block::title_bottom` methods for
positioning.

Titles avoid being rendered in corners when borders are present, but will align to edges when no
border exists on that side:

```plain
┌With at least a left border───

Without left border───
```

# Nesting Widgets with `inner`

The `Block::inner` method computes the area inside the block after accounting for borders,
titles, and padding. This allows you to nest widgets inside a block by rendering the block
first, then rendering other widgets in the returned inner area.

For example, you can nest a block inside another block:

```rust
use ratatui::Frame;
use ratatui::widgets::Block;

fn render_nested_block(frame: &mut Frame) {
let outer_block = Block::bordered().title("Outer");
let inner_block = Block::bordered().title("Inner");

let outer_area = frame.area();
let inner_area = outer_block.inner(outer_area);

frame.render_widget(outer_block, outer_area);
frame.render_widget(inner_block, inner_area);
}
```

You can also use the standard `Layout` functionality to further subdivide the inner area and
lay out multiple widgets inside a block.

# Integration with Other Widgets

Most widgets in Ratatui accept a block parameter. For example, [`Paragraph`](./paragraph.md), [`List`](./list.md),
[`Table`](./table.md), and other widgets can be wrapped with a block:

```rust
use ratatui::widgets::{Block, Paragraph};

let paragraph = Paragraph::new("Hello, world!").block(Block::bordered().title("My Paragraph"));
```

This pattern allows widgets to focus on their content while blocks handle the visual framing.

# Styling

Styles are applied in a specific order: first the block's base style, then border styles, then
title styles, and finally any content widget styles. This layered approach allows for flexible
styling where outer styles provide defaults that inner styles can override.

`Block` implements [`Stylize`](ratatui_core::style::Stylize), allowing you to use style
shorthand methods:

```rust
use ratatui::style::Stylize;
use ratatui::widgets::Block;

let block = Block::bordered().red().on_white().bold();
```

# Examples

Create a simple bordered block:

```rust
use ratatui::widgets::Block;

let block = Block::bordered().title("My Block");
```

Create a block with custom border styling:

```rust
use ratatui::style::{Color, Style, Stylize};
use ratatui::widgets::{Block, BorderType};

let block = Block::bordered()
    .title("Styled Block")
    .border_type(BorderType::Rounded)
    .border_style(Style::new().cyan())
    .style(Style::new().on_black());
```

Use a block to wrap another widget:

```rust
use ratatui::widgets::{Block, Paragraph};

let paragraph = Paragraph::new("Hello, world!").block(Block::bordered().title("Greeting"));
```

Add multiple titles with different alignments:

```rust
use ratatui::text::Line;
use ratatui::widgets::Block;

let block = Block::bordered()
    .title_top(Line::from("Left").left_aligned())
    .title_top(Line::from("Center").centered())
    .title_top(Line::from("Right").right_aligned())
    .title_bottom("Status: OK");
```

# See Also

- [Block recipe] - Visual examples and common patterns (on the ratatui website)
- [Collapse borders recipe] - Techniques for creating seamless layouts (on the ratatui website)
- [`MergeStrategy`](../ratatui_core/symbols/merge.md) - Controls how borders merge with adjacent elements

#### Implementations

- `const fn new() -> Self`

  Creates a new block with no [`Borders`](./borders.md) or [`Padding`](./index.md).

- `const fn bordered() -> Self`

  Create a new block with [all borders](Borders::ALL) shown

  

  ```rust

  use ratatui::widgets::{Block, Borders};

  

  assert_eq!(Block::bordered(), Block::new().borders(Borders::ALL));

  ```

- `fn title<T>(self, title: T) -> Self`

  Adds a title to the block using the default position.

  

  The position of the title is determined by the `title_position` field of the block, which

  defaults to `Top`. This can be changed using the `Block::title_position` method. For

  explicit positioning, use `Block::title_top` or `Block::title_bottom`.

  

  The `title` function allows you to add a title to the block. You can call this function

  multiple times to add multiple titles.

  

  Each title will be rendered with a single space separating titles that are in the same

  position or alignment. When both centered and non-centered titles are rendered, the centered

  space is calculated based on the full width of the block, rather than the leftover width.

  

  You can provide any type that can be converted into [`Line`](../ratatui_core/index.md) including: strings, string

  slices (`&str`), borrowed strings (`Cow<str>`), [spans](ratatui_core::text::Span), or

  vectors of [spans](ratatui_core::text::Span) (`Vec<Span>`).

  

  By default, the titles will avoid being rendered in the corners of the block but will align

  against the left or right edge of the block if there is no border on that edge. The

  following demonstrates this behavior, notice the second title is one character off to the

  left.

  

  ```plain

  ┌With at least a left border───

  

  Without left border───

  ```

  

  Note: If the block is too small and multiple titles overlap, the border might get cut off at

  a corner.

  

  # Examples

  

  See the [Block example] for a visual representation of how the various borders and styles

  look when rendered.

  

  The following example demonstrates:

  - Default title alignment

  - Multiple titles (notice "Center" is centered according to the full with of the block, not

    the leftover space)

  - Two titles with the same alignment (notice the left titles are separated)

  ```rust

  use ratatui::text::Line;

  use ratatui::widgets::Block;

  

  Block::bordered()

      .title("Title")

      .title(Line::from("Left").left_aligned())

      .title(Line::from("Right").right_aligned())

      .title(Line::from("Center").centered());

  ```

  

  # See also

  

  Titles attached to a block can have default behaviors. See

  - `Block::title_style`

  - `Block::title_alignment`

  

  # History

  

  In previous releases of Ratatui this method accepted `Into<Title>` instead of

  `Into<Line>`. We found that storing the position in the block and the alignment in the

  line better reflects the intended use of the block and its titles. See

  <https://github.com/ratatui/ratatui/issues/738> for more information.

- `fn title_top<T: Into<Line<'a>>>(self, title: T) -> Self`

  Adds a title to the top of the block.

  

  You can provide any type that can be converted into [`Line`](../ratatui_core/index.md) including: strings, string

  slices (`&str`), borrowed strings (`Cow<str>`), [spans](ratatui_core::text::Span), or

  vectors of [spans](ratatui_core::text::Span) (`Vec<Span>`).

  

  # Example

  

  ```rust

  use ratatui::{ widgets::Block, text::Line };

  

  Block::bordered()

      .title_top("Left1") // By default in the top left corner

      .title_top(Line::from("Left2").left_aligned())

      .title_top(Line::from("Right").right_aligned())

      .title_top(Line::from("Center").centered());

  

  // Renders

  // ┌Left1─Left2───Center─────────Right┐

  // │                                  │

  // └──────────────────────────────────┘

  ```

- `fn title_bottom<T: Into<Line<'a>>>(self, title: T) -> Self`

  Adds a title to the bottom of the block.

  

  You can provide any type that can be converted into [`Line`](../ratatui_core/index.md) including: strings, string

  slices (`&str`), borrowed strings (`Cow<str>`), [spans](ratatui_core::text::Span), or

  vectors of [spans](ratatui_core::text::Span) (`Vec<Span>`).

  

  # Example

  

  ```rust

  use ratatui::{ widgets::Block, text::Line };

  

  Block::bordered()

      .title_bottom("Left1") // By default in the top left corner

      .title_bottom(Line::from("Left2").left_aligned())

      .title_bottom(Line::from("Right").right_aligned())

      .title_bottom(Line::from("Center").centered());

  

  // Renders

  // ┌──────────────────────────────────┐

  // │                                  │

  // └Left1─Left2───Center─────────Right┘

  ```

- `fn title_style<S: Into<Style>>(self, style: S) -> Self`

  Applies the style to all titles.

  

  This style will be applied to all titles of the block. If a title has a style set, it will

  be applied after this style. This style will be applied after any `Block::style` or

  `Block::border_style` is applied.

  

  See [`Style`](../ratatui_core/style.md) for more information on how merging styles works.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

- `const fn title_alignment(self, alignment: Alignment) -> Self`

  Sets the default [`Alignment`](../ratatui_core/index.md) for all block titles.

  

  Titles that explicitly set an [`Alignment`](../ratatui_core/index.md) will ignore this.

  

  # Example

  

  This example aligns all titles in the center except the "right" title which explicitly sets

  `Alignment::Right`.

  ```rust

  use ratatui::layout::Alignment;

  use ratatui::text::Line;

  use ratatui::widgets::Block;

  

  Block::bordered()

      .title_alignment(Alignment::Center)

      // This title won't be aligned in the center

      .title(Line::from("right").right_aligned())

      .title("foo")

      .title("bar");

  ```

- `const fn title_position(self, position: TitlePosition) -> Self` — [`TitlePosition`](#titleposition)

  Sets the default [`TitlePosition`](#titleposition) for all block titles.

  

  # Example

  

  This example positions all titles on the bottom by default. The "top" title explicitly sets

  its position to `Top`, so it is not affected. The "foo" and "bar" titles will be positioned

  at the bottom.

  

  ```rust

  use ratatui::widgets::{Block, TitlePosition};

  

  Block::bordered()

      .title_position(TitlePosition::Bottom)

      .title("foo") // will be at the bottom

      .title_top("top") // will be at the top

      .title("bar"); // will be at the bottom

  ```

- `fn border_style<S: Into<Style>>(self, style: S) -> Self`

  Defines the style of the borders.

  

  This style is applied only to the areas covered by borders, and is applied to the block

  after any `Block::style` is applied.

  

  See [`Style`](../ratatui_core/style.md) for more information on how merging styles works.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  # Example

  

  This example shows a `Block` with blue borders.

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::Block;

  Block::bordered().border_style(Style::new().blue());

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Defines the style of the entire block.

  

  This is the most generic [`Style`](../ratatui_core/style.md) a block can receive, it will be merged with any other

  more specific styles. Elements can be styled further with `Block::title_style` and

  `Block::border_style`, which will be applied on top of this style. If the block is used as

  a container for another widget (e.g. a [`Paragraph`](./paragraph.md)), then the style of the widget is

  generally applied before this style.

  

  See [`Style`](../ratatui_core/style.md) for more information on how merging styles works.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  # Example

  

  ```rust

  use ratatui::style::{Color, Style, Stylize};

  use ratatui::widgets::{Block, Paragraph};

  

  let block = Block::new().style(Style::new().red().on_black());

  

  // For border and title you can additionally apply styles on top of the block level style.

  let block = Block::new()

      .style(Style::new().red().bold().italic())

      .border_style(Style::new().not_italic()) // will be red and bold

      .title_style(Style::new().not_bold()) // will be red and italic

      .title("Title");

  

  // To style the inner widget, you can style the widget itself.

  let paragraph = Paragraph::new("Content")

      .block(block)

      .style(Style::new().white().not_bold()); // will be white, and italic

  ```

  

- `const fn borders(self, flag: Borders) -> Self` — [`Borders`](./borders.md#borders)

  Defines which borders to display.

  

  [`Borders`](./borders.md) can also be styled with `Block::border_style` and `Block::border_type`.

  

  # Examples

  

  Display left and right borders.

  ```rust

  use ratatui::widgets::{Block, Borders};

  Block::new().borders(Borders::LEFT | Borders::RIGHT);

  ```

  

  To show all borders you can abbreviate this with `Block::bordered`

- `const fn border_type(self, border_type: BorderType) -> Self` — [`BorderType`](./borders.md#bordertype)

  Sets the symbols used to display the border (e.g. single line, double line, thick or

  rounded borders).

  

  Setting this overwrites any custom [`border_set`](Block::border_set) that was set.

  

  See [`BorderType`](./borders.md) for the full list of available symbols.

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Block, BorderType};

  Block::bordered()

      .border_type(BorderType::Rounded)

      .title("Block");

  // Renders

  // ╭Block╮

  // │     │

  // ╰─────╯

  ```

- `const fn border_set(self, border_set: border::Set<'a>) -> Self`

  Sets the symbols used to display the border as a [`ratatui_core::symbols::border::Set`](../ratatui_core/symbols/block.md).

  

  Setting this overwrites any [`border_type`](Block::border_type) that was set.

  

  # Examples

  

  ```rust

  use ratatui::{widgets::Block, symbols};

  

  Block::bordered().border_set(symbols::border::DOUBLE).title("Block");

  // Renders

  // ╔Block╗

  // ║     ║

  // ╚═════╝

- `const fn padding(self, padding: Padding) -> Self` — [`Padding`](./index.md#padding)

  Defines the padding inside a `Block`.

  

  See [`Padding`](./index.md) for more information.

  

  # Examples

  

  This renders a `Block` with no padding (the default).

  ```rust

  use ratatui::widgets::{Block, Padding};

  

  Block::bordered().padding(Padding::ZERO);

  // Renders

  // ┌───────┐

  // │content│

  // └───────┘

  ```

  

  This example shows a `Block` with padding left and right (`Padding::horizontal`).

  Notice the two spaces before and after the content.

  ```rust

  use ratatui::widgets::{Block, Padding};

  

  Block::bordered().padding(Padding::horizontal(2));

  // Renders

  // ┌───────────┐

  // │  content  │

  // └───────────┘

  ```

- `const fn merge_borders(self, strategy: MergeStrategy) -> Self`

  Sets the block's [`MergeStrategy`](../ratatui_core/symbols/merge.md) for overlapping characters, defaulting to `Replace`.

  

  Changing the strategy to `Exact` or `Fuzzy` collapses border characters that intersect

  with any previously rendered borders.

  

  For more information and examples, see the [collapse borders recipe] and [`MergeStrategy`](../ratatui_core/symbols/merge.md)

  docs.

  

  # Example

  

  ```rust

  use ratatui::symbols::merge::MergeStrategy;

  use ratatui::widgets::{Block, BorderType};

  

  // Given several blocks with plain borders (1)

  Block::bordered();

  // and other blocks with thick borders (2) which are rendered on top of the first

  Block::bordered()

      .border_type(BorderType::Thick)

      .merge_borders(MergeStrategy::Exact);

  ```

  

  Rendering these blocks with `MergeStrategy::Exact` or `MergeStrategy::Fuzzy` will collapse

  the borders, resulting in a clean layout without connected borders.

  

  ```plain

  ┌───┐    ┌───┐  ┌───┲━━━┓┌───┐

  │   │    │ 1 │  │   ┃   ┃│   │

  │ 1 │    │ ┏━┿━┓│ 1 ┃ 2 ┃│ 1 │

  │   │    │ ┃ │ ┃│   ┃   ┃│   │

  └───╆━━━┓└─╂─┘ ┃└───┺━━━┛┢━━━┪

      ┃   ┃  ┃ 2 ┃         ┃   ┃

      ┃ 2 ┃  ┗━━━┛         ┃ 2 ┃

      ┃   ┃                ┃   ┃

      ┗━━━┛                ┗━━━┛

  ```

  

  

  

- `fn shadow(self, shadow: Shadow) -> Self` — [`Shadow`](./index.md#shadow)

  Adds a shadow behind the block.

  

  The shadow is rendered using the block area plus the shadow's configured offset.

  

  # Example

  

  ```rust

  use ratatui::layout::Offset;

  use ratatui::style::Stylize;

  use ratatui::widgets::{Block, Shadow};

  

  let block = Block::bordered().title("Popup").shadow(

      Shadow::dark_shade()

          .black()

          .on_white()

          .offset(Offset::new(2, 1)),

  );

  ```

- `fn inner(&self, area: Rect) -> Rect`

  Computes the inner area of a block after subtracting space for borders, titles, and padding.

  

  # Examples

  

  Draw a block nested within another block

  ```rust

  use ratatui::Frame;

  use ratatui::widgets::Block;

  

  fn render_nested_block(frame: &mut Frame) {

  let outer_block = Block::bordered().title("Outer");

  let inner_block = Block::bordered().title("Inner");

  

  let outer_area = frame.area();

  let inner_area = outer_block.inner(outer_area);

  

  frame.render_widget(outer_block, outer_area);

  frame.render_widget(inner_block, inner_area);

  }

  // Renders

  // ┌Outer────────┐

  // │┌Inner──────┐│

  // ││           ││

  // │└───────────┘│

  // └─────────────┘

  ```

#### Trait Implementations

##### `impl AsRef for crate::block::Block<'a>`

- `fn as_ref(&self) -> &crate::block::Block<'a>` — [`Block`](#block)

##### `impl Clone for Block<'a>`

- `fn clone(&self) -> Block<'a>` — [`Block`](#block)

##### `impl Debug for Block<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Block<'a>`

- `fn default() -> Block<'a>` — [`Block`](#block)

##### `impl Eq for Block<'a>`

##### `impl<K> Equivalent for Block<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Block<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Block<'a>`

##### `impl PartialEq for Block<'a>`

- `fn eq(&self, other: &Block<'a>) -> bool` — [`Block`](#block)

##### `impl StructuralPartialEq for Block<'a>`

##### `impl Styled for Block<'_>`

- `type Item = Block<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Block<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for Block<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

## Enums

### `TitlePosition`

```rust
enum TitlePosition {
    Top,
    Bottom,
}
```

Defines the position of the title.

The title can be positioned on top or at the bottom of the block.

# Example

```rust
use ratatui::widgets::{Block, TitlePosition};

Block::bordered()
    .title_position(TitlePosition::Top)
    .title("Top Title");
Block::bordered()
    .title_position(TitlePosition::Bottom)
    .title("Bottom Title");
```

#### Variants

- **`Top`**

  Position the title at the top of the block.

- **`Bottom`**

  Position the title at the bottom of the block.

#### Trait Implementations

##### `impl Clone for TitlePosition`

- `fn clone(&self) -> TitlePosition` — [`TitlePosition`](#titleposition)

##### `impl Copy for TitlePosition`

##### `impl Debug for TitlePosition`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for TitlePosition`

- `fn default() -> TitlePosition` — [`TitlePosition`](#titleposition)

##### `impl Display for TitlePosition`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for TitlePosition`

##### `impl<K> Equivalent for TitlePosition`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for TitlePosition`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<TitlePosition, <Self as ::core::str::FromStr>::Err>` — [`TitlePosition`](#titleposition)

##### `impl Hash for TitlePosition`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for TitlePosition`

##### `impl PartialEq for TitlePosition`

- `fn eq(&self, other: &TitlePosition) -> bool` — [`TitlePosition`](#titleposition)

##### `impl StructuralPartialEq for TitlePosition`

##### `impl ToCompactString for TitlePosition`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for TitlePosition`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for TitlePosition`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for TitlePosition`

- `fn to_string(&self) -> String`

##### `impl ToText for TitlePosition`

- `fn to_text(&self) -> Text<'_>`

## Traits

### `CellEffect`

```rust
trait CellEffect: fmt::Debug { ... }
```

A cell effect that modifies the cells covered by a [`Shadow`](./index.md).

See `Shadow::custom` for how to create a shadow from a custom effect.

#### Required Methods

- `fn apply(&self, shadow_area: Rect, base_area: Rect, buf: &mut Buffer)`

  Applies the effect to the cells in `shadow_area`.

#### Implementors

- [`Dimmed`](./index.md#dimmed)

### `BlockExt`

```rust
trait BlockExt { ... }
```

An extension trait for [`Block`](#block) that provides some convenience methods.

This is implemented for [`Option<Block>`](Option) to simplify the common case of having a
widget with an optional block.

#### Required Methods

- `fn inner_if_some(&self, area: Rect) -> Rect`

  Return the inner area of the block if it is `Some`. Otherwise, returns `area`.

#### Implementors

- `Option<Block<'_>>`

## Functions

### `dimmed`

```rust
const fn dimmed() -> Dimmed
```

Creates a [`Dimmed`](./index.md) shadow effect.

