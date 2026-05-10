*[ratatui_core](./index.md) / [text](#)*

---

# Module `text`

Primitives for styled text.

A terminal UI is at its root a lot of strings. In order to make it accessible and stylish, those
strings may be associated to a set of styles. `ratatui` has three ways to represent them:
- A single line string where all graphemes have the same style is represented by a [`Span`](./index.md).
- A single line string where each grapheme may have its own style is represented by [`Line`](./index.md).
- A multiple line string where each grapheme may have its own style is represented by a
  [`Text`](./index.md).

These types form a hierarchy: [`Line`](./index.md) is a collection of [`Span`](./index.md) and each line of [`Text`](./index.md) is
a [`Line`](./index.md).

Keep it mind that a lot of widgets will use those types to advertise what kind of string is
supported for their properties. Moreover, `ratatui` provides convenient `From` implementations
so that you can start by using simple `String` or `&str` and then promote them to the previous
primitives when you need additional styling capabilities.

For example, for the `Block` widget, all the following calls are valid to set its `title`
property (which is a [`Line`](./index.md) under the hood):

```rust,ignore
use ratatui_core::{
    style::{Color, Style},
    text::{Line, Span},
    widgets::Block,
};

// A simple string with no styling.
// Converted to Line(vec![
//   Span { content: Cow::Borrowed("My title"), style: Style { .. } }
// ])
let block = Block::new().title("My title");

// A simple string with a unique style.
// Converted to Line(vec![
//   Span { content: Cow::Borrowed("My title"), style: Style { fg: Some(Color::Yellow), .. }
// ])
let block = Block::new().title(Span::styled("My title", Style::default().fg(Color::Yellow)));

// A string with multiple styles.
// Converted to Line(vec![
//   Span { content: Cow::Borrowed("My"), style: Style { fg: Some(Color::Yellow), .. } },
//   Span { content: Cow::Borrowed(" title"), .. }
// ])
let block = Block::new().title(vec![
    Span::styled("My", Style::default().fg(Color::Yellow)),
    Span::raw(" title"),
]);
```

## Contents

- [Structs](#structs)
  - [`StyledGrapheme`](#styledgrapheme)
  - [`Line`](#line)
  - [`Masked`](#masked)
  - [`Span`](#span)
  - [`Text`](#text)
- [Traits](#traits)
  - [`ToLine`](#toline)
  - [`ToSpan`](#tospan)
  - [`ToText`](#totext)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`StyledGrapheme`](#styledgrapheme) | struct |  |
| [`Line`](#line) | struct |  |
| [`Masked`](#masked) | struct |  |
| [`Span`](#span) | struct |  |
| [`Text`](#text) | struct |  |
| [`ToLine`](#toline) | trait |  |
| [`ToSpan`](#tospan) | trait |  |
| [`ToText`](#totext) | trait |  |

## Structs

### `StyledGrapheme<'a>`

```rust
struct StyledGrapheme<'a> {
    pub symbol: &'a str,
    pub style: crate::style::Style,
}
```

A grapheme associated to a style.
Note that, although `StyledGrapheme` is the smallest divisible unit of text,
it actually is not a member of the text type hierarchy (`Text` -> `Line` -> `Span`).
It is a separate type used mostly for rendering purposes. A `Span` consists of components that
can be split into `StyledGrapheme`s, but it does not contain a collection of `StyledGrapheme`s.

#### Implementations

- `fn new<S: Into<Style>>(symbol: &'a str, style: S) -> Self`

  Creates a new `StyledGrapheme` with the given symbol and style.

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

- `fn is_whitespace(&self) -> bool`

#### Trait Implementations

##### `impl Clone for StyledGrapheme<'a>`

- `fn clone(&self) -> StyledGrapheme<'a>` — [`StyledGrapheme`](./index.md#styledgrapheme)

##### `impl Debug for StyledGrapheme<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for StyledGrapheme<'a>`

- `fn default() -> StyledGrapheme<'a>` — [`StyledGrapheme`](./index.md#styledgrapheme)

##### `impl Eq for StyledGrapheme<'a>`

##### `impl<K> Equivalent for StyledGrapheme<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for StyledGrapheme<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for StyledGrapheme<'a>`

##### `impl PartialEq for StyledGrapheme<'a>`

- `fn eq(&self, other: &StyledGrapheme<'a>) -> bool` — [`StyledGrapheme`](./index.md#styledgrapheme)

##### `impl StructuralPartialEq for StyledGrapheme<'a>`

##### `impl Styled for StyledGrapheme<'_>`

- `type Item = StyledGrapheme<'_>`

- `fn style(&self) -> Style` — [`Style`](./style.md#style)

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item` — [`Styled`](./index.md#styled)

##### `impl<T> Stylize for StyledGrapheme<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T` — [`Modifier`](./style.md#modifier)

- `fn remove_modifier(self, modifier: Modifier) -> T` — [`Modifier`](./style.md#modifier)

- `fn reset(self) -> T`

### `Line<'a>`

```rust
struct Line<'a> {
    pub style: crate::style::Style,
    pub alignment: Option<crate::layout::Alignment>,
    pub spans: alloc::vec::Vec<crate::text::Span<'a>>,
}
```

A line of text, consisting of one or more [`Span`](./index.md)s.

[`Line`](./index.md)s are used wherever text is displayed in the terminal and represent a single line of
text. When a [`Line`](./index.md) is rendered, it is rendered as a single line of text, with each [`Span`](./index.md)
being rendered in order (left to right).

Any newlines in the content are removed when creating a [`Line`](./index.md) using the constructor or
conversion methods.

# Constructor Methods

- `Line::default` creates a line with empty content and the default style.
- `Line::raw` creates a line with the given content and the default style.
- `Line::styled` creates a line with the given content and style.

# Conversion Methods

- `Line::from` creates a `Line` from a `String`.
- `Line::from` creates a `Line` from a `&str`.
- `Line::from` creates a `Line` from a `Vec` of [`Span`](./index.md)s.
- `Line::from` creates a `Line` from a `&[Into<Span>]`.
- `Line::from` creates a `Line` from single [`Span`](./index.md).
- `String::from` converts a line into a `String`.
- `Line::from_iter` creates a line from an iterator of items that are convertible to [`Span`](./index.md).

# Setter Methods

These methods are fluent setters. They return a `Line` with the property set.

- `Line::spans` sets the content of the line.
- `Line::style` sets the style of the line.
- `Line::alignment` sets the alignment of the line.
- `Line::left_aligned` sets the alignment of the line to [`Alignment::Left`](./index.md).
- `Line::centered` sets the alignment of the line to [`Alignment::Center`](./index.md).
- `Line::right_aligned` sets the alignment of the line to [`Alignment::Right`](./index.md).

# Iteration Methods

- `Line::iter` returns an iterator over the spans of this line.
- `Line::iter_mut` returns a mutable iterator over the spans of this line.
- `Line::into_iter` returns an iterator over the spans of this line.

# Other Methods

- `Line::patch_style` patches the style of the line, adding modifiers from the given style.
- `Line::reset_style` resets the style of the line.
- `Line::width` returns the unicode width of the content held by this line.
- `Line::styled_graphemes` returns an iterator over the graphemes held by this line.
- `Line::push_span` adds a span to the line.

# Compatibility Notes

Before v0.26.0, [`Line`](./index.md) did not have a `style` field and instead relied on only the styles that
were set on each [`Span`](./index.md) contained in the `spans` field. The `Line::patch_style` method was
the only way to set the overall style for individual lines. For this reason, this field may not
be supported yet by all widgets (outside of the `ratatui` crate itself).

# Examples

## Creating Lines
[`Line`](./index.md)s can be created from [`Span`](./index.md)s, `String`s, and `&str`s. They can be styled with a
[`Style`](./style.md).

```rust
use ratatui_core::style::{Color, Modifier, Style, Stylize};
use ratatui_core::text::{Line, Span};

let style = Style::new().yellow();
let line = Line::raw("Hello, world!").style(style);
let line = Line::styled("Hello, world!", style);
let line = Line::styled("Hello, world!", (Color::Yellow, Modifier::BOLD));

let line = Line::from("Hello, world!");
let line = Line::from(String::from("Hello, world!"));
let line = Line::from(vec![
    Span::styled("Hello", Style::new().blue()),
    Span::raw(" world!"),
]);
```

## Styling Lines

The line's [`Style`](./style.md) is used by the rendering widget to determine how to style the line. Each
[`Span`](./index.md) in the line will be styled with the [`Style`](./style.md) of the line, and then with its own
[`Style`](./style.md). If the line is longer than the available space, the style is applied to the entire
line, and the line is truncated. `Line` also implements [`Styled`](./index.md) which means you can use the
methods of the [`Stylize`](./index.md) trait.

```rust
use ratatui_core::style::{Color, Modifier, Style, Stylize};
use ratatui_core::text::Line;

let line = Line::from("Hello world!").style(Style::new().yellow().italic());
let line = Line::from("Hello world!").style(Color::Yellow);
let line = Line::from("Hello world!").style((Color::Yellow, Color::Black));
let line = Line::from("Hello world!").style((Color::Yellow, Modifier::ITALIC));
let line = Line::from("Hello world!").yellow().italic();
```

## Aligning Lines

The line's [`Alignment`](./index.md) is used by the rendering widget to determine how to align the line
within the available space. If the line is longer than the available space, the alignment is
ignored and the line is truncated.

```rust
use ratatui_core::layout::Alignment;
use ratatui_core::text::Line;

let line = Line::from("Hello world!").alignment(Alignment::Right);
let line = Line::from("Hello world!").centered();
let line = Line::from("Hello world!").left_aligned();
let line = Line::from("Hello world!").right_aligned();
```

## Rendering Lines

`Line` implements the [`Widget`](./index.md) trait, which means it can be rendered to a [`Buffer`](./index.md).

```rust
use ratatui_core::buffer::Buffer;
use ratatui_core::layout::Rect;
use ratatui_core::style::{Style, Stylize};
use ratatui_core::text::Line;
use ratatui_core::widgets::Widget;

fn render(area: Rect, buf: &mut Buffer) {
// in another widget's render method
let line = Line::from("Hello world!").style(Style::new().yellow().italic());
line.render(area, buf);
}
```

Or you can use the `render_widget` method on the `Frame` in a `Terminal::draw` closure.

```rust,ignore
use ratatui::{Frame, layout::Rect, text::Line};
fn draw(frame: &mut Frame, area: Rect) {
let line = Line::from("Hello world!");
frame.render_widget(line, area);
}
```
## Rendering Lines with a Paragraph widget

Usually apps will use the `Paragraph` widget instead of rendering a [`Line`](./index.md) directly as it
provides more functionality.

```rust,ignore
use ratatui::{
    buffer::Buffer,
    layout::Rect,
    style::Stylize,
    text::Line,
    widgets::{Paragraph, Widget, Wrap},
};

fn render(area: Rect, buf: &mut Buffer) {
let line = Line::from("Hello world!").yellow().italic();
Paragraph::new(line)
    .wrap(Wrap { trim: true })
    .render(area, buf);
}
```

#### Fields

- **`style`**: `crate::style::Style`

  The style of this line of text.

- **`alignment`**: `Option<crate::layout::Alignment>`

  The alignment of this line of text.

- **`spans`**: `alloc::vec::Vec<crate::text::Span<'a>>`

  The spans that make up this line of text.

#### Implementations

- `fn raw<T>(content: T) -> Self`

  Create a line with the default style.

  

  `content` can be any type that is convertible to `Cow<str>` (e.g. `&str`, `String`,

  `Cow<str>`, or your own type that implements `Into<Cow<str>>`).

  

  A [`Line`](./index.md) can specify a [`Style`](./style.md), which will be applied before the style of each [`Span`](./index.md)

  in the line.

  

  Any newlines in the content are removed.

  

  # Examples

  

  ```rust

  use std::borrow::Cow;

  

  use ratatui_core::text::Line;

  

  Line::raw("test content");

  Line::raw(String::from("test content"));

  Line::raw(Cow::from("test content"));

  ```

- `fn styled<T, S>(content: T, style: S) -> Self`

  Create a line with the given style.

  

  `content` can be any type that is convertible to `Cow<str>` (e.g. `&str`, `String`,

  `Cow<str>`, or your own type that implements `Into<Cow<str>>`).

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  # Examples

  

  Any newlines in the content are removed.

  

  ```rust

  use std::borrow::Cow;

  

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Line;

  

  let style = Style::new().yellow().italic();

  Line::styled("My text", style);

  Line::styled(String::from("My text"), style);

  Line::styled(Cow::from("test content"), style);

  ```

- `fn spans<I>(self, spans: I) -> Self`

  Sets the spans of this line of text.

  

  `spans` accepts any iterator that yields items that are convertible to [`Span`](./index.md) (e.g.

  `&str`, `String`, [`Span`](./index.md), or your own type that implements `Into<Span>`).

  

  # Examples

  

  ```rust

  use ratatui_core::style::Stylize;

  use ratatui_core::text::Line;

  

  let line = Line::default().spans(vec!["Hello".blue(), " world!".green()]);

  let line = Line::default().spans([1, 2, 3].iter().map(|i| format!("Item {}", i)));

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of this line of text.

  

  Defaults to `Style::default()`.

  

  Note: This field was added in v0.26.0. Prior to that, the style of a line was determined

  only by the style of each [`Span`](./index.md) contained in the line. For this reason, this field may

  not be supported by all widgets (outside of the `ratatui` crate itself).

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  # Examples

  ```rust

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Line;

  

  let mut line = Line::from("foo").style(Style::new().red());

  ```

- `fn alignment(self, alignment: Alignment) -> Self` — [`Alignment`](./index.md#alignment)

  Sets the target alignment for this line of text.

  

  Defaults to: [`None`](./index.md), meaning the alignment is determined by the rendering widget.

  Setting the alignment of a Line generally overrides the alignment of its

  parent Text or Widget.

  

  # Examples

  

  ```rust

  use ratatui_core::layout::Alignment;

  use ratatui_core::text::Line;

  

  let mut line = Line::from("Hi, what's up?");

  assert_eq!(None, line.alignment);

  assert_eq!(

      Some(Alignment::Right),

      line.alignment(Alignment::Right).alignment

  )

  ```

- `fn left_aligned(self) -> Self`

  Left-aligns this line of text.

  

  Convenience shortcut for `Line::alignment(Alignment::Left)`.

  Setting the alignment of a Line generally overrides the alignment of its

  parent Text or Widget, with the default alignment being inherited from the parent.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Line;

  

  let line = Line::from("Hi, what's up?").left_aligned();

  ```

- `fn centered(self) -> Self`

  Center-aligns this line of text.

  

  Convenience shortcut for `Line::alignment(Alignment::Center)`.

  Setting the alignment of a Line generally overrides the alignment of its

  parent Text or Widget, with the default alignment being inherited from the parent.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Line;

  

  let line = Line::from("Hi, what's up?").centered();

  ```

- `fn right_aligned(self) -> Self`

  Right-aligns this line of text.

  

  Convenience shortcut for `Line::alignment(Alignment::Right)`.

  Setting the alignment of a Line generally overrides the alignment of its

  parent Text or Widget, with the default alignment being inherited from the parent.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Line;

  

  let line = Line::from("Hi, what's up?").right_aligned();

  ```

- `fn width(&self) -> usize`

  Returns the width of the underlying string.

  

  # Examples

  

  ```rust

  use ratatui_core::style::Stylize;

  use ratatui_core::text::Line;

  

  let line = Line::from(vec!["Hello".blue(), " world!".green()]);

  assert_eq!(12, line.width());

  ```

- `fn styled_graphemes<S: Into<Style>>(self: &'a Self, base_style: S) -> impl Iterator<Item = StyledGrapheme<'a>>` — [`StyledGrapheme`](./index.md#styledgrapheme)

  Returns an iterator over the graphemes held by this line.

  

  `base_style` is the [`Style`](./style.md) that will be patched with each grapheme [`Style`](./style.md) to get

  the resulting [`Style`](./style.md).

  

  `base_style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md),

  or your own type that implements `Into<Style>`).

  

  # Examples

  

  ```rust

  use std::iter::Iterator;

  

  use ratatui_core::style::{Color, Style};

  use ratatui_core::text::{Line, StyledGrapheme};

  

  let line = Line::styled("Text", Style::default().fg(Color::Yellow));

  let style = Style::default().fg(Color::Green).bg(Color::Black);

  assert_eq!(

      line.styled_graphemes(style)

          .collect::<Vec<StyledGrapheme>>(),

      vec![

          StyledGrapheme::new("T", Style::default().fg(Color::Yellow).bg(Color::Black)),

          StyledGrapheme::new("e", Style::default().fg(Color::Yellow).bg(Color::Black)),

          StyledGrapheme::new("x", Style::default().fg(Color::Yellow).bg(Color::Black)),

          StyledGrapheme::new("t", Style::default().fg(Color::Yellow).bg(Color::Black)),

      ]

  );

  ```

- `fn patch_style<S: Into<Style>>(self, style: S) -> Self`

  Patches the style of this Line, adding modifiers from the given style.

  

  This is useful for when you want to apply a style to a line that already has some styling.

  In contrast to `Line::style`, this method will not overwrite the existing style, but

  instead will add the given style's modifiers to this Line's style.

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui_core::style::{Color, Modifier};

  use ratatui_core::text::Line;

  

  let line = Line::styled("My text", Modifier::ITALIC);

  

  let styled_line = Line::styled("My text", (Color::Yellow, Modifier::ITALIC));

  

  assert_eq!(styled_line, line.patch_style(Color::Yellow));

  ```

- `fn reset_style(self) -> Self`

  Resets the style of this Line.

  

  Equivalent to calling `patch_style(Style::reset())`.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  let style = Style::default().yellow();

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Line;

  

  let line = Line::styled("My text", style);

  

  assert_eq!(Style::reset(), line.reset_style().style);

  ```

- `fn iter(&self) -> core::slice::Iter<'_, Span<'a>>` — [`Span`](./index.md#span)

  Returns an iterator over the spans of this line.

- `fn iter_mut(&mut self) -> core::slice::IterMut<'_, Span<'a>>` — [`Span`](./index.md#span)

  Returns a mutable iterator over the spans of this line.

- `fn push_span<T: Into<Span<'a>>>(&mut self, span: T)`

  Adds a span to the line.

  

  `span` can be any type that is convertible into a `Span`. For example, you can pass a

  `&str`, a `String`, or a `Span`.

  

  # Examples

  

  ```rust

  use ratatui_core::text::{Line, Span};

  

  let mut line = Line::from("Hello, ");

  line.push_span(Span::raw("world!"));

  line.push_span(" How are you?");

  ```

#### Trait Implementations

##### `impl Add for Line<'a>`

- `type Output = Line<'a>`

- `fn add(self, rhs: Span<'a>) -> <Self as >::Output` — [`Span`](./index.md#span)

##### `impl AddAssign for Line<'a>`

- `fn add_assign(&mut self, rhs: Span<'a>)` — [`Span`](./index.md#span)

##### `impl Clone for Line<'a>`

- `fn clone(&self) -> Line<'a>` — [`Line`](./index.md#line)

##### `impl Debug for Line<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Line<'a>`

- `fn default() -> Line<'a>` — [`Line`](./index.md#line)

##### `impl Display for Line<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Line<'a>`

##### `impl<K> Equivalent for Line<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Extend for Line<'a>`

- `fn extend<T: IntoIterator<Item = Span<'a>>>(&mut self, iter: T)`

##### `impl<T> FromIterator for Line<'a>`

- `fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self`

##### `impl Hash for Line<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Line<'a>`

##### `impl IntoIterator for Line<'a>`

- `type Item = Span<'a>`

- `type IntoIter = IntoIter<Span<'a>>`

- `fn into_iter(self) -> <Self as >::IntoIter`

##### `impl PartialEq for Line<'a>`

- `fn eq(&self, other: &Line<'a>) -> bool` — [`Line`](./index.md#line)

##### `impl StructuralPartialEq for Line<'a>`

##### `impl Styled for Line<'_>`

- `type Item = Line<'_>`

- `fn style(&self) -> Style` — [`Style`](./style.md#style)

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item` — [`Styled`](./index.md#styled)

##### `impl<T> Stylize for Line<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T` — [`Modifier`](./style.md#modifier)

- `fn remove_modifier(self, modifier: Modifier) -> T` — [`Modifier`](./style.md#modifier)

- `fn reset(self) -> T`

##### `impl ToCompactString for Line<'a>`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Line<'a>`

- `fn to_line(&self) -> Line<'_>` — [`Line`](./index.md#line)

##### `impl ToSpan for Line<'a>`

- `fn to_span(&self) -> Span<'_>` — [`Span`](./index.md#span)

##### `impl ToString for Line<'a>`

- `fn to_string(&self) -> String`

##### `impl ToText for Line<'a>`

- `fn to_text(&self) -> Text<'_>` — [`Text`](./index.md#text)

##### `impl UnicodeWidthStr for Line<'_>`

- `fn width(&self) -> usize`

- `fn width_cjk(&self) -> usize`

##### `impl Widget for Line<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)` — [`Rect`](./index.md#rect), [`Buffer`](./index.md#buffer)

### `Masked<'a>`

```rust
struct Masked<'a> {
    // [REDACTED: Private Fields]
}
```

A wrapper around a string that is masked when displayed.

The masked string is displayed as a series of the same character. This might be used to display
a password field or similar secure data.

# Examples

```rust
use ratatui_core::buffer::Buffer;
use ratatui_core::layout::Rect;
use ratatui_core::text::{Masked, Text};
use ratatui_core::widgets::Widget;

let mut buffer = Buffer::empty(Rect::new(0, 0, 5, 1));
let password = Masked::new("12345", 'x');

Text::from(password).render(buffer.area, &mut buffer);
assert_eq!(buffer, Buffer::with_lines(["xxxxx"]));
```

#### Implementations

- `fn new(s: impl Into<Cow<'a, str>>, mask_char: char) -> Self`

- `const fn mask_char(&self) -> char`

  The character to use for masking.

- `fn value(&self) -> Cow<'a, str>`

  The underlying string, with all characters masked.

#### Trait Implementations

##### `impl Clone for Masked<'a>`

- `fn clone(&self) -> Masked<'a>` — [`Masked`](./index.md#masked)

##### `impl Debug for Masked<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

  Debug representation of a masked string is the underlying string

##### `impl Default for Masked<'a>`

- `fn default() -> Masked<'a>` — [`Masked`](./index.md#masked)

##### `impl Display for Masked<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

  Display representation of a masked string is the masked string

##### `impl Eq for Masked<'a>`

##### `impl<K> Equivalent for Masked<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Masked<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Masked<'a>`

##### `impl PartialEq for Masked<'a>`

- `fn eq(&self, other: &Masked<'a>) -> bool` — [`Masked`](./index.md#masked)

##### `impl StructuralPartialEq for Masked<'a>`

##### `impl ToCompactString for Masked<'a>`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Masked<'a>`

- `fn to_line(&self) -> Line<'_>` — [`Line`](./index.md#line)

##### `impl ToSpan for Masked<'a>`

- `fn to_span(&self) -> Span<'_>` — [`Span`](./index.md#span)

##### `impl ToString for Masked<'a>`

- `fn to_string(&self) -> String`

##### `impl ToText for Masked<'a>`

- `fn to_text(&self) -> Text<'_>` — [`Text`](./index.md#text)

### `Span<'a>`

```rust
struct Span<'a> {
    pub style: crate::style::Style,
    pub content: alloc::borrow::Cow<'a, str>,
}
```

Represents a part of a line that is contiguous and where all characters share the same style.

A `Span` is the smallest unit of text that can be styled. It is usually combined in the [`Line`](./index.md)
type to represent a line of text where each `Span` may have a different style.

# Constructor Methods

- `Span::default` creates an span with empty content and the default style.
- `Span::raw` creates an span with the specified content and the default style.
- `Span::styled` creates an span with the specified content and style.

# Setter Methods

These methods are fluent setters. They return a new `Span` with the specified property set.

- `Span::content` sets the content of the span.
- `Span::style` sets the style of the span.

# Other Methods

- `Span::patch_style` patches the style of the span, adding modifiers from the given style.
- `Span::reset_style` resets the style of the span.
- `Span::width` returns the unicode width of the content held by this span.
- `Span::styled_graphemes` returns an iterator over the graphemes held by this span.

# Examples

A `Span` with `style` set to `Style::default()` can be created from a `&str`, a `String`, or
any type convertible to `Cow<str>`.

```rust
use ratatui_core::text::Span;

let span = Span::raw("test content");
let span = Span::raw(String::from("test content"));
let span = Span::from("test content");
let span = Span::from(String::from("test content"));
let span: Span = "test content".into();
let span: Span = String::from("test content").into();
```

Styled spans can be created using `Span::styled` or by converting strings using methods from
the [`Stylize`](./index.md) trait.

```rust
use ratatui_core::style::{Style, Stylize};
use ratatui_core::text::Span;

let span = Span::styled("test content", Style::new().green());
let span = Span::styled(String::from("test content"), Style::new().green());

// using Stylize trait shortcuts
let span = "test content".green();
let span = String::from("test content").green();
```

`Span` implements the [`Styled`](./index.md) trait, which allows it to be styled using the shortcut methods
defined in the [`Stylize`](./index.md) trait.

```rust
use ratatui_core::style::Stylize;
use ratatui_core::text::Span;

let span = Span::raw("test content").green().on_yellow().italic();
let span = Span::raw(String::from("test content"))
    .green()
    .on_yellow()
    .italic();
```

`Span` implements the [`Widget`](./index.md) trait, which allows it to be rendered to a [`Buffer`](./index.md). Often
apps will use the `Paragraph` widget instead of rendering `Span` directly, as it handles text
wrapping and alignment for you.

```rust,ignore
use ratatui::{style::Stylize, Frame};

fn render_frame(frame: &mut Frame) {
frame.render_widget("test content".green().on_yellow().italic(), frame.area());
}
```

#### Fields

- **`style`**: `crate::style::Style`

  The style of the span.

- **`content`**: `alloc::borrow::Cow<'a, str>`

  The content of the span as a Clone-on-write string.

#### Implementations

- `fn raw<T>(content: T) -> Self`

  Create a span with the default style.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Span;

  

  Span::raw("test content");

  Span::raw(String::from("test content"));

  ```

- `fn styled<T, S>(content: T, style: S) -> Self`

  Create a span with the specified style.

  

  `content` accepts any type that is convertible to `Cow<str>` (e.g. `&str`, `String`,

  `&String`, etc.).

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  # Examples

  

  ```rust

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Span;

  

  let style = Style::new().yellow().on_green().italic();

  Span::styled("test content", style);

  Span::styled(String::from("test content"), style);

  ```

- `fn content<T>(self, content: T) -> Self`

  Sets the content of the span.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  Accepts any type that can be converted to `Cow<str>` (e.g. `&str`, `String`, `&String`,

  etc.).

  

  # Examples

  

  ```rust

  use ratatui_core::text::Span;

  

  let mut span = Span::default().content("content");

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of the span.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  In contrast to `Span::patch_style`, this method replaces the style of the span instead of

  patching it.

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  # Examples

  

  ```rust

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Span;

  

  let mut span = Span::default().style(Style::new().green());

  ```

- `fn patch_style<S: Into<Style>>(self, style: S) -> Self`

  Patches the style of the Span, adding modifiers from the given style.

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  

  ```rust

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Span;

  

  let span = Span::styled("test content", Style::new().green().italic())

      .patch_style(Style::new().red().on_yellow().bold());

  assert_eq!(span.style, Style::new().red().on_yellow().italic().bold());

  ```

- `fn reset_style(self) -> Self`

  Resets the style of the Span.

  

  This is Equivalent to calling `patch_style(Style::reset())`.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  

  ```rust

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Span;

  

  let span = Span::styled(

      "Test Content",

      Style::new().dark_gray().on_yellow().italic(),

  )

  .reset_style();

  assert_eq!(span.style, Style::reset());

  ```

- `fn width(&self) -> usize`

  Returns the unicode width of the content held by this span.

- `fn styled_graphemes<S: Into<Style>>(self: &'a Self, base_style: S) -> impl Iterator<Item = StyledGrapheme<'a>>` — [`StyledGrapheme`](./index.md#styledgrapheme)

  Returns an iterator over the graphemes held by this span.

  

  `base_style` is the [`Style`](./style.md) that will be patched with the `Span`'s `style` to get the

  resulting [`Style`](./style.md).

  

  `base_style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md),

  or your own type that implements `Into<Style>`).

  

  # Example

  

  ```rust

  use std::iter::Iterator;

  

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::{Span, StyledGrapheme};

  

  let span = Span::styled("Test", Style::new().green().italic());

  let style = Style::new().red().on_yellow();

  assert_eq!(

      span.styled_graphemes(style)

          .collect::<Vec<StyledGrapheme>>(),

      vec![

          StyledGrapheme::new("T", Style::new().green().on_yellow().italic()),

          StyledGrapheme::new("e", Style::new().green().on_yellow().italic()),

          StyledGrapheme::new("s", Style::new().green().on_yellow().italic()),

          StyledGrapheme::new("t", Style::new().green().on_yellow().italic()),

      ],

  );

  ```

- `fn into_left_aligned_line(self) -> Line<'a>` — [`Line`](./index.md#line)

  Converts this Span into a left-aligned [`Line`](./index.md)

  

  # Example

  

  ```rust

  use ratatui_core::style::Stylize;

  

  let line = "Test Content".green().italic().into_left_aligned_line();

  ```

- `fn to_left_aligned_line(self) -> Line<'a>` — [`Line`](./index.md#line)

- `fn into_centered_line(self) -> Line<'a>` — [`Line`](./index.md#line)

  Converts this Span into a center-aligned [`Line`](./index.md)

  

  # Example

  

  ```rust

  use ratatui_core::style::Stylize;

  

  let line = "Test Content".green().italic().into_centered_line();

  ```

- `fn to_centered_line(self) -> Line<'a>` — [`Line`](./index.md#line)

- `fn into_right_aligned_line(self) -> Line<'a>` — [`Line`](./index.md#line)

  Converts this Span into a right-aligned [`Line`](./index.md)

  

  # Example

  

  ```rust

  use ratatui_core::style::Stylize;

  

  let line = "Test Content".green().italic().into_right_aligned_line();

  ```

- `fn to_right_aligned_line(self) -> Line<'a>` — [`Line`](./index.md#line)

#### Trait Implementations

##### `impl Add for Line<'a>`

- `type Output = Line<'a>`

- `fn add(self, rhs: Span<'a>) -> <Self as >::Output` — [`Span`](./index.md#span)

##### `impl AddAssign for Line<'a>`

- `fn add_assign(&mut self, rhs: Span<'a>)` — [`Span`](./index.md#span)

##### `impl Clone for Span<'a>`

- `fn clone(&self) -> Span<'a>` — [`Span`](./index.md#span)

##### `impl Debug for Span<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Span<'a>`

- `fn default() -> Span<'a>` — [`Span`](./index.md#span)

##### `impl Display for Span<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Span<'a>`

##### `impl<K> Equivalent for Span<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Extend for Line<'a>`

- `fn extend<T: IntoIterator<Item = Span<'a>>>(&mut self, iter: T)`

##### `impl Hash for Span<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Span<'a>`

##### `impl PartialEq for Span<'a>`

- `fn eq(&self, other: &Span<'a>) -> bool` — [`Span`](./index.md#span)

##### `impl StructuralPartialEq for Span<'a>`

##### `impl Styled for Span<'_>`

- `type Item = Span<'_>`

- `fn style(&self) -> Style` — [`Style`](./style.md#style)

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item` — [`Styled`](./index.md#styled)

##### `impl<T> Stylize for Span<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T` — [`Modifier`](./style.md#modifier)

- `fn remove_modifier(self, modifier: Modifier) -> T` — [`Modifier`](./style.md#modifier)

- `fn reset(self) -> T`

##### `impl ToCompactString for Span<'a>`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Span<'a>`

- `fn to_line(&self) -> Line<'_>` — [`Line`](./index.md#line)

##### `impl ToSpan for Span<'a>`

- `fn to_span(&self) -> Span<'_>` — [`Span`](./index.md#span)

##### `impl ToString for Span<'a>`

- `fn to_string(&self) -> String`

##### `impl ToText for Span<'a>`

- `fn to_text(&self) -> Text<'_>` — [`Text`](./index.md#text)

##### `impl UnicodeWidthStr for Span<'_>`

- `fn width(&self) -> usize`

- `fn width_cjk(&self) -> usize`

##### `impl Widget for Span<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)` — [`Rect`](./index.md#rect), [`Buffer`](./index.md#buffer)

### `Text<'a>`

```rust
struct Text<'a> {
    pub alignment: Option<crate::layout::Alignment>,
    pub style: crate::style::Style,
    pub lines: alloc::vec::Vec<crate::text::Line<'a>>,
}
```

A string split over one or more lines.

[`Text`](./index.md) is used wherever text is displayed in the terminal and represents one or more [`Line`](./index.md)s
of text. When a [`Text`](./index.md) is rendered, each line is rendered as a single line of text from top to
bottom of the area. The text can be styled and aligned.

# Constructor Methods

- `Text::raw` creates a `Text` (potentially multiple lines) with no style.
- `Text::styled` creates a `Text` (potentially multiple lines) with a style.
- `Text::default` creates a `Text` with empty content and the default style.

# Conversion Methods

- `Text::from` creates a `Text` from a `String`.
- `Text::from` creates a `Text` from a `&str`.
- `Text::from` creates a `Text` from a `Cow<str>`.
- `Text::from` creates a `Text` from a [`Span`](./index.md).
- `Text::from` creates a `Text` from a [`Line`](./index.md).
- `Text::from` creates a `Text` from a `Vec<Line>`.
- `Text::from` creates a `Text` from a `&[Into<Line>]`.
- `Text::from_iter` creates a `Text` from an iterator of items that can be converted into
  `Line`.

# Setter Methods

These methods are fluent setters. They return a `Text` with the property set.

- `Text::style` sets the style of this `Text`.
- `Text::alignment` sets the alignment for this `Text`.
- `Text::left_aligned` sets the alignment to [`Alignment::Left`](./index.md).
- `Text::centered` sets the alignment to [`Alignment::Center`](./index.md).
- `Text::right_aligned` sets the alignment to [`Alignment::Right`](./index.md).

# Iteration Methods

- `Text::iter` returns an iterator over the lines of the text.
- `Text::iter_mut` returns an iterator that allows modifying each line.
- `Text::into_iter` returns an iterator over the lines of the text.

# Other Methods

- `Text::width` returns the max width of all the lines.
- `Text::height` returns the height.
- `Text::patch_style` patches the style of this `Text`, adding modifiers from the given style.
- `Text::reset_style` resets the style of the `Text`.
- `Text::push_line` adds a line to the text.
- `Text::push_span` adds a span to the last line of the text.

# Examples

## Creating Text

A [`Text`](./index.md), like a [`Line`](./index.md), can be constructed using one of the many `From` implementations or
via the `Text::raw` and `Text::styled` methods. Helpfully, [`Text`](./index.md) also implements
`core::iter::Extend` which enables the concatenation of several [`Text`](./index.md) blocks.

```rust
use std::borrow::Cow;
use std::iter;

use ratatui_core::style::{Color, Modifier, Style, Stylize};
use ratatui_core::text::{Line, Span, Text};

let style = Style::new().yellow().italic();
let text = Text::raw("The first line\nThe second line").style(style);
let text = Text::styled("The first line\nThe second line", style);
let text = Text::styled(
    "The first line\nThe second line",
    (Color::Yellow, Modifier::ITALIC),
);

let text = Text::from("The first line\nThe second line");
let text = Text::from(String::from("The first line\nThe second line"));
let text = Text::from(Cow::Borrowed("The first line\nThe second line"));
let text = Text::from(Span::styled("The first line\nThe second line", style));
let text = Text::from(Line::from("The first line"));
let text = Text::from(vec![
    Line::from("The first line"),
    Line::from("The second line"),
]);
let text = Text::from_iter(iter::once("The first line").chain(iter::once("The second line")));

let mut text = Text::default();
text.extend(vec![
    Line::from("The first line"),
    Line::from("The second line"),
]);
text.extend(Text::from("The third line\nThe fourth line"));
```

## Styling Text

The text's [`Style`](./style.md) is used by the rendering widget to determine how to style the text. Each
[`Line`](./index.md) in the text will be styled with the [`Style`](./style.md) of the text, and then with its own
[`Style`](./style.md). `Text` also implements [`Styled`](./index.md) which means you can use the methods of the
[`Stylize`](./index.md) trait.

```rust
use ratatui_core::style::{Color, Modifier, Style, Stylize};
use ratatui_core::text::{Line, Text};

let text = Text::from("The first line\nThe second line").style(Style::new().yellow().italic());
let text = Text::from("The first line\nThe second line")
    .yellow()
    .italic();
let text = Text::from(vec![
    Line::from("The first line").yellow(),
    Line::from("The second line").yellow(),
])
.italic();
```

## Aligning Text
The text's [`Alignment`](./index.md) can be set using `Text::alignment` or the related helper methods.
Lines composing the text can also be individually aligned with `Line::alignment`.

```rust
use ratatui_core::layout::Alignment;
use ratatui_core::text::{Line, Text};

let text = Text::from("The first line\nThe second line").alignment(Alignment::Right);
let text = Text::from("The first line\nThe second line").right_aligned();
let text = Text::from(vec![
    Line::from("The first line").left_aligned(),
    Line::from("The second line").right_aligned(),
    Line::from("The third line"),
])
.centered();
```

## Rendering Text
`Text` implements the [`Widget`](./index.md) trait, which means it can be rendered to a [`Buffer`](./index.md) or to a
`Frame`.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect};
use ratatui_core::text::Text;
use ratatui_core::widgets::Widget;

// within another widget's `render` method:
fn render(area: Rect, buf: &mut Buffer) {
let text = Text::from("The first line\nThe second line");
text.render(area, buf);
}
```

Or you can use the `render_widget` method on a `Frame` within a `Terminal::draw` closure.

```rust,ignore
use ratatui::{Frame, layout::Rect, text::Text};
fn draw(frame: &mut Frame, area: Rect) {
let text = Text::from("The first line\nThe second line");
frame.render_widget(text, area);
}
```

## Rendering Text with a Paragraph Widget

Usually apps will use the `Paragraph` widget instead of rendering a `Text` directly as it
provides more functionality.

```rust,ignore
use ratatui::{
    buffer::Buffer,
    layout::Rect,
    text::Text,
    widgets::{Paragraph, Widget, Wrap},
};

fn render(area: Rect, buf: &mut Buffer) {
let text = Text::from("The first line\nThe second line");
let paragraph = Paragraph::new(text)
    .wrap(Wrap { trim: true })
    .scroll((1, 1))
    .render(area, buf);
}
```

#### Fields

- **`alignment`**: `Option<crate::layout::Alignment>`

  The alignment of this text.

- **`style`**: `crate::style::Style`

  The style of this text.

- **`lines`**: `alloc::vec::Vec<crate::text::Line<'a>>`

  The lines that make up this piece of text.

#### Implementations

- `fn raw<T>(content: T) -> Self`

  Create some text (potentially multiple lines) with no style.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Text;

  

  Text::raw("The first line\nThe second line");

  Text::raw(String::from("The first line\nThe second line"));

  ```

- `fn styled<T, S>(content: T, style: S) -> Self`

  Create some text (potentially multiple lines) with a style.

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  # Examples

  

  ```rust

  use ratatui_core::style::{Color, Modifier, Style};

  use ratatui_core::text::Text;

  

  let style = Style::default()

      .fg(Color::Yellow)

      .add_modifier(Modifier::ITALIC);

  Text::styled("The first line\nThe second line", style);

  Text::styled(String::from("The first line\nThe second line"), style);

  ```

- `fn width(&self) -> usize`

  Returns the max width of all the lines.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Text;

  

  let text = Text::from("The first line\nThe second line");

  assert_eq!(15, text.width());

  ```

- `const fn height(&self) -> usize`

  Returns the height.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Text;

  

  let text = Text::from("The first line\nThe second line");

  assert_eq!(2, text.height());

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of this text.

  

  Defaults to `Style::default()`.

  

  Note: This field was added in v0.26.0. Prior to that, the style of a text was determined

  only by the style of each [`Line`](./index.md) contained in the line. For this reason, this field may

  not be supported by all widgets (outside of the `ratatui` crate itself).

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  # Examples

  ```rust

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Text;

  

  let mut line = Text::from("foo").style(Style::new().red());

  ```

- `fn patch_style<S: Into<Style>>(self, style: S) -> Self`

  Patches the style of this Text, adding modifiers from the given style.

  

  This is useful for when you want to apply a style to a text that already has some styling.

  In contrast to `Text::style`, this method will not overwrite the existing style, but

  instead will add the given style's modifiers to this text's style.

  

  `Text` also implements [`Styled`](./index.md) which means you can use the methods of the [`Stylize`](./index.md)

  trait.

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui_core::style::{Color, Modifier};

  use ratatui_core::text::Text;

  

  let raw_text = Text::styled("The first line\nThe second line", Modifier::ITALIC);

  let styled_text = Text::styled(

      String::from("The first line\nThe second line"),

      (Color::Yellow, Modifier::ITALIC),

  );

  assert_ne!(raw_text, styled_text);

  

  let raw_text = raw_text.patch_style(Color::Yellow);

  assert_eq!(raw_text, styled_text);

  ```

  

- `fn reset_style(self) -> Self`

  Resets the style of the Text.

  

  Equivalent to calling [`patch_style(Style::reset())`](Text::patch_style).

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui_core::style::{Color, Modifier, Style};

  use ratatui_core::text::Text;

  

  let text = Text::styled(

      "The first line\nThe second line",

      (Color::Yellow, Modifier::ITALIC),

  );

  

  let text = text.reset_style();

  assert_eq!(Style::reset(), text.style);

  ```

- `fn alignment(self, alignment: Alignment) -> Self` — [`Alignment`](./index.md#alignment)

  Sets the alignment for this text.

  

  Defaults to: [`None`](./index.md), meaning the alignment is determined by the rendering widget.

  Setting the alignment of a Text generally overrides the alignment of its

  parent Widget.

  

  Alignment can be set individually on each line to override this text's alignment.

  

  # Examples

  

  Set alignment to the whole text.

  

  ```rust

  use ratatui_core::layout::Alignment;

  use ratatui_core::text::Text;

  

  let mut text = Text::from("Hi, what's up?");

  assert_eq!(None, text.alignment);

  assert_eq!(

      Some(Alignment::Right),

      text.alignment(Alignment::Right).alignment

  )

  ```

  

  Set a default alignment and override it on a per line basis.

  

  ```rust

  use ratatui_core::layout::Alignment;

  use ratatui_core::text::{Line, Text};

  

  let text = Text::from(vec![

      Line::from("left").alignment(Alignment::Left),

      Line::from("default"),

      Line::from("default"),

      Line::from("right").alignment(Alignment::Right),

  ])

  .alignment(Alignment::Center);

  ```

  

  Will render the following

  

  ```plain

  left

    default

    default

        right

  ```

- `fn left_aligned(self) -> Self`

  Left-aligns the whole text.

  

  Convenience shortcut for `Text::alignment(Alignment::Left)`.

  Setting the alignment of a Text generally overrides the alignment of its

  parent Widget, with the default alignment being inherited from the parent.

  

  Alignment can be set individually on each line to override this text's alignment.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Text;

  

  let text = Text::from("Hi, what's up?").left_aligned();

  ```

- `fn centered(self) -> Self`

  Center-aligns the whole text.

  

  Convenience shortcut for `Text::alignment(Alignment::Center)`.

  Setting the alignment of a Text generally overrides the alignment of its

  parent Widget, with the default alignment being inherited from the parent.

  

  Alignment can be set individually on each line to override this text's alignment.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Text;

  

  let text = Text::from("Hi, what's up?").centered();

  ```

- `fn right_aligned(self) -> Self`

  Right-aligns the whole text.

  

  Convenience shortcut for `Text::alignment(Alignment::Right)`.

  Setting the alignment of a Text generally overrides the alignment of its

  parent Widget, with the default alignment being inherited from the parent.

  

  Alignment can be set individually on each line to override this text's alignment.

  

  # Examples

  

  ```rust

  use ratatui_core::text::Text;

  

  let text = Text::from("Hi, what's up?").right_aligned();

  ```

- `fn iter(&self) -> core::slice::Iter<'_, Line<'a>>` — [`Line`](./index.md#line)

  Returns an iterator over the lines of the text.

- `fn iter_mut(&mut self) -> core::slice::IterMut<'_, Line<'a>>` — [`Line`](./index.md#line)

  Returns an iterator that allows modifying each line.

- `fn push_line<T: Into<Line<'a>>>(&mut self, line: T)`

  Adds a line to the text.

  

  `line` can be any type that can be converted into a `Line`. For example, you can pass a

  `&str`, a `String`, a `Span`, or a `Line`.

  

  # Examples

  

  ```rust

  use ratatui_core::text::{Line, Span, Text};

  

  let mut text = Text::from("Hello, world!");

  text.push_line(Line::from("How are you?"));

  text.push_line(Span::from("How are you?"));

  text.push_line("How are you?");

  ```

- `fn push_span<T: Into<Span<'a>>>(&mut self, span: T)`

  Adds a span to the last line of the text.

  

  `span` can be any type that is convertible into a `Span`. For example, you can pass a

  `&str`, a `String`, or a `Span`.

  

  # Examples

  

  ```rust

  use ratatui_core::text::{Span, Text};

  

  let mut text = Text::from("Hello, world!");

  text.push_span(Span::from("How are you?"));

  text.push_span("How are you?");

  ```

#### Trait Implementations

##### `impl Add for Text<'a>`

- `type Output = Text<'a>`

- `fn add(self, line: Line<'a>) -> <Self as >::Output` — [`Line`](./index.md#line)

##### `impl AddAssign for Text<'_>`

- `fn add_assign(&mut self, rhs: Self)`

##### `impl Clone for Text<'a>`

- `fn clone(&self) -> Text<'a>` — [`Text`](./index.md#text)

##### `impl Debug for Text<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Text<'a>`

- `fn default() -> Text<'a>` — [`Text`](./index.md#text)

##### `impl Display for Text<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Text<'a>`

##### `impl<K> Equivalent for Text<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl<T> Extend for Text<'a>`

- `fn extend<I: IntoIterator<Item = T>>(&mut self, iter: I)`

##### `impl<T> FromIterator for Text<'a>`

- `fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self`

##### `impl Hash for Text<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Text<'a>`

##### `impl IntoIterator for Text<'a>`

- `type Item = Line<'a>`

- `type IntoIter = IntoIter<<Text<'a> as IntoIterator>::Item>`

- `fn into_iter(self) -> <Self as >::IntoIter`

##### `impl PartialEq for Text<'a>`

- `fn eq(&self, other: &Text<'a>) -> bool` — [`Text`](./index.md#text)

##### `impl StructuralPartialEq for Text<'a>`

##### `impl Styled for Text<'_>`

- `type Item = Text<'_>`

- `fn style(&self) -> Style` — [`Style`](./style.md#style)

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item` — [`Styled`](./index.md#styled)

##### `impl<T> Stylize for Text<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T` — [`Modifier`](./style.md#modifier)

- `fn remove_modifier(self, modifier: Modifier) -> T` — [`Modifier`](./style.md#modifier)

- `fn reset(self) -> T`

##### `impl ToCompactString for Text<'a>`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Text<'a>`

- `fn to_line(&self) -> Line<'_>` — [`Line`](./index.md#line)

##### `impl ToSpan for Text<'a>`

- `fn to_span(&self) -> Span<'_>` — [`Span`](./index.md#span)

##### `impl ToString for Text<'a>`

- `fn to_string(&self) -> String`

##### `impl ToText for Text<'a>`

- `fn to_text(&self) -> Text<'_>` — [`Text`](./index.md#text)

##### `impl UnicodeWidthStr for Text<'_>`

- `fn width(&self) -> usize`

  Returns the max width of all the lines.

- `fn width_cjk(&self) -> usize`

##### `impl Widget for Text<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)` — [`Rect`](./index.md#rect), [`Buffer`](./index.md#buffer)

## Traits

### `ToLine`

```rust
trait ToLine { ... }
```

A trait for converting a value to a [`Line`](./index.md).

This trait is automatically implemented for any type that implements the `Display` trait. As
such, `ToLine` shouldn't be implemented directly: `Display` should be implemented instead, and
you get the `ToLine` implementation for free.

#### Required Methods

- `fn to_line(&self) -> Line<'_>`

  Converts the value to a [`Line`](./index.md).

#### Implementors

- `T`

### `ToSpan`

```rust
trait ToSpan { ... }
```

A trait for converting a value to a [`Span`](./index.md).

This trait is automatically implemented for any type that implements the `Display` trait. As
such, `ToSpan` shouldn't be implemented directly: `Display` should be implemented instead, and
you get the `ToSpan` implementation for free.

#### Required Methods

- `fn to_span(&self) -> Span<'_>`

  Converts the value to a [`Span`](./index.md).

#### Implementors

- `T`

### `ToText`

```rust
trait ToText { ... }
```

A trait for converting a value to a [`Text`](./index.md).

This trait is automatically implemented for any type that implements the `Display` trait. As
such, `ToText` shouldn't be implemented directly: `Display` should be implemented instead, and
you get the `ToText` implementation for free.

#### Required Methods

- `fn to_text(&self) -> Text<'_>`

  Converts the value to a [`Text`](./index.md).

#### Implementors

- `T`

