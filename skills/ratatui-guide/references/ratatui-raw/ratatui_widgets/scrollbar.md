*[ratatui_widgets](./index.md) / [scrollbar](#)*

---

# Module `scrollbar`

The [`Scrollbar`](#scrollbar) widget is used to display a scrollbar alongside other widgets.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Scrollbar`](#scrollbar) | struct | A widget to display a scrollbar |
| [`ScrollbarState`](#scrollbarstate) | struct | A struct representing the state of a Scrollbar widget. |
| [`ScrollbarOrientation`](#scrollbarorientation) | enum | This is the position of the scrollbar around a given area. |
| [`ScrollDirection`](#scrolldirection) | enum | An enum representing a scrolling direction. |

## Structs

### `Scrollbar<'a>`

```rust
struct Scrollbar<'a> {
    // [REDACTED: Private Fields]
}
```

A widget to display a scrollbar

The following components of the scrollbar are customizable in symbol and style. Note the
scrollbar is represented horizontally but it can also be set vertically (which is actually the
default).

```text
<--▮------->
^  ^   ^   ^
│  │   │   └ end
│  │   └──── track
│  └──────── thumb
└─────────── begin
```

# Important

You must specify the `ScrollbarState::content_length` before rendering the `Scrollbar`, or
else the `Scrollbar` will render blank.

# Examples

```rust
use ratatui::Frame;
use ratatui::layout::{Margin, Rect};
use ratatui::text::Line;
use ratatui::widgets::{
    Block, Borders, Paragraph, Scrollbar, ScrollbarOrientation, ScrollbarState, StatefulWidget,
};

fn render_paragraph_with_scrollbar(frame: &mut Frame, area: Rect) {
let vertical_scroll = 0; // from app state

let items = vec![
    Line::from("Item 1"),
    Line::from("Item 2"),
    Line::from("Item 3"),
];
let paragraph = Paragraph::new(items.clone())
    .scroll((vertical_scroll as u16, 0))
    .block(Block::new().borders(Borders::RIGHT)); // to show a background for the scrollbar

let scrollbar = Scrollbar::new(ScrollbarOrientation::VerticalRight)
    .begin_symbol(Some("↑"))
    .end_symbol(Some("↓"));

let mut scrollbar_state = ScrollbarState::new(items.len()).position(vertical_scroll);

let area = frame.area();
// Note we render the paragraph
frame.render_widget(paragraph, area);
// and the scrollbar, those are separate widgets
frame.render_stateful_widget(
    scrollbar,
    area.inner(Margin {
        // using an inner vertical margin of 1 unit makes the scrollbar inside the block
        vertical: 1,
        horizontal: 0,
    }),
    &mut scrollbar_state,
);
}
```

#### Implementations

- `const fn new(orientation: ScrollbarOrientation) -> Self` — [`ScrollbarOrientation`](#scrollbarorientation)

  Creates a new scrollbar with the given orientation.

  

  Most of the time you'll want [`ScrollbarOrientation::VerticalRight`](./index.md) or

  [`ScrollbarOrientation::HorizontalBottom`](./index.md). See [`ScrollbarOrientation`](#scrollbarorientation) for more options.

- `const fn orientation(self, orientation: ScrollbarOrientation) -> Self` — [`ScrollbarOrientation`](#scrollbarorientation)

  Sets the position of the scrollbar.

  

  The orientation of the scrollbar is the position it will take around a [`Rect`](../ratatui_core/index.md). See

  [`ScrollbarOrientation`](#scrollbarorientation) for more details.

  

  Resets the symbols to [`DOUBLE_VERTICAL`](../ratatui_core/symbols/scrollbar.md) or [`DOUBLE_HORIZONTAL`](../ratatui_core/symbols/line.md) based on orientation.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn orientation_and_symbol(self, orientation: ScrollbarOrientation, symbols: Set<'a>) -> Self` — [`ScrollbarOrientation`](#scrollbarorientation)

  Sets the orientation and symbols for the scrollbar from a [`Set`](../ratatui_core/symbols/block.md).

  

  This has the same effect as calling `Scrollbar::orientation` and then

  `Scrollbar::symbols`. See those for more details.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn thumb_symbol(self, thumb_symbol: &'a str) -> Self`

  Sets the symbol that represents the thumb of the scrollbar.

  

  The thumb is the handle representing the progression on the scrollbar. See [`Scrollbar`](#scrollbar)

  for a visual example of what this represents.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn thumb_style<S: Into<Style>>(self, thumb_style: S) -> Self`

  Sets the style on the scrollbar thumb.

  

  The thumb is the handle representing the progression on the scrollbar. See [`Scrollbar`](#scrollbar)

  for a visual example of what this represents.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn track_symbol(self, track_symbol: Option<&'a str>) -> Self`

  Sets the symbol that represents the track of the scrollbar.

  

  See [`Scrollbar`](#scrollbar) for a visual example of what this represents.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn track_style<S: Into<Style>>(self, track_style: S) -> Self`

  Sets the style that is used for the track of the scrollbar.

  

  See [`Scrollbar`](#scrollbar) for a visual example of what this represents.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn begin_symbol(self, begin_symbol: Option<&'a str>) -> Self`

  Sets the symbol that represents the beginning of the scrollbar.

  

  See [`Scrollbar`](#scrollbar) for a visual example of what this represents.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn begin_style<S: Into<Style>>(self, begin_style: S) -> Self`

  Sets the style that is used for the beginning of the scrollbar.

  

  See [`Scrollbar`](#scrollbar) for a visual example of what this represents.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn end_symbol(self, end_symbol: Option<&'a str>) -> Self`

  Sets the symbol that represents the end of the scrollbar.

  

  See [`Scrollbar`](#scrollbar) for a visual example of what this represents.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn end_style<S: Into<Style>>(self, end_style: S) -> Self`

  Sets the style that is used for the end of the scrollbar.

  

  See [`Scrollbar`](#scrollbar) for a visual example of what this represents.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn symbols(self, symbols: Set<'a>) -> Self`

  Sets the symbols used for the various parts of the scrollbar from a [`Set`](../ratatui_core/symbols/block.md).

  

  ```text

  <--▮------->

  ^  ^   ^   ^

  │  │   │   └ end

  │  │   └──── track

  │  └──────── thumb

  └─────────── begin

  ```

  

  Only sets `begin_symbol`, `end_symbol` and `track_symbol` if they already contain a value.

  If they were set to `None` explicitly, this function will respect that choice. Use their

  respective setters to change their value.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style used for the various parts of the scrollbar from a [`Style`](../ratatui_core/style.md).

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  ```text

  <--▮------->

  ^  ^   ^   ^

  │  │   │   └ end

  │  │   └──── track

  │  └──────── thumb

  └─────────── begin

  ```

  

  This is a fluent setter method which must be chained or used as it consumes self

#### Trait Implementations

##### `impl AsRef for crate::scrollbar::Scrollbar<'a>`

- `fn as_ref(&self) -> &crate::scrollbar::Scrollbar<'a>` — [`Scrollbar`](#scrollbar)

##### `impl Clone for Scrollbar<'a>`

- `fn clone(&self) -> Scrollbar<'a>` — [`Scrollbar`](#scrollbar)

##### `impl Debug for Scrollbar<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Scrollbar<'_>`

- `fn default() -> Self`

##### `impl Eq for Scrollbar<'a>`

##### `impl<K> Equivalent for Scrollbar<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Scrollbar<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Scrollbar<'a>`

##### `impl PartialEq for Scrollbar<'a>`

- `fn eq(&self, other: &Scrollbar<'a>) -> bool` — [`Scrollbar`](#scrollbar)

##### `impl StatefulWidget for Scrollbar<'_>`

- `type State = ScrollbarState`

- `fn render(self, area: Rect, buf: &mut Buffer, state: &mut <Self as >::State)`

##### `impl StructuralPartialEq for Scrollbar<'a>`

### `ScrollbarState`

```rust
struct ScrollbarState {
    // [REDACTED: Private Fields]
}
```

A struct representing the state of a Scrollbar widget.

# Important

It's essential to set the `content_length` field when using this struct. This field
represents the total length of the scrollable content. The default value is zero
which will result in the Scrollbar not rendering.

For example, in the following list, assume there are 4 bullet points:

- the `content_length` is 4
- the `position` is 0
- the `viewport_content_length` is 2

```text
┌───────────────┐
│1. this is a   █
│   single item █
│2. this is a   ║
│   second item ║
└───────────────┘
```

If you don't have multi-line content, you can leave the `viewport_content_length` set to the
default and it'll use the track size as a `viewport_content_length`.

#### Implementations

- `const fn new(content_length: usize) -> Self`

  Constructs a new [`ScrollbarState`](#scrollbarstate) with the specified content length.

  

  `content_length` is the total number of element, that can be scrolled. See

  [`ScrollbarState`](#scrollbarstate) for more details.

- `const fn position(self, position: usize) -> Self`

  Sets the scroll position of the scrollbar.

  

  This represents the number of scrolled items.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn content_length(self, content_length: usize) -> Self`

  Sets the length of the scrollable content.

  

  This is the number of scrollable items. If items have a length of one, then this is the

  same as the number of scrollable cells.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn viewport_content_length(self, viewport_content_length: usize) -> Self`

  Sets the items' size.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn prev(&mut self)`

  Decrements the scroll position by one, ensuring it doesn't go below zero.

- `fn next(&mut self)`

  Increments the scroll position by one, ensuring it doesn't exceed the length of the content.

- `const fn first(&mut self)`

  Sets the scroll position to the start of the scrollable content.

- `const fn last(&mut self)`

  Sets the scroll position to the end of the scrollable content.

- `fn scroll(&mut self, direction: ScrollDirection)` — [`ScrollDirection`](#scrolldirection)

  Changes the scroll position based on the provided [`ScrollDirection`](#scrolldirection).

- `const fn get_position(&self) -> usize`

  Returns the current position within the scrollable content.

#### Trait Implementations

##### `impl Clone for ScrollbarState`

- `fn clone(&self) -> ScrollbarState` — [`ScrollbarState`](#scrollbarstate)

##### `impl Copy for ScrollbarState`

##### `impl Debug for ScrollbarState`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for ScrollbarState`

- `fn default() -> ScrollbarState` — [`ScrollbarState`](#scrollbarstate)

##### `impl Eq for ScrollbarState`

##### `impl<K> Equivalent for ScrollbarState`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for ScrollbarState`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ScrollbarState`

##### `impl PartialEq for ScrollbarState`

- `fn eq(&self, other: &ScrollbarState) -> bool` — [`ScrollbarState`](#scrollbarstate)

##### `impl StructuralPartialEq for ScrollbarState`

## Enums

### `ScrollbarOrientation`

```rust
enum ScrollbarOrientation {
    VerticalRight,
    VerticalLeft,
    HorizontalBottom,
    HorizontalTop,
}
```

This is the position of the scrollbar around a given area.

```plain
          HorizontalTop
            ┌───────┐
VerticalLeft│       │VerticalRight
            └───────┘
         HorizontalBottom
```

#### Variants

- **`VerticalRight`**

  Positions the scrollbar on the right, scrolling vertically

- **`VerticalLeft`**

  Positions the scrollbar on the left, scrolling vertically

- **`HorizontalBottom`**

  Positions the scrollbar on the bottom, scrolling horizontally

- **`HorizontalTop`**

  Positions the scrollbar on the top, scrolling horizontally

#### Implementations

- `const fn is_vertical(&self) -> bool`

  Returns `true` if the scrollbar is vertical.

- `const fn is_horizontal(&self) -> bool`

  Returns `true` if the scrollbar is horizontal.

#### Trait Implementations

##### `impl Clone for ScrollbarOrientation`

- `fn clone(&self) -> ScrollbarOrientation` — [`ScrollbarOrientation`](#scrollbarorientation)

##### `impl Debug for ScrollbarOrientation`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for ScrollbarOrientation`

- `fn default() -> ScrollbarOrientation` — [`ScrollbarOrientation`](#scrollbarorientation)

##### `impl Display for ScrollbarOrientation`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for ScrollbarOrientation`

##### `impl<K> Equivalent for ScrollbarOrientation`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for ScrollbarOrientation`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<ScrollbarOrientation, <Self as ::core::str::FromStr>::Err>` — [`ScrollbarOrientation`](#scrollbarorientation)

##### `impl Hash for ScrollbarOrientation`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ScrollbarOrientation`

##### `impl PartialEq for ScrollbarOrientation`

- `fn eq(&self, other: &ScrollbarOrientation) -> bool` — [`ScrollbarOrientation`](#scrollbarorientation)

##### `impl StructuralPartialEq for ScrollbarOrientation`

##### `impl ToCompactString for ScrollbarOrientation`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for ScrollbarOrientation`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for ScrollbarOrientation`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for ScrollbarOrientation`

- `fn to_string(&self) -> String`

##### `impl ToText for ScrollbarOrientation`

- `fn to_text(&self) -> Text<'_>`

### `ScrollDirection`

```rust
enum ScrollDirection {
    Forward,
    Backward,
}
```

An enum representing a scrolling direction.

This is used with `ScrollbarState::scroll`.

It is useful for example when you want to store in which direction to scroll.

#### Variants

- **`Forward`**

  Forward scroll direction, usually corresponds to scrolling downwards or rightwards.

- **`Backward`**

  Backward scroll direction, usually corresponds to scrolling upwards or leftwards.

#### Trait Implementations

##### `impl Clone for ScrollDirection`

- `fn clone(&self) -> ScrollDirection` — [`ScrollDirection`](#scrolldirection)

##### `impl Copy for ScrollDirection`

##### `impl Debug for ScrollDirection`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for ScrollDirection`

- `fn default() -> ScrollDirection` — [`ScrollDirection`](#scrolldirection)

##### `impl Display for ScrollDirection`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for ScrollDirection`

##### `impl<K> Equivalent for ScrollDirection`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for ScrollDirection`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<ScrollDirection, <Self as ::core::str::FromStr>::Err>` — [`ScrollDirection`](#scrolldirection)

##### `impl Hash for ScrollDirection`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ScrollDirection`

##### `impl PartialEq for ScrollDirection`

- `fn eq(&self, other: &ScrollDirection) -> bool` — [`ScrollDirection`](#scrolldirection)

##### `impl StructuralPartialEq for ScrollDirection`

##### `impl ToCompactString for ScrollDirection`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for ScrollDirection`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for ScrollDirection`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for ScrollDirection`

- `fn to_string(&self) -> String`

##### `impl ToText for ScrollDirection`

- `fn to_text(&self) -> Text<'_>`

