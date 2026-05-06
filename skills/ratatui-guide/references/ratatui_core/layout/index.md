*[ratatui_core](../index.md) / [layout](index.md)*

---

# Module `layout`

Layout and positioning in terminal user interfaces.

This module provides a comprehensive set of types and traits for working with layout and
positioning in terminal applications. It implements a flexible layout system that allows you to
divide the terminal screen into different areas using constraints, manage positioning and
sizing, and handle complex UI arrangements.

The layout system in Ratatui is based on the Cassowary constraint solver algorithm, implemented
through the `kasuari` crate. This allows for sophisticated constraint-based layouts where
multiple requirements can be satisfied simultaneously, with priorities determining which
constraints take precedence when conflicts arise.

# Core Concepts

## Coordinate System

The coordinate system runs left to right, top to bottom, with the origin `(0, 0)` in the top
left corner of the terminal. The x and y coordinates are represented by `u16` values.

```text
     x (columns)
  ┌─────────────→
y │ (0,0)
  │
(rows)
  ↓
```

## Layout Fundamentals

Layouts form the structural foundation of your terminal UI. The [`Layout`](../index.md) struct divides
available screen space into rectangular areas using a constraint-based approach. You define
multiple constraints for how space should be allocated, and the Cassowary solver determines
the optimal layout that satisfies as many constraints as possible. These areas can then be
used to render widgets or nested layouts.

Note that the [`Layout`](../index.md) struct is not required to create layouts - you can also manually
calculate and create [`Rect`](../index.md) areas using simple mathematics to divide up the terminal space
if you prefer direct control over positioning and sizing.

## Rectangular Areas

All layout operations work with rectangular areas represented by the [`Rect`](../index.md) type. A [`Rect`](../index.md)
defines a position and size in the terminal, specified by its top-left corner coordinates and
dimensions.

# Available Types

## Core Layout Types

- [`Layout`](../index.md) - The primary layout engine that divides space using constraints and direction
- [`Rect`](../index.md) - Represents a rectangular area with position and dimensions
- [`Constraint`](../index.md) - Defines how space should be allocated (length, percentage, ratio, etc.)
- [`Direction`](../index.md) - Specifies layout orientation (horizontal or vertical)
- [`Flex`](../index.md) - Controls space distribution when constraints are satisfied

## Positioning and Sizing

- [`Position`](../index.md) - Represents a point in the terminal coordinate system
- [`Size`](../index.md) - Represents dimensions (width and height)
- [`Margin`](../index.md) - Defines spacing around rectangular areas
- [`Offset`](../index.md) - Represents relative movement in the coordinate system
- [`Spacing`](../index.md) - Controls spacing or overlap between layout segments

## Alignment

- [`Alignment`](../index.md) (alias for [`HorizontalAlignment`](../index.md)) - Horizontal text/content alignment
- [`HorizontalAlignment`](../index.md) - Horizontal alignment options (left, center, right)
- [`VerticalAlignment`](../index.md) - Vertical alignment options (top, center, bottom)

## Iteration Support

- [`Rows`](../index.md) - Iterator over horizontal rows within a rectangular area
- [`Columns`](../index.md) - Iterator over vertical columns within a rectangular area
- [`Positions`](../index.md) - Iterator over all positions within a rectangular area

# Quick Start

Here's a simple example of creating a basic layout using the [`Layout`](../index.md) struct:

```rust
use ratatui_core::layout::{Constraint, Direction, Layout, Rect};

// Create a terminal area
let area = Rect::new(0, 0, 80, 24);

// Divide it vertically into two equal parts using Layout
let layout = Layout::vertical([Constraint::Percentage(50), Constraint::Percentage(50)]);
let [top, bottom] = layout.areas(area);

// Now you have two areas: top and bottom
```

**Note**: When the number of layout areas is known at compile time, use destructuring
assignment with descriptive variable names for better readability:

```rust
use ratatui_core::layout::{Constraint, Layout, Rect};

let area = Rect::new(0, 0, 80, 24);
let [header, content, footer] = Layout::vertical([
    Constraint::Length(3),
    Constraint::Fill(1),
    Constraint::Length(1),
])
.areas(area);
```

Use `Layout::split` when the number of areas is only known at runtime.

Alternatively, you can create layouts manually using mathematics:

```rust
use ratatui_core::layout::Rect;

// Create a terminal area
let area = Rect::new(0, 0, 80, 24);

// Manually divide into two equal parts
let top_half = Rect::new(area.x, area.y, area.width, area.height / 2);
let bottom_half = Rect::new(
    area.x,
    area.y + area.height / 2,
    area.width,
    area.height / 2,
);
```

# Layout Examples

## Basic Vertical Split

```rust
use ratatui_core::layout::{Constraint, Layout, Rect};

let area = Rect::new(0, 0, 80, 24);
let [header, content, footer] = Layout::vertical([
    Constraint::Length(3), // Header: fixed height
    Constraint::Fill(1),   // Content: flexible
    Constraint::Length(1), // Footer: fixed height
])
.areas(area);
```

## Horizontal Sidebar Layout

```rust
use ratatui_core::layout::{Constraint, Layout, Rect};

let area = Rect::new(0, 0, 80, 24);
let [sidebar, main] = Layout::horizontal([
    Constraint::Length(20), // Sidebar: fixed width
    Constraint::Fill(1),    // Main content: flexible
])
.areas(area);
```

## Complex Nested Layout

```rust
use ratatui_core::layout::{Constraint, Layout, Rect};

fn create_complex_layout(area: Rect) -> [Rect; 4] {
    // First, split vertically
    let [header, body, footer] = Layout::vertical([
        Constraint::Length(3), // Header
        Constraint::Fill(1),   // Body
        Constraint::Length(1), // Footer
    ])
    .areas(area);

    // Then split the body horizontally
    let [sidebar, main] = Layout::horizontal([
        Constraint::Length(20), // Sidebar
        Constraint::Fill(1),    // Main
    ])
    .areas(body);

    [header, sidebar, main, footer]
}
```

# Working with Constraints

[`Constraint`](../index.md)s define how space is allocated within a layout using the Cassowary constraint
solver algorithm. The constraint solver attempts to satisfy all constraints simultaneously,
with priorities determining which constraints take precedence when conflicts arise. Different
constraint types serve different purposes:

- [`Constraint::Min`](../index.md) - Minimum size constraint
- [`Constraint::Max`](../index.md) - Maximum size constraint
- [`Constraint::Length`](../index.md) - Fixed size in character cells
- [`Constraint::Percentage`](../index.md) - Relative size as a percentage of available space
- [`Constraint::Ratio`](../index.md) - Proportional size using ratios
- [`Constraint::Fill`](../index.md) - Proportional fill of remaining space

Constraints are resolved in priority order, with [`Constraint::Min`](../index.md) having the highest
priority and [`Constraint::Fill`](../index.md) having the lowest. The constraint solver will satisfy as
many constraints as possible while respecting these priorities.

# Flexible Space Distribution

The [`Flex`](../index.md) enum controls how extra space is distributed when constraints are satisfied:

- [`Flex::Start`](../index.md) - Align content to the start, leaving excess space at the end
- [`Flex::End`](../index.md) - Align content to the end, leaving excess space at the start
- [`Flex::Center`](../index.md) - Center content, distributing excess space equally on both sides
- [`Flex::SpaceBetween`](../index.md) - Distribute excess space evenly *between* elements, none at the ends
- [`Flex::SpaceAround`](../index.md) - Distribute space *around* elements: equal padding on both sides of
  each element; gaps between elements are twice the edge spacing
- [`Flex::SpaceEvenly`](../index.md) - Distribute space *evenly*: equal spacing between all elements,
  including before the first and after the last.
- [`Flex::Legacy`](../index.md) - Legacy behavior (puts excess space in the last element)

# Positioning and Alignment

Use [`Position`](../index.md) to represent specific points in the terminal, [`Size`](../index.md) for dimensions, and the
alignment types for controlling content positioning within areas:

```rust
use ratatui_core::layout::{Alignment, Position, Rect, Size};

let pos = Position::new(10, 5);
let size = Size::new(80, 24);
let rect = Rect::new(pos.x, pos.y, size.width, size.height);

// Alignment for content within areas
let center = Alignment::Center;
```

# Advanced Features

## Margins and Spacing

Add spacing around areas using uniform margins or between layout segments using [`Spacing`](../index.md):

```rust
use ratatui_core::layout::{Constraint, Layout, Margin, Rect, Spacing};

let layout = Layout::vertical([Constraint::Fill(1), Constraint::Fill(1)])
    .margin(2) // 2-cell margin on all sides
    .spacing(Spacing::Space(1)); // 1-cell spacing between segments

// For asymmetric margins, use the Rect inner method directly
let area = Rect::new(0, 0, 80, 24).inner(Margin::new(2, 1));
```

## Area Iteration

Iterate over rows, columns, or all positions within a rectangular area. The `rows()` and
`columns()` iterators return full [`Rect`](../index.md) regions that can be used to render widgets or
passed to other layout methods for more complex nested layouts. The `positions()` iterator
returns [`Position`](../index.md) values representing individual cell coordinates:

```rust
use ratatui_core::buffer::Buffer;
use ratatui_core::layout::{Constraint, Layout, Rect};
use ratatui_core::widgets::Widget;

let area = Rect::new(0, 0, 20, 10);
let mut buffer = Buffer::empty(area);

// Renders "Row 0", "Row 1", etc. in each horizontal row
for (i, row) in area.rows().enumerate() {
    format!("Row {i}").render(row, &mut buffer);
}

// Renders column indices (0-9 repeating) in each vertical column
for (i, col) in area.columns().enumerate() {
    format!("{}", i % 10).render(col, &mut buffer);
}

// Renders position indices (0-9 repeating) at each cell position
for (i, pos) in area.positions().enumerate() {
    buffer[pos].set_symbol(&format!("{}", i % 10));
}
```

# Performance Considerations

The layout system includes optional caching to improve performance for repeated layout
calculations. Layout caching is enabled by default in the main `ratatui` crate, but requires
explicitly enabling the `layout-cache` feature when using `ratatui-core` directly. When
enabled, layout results are cached based on the area and layout configuration.

# Related Documentation

For more detailed information and practical examples:

- [Layout Concepts](https://ratatui.rs/concepts/layout/) - Comprehensive guide to layout
  concepts
- [Layout Recipes](https://ratatui.rs/recipes/layout/) - Practical layout examples and patterns
- [Grid Layout Recipe](https://ratatui.rs/recipes/layout/grid/) - Creating grid-based layouts
- [Center a Widget Recipe](https://ratatui.rs/recipes/layout/center-a-widget/) - Centering
  content
- [Dynamic Layouts Recipe](https://ratatui.rs/recipes/layout/dynamic/) - Creating responsive
  layouts

# Examples

See the Ratatui repository for complete examples:

- [`constraints`](https://github.com/ratatui/ratatui/blob/main/examples/apps/constraints/) -
  Demonstrates different constraint types
- [`flex`](https://github.com/ratatui/ratatui/blob/main/examples/apps/flex/) - Shows flex space
  distribution
- [`layout`](https://github.com/ratatui/ratatui/blob/main/examples/apps/layout/) - Basic layout
  examples

## Contents

- [Structs](#structs)
  - [`Layout`](#layout)
  - [`Margin`](#margin)
  - [`Offset`](#offset)
  - [`Position`](#position)
  - [`Columns`](#columns)
  - [`Positions`](#positions)
  - [`Rect`](#rect)
  - [`Rows`](#rows)
  - [`Size`](#size)
- [Enums](#enums)
  - [`HorizontalAlignment`](#horizontalalignment)
  - [`VerticalAlignment`](#verticalalignment)
  - [`Constraint`](#constraint)
  - [`Direction`](#direction)
  - [`Flex`](#flex)
  - [`Spacing`](#spacing)
- [Type Aliases](#type-aliases)
  - [`Alignment`](#alignment)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Layout`](#layout) | struct |  |
| [`Margin`](#margin) | struct |  |
| [`Offset`](#offset) | struct |  |
| [`Position`](#position) | struct |  |
| [`Columns`](#columns) | struct |  |
| [`Positions`](#positions) | struct |  |
| [`Rect`](#rect) | struct |  |
| [`Rows`](#rows) | struct |  |
| [`Size`](#size) | struct |  |
| [`HorizontalAlignment`](#horizontalalignment) | enum |  |
| [`VerticalAlignment`](#verticalalignment) | enum |  |
| [`Constraint`](#constraint) | enum |  |
| [`Direction`](#direction) | enum |  |
| [`Flex`](#flex) | enum |  |
| [`Spacing`](#spacing) | enum |  |
| [`Alignment`](#alignment) | type |  |

## Structs

### `Layout`

```rust
struct Layout {
    // [REDACTED: Private Fields]
}
```

The primary layout engine for dividing terminal space using constraints and direction.

A layout is a set of constraints that can be applied to a given area to split it into smaller
rectangular areas. This is the core building block for creating structured user interfaces in
terminal applications.

A layout is composed of:
- a direction (horizontal or vertical)
- a set of constraints (length, ratio, percentage, fill, min, max)
- a margin (horizontal and vertical), the space between the edge of the main area and the split
  areas
- a flex option that controls space distribution
- a spacing option that controls gaps between segments

The algorithm used to compute the layout is based on the `kasuari` solver, a linear constraint
solver that computes positions and sizes to satisfy as many constraints as possible in order of
their priorities.

When the layout is computed, the result is cached in a thread-local cache, so that subsequent
calls with the same parameters are faster. The cache is a `LruCache`, and the size of the cache
can be configured using `Layout::init_cache()` when the `layout-cache` feature is enabled.

# Construction

- [`default`](Default::default) - Create a layout with default values (vertical direction, no
  constraints, no margin)
- [`new`](Self::new) - Create a new layout with a given direction and constraints
- [`vertical`](Self::vertical) - Create a new vertical layout with the given constraints
- [`horizontal`](Self::horizontal) - Create a new horizontal layout with the given constraints

# Configuration

- [`direction`](Self::direction) - Set the direction of the layout
- [`constraints`](Self::constraints) - Set the constraints of the layout
- [`margin`](Self::margin) - Set uniform margin on all sides
- [`horizontal_margin`](Self::horizontal_margin) - Set the horizontal margin of the layout
- [`vertical_margin`](Self::vertical_margin) - Set the vertical margin of the layout
- [`flex`](Self::flex) - Set the way space is distributed when constraints are satisfied
- [`spacing`](Self::spacing) - Set the gap between the constraints of the layout

# Layout Operations

- [`areas`](Self::areas) - Split area into fixed number of rectangles (compile-time known)
- [`spacers`](Self::spacers) - Get spacer rectangles between layout areas
- [`split`](Self::split) - Split area into rectangles (runtime determined count)
- [`split_with_spacers`](Self::split_with_spacers) - Split area and return both areas and
  spacers

# Cache Management

- [`init_cache`](Self::init_cache) - Initialize layout cache with custom size

# Example

```rust
use ratatui_core::buffer::Buffer;
use ratatui_core::layout::{Constraint, Direction, Layout, Rect};
use ratatui_core::text::Text;
use ratatui_core::widgets::Widget;

fn render(area: Rect, buf: &mut Buffer) {
    let layout = Layout::vertical([Constraint::Length(5), Constraint::Fill(1)]);
    let [top, bottom] = layout.areas(area);
    Text::from("foo").render(top, buf);
    Text::from("bar").render(bottom, buf);
}
```

See the `layout`, `flex`, and `constraints` examples in the [Examples] folder for more details
about how to use layouts.

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

![layout
example](https://camo.githubusercontent.com/77d22f3313b782a81e5e033ef82814bb48d786d2598699c27f8e757ccee62021/68747470733a2f2f7668732e636861726d2e73682f7668732d315a4e6f4e4c4e6c4c746b4a58706767396e435635652e676966)

#### Implementations

- `const DEFAULT_CACHE_SIZE: usize`

- `fn new<I>(direction: Direction, constraints: I) -> Self` — [`Direction`](../index.md#direction)

  Creates a new layout with default values.

  

  The `constraints` parameter accepts any type that implements `IntoIterator<Item =

  Into<Constraint>>`. This includes arrays, slices, vectors, iterators. `Into<Constraint>` is

  implemented on `u16`, so you can pass an array, `Vec`, etc. of `u16` to this function to

  create a layout with fixed size chunks.

  

  Default values for the other fields are:

  

  - `margin`: 0, 0

  - `flex`: [`Flex::Start`](../index.md)

  - `spacing`: 0

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Direction, Layout};

  

  Layout::new(

      Direction::Horizontal,

      [Constraint::Length(5), Constraint::Fill(1)],

  );

  

  Layout::new(

      Direction::Vertical,

      [1, 2, 3].iter().map(|&c| Constraint::Length(c)),

  );

  

  Layout::new(Direction::Horizontal, vec![1, 2]);

  ```

- `fn vertical<I>(constraints: I) -> Self`

  Creates a new vertical layout with default values.

  

  The `constraints` parameter accepts any type that implements `IntoIterator<Item =

  Into<Constraint>>`. This includes arrays, slices, vectors, iterators, etc.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout};

  

  let layout = Layout::vertical([Constraint::Length(5), Constraint::Fill(1)]);

  ```

- `fn horizontal<I>(constraints: I) -> Self`

  Creates a new horizontal layout with default values.

  

  The `constraints` parameter accepts any type that implements `IntoIterator<Item =

  Into<Constraint>>`. This includes arrays, slices, vectors, iterators, etc.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout};

  

  let layout = Layout::horizontal([Constraint::Length(5), Constraint::Fill(1)]);

  ```

- `fn init_cache(cache_size: NonZeroUsize)`

  Initialize an empty cache with a custom size. The cache is keyed on the layout and area, so

  that subsequent calls with the same parameters are faster. The cache is a `LruCache`, and

  grows until `cache_size` is reached.

  

  By default, the cache size is `Self::DEFAULT_CACHE_SIZE`.

- `const fn direction(self, direction: Direction) -> Self` — [`Direction`](../index.md#direction)

  Set the direction of the layout.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Direction, Layout, Rect};

  

  let layout = Layout::default()

      .direction(Direction::Horizontal)

      .constraints([Constraint::Length(5), Constraint::Fill(1)])

      .split(Rect::new(0, 0, 10, 10));

  assert_eq!(layout[..], [Rect::new(0, 0, 5, 10), Rect::new(5, 0, 5, 10)]);

  

  let layout = Layout::default()

      .direction(Direction::Vertical)

      .constraints([Constraint::Length(5), Constraint::Fill(1)])

      .split(Rect::new(0, 0, 10, 10));

  assert_eq!(layout[..], [Rect::new(0, 0, 10, 5), Rect::new(0, 5, 10, 5)]);

  ```

- `fn constraints<I>(self, constraints: I) -> Self`

  Sets the constraints of the layout.

  

  The `constraints` parameter accepts any type that implements `IntoIterator<Item =

  Into<Constraint>>`. This includes arrays, slices, vectors, iterators. `Into<Constraint>` is

  implemented on u16, so you can pass an array or vec of u16 to this function to create a

  layout with fixed size chunks.

  

  Note that the constraints are applied to the whole area that is to be split, so using

  percentages and ratios with the other constraints may not have the desired effect of

  splitting the area up. (e.g. splitting 100 into [min 20, 50%, 50%], may not result in [20,

  40, 40] but rather an indeterminate result between [20, 50, 30] and [20, 30, 50]).

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let layout = Layout::default()

      .constraints([

          Constraint::Percentage(20),

          Constraint::Ratio(1, 5),

          Constraint::Length(2),

          Constraint::Min(2),

          Constraint::Max(2),

      ])

      .split(Rect::new(0, 0, 10, 10));

  assert_eq!(

      layout[..],

      [

          Rect::new(0, 0, 10, 2),

          Rect::new(0, 2, 10, 2),

          Rect::new(0, 4, 10, 2),

          Rect::new(0, 6, 10, 2),

          Rect::new(0, 8, 10, 2),

      ]

  );

  

  Layout::default().constraints([Constraint::Fill(1)]);

  Layout::default().constraints(&[Constraint::Fill(1)]);

  Layout::default().constraints(vec![Constraint::Fill(1)]);

  Layout::default().constraints([Constraint::Fill(1)].iter().filter(|_| true));

  Layout::default().constraints([1, 2, 3].iter().map(|&c| Constraint::Length(c)));

  Layout::default().constraints([1, 2, 3]);

  Layout::default().constraints(vec![1, 2, 3]);

  ```

- `const fn margin(self, margin: u16) -> Self`

  Set the margin of the layout.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let layout = Layout::default()

      .constraints([Constraint::Fill(1)])

      .margin(2)

      .split(Rect::new(0, 0, 10, 10));

  assert_eq!(layout[..], [Rect::new(2, 2, 6, 6)]);

  ```

- `const fn horizontal_margin(self, horizontal: u16) -> Self`

  Set the horizontal margin of the layout.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let layout = Layout::default()

      .constraints([Constraint::Fill(1)])

      .horizontal_margin(2)

      .split(Rect::new(0, 0, 10, 10));

  assert_eq!(layout[..], [Rect::new(2, 0, 6, 10)]);

  ```

- `const fn vertical_margin(self, vertical: u16) -> Self`

  Set the vertical margin of the layout.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let layout = Layout::default()

      .constraints([Constraint::Fill(1)])

      .vertical_margin(2)

      .split(Rect::new(0, 0, 10, 10));

  assert_eq!(layout[..], [Rect::new(0, 2, 10, 6)]);

  ```

- `const fn flex(self, flex: Flex) -> Self` — [`Flex`](../index.md#flex)

  The `flex` method  allows you to specify the flex behavior of the layout.

  

  # Arguments

  

  * `flex`: A [`Flex`](../index.md) enum value that represents the flex behavior of the layout. It can be

    one of the following:

    - [`Flex::Legacy`](../index.md): The last item is stretched to fill the excess space.

    - [`Flex::Start`](../index.md): The items are aligned to the start of the layout.

    - [`Flex::Center`](../index.md): The items are aligned to the center of the layout.

    - [`Flex::End`](../index.md): The items are aligned to the end of the layout.

    - [`Flex::SpaceBetween`](../index.md): The items are evenly distributed with equal space between them.

    - [`Flex::SpaceAround`](../index.md): The items are evenly distributed with equal space around them,

      except the first and last items, which have half the space on their sides.

    - [`Flex::SpaceEvenly`](../index.md): The items are evenly distributed with equal space around them.

  

  # Examples

  

  In this example, the items in the layout will be aligned to the start.

  

  ```rust

  use ratatui_core::layout::Constraint::*;

  use ratatui_core::layout::{Flex, Layout};

  

  let layout = Layout::horizontal([Length(20), Length(20), Length(20)]).flex(Flex::Start);

  ```

  

  In this example, the items in the layout will be stretched equally to fill the available

  space.

  

  ```rust

  use ratatui_core::layout::Constraint::*;

  use ratatui_core::layout::{Flex, Layout};

  

  let layout = Layout::horizontal([Length(20), Length(20), Length(20)]).flex(Flex::Legacy);

  ```

- `fn spacing<T>(self, spacing: T) -> Self`

  Sets the spacing between items in the layout.

  

  The `spacing` method sets the spacing between items in the layout. The spacing is applied

  evenly between all segments. The spacing value represents the number of cells between each

  item.

  

  Spacing can be positive integers, representing gaps between segments; or negative integers

  representing overlaps. Additionally, one of the variants of the [`Spacing`](../index.md) enum can be

  passed to this function. See the documentation of the [`Spacing`](../index.md) enum for more information.

  

  Note that if the layout has only one segment, the spacing will not be applied.

  Also, spacing will not be applied for [`Flex::SpaceAround`](../index.md), [`Flex::SpaceEvenly`](../index.md) and

  [`Flex::SpaceBetween`](../index.md)

  

  # Examples

  

  In this example, the spacing between each item in the layout is set to 2 cells.

  

  ```rust

  use ratatui_core::layout::Constraint::*;

  use ratatui_core::layout::Layout;

  

  let layout = Layout::horizontal([Length(20), Length(20), Length(20)]).spacing(2);

  ```

  

  In this example, the spacing between each item in the layout is set to -1 cells, i.e. the

  three segments will have an overlapping border.

  

  ```rust

  use ratatui_core::layout::Constraint::*;

  use ratatui_core::layout::Layout;

  let layout = Layout::horizontal([Length(20), Length(20), Length(20)]).spacing(-1);

  ```

- `fn areas<const N: usize>(&self, area: Rect) -> [Rect; N]` — [`Rect`](../index.md#rect)

  Split the rect into a number of sub-rects according to the given [`Layout`](../index.md).

  

  An ergonomic wrapper around `Layout::split` that returns an array of `Rect`s instead of

  `Rc<[Rect]>`.

  

  This method requires the number of constraints to be known at compile time. If you don't

  know the number of constraints at compile time, use `Layout::split` instead.

  

  # Panics

  

  Panics if the number of constraints is not equal to the length of the returned array.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let area = Rect::new(0, 0, 10, 10);

  let layout = Layout::vertical([Constraint::Length(1), Constraint::Fill(1)]);

  let [top, main] = layout.areas(area);

  

  // or explicitly specify the number of constraints:

  let areas = layout.areas::<2>(area);

  ```

- `fn try_areas<const N: usize>(&self, area: Rect) -> Result<[Rect; N], TryFromSliceError>` — [`Rect`](../index.md#rect)

  Split the rect into a number of sub-rects according to the given [`Layout`](../index.md).

  

  An ergonomic wrapper around `Layout::split` that returns an array of `Rect`s instead of

  `Rc<[Rect]>`.

  

  This method requires the number of constraints to be known at compile time. If you don't

  know the number of constraints at compile time, use `Layout::split` instead.

  

  # Errors

  

  Returns an error if the number of constraints is not equal to the length of the returned

  array.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let area = Rect::new(0, 0, 10, 10);

  let layout = Layout::vertical([Constraint::Length(1), Constraint::Min(0)]);

  let [top, main] = layout.try_areas(area)?;

  

  // or explicitly specify the number of constraints:

  let areas = layout.try_areas::<2>(area)?;

  Ok::<(), core::array::TryFromSliceError>(())

  ```

- `fn spacers<const N: usize>(&self, area: Rect) -> [Rect; N]` — [`Rect`](../index.md#rect)

  Split the rect into a number of sub-rects according to the given [`Layout`](../index.md) and return just

  the spacers between the areas.

  

  This method requires the number of constraints to be known at compile time. If you don't

  know the number of constraints at compile time, use `Layout::split_with_spacers` instead.

  

  This method is similar to `Layout::areas`, and can be called with the same parameters, but

  it returns just the spacers between the areas. The result of calling the `areas` method is

  cached, so this will generally not re-run the solver, but will just return the cached

  result.

  

  # Panics

  

  Panics if the number of constraints + 1 is not equal to the length of the returned array.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let area = Rect::new(0, 0, 10, 10);

  let layout = Layout::vertical([Constraint::Length(1), Constraint::Fill(1)]);

  let [top, main] = layout.areas(area);

  let [before, inbetween, after] = layout.spacers(area);

  

  // or explicitly specify the number of constraints:

  let spacers = layout.spacers::<3>(area);

  ```

- `fn split(&self, area: Rect) -> alloc::rc::Rc<[crate::layout::Rect]>` — [`Rect`](../index.md#rect)

  Wrapper function around the `kasuari` solver to be able to split a given area into

  smaller ones based on the preferred widths or heights and the direction.

  

  Note that the constraints are applied to the whole area that is to be split, so using

  percentages and ratios with the other constraints may not have the desired effect of

  splitting the area up. (e.g. splitting 100 into [min 20, 50%, 50%], may not result in [20,

  40, 40] but rather an indeterminate result between [20, 50, 30] and [20, 30, 50]).

  

  This method stores the result of the computation in a thread-local cache keyed on the layout

  and area, so that subsequent calls with the same parameters are faster. The cache is a

  `LruCache`, and grows until `Self::DEFAULT_CACHE_SIZE` is reached by default. If the cache

  is initialized with `Layout::init_cache()`, it grows until the initialized cache size.

  

  There is a helper method that can be used to split the whole area into smaller ones based on

  the layout: `Layout::areas()`. That method is a shortcut for calling this method. It

  allows you to destructure the result directly into variables, which is useful when you know

  at compile time the number of areas that will be created.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Direction, Layout, Rect};

  let layout = Layout::default()

      .direction(Direction::Vertical)

      .constraints([Constraint::Length(5), Constraint::Fill(1)])

      .split(Rect::new(2, 2, 10, 10));

  assert_eq!(layout[..], [Rect::new(2, 2, 10, 5), Rect::new(2, 7, 10, 5)]);

  

  let layout = Layout::default()

      .direction(Direction::Horizontal)

      .constraints([Constraint::Ratio(1, 3), Constraint::Ratio(2, 3)])

      .split(Rect::new(0, 0, 9, 2));

  assert_eq!(layout[..], [Rect::new(0, 0, 3, 2), Rect::new(3, 0, 6, 2)]);

  ```

- `fn split_with_spacers(&self, area: Rect) -> (alloc::rc::Rc<[crate::layout::Rect]>, alloc::rc::Rc<[crate::layout::Rect]>)` — [`Rect`](../index.md#rect)

  Wrapper function around the `kasuari` solver that splits the given area into smaller ones

  based on the preferred widths or heights and the direction, with the ability to include

  spacers between the areas.

  

  This method is similar to `split`, but it returns two sets of rectangles: one for the areas

  and one for the spacers.

  

  This method stores the result of the computation in a thread-local cache keyed on the layout

  and area, so that subsequent calls with the same parameters are faster. The cache is a

  `LruCache`, and grows until `Self::DEFAULT_CACHE_SIZE` is reached by default. If the cache

  is initialized with `Layout::init_cache()`, it grows until the initialized cache size.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Direction, Layout, Rect};

  

  let (areas, spacers) = Layout::default()

      .direction(Direction::Vertical)

      .constraints([Constraint::Length(5), Constraint::Fill(1)])

      .split_with_spacers(Rect::new(2, 2, 10, 10));

  assert_eq!(areas[..], [Rect::new(2, 2, 10, 5), Rect::new(2, 7, 10, 5)]);

  assert_eq!(

      spacers[..],

      [

          Rect::new(2, 2, 10, 0),

          Rect::new(2, 7, 10, 0),

          Rect::new(2, 12, 10, 0)

      ]

  );

  

  let (areas, spacers) = Layout::default()

      .direction(Direction::Horizontal)

      .spacing(1)

      .constraints([Constraint::Ratio(1, 3), Constraint::Ratio(2, 3)])

      .split_with_spacers(Rect::new(0, 0, 10, 2));

  assert_eq!(areas[..], [Rect::new(0, 0, 3, 2), Rect::new(4, 0, 6, 2)]);

  assert_eq!(

      spacers[..],

      [

          Rect::new(0, 0, 0, 2),

          Rect::new(3, 0, 1, 2),

          Rect::new(10, 0, 0, 2)

      ]

  );

  ```

#### Trait Implementations

##### `impl Clone for Layout`

- `fn clone(&self) -> Layout` — [`Layout`](../index.md#layout)

##### `impl Debug for Layout`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Layout`

- `fn default() -> Layout` — [`Layout`](../index.md#layout)

##### `impl Eq for Layout`

##### `impl<K> Equivalent for Layout`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Layout`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Layout`

##### `impl PartialEq for Layout`

- `fn eq(&self, other: &Layout) -> bool` — [`Layout`](../index.md#layout)

##### `impl StructuralPartialEq for Layout`

### `Margin`

```rust
struct Margin {
    pub horizontal: u16,
    pub vertical: u16,
}
```

Represents spacing around rectangular areas.

`Margin` defines the horizontal and vertical spacing that should be applied around a rectangular
area. It's commonly used with [`Layout`](crate::layout::Layout) to add space between the
layout's boundaries and its contents, or with [`Rect::inner`](crate::layout::Rect::inner) and
[`Rect::outer`](crate::layout::Rect::outer) to create padded areas.

The margin values represent the number of character cells to add on each side. For horizontal
margin, the space is applied to both the left and right sides. For vertical margin, the space
is applied to both the top and bottom sides.

# Construction

- [`new`](Self::new) - Create a new margin with horizontal and vertical spacing
- [`default`](Default::default) - Create with zero margin

# Examples

```rust
use ratatui_core::layout::{Constraint, Layout, Margin, Rect};

// Create a margin of 2 cells horizontally and 1 cell vertically
let margin = Margin::new(2, 1);

// Apply directly to a rectangle
let area = Rect::new(0, 0, 80, 24);
let inner_area = area.inner(margin);

// Or use with a layout (which only accepts uniform margins)
let layout = Layout::vertical([Constraint::Fill(1)]).margin(2);
```

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Implementations

- `const fn new(horizontal: u16, vertical: u16) -> Self`

#### Trait Implementations

##### `impl Clone for Margin`

- `fn clone(&self) -> Margin` — [`Margin`](../index.md#margin)

##### `impl Copy for Margin`

##### `impl Debug for Margin`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Margin`

- `fn default() -> Margin` — [`Margin`](../index.md#margin)

##### `impl Display for Margin`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Margin`

##### `impl<K> Equivalent for Margin`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Margin`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Margin`

##### `impl PartialEq for Margin`

- `fn eq(&self, other: &Margin) -> bool` — [`Margin`](../index.md#margin)

##### `impl StructuralPartialEq for Margin`

##### `impl ToCompactString for Margin`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Margin`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Margin`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Margin`

- `fn to_string(&self) -> String`

##### `impl ToText for Margin`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `Offset`

```rust
struct Offset {
    pub x: i32,
    pub y: i32,
}
```

Amounts by which to move a [`Rect`](crate::layout::Rect).

Positive numbers move to the right/bottom and negative to the left/top.

See [`Rect::offset`](crate::layout::Rect::offset) for usage.

#### Fields

- **`x`**: `i32`

  How much to move on the X axis

- **`y`**: `i32`

  How much to move on the Y axis

#### Implementations

- `const ZERO: Self`

- `const MIN: Self`

- `const MAX: Self`

- `const fn new(x: i32, y: i32) -> Self`

  Creates a new `Offset` with the given values.

#### Trait Implementations

##### `impl Add for Position`

- `type Output = Position`

- `fn add(self, offset: Offset) -> Self` — [`Offset`](../index.md#offset)

  Moves the position by the given offset.

  

  Values that would move the position outside the `u16` range are clamped to the nearest

  edge.

##### `impl AddAssign for Position`

- `fn add_assign(&mut self, offset: Offset)` — [`Offset`](../index.md#offset)

  Moves the position in place by the given offset.

  

  Values that would move the position outside the `u16` range are clamped to the nearest

  edge.

##### `impl Clone for Offset`

- `fn clone(&self) -> Offset` — [`Offset`](../index.md#offset)

##### `impl Copy for Offset`

##### `impl Debug for Offset`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Offset`

- `fn default() -> Offset` — [`Offset`](../index.md#offset)

##### `impl Eq for Offset`

##### `impl<K> Equivalent for Offset`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Offset`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Offset`

##### `impl Neg for crate::layout::Offset`

- `type Output = Offset`

- `fn neg(self) -> Self`

  Negates the offset.

  

  # Panics

  

  Panics if the negated value overflows (i.e. `x` or `y` is `i32::MIN`).

##### `impl PartialEq for Offset`

- `fn eq(&self, other: &Offset) -> bool` — [`Offset`](../index.md#offset)

##### `impl StructuralPartialEq for Offset`

##### `impl Sub for Position`

- `type Output = Position`

- `fn sub(self, offset: Offset) -> Self` — [`Offset`](../index.md#offset)

  Moves the position by the inverse of the given offset.

  

  Values that would move the position outside the `u16` range are clamped to the nearest

  edge.

##### `impl SubAssign for Position`

- `fn sub_assign(&mut self, offset: Offset)` — [`Offset`](../index.md#offset)

  Moves the position in place by the inverse of the given offset.

  

  Values that would move the position outside the `u16` range are clamped to the nearest

  edge.

### `Position`

```rust
struct Position {
    pub x: u16,
    pub y: u16,
}
```

Position in the terminal coordinate system.

The position is relative to the top left corner of the terminal window, with the top left corner
being (0, 0). The x axis is horizontal increasing to the right, and the y axis is vertical
increasing downwards.

`Position` is used throughout the layout system to represent specific points in the terminal.
It can be created from coordinates, tuples, or extracted from rectangular areas.

# Construction

- [`new`](Self::new) - Create a new position from x and y coordinates
- [`default`](Default::default) - Create at origin (0, 0)

# Conversion

- [`from((u16, u16))`](Self::from) - Create from `(u16, u16)` tuple
- [`from(Rect)`](Self::from) - Create from [`Rect`](../index.md) (uses top-left corner)
- `into((u16, u16))` - Convert to `(u16, u16)` tuple

# Movement

- [`offset`](Self::offset) - Move by an [`Offset`](../index.md)
- [`Add<Offset>`](core::ops::Add) and [`Sub<Offset>`](core::ops::Sub) - Shift by offsets with
  clamping
- [`AddAssign<Offset>`](core::ops::AddAssign) and [`SubAssign<Offset>`](core::ops::SubAssign) -
  In-place shifting

# Examples

```rust
use ratatui_core::layout::{Offset, Position, Rect};

// the following are all equivalent
let position = Position { x: 1, y: 2 };
let position = Position::new(1, 2);
let position = Position::from((1, 2));
let position = Position::from(Rect::new(1, 2, 3, 4));

// position can be converted back into the components when needed
let (x, y) = position.into();

// movement by offsets
let position = Position::new(5, 5) + Offset::new(2, -3);
assert_eq!(position, Position::new(7, 2));
```

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Fields

- **`x`**: `u16`

  The x coordinate of the position
  
  The x coordinate is relative to the left edge of the terminal window, with the left edge
  being 0.

- **`y`**: `u16`

  The y coordinate of the position
  
  The y coordinate is relative to the top edge of the terminal window, with the top edge
  being 0.

#### Implementations

- `const ORIGIN: Self`

- `const MIN: Self`

- `const MAX: Self`

- `const fn new(x: u16, y: u16) -> Self`

  Create a new position

- `fn offset(self, offset: Offset) -> Self` — [`Offset`](../index.md#offset)

  Moves the position by the given offset.

  

  Positive offsets move right and down, negative offsets move left and up. Values that would

  move the position outside the `u16` range are clamped to the nearest edge.

#### Trait Implementations

##### `impl Add for Position`

- `type Output = Position`

- `fn add(self, offset: Offset) -> Self` — [`Offset`](../index.md#offset)

  Moves the position by the given offset.

  

  Values that would move the position outside the `u16` range are clamped to the nearest

  edge.

##### `impl AddAssign for Position`

- `fn add_assign(&mut self, offset: Offset)` — [`Offset`](../index.md#offset)

  Moves the position in place by the given offset.

  

  Values that would move the position outside the `u16` range are clamped to the nearest

  edge.

##### `impl Clone for Position`

- `fn clone(&self) -> Position` — [`Position`](../index.md#position)

##### `impl<K> Comparable for Position`

- `fn compare(&self, key: &K) -> Ordering`

##### `impl Copy for Position`

##### `impl Debug for Position`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Position`

- `fn default() -> Position` — [`Position`](../index.md#position)

##### `impl Display for Position`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Position`

##### `impl<K> Equivalent for Position`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Position`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Position`

##### `impl Ord for Position`

- `fn cmp(&self, other: &Position) -> cmp::Ordering` — [`Position`](../index.md#position)

##### `impl PartialEq for Position`

- `fn eq(&self, other: &Position) -> bool` — [`Position`](../index.md#position)

##### `impl PartialOrd for Position`

- `fn partial_cmp(&self, other: &Position) -> option::Option<cmp::Ordering>` — [`Position`](../index.md#position)

##### `impl StructuralPartialEq for Position`

##### `impl Sub for Position`

- `type Output = Position`

- `fn sub(self, offset: Offset) -> Self` — [`Offset`](../index.md#offset)

  Moves the position by the inverse of the given offset.

  

  Values that would move the position outside the `u16` range are clamped to the nearest

  edge.

##### `impl SubAssign for Position`

- `fn sub_assign(&mut self, offset: Offset)` — [`Offset`](../index.md#offset)

  Moves the position in place by the inverse of the given offset.

  

  Values that would move the position outside the `u16` range are clamped to the nearest

  edge.

##### `impl ToCompactString for Position`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Position`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Position`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Position`

- `fn to_string(&self) -> String`

##### `impl ToText for Position`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `Columns`

```rust
struct Columns {
    // [REDACTED: Private Fields]
}
```

An iterator over columns within a `Rect`.

#### Implementations

- `const fn new(rect: Rect) -> Self` — [`Rect`](../index.md#rect)

  Creates a new `Columns` iterator.

#### Trait Implementations

##### `impl DoubleEndedIterator for Columns`

- `fn next_back(&mut self) -> Option<<Self as >::Item>`

  Retrieves the previous column within the `Rect`.

  

  Returns `None` when there are no more columns to iterate through.

##### `impl IntoEither for Columns`

##### `impl IntoIterator for Columns`

- `type Item = <I as Iterator>::Item`

- `type IntoIter = I`

- `fn into_iter(self) -> I`

##### `impl Iterator for Columns`

- `type Item = Rect`

- `fn next(&mut self) -> Option<<Self as >::Item>`

  Retrieves the next column within the `Rect`.

  

  Returns `None` when there are no more columns to iterate through.

- `fn size_hint(&self) -> (usize, Option<usize>)`

##### `impl Itertools for Columns`

### `Positions`

```rust
struct Positions {
    // [REDACTED: Private Fields]
}
```

An iterator over positions within a `Rect`.

The iterator will yield all positions within the `Rect` in a row-major order.

#### Implementations

- `const fn new(rect: Rect) -> Self` — [`Rect`](../index.md#rect)

  Creates a new `Positions` iterator.

#### Trait Implementations

##### `impl IntoEither for Positions`

##### `impl IntoIterator for Positions`

- `type Item = <I as Iterator>::Item`

- `type IntoIter = I`

- `fn into_iter(self) -> I`

##### `impl Iterator for Positions`

- `type Item = Position`

- `fn next(&mut self) -> Option<<Self as >::Item>`

  Retrieves the next position within the `Rect`.

  

  Returns `None` when there are no more positions to iterate through.

- `fn size_hint(&self) -> (usize, Option<usize>)`

##### `impl Itertools for Positions`

### `Rect`

```rust
struct Rect {
    pub x: u16,
    pub y: u16,
    pub width: u16,
    pub height: u16,
}
```

A rectangular area in the terminal.

A `Rect` represents a rectangular region in the terminal coordinate system, defined by its
top-left corner position and dimensions. This is the fundamental building block for all layout
operations and widget rendering in Ratatui.

Rectangles are used throughout the layout system to define areas where widgets can be rendered.
They are typically created by [`Layout`](../index.md) operations that divide terminal space, but can also be
manually constructed for specific positioning needs.

The coordinate system uses the top-left corner as the origin (0, 0), with x increasing to the
right and y increasing downward. All measurements are in character cells.

# Construction and Conversion

- [`new`](Self::new) - Create a new rectangle from coordinates and dimensions
- [`as_position`](Self::as_position) - Convert to a position at the top-left corner
- [`as_size`](Self::as_size) - Convert to a size representing the dimensions
- [`from((Position, Size))`](Self::from) - Create from `(Position, Size)` tuple
- [`from(((u16, u16), (u16, u16)))`](Self::from) - Create from `((u16, u16), (u16, u16))`
  coordinate and dimension tuples
- `into((Position, Size))` - Convert to `(Position, Size)` tuple
- [`default`](Self::default) - Create a zero-sized rectangle at origin

# Geometry and Properties

- [`area`](Self::area) - Calculate the total area in character cells
- [`is_empty`](Self::is_empty) - Check if the rectangle has zero area
- [`left`](Self::left), [`right`](Self::right), [`top`](Self::top), [`bottom`](Self::bottom) -
  Get edge coordinates

# Spatial Operations

- [`inner`](Self::inner), [`outer`](Self::outer) - Apply margins to shrink or expand
- [`offset`](Self::offset) - Move the rectangle by a relative amount
- [`resize`](Self::resize) - Change the rectangle size while keeping the bottom/right in range
- [`union`](Self::union) - Combine with another rectangle to create a bounding box
- [`intersection`](Self::intersection) - Find the overlapping area with another rectangle
- [`clamp`](Self::clamp) - Constrain the rectangle to fit within another

# Positioning and Centering

- [`centered_horizontally`](Self::centered_horizontally) - Center horizontally within a
  constraint
- [`centered_vertically`](Self::centered_vertically) - Center vertically within a constraint
- [`centered`](Self::centered) - Center both horizontally and vertically

# Testing and Iteration

- [`contains`](Self::contains) - Check if a position is within the rectangle
- [`intersects`](Self::intersects) - Check if it overlaps with another rectangle
- [`rows`](Self::rows) - Iterate over horizontal rows within the rectangle
- [`columns`](Self::columns) - Iterate over vertical columns within the rectangle
- [`positions`](Self::positions) - Iterate over all positions within the rectangle

# Examples

To create a new `Rect`, use `Rect::new`. The size of the `Rect` will be clamped to keep the
right and bottom coordinates within `u16`. Note that this clamping does not occur when creating
a `Rect` directly.

```rust
use ratatui_core::layout::Rect;

let rect = Rect::new(1, 2, 3, 4);
assert_eq!(
    rect,
    Rect {
        x: 1,
        y: 2,
        width: 3,
        height: 4
    }
);
```

You can also create a `Rect` from a [`Position`](../index.md) and a [`Size`](../index.md).

```rust
use ratatui_core::layout::{Position, Rect, Size};

let position = Position::new(1, 2);
let size = Size::new(3, 4);
let rect = Rect::from((position, size));
assert_eq!(
    rect,
    Rect {
        x: 1,
        y: 2,
        width: 3,
        height: 4
    }
);
```

To move a `Rect` without modifying its size, add or subtract an [`Offset`](../index.md) to it.

```rust
use ratatui_core::layout::{Offset, Rect};

let rect = Rect::new(1, 2, 3, 4);
let offset = Offset::new(5, 6);
let moved_rect = rect + offset;
assert_eq!(moved_rect, Rect::new(6, 8, 3, 4));
```

To resize a `Rect` while ensuring it stays within bounds, use `Rect::resize`. The size is
clamped so that `right()` and `bottom()` do not exceed `u16::MAX`.

```rust
use ratatui_core::layout::{Rect, Size};

let rect = Rect::new(u16::MAX - 1, u16::MAX - 1, 1, 1).resize(Size::new(10, 10));
assert_eq!(rect, Rect::new(u16::MAX - 1, u16::MAX - 1, 1, 1));
```

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Fields

- **`x`**: `u16`

  The x coordinate of the top left corner of the `Rect`.

- **`y`**: `u16`

  The y coordinate of the top left corner of the `Rect`.

- **`width`**: `u16`

  The width of the `Rect`.

- **`height`**: `u16`

  The height of the `Rect`.

#### Implementations

- `const ZERO: Self`

- `const MIN: Self`

- `const MAX: Self`

- `const fn new(x: u16, y: u16, width: u16, height: u16) -> Self`

  Creates a new `Rect`, with width and height limited to keep both bounds within `u16`.

  

  If the width or height would cause the right or bottom coordinate to be larger than the

  maximum value of `u16`, the width or height will be clamped to keep the right or bottom

  coordinate within `u16`.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::Rect;

  

  let rect = Rect::new(1, 2, 3, 4);

  ```

- `const fn area(self) -> u32`

  The area of the `Rect`.

- `const fn is_empty(self) -> bool`

  Returns true if the `Rect` has no area.

- `const fn left(self) -> u16`

  Returns the left coordinate of the `Rect`.

- `const fn right(self) -> u16`

  Returns the right coordinate of the `Rect`. This is the first coordinate outside of the

  `Rect`.

  

  If the right coordinate is larger than the maximum value of u16, it will be clamped to

  `u16::MAX`.

- `const fn top(self) -> u16`

  Returns the top coordinate of the `Rect`.

- `const fn bottom(self) -> u16`

  Returns the bottom coordinate of the `Rect`. This is the first coordinate outside of the

  `Rect`.

  

  If the bottom coordinate is larger than the maximum value of u16, it will be clamped to

  `u16::MAX`.

- `const fn inner(self, margin: Margin) -> Self` — [`Margin`](../index.md#margin)

  Returns a new `Rect` inside the current one, with the given margin on each side.

  

  If the margin is larger than the `Rect`, the returned `Rect` will have no area.

- `const fn outer(self, margin: Margin) -> Self` — [`Margin`](../index.md#margin)

  Returns a new `Rect` outside the current one, with the given margin applied on each side.

  

  If the margin causes the `Rect`'s bounds to be outside the range of a `u16`, the `Rect` will

  be truncated to keep the bounds within `u16`. This will cause the size of the `Rect` to

  change.

  

  The generated `Rect` may not fit inside the buffer or containing area, so it consider

  constraining the resulting `Rect` with `Rect::clamp` before using it.

- `fn offset(self, offset: Offset) -> Self` — [`Offset`](../index.md#offset)

  Moves the `Rect` without modifying its size.

  

  Moves the `Rect` according to the given offset without modifying its [`width`](Rect::width)

  or [`height`](Rect::height).

  - Positive `x` moves the whole `Rect` to the right, negative to the left.

  - Positive `y` moves the whole `Rect` to the bottom, negative to the top.

  

  See [`Offset`](../index.md) for details.

- `const fn resize(self, size: Size) -> Self` — [`Size`](../index.md#size)

  Resizes the `Rect`, clamping to keep the right and bottom within `u16::MAX`.

  

  The position is preserved. If the requested size would push the `Rect` beyond the bounds of

  `u16`, the width or height is reduced so that [`right`](Self::right) and

  [`bottom`](Self::bottom) remain within range.

- `fn union(self, other: Self) -> Self`

  Returns a new `Rect` that contains both the current one and the given one.

- `fn intersection(self, other: Self) -> Self`

  Returns a new `Rect` that is the intersection of the current one and the given one.

  

  If the two `Rect`s do not intersect, the returned `Rect` will have no area.

- `const fn intersects(self, other: Self) -> bool`

  Returns true if the two `Rect`s intersect.

- `const fn contains(self, position: Position) -> bool` — [`Position`](../index.md#position)

  Returns true if the given position is inside the `Rect`.

  

  The position is considered inside the `Rect` if it is on the `Rect`'s border.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Position, Rect};

  

  let rect = Rect::new(1, 2, 3, 4);

  assert!(rect.contains(Position { x: 1, y: 2 }));

  ````

- `fn clamp(self, other: Self) -> Self`

  Clamp this `Rect` to fit inside the other `Rect`.

  

  If the width or height of this `Rect` is larger than the other `Rect`, it will be clamped to

  the other `Rect`'s width or height.

  

  If the left or top coordinate of this `Rect` is smaller than the other `Rect`, it will be

  clamped to the other `Rect`'s left or top coordinate.

  

  If the right or bottom coordinate of this `Rect` is larger than the other `Rect`, it will be

  clamped to the other `Rect`'s right or bottom coordinate.

  

  This is different from `Rect::intersection` because it will move this `Rect` to fit inside

  the other `Rect`, while `Rect::intersection` instead would keep this `Rect`'s position and

  truncate its size to only that which is inside the other `Rect`.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::Rect;

  

  let area = Rect::new(0, 0, 100, 100);

  let rect = Rect::new(80, 80, 30, 30).clamp(area);

  assert_eq!(rect, Rect::new(70, 70, 30, 30));

  ```

- `const fn rows(self) -> Rows` — [`Rows`](../index.md#rows)

  An iterator over rows within the `Rect`.

  

  Each row is a full `Rect` region with height 1 that can be used for rendering widgets

  or as input to further layout methods.

  

  # Example

  

  ```rust

  use ratatui_core::buffer::Buffer;

  use ratatui_core::layout::{Constraint, Layout, Rect};

  use ratatui_core::widgets::Widget;

  

  fn render_list(area: Rect, buf: &mut Buffer) {

      // Renders "Item 0", "Item 1", etc. in each row

      for (i, row) in area.rows().enumerate() {

          format!("Item {i}").render(row, buf);

      }

  }

  

  fn render_with_nested_layout(area: Rect, buf: &mut Buffer) {

      // Splits each row into left/right areas and renders labels and content

      for (i, row) in area.rows().take(3).enumerate() {

          let [left, right] =

              Layout::horizontal([Constraint::Percentage(30), Constraint::Fill(1)]).areas(row);

  

          format!("{i}:").render(left, buf);

          "Content".render(right, buf);

      }

  }

  ```

- `const fn columns(self) -> Columns` — [`Columns`](../index.md#columns)

  An iterator over columns within the `Rect`.

  

  Each column is a full `Rect` region with width 1 that can be used for rendering widgets

  or as input to further layout methods.

  

  # Example

  

  ```rust

  use ratatui_core::buffer::Buffer;

  use ratatui_core::layout::Rect;

  use ratatui_core::widgets::Widget;

  

  fn render_columns(area: Rect, buf: &mut Buffer) {

      // Renders column indices (0-9 repeating) in each column

      for (i, column) in area.columns().enumerate() {

          format!("{}", i % 10).render(column, buf);

      }

  }

  ```

- `const fn positions(self) -> Positions` — [`Positions`](../index.md#positions)

  An iterator over the positions within the `Rect`.

  

  The positions are returned in a row-major order (left-to-right, top-to-bottom).

  Each position is a `Position` that represents a single cell coordinate.

  

  # Example

  

  ```rust

  use ratatui_core::buffer::Buffer;

  use ratatui_core::layout::{Position, Rect};

  use ratatui_core::widgets::Widget;

  

  fn render_positions(area: Rect, buf: &mut Buffer) {

      // Renders position indices (0-9 repeating) at each cell position

      for (i, position) in area.positions().enumerate() {

          buf[position].set_symbol(&format!("{}", i % 10));

      }

  }

  ```

- `const fn as_position(self) -> Position` — [`Position`](../index.md#position)

  Returns a [`Position`](../index.md) with the same coordinates as this `Rect`.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::Rect;

  

  let rect = Rect::new(1, 2, 3, 4);

  let position = rect.as_position();

  ````

- `const fn as_size(self) -> Size` — [`Size`](../index.md#size)

  Converts the `Rect` into a size struct.

- `fn centered_horizontally(self, constraint: Constraint) -> Self` — [`Constraint`](../index.md#constraint)

  Returns a new Rect, centered horizontally based on the provided constraint.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::Constraint;

  use ratatui_core::terminal::Frame;

  

  fn render(frame: &mut Frame) {

      let area = frame.area().centered_horizontally(Constraint::Ratio(1, 2));

  }

  ```

- `fn centered_vertically(self, constraint: Constraint) -> Self` — [`Constraint`](../index.md#constraint)

  Returns a new Rect, centered vertically based on the provided constraint.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::Constraint;

  use ratatui_core::terminal::Frame;

  

  fn render(frame: &mut Frame) {

      let area = frame.area().centered_vertically(Constraint::Ratio(1, 2));

  }

  ```

- `fn centered(self, horizontal_constraint: Constraint, vertical_constraint: Constraint) -> Self` — [`Constraint`](../index.md#constraint)

  Returns a new Rect, centered horizontally and vertically based on the provided constraints.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::Constraint;

  use ratatui_core::terminal::Frame;

  

  fn render(frame: &mut Frame) {

      let area = frame

          .area()

          .centered(Constraint::Ratio(1, 2), Constraint::Ratio(1, 3));

  }

  ```

- `fn layout<const N: usize>(self, layout: &Layout) -> [Self; N]` — [`Layout`](../index.md#layout)

  Split the rect into a number of sub-rects according to the given [`Layout`](../index.md).

  

  An ergonomic wrapper around `Layout::split` that returns an array of `Rect`s instead of

  `Rc<[Rect]>`.

  

  This method requires the number of constraints to be known at compile time. If you don't

  know the number of constraints at compile time, use `Layout::split` instead.

  

  # Panics

  

  Panics if the number of constraints is not equal to the length of the returned array.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let area = Rect::new(0, 0, 10, 10);

  let layout = Layout::vertical([Constraint::Length(1), Constraint::Min(0)]);

  let [top, main] = area.layout(&layout);

  assert_eq!(top, Rect::new(0, 0, 10, 1));

  assert_eq!(main, Rect::new(0, 1, 10, 9));

  

  // or explicitly specify the number of constraints:

  let areas = area.layout::<2>(&layout);

  assert_eq!(areas, [Rect::new(0, 0, 10, 1), Rect::new(0, 1, 10, 9),]);

  ```

- `fn layout_vec(self, layout: &Layout) -> alloc::vec::Vec<Self>` — [`Layout`](../index.md#layout)

  Split the rect into a number of sub-rects according to the given [`Layout`](../index.md).

  

  An ergonomic wrapper around `Layout::split` that returns a `Vec` of `Rect`s instead of

  `Rc<[Rect]>`.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let area = Rect::new(0, 0, 10, 10);

  let layout = Layout::vertical([Constraint::Length(1), Constraint::Min(0)]);

  let areas = area.layout_vec(&layout);

  assert_eq!(areas, vec![Rect::new(0, 0, 10, 1), Rect::new(0, 1, 10, 9),]);

  ```

- `fn try_layout<const N: usize>(self, layout: &Layout) -> Result<[Self; N], TryFromSliceError>` — [`Layout`](../index.md#layout)

  Try to split the rect into a number of sub-rects according to the given [`Layout`](../index.md).

  

  An ergonomic wrapper around `Layout::split` that returns an array of `Rect`s instead of

  `Rc<[Rect]>`.

  

  # Errors

  

  Returns an error if the number of constraints is not equal to the length of the returned

  array.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::{Constraint, Layout, Rect};

  

  let area = Rect::new(0, 0, 10, 10);

  let layout = Layout::vertical([Constraint::Length(1), Constraint::Min(0)]);

  let [top, main] = area.try_layout(&layout)?;

  assert_eq!(top, Rect::new(0, 0, 10, 1));

  assert_eq!(main, Rect::new(0, 1, 10, 9));

  

  // or explicitly specify the number of constraints:

  let areas = area.try_layout::<2>(&layout)?;

  assert_eq!(areas, [Rect::new(0, 0, 10, 1), Rect::new(0, 1, 10, 9),]);

  Ok::<(), core::array::TryFromSliceError>(())

  ``````

#### Trait Implementations

##### `impl Add for super::Rect`

- `type Output = Rect`

- `fn add(self, offset: Offset) -> Self` — [`Offset`](../index.md#offset)

  Moves the rect by an offset without changing its size.

  

  If the offset would move the any of the rect's edges outside the bounds of `u16`, the

  rect's position is clamped to the nearest edge.

##### `impl AddAssign for super::Rect`

- `fn add_assign(&mut self, offset: Offset)` — [`Offset`](../index.md#offset)

  Moves the rect by an offset in place without changing its size.

  

  If the offset would move the any of the rect's edges outside the bounds of `u16`, the

  rect's position is clamped to the nearest edge.

##### `impl Clone for Rect`

- `fn clone(&self) -> Rect` — [`Rect`](../index.md#rect)

##### `impl Copy for Rect`

##### `impl Debug for Rect`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Rect`

- `fn default() -> Rect` — [`Rect`](../index.md#rect)

##### `impl Display for Rect`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Rect`

##### `impl<K> Equivalent for Rect`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Rect`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Rect`

##### `impl PartialEq for Rect`

- `fn eq(&self, other: &Rect) -> bool` — [`Rect`](../index.md#rect)

##### `impl StructuralPartialEq for Rect`

##### `impl Sub for super::Rect`

- `type Output = Rect`

- `fn sub(self, offset: Offset) -> Self` — [`Offset`](../index.md#offset)

  Subtracts an offset from the rect without changing its size.

  

  If the offset would move the any of the rect's edges outside the bounds of `u16`, the

  rect's position is clamped to the nearest

##### `impl SubAssign for super::Rect`

- `fn sub_assign(&mut self, offset: Offset)` — [`Offset`](../index.md#offset)

  Moves the rect by an offset in place without changing its size.

  

  If the offset would move the any of the rect's edges outside the bounds of `u16`, the

  rect's position is clamped to the nearest edge.

##### `impl ToCompactString for Rect`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Rect`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Rect`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Rect`

- `fn to_string(&self) -> String`

##### `impl ToText for Rect`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `Rows`

```rust
struct Rows {
    // [REDACTED: Private Fields]
}
```

An iterator over rows within a `Rect`.

#### Implementations

- `const fn new(rect: Rect) -> Self` — [`Rect`](../index.md#rect)

  Creates a new `Rows` iterator.

#### Trait Implementations

##### `impl DoubleEndedIterator for Rows`

- `fn next_back(&mut self) -> Option<<Self as >::Item>`

  Retrieves the previous row within the `Rect`.

  

  Returns `None` when there are no more rows to iterate through.

##### `impl IntoEither for Rows`

##### `impl IntoIterator for Rows`

- `type Item = <I as Iterator>::Item`

- `type IntoIter = I`

- `fn into_iter(self) -> I`

##### `impl Iterator for Rows`

- `type Item = Rect`

- `fn next(&mut self) -> Option<<Self as >::Item>`

  Retrieves the next row within the `Rect`.

  

  Returns `None` when there are no more rows to iterate through.

- `fn size_hint(&self) -> (usize, Option<usize>)`

##### `impl Itertools for Rows`

### `Size`

```rust
struct Size {
    pub width: u16,
    pub height: u16,
}
```

A simple size struct for representing dimensions in the terminal.

The width and height are stored as `u16` values and represent the number of columns and rows
respectively. This is used throughout the layout system to represent dimensions of rectangular
areas and other layout elements.

Size can be created from tuples, extracted from rectangular areas, or constructed directly.
It's commonly used in conjunction with [`Position`](crate::layout::Position) to define
rectangular areas.

# Construction

- [`new`](Self::new) - Create a new size from width and height
- [`default`](Default::default) - Create with zero dimensions

# Conversion

- [`from((u16, u16))`](Self::from) - Create from `(u16, u16)` tuple
- [`from(Rect)`](Self::from) - Create from [`Rect`](../index.md) (uses width and height)
- `into((u16, u16))` - Convert to `(u16, u16)` tuple

# Computation

- [`area`](Self::area) - Compute the total number of cells covered by the size

# Examples

```rust
use ratatui_core::layout::{Rect, Size};

let size = Size::new(80, 24);
assert_eq!(size.area(), 1920);
let size = Size::from((80, 24));
let size = Size::from(Rect::new(0, 0, 80, 24));
assert_eq!(size.area(), 1920);
```

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Fields

- **`width`**: `u16`

  The width in columns

- **`height`**: `u16`

  The height in rows

#### Implementations

- `const ZERO: Self`

- `const MIN: Self`

- `const MAX: Self`

- `const fn new(width: u16, height: u16) -> Self`

  Create a new `Size` struct

- `const fn area(self) -> u32`

  Compute the total area of the size as a `u32`.

  

  The multiplication uses `u32` to avoid overflow when the width and height are at their

  `u16` maximum values.

#### Trait Implementations

##### `impl Clone for Size`

- `fn clone(&self) -> Size` — [`Size`](../index.md#size)

##### `impl Copy for Size`

##### `impl Debug for Size`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Size`

- `fn default() -> Size` — [`Size`](../index.md#size)

##### `impl Display for Size`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Size`

##### `impl<K> Equivalent for Size`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Size`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Size`

##### `impl PartialEq for Size`

- `fn eq(&self, other: &Size) -> bool` — [`Size`](../index.md#size)

##### `impl StructuralPartialEq for Size`

##### `impl ToCompactString for Size`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Size`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Size`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Size`

- `fn to_string(&self) -> String`

##### `impl ToText for Size`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

## Enums

### `HorizontalAlignment`

```rust
enum HorizontalAlignment {
    Left,
    Center,
    Right,
}
```

Horizontal content alignment within a layout area.

Prior to Ratatui 0.30.0, this type was named `Alignment`. In Ratatui 0.30.0, the name was
changed to `HorizontalAlignment` to make it more descriptive. The old name is still available as
an alias for backwards compatibility.

This type is used throughout Ratatui to control how content is positioned horizontally within
available space. It's commonly used with widgets to control text alignment, but can also be
used in layout calculations.

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Trait Implementations

##### `impl Clone for HorizontalAlignment`

- `fn clone(&self) -> HorizontalAlignment` — [`HorizontalAlignment`](../index.md#horizontalalignment)

##### `impl Copy for HorizontalAlignment`

##### `impl Debug for HorizontalAlignment`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for HorizontalAlignment`

- `fn default() -> HorizontalAlignment` — [`HorizontalAlignment`](../index.md#horizontalalignment)

##### `impl Display for HorizontalAlignment`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for HorizontalAlignment`

##### `impl<K> Equivalent for HorizontalAlignment`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for HorizontalAlignment`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<HorizontalAlignment, <Self as ::core::str::FromStr>::Err>` — [`HorizontalAlignment`](../index.md#horizontalalignment)

##### `impl Hash for HorizontalAlignment`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for HorizontalAlignment`

##### `impl PartialEq for HorizontalAlignment`

- `fn eq(&self, other: &HorizontalAlignment) -> bool` — [`HorizontalAlignment`](../index.md#horizontalalignment)

##### `impl StructuralPartialEq for HorizontalAlignment`

##### `impl ToCompactString for HorizontalAlignment`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for HorizontalAlignment`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for HorizontalAlignment`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for HorizontalAlignment`

- `fn to_string(&self) -> String`

##### `impl ToText for HorizontalAlignment`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `VerticalAlignment`

```rust
enum VerticalAlignment {
    Top,
    Center,
    Bottom,
}
```

Vertical content alignment within a layout area.

This type is used to control how content is positioned vertically within available space.
It complements [`HorizontalAlignment`](../index.md) to provide full 2D positioning control.

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Trait Implementations

##### `impl Clone for VerticalAlignment`

- `fn clone(&self) -> VerticalAlignment` — [`VerticalAlignment`](../index.md#verticalalignment)

##### `impl Copy for VerticalAlignment`

##### `impl Debug for VerticalAlignment`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for VerticalAlignment`

- `fn default() -> VerticalAlignment` — [`VerticalAlignment`](../index.md#verticalalignment)

##### `impl Display for VerticalAlignment`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for VerticalAlignment`

##### `impl<K> Equivalent for VerticalAlignment`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for VerticalAlignment`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<VerticalAlignment, <Self as ::core::str::FromStr>::Err>` — [`VerticalAlignment`](../index.md#verticalalignment)

##### `impl Hash for VerticalAlignment`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for VerticalAlignment`

##### `impl PartialEq for VerticalAlignment`

- `fn eq(&self, other: &VerticalAlignment) -> bool` — [`VerticalAlignment`](../index.md#verticalalignment)

##### `impl StructuralPartialEq for VerticalAlignment`

##### `impl ToCompactString for VerticalAlignment`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for VerticalAlignment`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for VerticalAlignment`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for VerticalAlignment`

- `fn to_string(&self) -> String`

##### `impl ToText for VerticalAlignment`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `Constraint`

```rust
enum Constraint {
    Min(u16),
    Max(u16),
    Length(u16),
    Percentage(u16),
    Ratio(u32, u32),
    Fill(u16),
}
```

A constraint that defines the size of a layout element.

Constraints are the core mechanism for defining how space should be allocated within a
[`Layout`](crate::layout::Layout). They can specify fixed sizes (length), proportional sizes
(percentage, ratio), size limits (min, max), or proportional fill values for layout elements.
Relative constraints (percentage, ratio) are calculated relative to the entire space being
divided, rather than the space available after applying more fixed constraints (min, max,
length).

Constraints are prioritized in the following order:

1. [`Constraint::Min`](../index.md)
2. [`Constraint::Max`](../index.md)
3. [`Constraint::Length`](../index.md)
4. [`Constraint::Percentage`](../index.md)
5. [`Constraint::Ratio`](../index.md)
6. [`Constraint::Fill`](../index.md)

# Size Calculation

- [`apply`](Self::apply) - Apply the constraint to a length and return the resulting size

# Collection Creation

- [`from_lengths`](Self::from_lengths) - Create a collection of length constraints
- [`from_ratios`](Self::from_ratios) - Create a collection of ratio constraints
- [`from_percentages`](Self::from_percentages) - Create a collection of percentage constraints
- [`from_maxes`](Self::from_maxes) - Create a collection of maximum constraints
- [`from_mins`](Self::from_mins) - Create a collection of minimum constraints
- [`from_fills`](Self::from_fills) - Create a collection of fill constraints

# Conversion and Construction

- [`from(u16)`](Self::from) - Create a [`Length`](Self::Length) constraint from `u16`
- [`from(&Constraint)`](Self::from) - Create from `&Constraint` (copy)
- [`as_ref()`](Self::as_ref) - Get a reference to self
- [`default()`](Self::default) - Create default constraint
  ([`Percentage(100)`](Self::Percentage))

# Examples

`Constraint` provides helper methods to create lists of constraints from various input formats.

```rust
use ratatui_core::layout::Constraint;

// Create a layout with specified lengths for each element
let constraints = Constraint::from_lengths([10, 20, 10]);

// Create a centered layout using ratio or percentage constraints
let constraints = Constraint::from_ratios([(1, 4), (1, 2), (1, 4)]);
let constraints = Constraint::from_percentages([25, 50, 25]);

// Create a centered layout with a minimum size constraint for specific elements
let constraints = Constraint::from_mins([0, 100, 0]);

// Create a sidebar layout specifying maximum sizes for the columns
let constraints = Constraint::from_maxes([30, 170]);

// Create a layout with fill proportional sizes for each element
let constraints = Constraint::from_fills([1, 2, 1]);
```

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Variants

- **`Min`**

  Applies a minimum size constraint to the element
  
  The element size is set to at least the specified amount.
  
  # Examples
  
  `[Percentage(100), Min(20)]`
  
  ```plain
  ┌────────────────────────────┐┌──────────────────┐
  │            30 px           ││       20 px      │
  └────────────────────────────┘└──────────────────┘
  ```
  
  `[Percentage(100), Min(10)]`
  
  ```plain
  ┌──────────────────────────────────────┐┌────────┐
  │                 40 px                ││  10 px │
  └──────────────────────────────────────┘└────────┘
  ```

- **`Max`**

  Applies a maximum size constraint to the element
  
  The element size is set to at most the specified amount.
  
  # Examples
  
  `[Percentage(0), Max(20)]`
  
  ```plain
  ┌────────────────────────────┐┌──────────────────┐
  │            30 px           ││       20 px      │
  └────────────────────────────┘└──────────────────┘
  ```
  
  `[Percentage(0), Max(10)]`
  
  ```plain
  ┌──────────────────────────────────────┐┌────────┐
  │                 40 px                ││  10 px │
  └──────────────────────────────────────┘└────────┘
  ```

- **`Length`**

  Applies a length constraint to the element
  
  The element size is set to the specified amount.
  
  # Examples
  
  `[Length(20), Length(20)]`
  
  ```plain
  ┌──────────────────┐┌──────────────────┐
  │       20 px      ││       20 px      │
  └──────────────────┘└──────────────────┘
  ```
  
  `[Length(20), Length(30)]`
  
  ```plain
  ┌──────────────────┐┌────────────────────────────┐
  │       20 px      ││            30 px           │
  └──────────────────┘└────────────────────────────┘
  ```

- **`Percentage`**

  Applies a percentage of the available space to the element
  
  Converts the given percentage to a floating-point value and multiplies that with area. This
  value is rounded back to a integer as part of the layout split calculation.
  
  **Note**: As this value only accepts a `u16`, certain percentages that cannot be
  represented exactly (e.g. 1/3) are not possible. You might want to use
  [`Constraint::Ratio`](../index.md) or [`Constraint::Fill`](../index.md) in such cases.
  
  # Examples
  
  `[Percentage(75), Fill(1)]`
  
  ```plain
  ┌────────────────────────────────────┐┌──────────┐
  │                38 px               ││   12 px  │
  └────────────────────────────────────┘└──────────┘
  ```
  
  `[Percentage(50), Fill(1)]`
  
  ```plain
  ┌───────────────────────┐┌───────────────────────┐
  │         25 px         ││         25 px         │
  └───────────────────────┘└───────────────────────┘
  ```

- **`Ratio`**

  Applies a ratio of the available space to the element
  
  Converts the given ratio to a floating-point value and multiplies that with area.
  This value is rounded back to a integer as part of the layout split calculation.
  
  # Examples
  
  `[Ratio(1, 2) ; 2]`
  
  ```plain
  ┌───────────────────────┐┌───────────────────────┐
  │         25 px         ││         25 px         │
  └───────────────────────┘└───────────────────────┘
  ```
  
  `[Ratio(1, 4) ; 4]`
  
  ```plain
  ┌───────────┐┌──────────┐┌───────────┐┌──────────┐
  │   13 px   ││   12 px  ││   13 px   ││   12 px  │
  └───────────┘└──────────┘└───────────┘└──────────┘
  ```

- **`Fill`**

  Applies the scaling factor proportional to all other [`Constraint::Fill`](../index.md) elements
  to fill excess space
  
  The element will only expand or fill into excess available space, proportionally matching
  other [`Constraint::Fill`](../index.md) elements while satisfying all other constraints.
  
  # Examples
  
  
  `[Fill(1), Fill(2), Fill(3)]`
  
  ```plain
  ┌──────┐┌───────────────┐┌───────────────────────┐
  │ 8 px ││     17 px     ││         25 px         │
  └──────┘└───────────────┘└───────────────────────┘
  ```
  
  `[Fill(1), Percentage(50), Fill(1)]`
  
  ```plain
  ┌───────────┐┌───────────────────────┐┌──────────┐
  │   13 px   ││         25 px         ││   12 px  │
  └───────────┘└───────────────────────┘└──────────┘
  ```

#### Implementations

- `const fn is_min(&self) -> bool`

  Returns [true] if the enum is [Constraint::Min] otherwise [false]

- `const fn is_max(&self) -> bool`

  Returns [true] if the enum is [Constraint::Max] otherwise [false]

- `const fn is_length(&self) -> bool`

  Returns [true] if the enum is [Constraint::Length] otherwise [false]

- `const fn is_percentage(&self) -> bool`

  Returns [true] if the enum is [Constraint::Percentage] otherwise [false]

- `const fn is_ratio(&self) -> bool`

  Returns [true] if the enum is [Constraint::Ratio] otherwise [false]

- `const fn is_fill(&self) -> bool`

  Returns [true] if the enum is [Constraint::Fill] otherwise [false]

#### Trait Implementations

##### `impl AsRef for Constraint`

- `fn as_ref(&self) -> &Self`

##### `impl Clone for Constraint`

- `fn clone(&self) -> Constraint` — [`Constraint`](../index.md#constraint)

##### `impl Copy for Constraint`

##### `impl Debug for Constraint`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Constraint`

- `fn default() -> Self`

##### `impl Display for Constraint`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Constraint`

##### `impl<K> Equivalent for Constraint`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Constraint`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Constraint`

##### `impl PartialEq for Constraint`

- `fn eq(&self, other: &Constraint) -> bool` — [`Constraint`](../index.md#constraint)

##### `impl StructuralPartialEq for Constraint`

##### `impl ToCompactString for Constraint`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Constraint`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Constraint`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Constraint`

- `fn to_string(&self) -> String`

##### `impl ToText for Constraint`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `Direction`

```rust
enum Direction {
    Horizontal,
    Vertical,
}
```

Defines the direction of a layout.

This enumeration is used with [`Layout`](crate::layout::Layout) to specify whether layout
segments should be arranged horizontally or vertically.

- `Horizontal`: Layout segments are arranged side by side (left to right)
- `Vertical`: Layout segments are arranged top to bottom (default)

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Variants

- **`Horizontal`**

  Layout segments are arranged side by side (left to right).

- **`Vertical`**

  Layout segments are arranged top to bottom (default).

#### Implementations

- `const fn perpendicular(self) -> Self`

  The perpendicular direction to this direction.

  

  `Horizontal` returns `Vertical`, and `Vertical` returns `Horizontal`.

#### Trait Implementations

##### `impl Clone for Direction`

- `fn clone(&self) -> Direction` — [`Direction`](../index.md#direction)

##### `impl Copy for Direction`

##### `impl Debug for Direction`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Direction`

- `fn default() -> Direction` — [`Direction`](../index.md#direction)

##### `impl Display for Direction`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for Direction`

##### `impl<K> Equivalent for Direction`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for Direction`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<Direction, <Self as ::core::str::FromStr>::Err>` — [`Direction`](../index.md#direction)

##### `impl Hash for Direction`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Direction`

##### `impl PartialEq for Direction`

- `fn eq(&self, other: &Direction) -> bool` — [`Direction`](../index.md#direction)

##### `impl StructuralPartialEq for Direction`

##### `impl ToCompactString for Direction`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Direction`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Direction`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Direction`

- `fn to_string(&self) -> String`

##### `impl ToText for Direction`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `Flex`

```rust
enum Flex {
    Legacy,
    Start,
    End,
    Center,
    SpaceBetween,
    SpaceEvenly,
    SpaceAround,
}
```

Defines the options for layout flex justify content in a container.

This enumeration controls the distribution of space when layout constraints are met and there
is excess space available. The `Flex` option is used with [`Layout`](crate::layout::Layout) to
control how extra space is distributed among layout segments, which is particularly useful for
creating responsive layouts that adapt to different terminal sizes.

Available options:

- `Legacy`: Fills the available space within the container, putting excess space into the last
  element.
- `Start`: Aligns items to the start of the container.
- `End`: Aligns items to the end of the container.
- `Center`: Centers items within the container.
- `SpaceBetween`: Adds excess space between each element.
- `SpaceAround`: Adds excess space around each element.

For comprehensive layout documentation and examples, see the [`layout`](crate::layout) module.

#### Variants

- **`Legacy`**

  Fills the available space within the container, putting excess space into the last
  constraint of the lowest priority. This matches the default behavior of ratatui and tui
  applications without [`Flex`](../index.md)
  
  The following examples illustrate the allocation of excess in various combinations of
  constraints. As a refresher, the priorities of constraints are as follows:
  
  1. [`Constraint::Min`](../index.md)
  2. [`Constraint::Max`](../index.md)
  3. [`Constraint::Length`](../index.md)
  4. [`Constraint::Percentage`](../index.md)
  5. [`Constraint::Ratio`](../index.md)
  6. [`Constraint::Fill`](../index.md)
  
  When every constraint is `Length`, the last element gets the excess.
  
  ```plain
  <----------------------------------- 80 px ------------------------------------>
  ┌──────20 px───────┐┌──────20 px───────┐┌────────────────40 px─────────────────┐
  │    Length(20)    ││    Length(20)    ││              Length(20)              │
  └──────────────────┘└──────────────────┘└──────────────────────────────────────┘
                                          ^^^^^^^^^^^^^^^^ EXCESS ^^^^^^^^^^^^^^^^
  ```
  
  Fill constraints have the lowest priority amongst all the constraints and hence
  will always take up any excess space available.
  
  ```plain
  <----------------------------------- 80 px ------------------------------------>
  ┌──────20 px───────┐┌──────20 px───────┐┌──────20 px───────┐┌──────20 px───────┐
  │      Fill(0)     ││      Max(20)     ││    Length(20)    ││     Length(20)   │
  └──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘
  ^^^^^^ EXCESS ^^^^^^
  ```
  
  # Examples
  
  ```plain
  <------------------------------------80 px------------------------------------->
  ┌──────────────────────────60 px───────────────────────────┐┌──────20 px───────┐
  │                          Min(20)                         ││      Max(20)     │
  └──────────────────────────────────────────────────────────┘└──────────────────┘
  
  <------------------------------------80 px------------------------------------->
  ┌────────────────────────────────────80 px─────────────────────────────────────┐
  │                                    Max(20)                                   │
  └──────────────────────────────────────────────────────────────────────────────┘
  ```

- **`Start`**

  Aligns items to the start of the container.
  
  # Examples
  
  ```plain
  <------------------------------------80 px------------------------------------->
  ┌────16 px─────┐┌──────20 px───────┐┌──────20 px───────┐
  │Percentage(20)││    Length(20)    ││     Fixed(20)    │
  └──────────────┘└──────────────────┘└──────────────────┘
  
  <------------------------------------80 px------------------------------------->
  ┌──────20 px───────┐┌──────20 px───────┐
  │      Max(20)     ││      Max(20)     │
  └──────────────────┘└──────────────────┘
  
  <------------------------------------80 px------------------------------------->
  ┌──────20 px───────┐
  │      Max(20)     │
  └──────────────────┘
  ```

- **`End`**

  Aligns items to the end of the container.
  
  # Examples
  
  ```plain
  <------------------------------------80 px------------------------------------->
                          ┌────16 px─────┐┌──────20 px───────┐┌──────20 px───────┐
                          │Percentage(20)││    Length(20)    ││     Length(20)   │
                          └──────────────┘└──────────────────┘└──────────────────┘
  
  <------------------------------------80 px------------------------------------->
                                          ┌──────20 px───────┐┌──────20 px───────┐
                                          │      Max(20)     ││      Max(20)     │
                                          └──────────────────┘└──────────────────┘
  
  <------------------------------------80 px------------------------------------->
                                                              ┌──────20 px───────┐
                                                              │      Max(20)     │
                                                              └──────────────────┘
  ```

- **`Center`**

  Centers items within the container.
  
  # Examples
  
  ```plain
  <------------------------------------80 px------------------------------------->
              ┌────16 px─────┐┌──────20 px───────┐┌──────20 px───────┐
              │Percentage(20)││    Length(20)    ││     Length(20)   │
              └──────────────┘└──────────────────┘└──────────────────┘
  
  <------------------------------------80 px------------------------------------->
                      ┌──────20 px───────┐┌──────20 px───────┐
                      │      Max(20)     ││      Max(20)     │
                      └──────────────────┘└──────────────────┘
  
  <------------------------------------80 px------------------------------------->
                                ┌──────20 px───────┐
                                │      Max(20)     │
                                └──────────────────┘
  ```

- **`SpaceBetween`**

  Adds excess space between each element.
  
  # Examples
  
  ```plain
  <------------------------------------80 px------------------------------------->
  ┌────16 px─────┐            ┌──────20 px───────┐            ┌──────20 px───────┐
  │Percentage(20)│            │    Length(20)    │            │     Length(20)   │
  └──────────────┘            └──────────────────┘            └──────────────────┘
  
  <------------------------------------80 px------------------------------------->
  ┌──────20 px───────┐                                        ┌──────20 px───────┐
  │      Max(20)     │                                        │      Max(20)     │
  └──────────────────┘                                        └──────────────────┘
  
  <------------------------------------80 px------------------------------------->
  ┌────────────────────────────────────80 px─────────────────────────────────────┐
  │                                    Max(20)                                   │
  └──────────────────────────────────────────────────────────────────────────────┘
  ```

- **`SpaceEvenly`**

  Evenly distributes excess space between all elements, including before the first and after
  the last.
  
  # Examples
  
  ```plain
  <------------------------------------80 px------------------------------------->
        ┌────16 px─────┐      ┌──────20 px───────┐      ┌──────20 px───────┐
        │Percentage(20)│      │    Length(20)    │      │     Length(20)   │
        └──────────────┘      └──────────────────┘      └──────────────────┘
  
  <------------------------------------80 px------------------------------------->
               ┌──────20 px───────┐              ┌──────20 px───────┐
               │      Max(20)     │              │      Max(20)     │
               └──────────────────┘              └──────────────────┘
  
  <------------------------------------80 px------------------------------------->
                                ┌──────20 px───────┐
                                │      Max(20)     │
                                └──────────────────┘
  ```

- **`SpaceAround`**

  Adds excess space around each element.
  
  # Examples
  
  ```plain
  <------------------------------------80 px------------------------------------->
      ┌────16 px─────┐       ┌──────20 px───────┐       ┌──────20 px───────┐
      │Percentage(20)│       │    Length(20)    │       │     Length(20)   │
      └──────────────┘       └──────────────────┘       └──────────────────┘
  
  <------------------------------------80 px------------------------------------->
       ┌──────20 px───────┐                      ┌──────20 px───────┐
       │      Max(20)     │                      │      Max(20)     │
       └──────────────────┘                      └──────────────────┘
  
  <------------------------------------80 px------------------------------------->
                                ┌──────20 px───────┐
                                │      Max(20)     │
                                └──────────────────┘
  ```

#### Implementations

- `const fn is_legacy(&self) -> bool`

  Returns [true] if the enum is [Flex::Legacy] otherwise [false]

- `const fn is_start(&self) -> bool`

  Returns [true] if the enum is [Flex::Start] otherwise [false]

- `const fn is_end(&self) -> bool`

  Returns [true] if the enum is [Flex::End] otherwise [false]

- `const fn is_center(&self) -> bool`

  Returns [true] if the enum is [Flex::Center] otherwise [false]

- `const fn is_space_between(&self) -> bool`

  Returns [true] if the enum is [Flex::SpaceBetween] otherwise [false]

- `const fn is_space_evenly(&self) -> bool`

  Returns [true] if the enum is [Flex::SpaceEvenly] otherwise [false]

- `const fn is_space_around(&self) -> bool`

  Returns [true] if the enum is [Flex::SpaceAround] otherwise [false]

#### Trait Implementations

##### `impl Clone for Flex`

- `fn clone(&self) -> Flex` — [`Flex`](../index.md#flex)

##### `impl Copy for Flex`

##### `impl Debug for Flex`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Flex`

- `fn default() -> Flex` — [`Flex`](../index.md#flex)

##### `impl Display for Flex`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for Flex`

##### `impl<K> Equivalent for Flex`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for Flex`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<Flex, <Self as ::core::str::FromStr>::Err>` — [`Flex`](../index.md#flex)

##### `impl Hash for Flex`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Flex`

##### `impl PartialEq for Flex`

- `fn eq(&self, other: &Flex) -> bool` — [`Flex`](../index.md#flex)

##### `impl StructuralPartialEq for Flex`

##### `impl ToCompactString for Flex`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Flex`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Flex`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Flex`

- `fn to_string(&self) -> String`

##### `impl ToText for Flex`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `Spacing`

```rust
enum Spacing {
    Space(u16),
    Overlap(u16),
}
```

Represents the spacing between segments in a layout.

The `Spacing` enum is used to define the spacing between segments in a layout. It can represent
either positive spacing (space between segments) or negative spacing (overlap between segments).

# Variants

- `Space(u16)`: Represents positive spacing between segments. The value indicates the number of
  cells.
- `Overlap(u16)`: Represents negative spacing, causing overlap between segments. The value
  indicates the number of overlapping cells.

# Default

The default value for `Spacing` is `Space(0)`, which means no spacing or no overlap between
segments.

# Conversions

The `Spacing` enum can be created from different integer types:

- From `u16`: Directly converts the value to `Spacing::Space`.
- From `i16`: Converts negative values to `Spacing::Overlap` and non-negative values to
  `Spacing::Space`.
- From `i32`: Clamps the value to the range of `i16` and converts negative values to
  `Spacing::Overlap` and non-negative values to `Spacing::Space`.

See the `Layout::spacing` method for details on how to use this enum.

#### Trait Implementations

##### `impl Clone for Spacing`

- `fn clone(&self) -> Spacing` — [`Spacing`](../index.md#spacing)

##### `impl Debug for Spacing`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Spacing`

- `fn default() -> Self`

##### `impl Eq for Spacing`

##### `impl<K> Equivalent for Spacing`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Spacing`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Spacing`

##### `impl PartialEq for Spacing`

- `fn eq(&self, other: &Spacing) -> bool` — [`Spacing`](../index.md#spacing)

##### `impl StructuralPartialEq for Spacing`

## Type Aliases

### `Alignment`

```rust
type Alignment = HorizontalAlignment;
```

A type alias for `HorizontalAlignment`.

Prior to Ratatui 0.30.0, [`HorizontalAlignment`](../index.md) was named `Alignment`. This alias is provided
for backwards compatibility. Because this type is used almost everywhere in Ratatui related apps
and libraries, it's unlikely that this alias will be removed in the future.

