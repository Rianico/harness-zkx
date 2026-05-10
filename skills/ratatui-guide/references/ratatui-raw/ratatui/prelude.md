*[ratatui](./index.md) / [prelude](#)*

---

# Module `prelude`

A prelude for conveniently writing applications using this library.

The prelude module is no longer used universally in Ratatui, as it can make it harder to
distinguish between library and non-library types, especially when viewing source code
outside of an IDE (such as on GitHub or in a git diff). For more details and user feedback,
see [Issue #1150]. However, the prelude is still available for backward compatibility and for
those who prefer to use it.

# Examples

```rust,no_run
use ratatui::prelude::*;
```

Aside from the main types that are used in the library, this prelude also re-exports several
modules to make it easy to qualify types that would otherwise collide. E.g.:

```rust
use ratatui::prelude::*;
use ratatui::widgets::*;

#[derive(Debug, Default, PartialEq, Eq)]
struct Line;

assert_eq!(Line::default(), Line);
assert_eq!(text::Line::default(), ratatui::text::Line::from(vec![]));
```

## Contents

- [Structs](#structs)
  - [`VerticalAlignment`](#verticalalignment)
  - [`Color`](#color)
- [Traits](#traits)
  - [`Size`](#size)
  - [`style`](#style)
  - [`Modifier`](#modifier)
- [Functions](#functions)
  - [`backend`](#backend)
  - [`FromCrossterm`](#fromcrossterm)
  - [`IntoCrossterm`](#intocrossterm)
  - [`buffer`](#buffer)
  - [`Buffer`](#buffer)
  - [`Alignment`](#alignment)
  - [`Direction`](#direction)
  - [`Position`](#position)
  - [`Line`](#line)
  - [`Span`](#span)
  - [`StatefulWidget`](#statefulwidget)
  - [`Widget`](#widget)
  - [`Frame`](#frame)
- [Macros](#macros)
  - [`CrosstermBackend!`](#crosstermbackend)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`VerticalAlignment`](#verticalalignment) | struct |  |
| [`Color`](#color) | struct |  |
| [`Size`](#size) | trait |  |
| [`style`](#style) | trait |  |
| [`Modifier`](#modifier) | trait |  |
| [`backend`](#backend) | fn |  |
| [`FromCrossterm`](#fromcrossterm) | fn |  |
| [`IntoCrossterm`](#intocrossterm) | fn |  |
| [`buffer`](#buffer) | fn |  |
| [`Buffer`](#buffer) | fn |  |
| [`Alignment`](#alignment) | fn |  |
| [`Direction`](#direction) | fn |  |
| [`Position`](#position) | fn |  |
| [`Line`](#line) | fn |  |
| [`Span`](#span) | fn |  |
| [`StatefulWidget`](#statefulwidget) | fn |  |
| [`Widget`](#widget) | fn |  |
| [`Frame`](#frame) | fn |  |
| [`CrosstermBackend!`](#crosstermbackend) | macro |  |

## Structs

### `VerticalAlignment<'a>`

```rust
struct VerticalAlignment<'a> {
    pub style: crate::style::Style,
    pub content: alloc::borrow::Cow<'a, str>,
}
```

*Re-exported from `ratatui_core`*

Represents a part of a line that is contiguous and where all characters share the same style.

A `Span` is the smallest unit of text that can be styled. It is usually combined in the [`Line`](../ratatui_core/index.md)
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
the [`Stylize`](../ratatui_core/index.md) trait.

```rust
use ratatui_core::style::{Style, Stylize};
use ratatui_core::text::Span;

let span = Span::styled("test content", Style::new().green());
let span = Span::styled(String::from("test content"), Style::new().green());

// using Stylize trait shortcuts
let span = "test content".green();
let span = String::from("test content").green();
```

`Span` implements the [`Styled`](#styled) trait, which allows it to be styled using the shortcut methods
defined in the [`Stylize`](../ratatui_core/index.md) trait.

```rust
use ratatui_core::style::Stylize;
use ratatui_core::text::Span;

let span = Span::raw("test content").green().on_yellow().italic();
let span = Span::raw(String::from("test content"))
    .green()
    .on_yellow()
    .italic();
```

`Span` implements the [`Widget`](../ratatui_core/index.md) trait, which allows it to be rendered to a [`Buffer`](../ratatui_crossterm/index.md). Often
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

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements [`Into<Style>`](./backend.md)).

  

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

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements [`Into<Style>`](./backend.md)).

  

  # Examples

  

  ```rust

  use ratatui_core::style::{Style, Stylize};

  use ratatui_core::text::Span;

  

  let mut span = Span::default().style(Style::new().green());

  ```

- `fn patch_style<S: Into<Style>>(self, style: S) -> Self`

  Patches the style of the Span, adding modifiers from the given style.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements [`Into<Style>`](./backend.md)).

  

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

- `fn styled_graphemes<S: Into<Style>>(self: &'a Self, base_style: S) -> impl Iterator<Item = StyledGrapheme<'a>>` — [`dimmed`](./widgets.md#dimmed)

  Returns an iterator over the graphemes held by this span.

  

  `base_style` is the [`Style`](../ratatui_core/style.md) that will be patched with the `Span`'s `style` to get the

  resulting [`Style`](../ratatui_core/style.md).

  

  `base_style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md),

  or your own type that implements [`Into<Style>`](./backend.md)).

  

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

- `fn into_left_aligned_line(self) -> Line<'a>` — [`FromCrossterm`](./backend.md#fromcrossterm)

  Converts this Span into a left-aligned [`Line`](../ratatui_crossterm/index.md)

  

  # Example

  

  ```rust

  use ratatui_core::style::Stylize;

  

  let line = "Test Content".green().italic().into_left_aligned_line();

  ```

- `fn to_left_aligned_line(self) -> Line<'a>` — [`FromCrossterm`](./backend.md#fromcrossterm)

- `fn into_centered_line(self) -> Line<'a>` — [`FromCrossterm`](./backend.md#fromcrossterm)

  Converts this Span into a center-aligned [`Line`](../ratatui_crossterm/index.md)

  

  # Example

  

  ```rust

  use ratatui_core::style::Stylize;

  

  let line = "Test Content".green().italic().into_centered_line();

  ```

- `fn to_centered_line(self) -> Line<'a>` — [`FromCrossterm`](./backend.md#fromcrossterm)

- `fn into_right_aligned_line(self) -> Line<'a>` — [`FromCrossterm`](./backend.md#fromcrossterm)

  Converts this Span into a right-aligned [`Line`](../ratatui_crossterm/index.md)

  

  # Example

  

  ```rust

  use ratatui_core::style::Stylize;

  

  let line = "Test Content".green().italic().into_right_aligned_line();

  ```

- `fn to_right_aligned_line(self) -> Line<'a>` — [`FromCrossterm`](./backend.md#fromcrossterm)

#### Trait Implementations

##### `impl Add for Span<'a>`

- `type Output = Line<'a>`

- `fn add(self, rhs: Self) -> <Self as >::Output`

##### `impl Clone for Span<'a>`

- `fn clone(&self) -> Span<'a>` — [`VerticalAlignment`](#verticalalignment)

##### `impl Debug for Span<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result` — [`Bar`](./widgets.md#bar), [`Bar`](./widgets.md#bar)

##### `impl Default for Span<'a>`

- `fn default() -> Span<'a>` — [`VerticalAlignment`](#verticalalignment)

##### `impl Display for Span<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result` — [`Bar`](./widgets.md#bar), [`Bar`](./widgets.md#bar)

##### `impl Eq for Span<'a>`

##### `impl<K> Equivalent for Span<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Span<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Span<'a>`

##### `impl PartialEq for Span<'a>`

- `fn eq(&self, other: &Span<'a>) -> bool` — [`VerticalAlignment`](#verticalalignment)

##### `impl StructuralPartialEq for Span<'a>`

##### `impl Styled for Span<'_>`

- `type Item = Span<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Span<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl ToCompactString for Span<'a>`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>` — [`Widget`](#widget)

##### `impl ToLine for Span<'a>`

- `fn to_line(&self) -> Line<'_>` — [`FromCrossterm`](./backend.md#fromcrossterm)

##### `impl ToSpan for Span<'a>`

- `fn to_span(&self) -> Span<'_>` — [`VerticalAlignment`](#verticalalignment)

##### `impl ToString for Span<'a>`

- `fn to_string(&self) -> String`

##### `impl ToText for Span<'a>`

- `fn to_text(&self) -> Text<'_>` — [`Color`](#color)

##### `impl UnicodeWidthStr for Span<'_>`

- `fn width(&self) -> usize`

- `fn width_cjk(&self) -> usize`

##### `impl Widget for Span<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)` — [`run`](./index.md#run), [`IntoCrossterm`](./backend.md#intocrossterm)

### `Color<'a>`

```rust
struct Color<'a> {
    pub alignment: Option<crate::layout::Alignment>,
    pub style: crate::style::Style,
    pub lines: alloc::vec::Vec<crate::text::Line<'a>>,
}
```

*Re-exported from `ratatui_core`*

A string split over one or more lines.

[`Text`](#text) is used wherever text is displayed in the terminal and represents one or more [`Line`](../ratatui_crossterm/index.md)s
of text. When a [`Text`](#text) is rendered, each line is rendered as a single line of text from top to
bottom of the area. The text can be styled and aligned.

# Constructor Methods

- `Text::raw` creates a `Text` (potentially multiple lines) with no style.
- `Text::styled` creates a `Text` (potentially multiple lines) with a style.
- `Text::default` creates a `Text` with empty content and the default style.

# Conversion Methods

- `Text::from` creates a `Text` from a `String`.
- `Text::from` creates a `Text` from a `&str`.
- `Text::from` creates a `Text` from a `Cow<str>`.
- `Text::from` creates a `Text` from a [`Span`](#span).
- `Text::from` creates a `Text` from a [`Line`](../ratatui_crossterm/index.md).
- `Text::from` creates a `Text` from a `Vec<Line>`.
- `Text::from` creates a `Text` from a `&[Into<Line>]`.
- `Text::from_iter` creates a `Text` from an iterator of items that can be converted into
  `Line`.

# Setter Methods

These methods are fluent setters. They return a `Text` with the property set.

- `Text::style` sets the style of this `Text`.
- `Text::alignment` sets the alignment for this `Text`.
- `Text::left_aligned` sets the alignment to `Alignment::Left`.
- `Text::centered` sets the alignment to `Alignment::Center`.
- `Text::right_aligned` sets the alignment to `Alignment::Right`.

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

A [`Text`](#text), like a [`Line`](../ratatui_crossterm/index.md), can be constructed using one of the many `From` implementations or
via the `Text::raw` and `Text::styled` methods. Helpfully, [`Text`](#text) also implements
`core::iter::Extend` which enables the concatenation of several [`Text`](#text) blocks.

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

The text's [`Style`](../ratatui_core/style.md) is used by the rendering widget to determine how to style the text. Each
[`Line`](../ratatui_crossterm/index.md) in the text will be styled with the [`Style`](../ratatui_core/style.md) of the text, and then with its own
[`Style`](../ratatui_core/style.md). `Text` also implements [`Styled`](#styled) which means you can use the methods of the
[`Stylize`](../ratatui_core/index.md) trait.

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
The text's [`Alignment`](../ratatui_core/index.md) can be set using `Text::alignment` or the related helper methods.
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
`Text` implements the [`Widget`](../ratatui_core/index.md) trait, which means it can be rendered to a [`Buffer`](../ratatui_crossterm/index.md) or to a
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

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements [`Into<Style>`](./backend.md)).

  

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

  only by the style of each [`Line`](../ratatui_crossterm/index.md) contained in the line. For this reason, this field may

  not be supported by all widgets (outside of the `ratatui` crate itself).

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements [`Into<Style>`](./backend.md)).

  

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

  

  `Text` also implements [`Styled`](#styled) which means you can use the methods of the [`Stylize`](../ratatui_core/index.md)

  trait.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements [`Into<Style>`](./backend.md)).

  

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

- `fn alignment(self, alignment: Alignment) -> Self`

  Sets the alignment for this text.

  

  Defaults to: [`None`](#none), meaning the alignment is determined by the rendering widget.

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

- `fn iter(&self) -> core::slice::Iter<'_, Line<'a>>` — [`FromCrossterm`](./backend.md#fromcrossterm)

  Returns an iterator over the lines of the text.

- `fn iter_mut(&mut self) -> core::slice::IterMut<'_, Line<'a>>` — [`FromCrossterm`](./backend.md#fromcrossterm)

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

##### `impl Add for Text<'_>`

- `type Output = Text<'_>`

- `fn add(self, text: Self) -> <Self as >::Output`

##### `impl Add for Text<'a>`

- `type Output = Text<'a>`

- `fn add(self, line: Line<'a>) -> <Self as >::Output` — [`FromCrossterm`](./backend.md#fromcrossterm)

##### `impl AddAssign for Text<'_>`

- `fn add_assign(&mut self, rhs: Self)`

##### `impl AddAssign for Text<'a>`

- `fn add_assign(&mut self, line: Line<'a>)` — [`FromCrossterm`](./backend.md#fromcrossterm)

##### `impl Clone for Text<'a>`

- `fn clone(&self) -> Text<'a>` — [`Color`](#color)

##### `impl Debug for Text<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result` — [`Bar`](./widgets.md#bar), [`Bar`](./widgets.md#bar)

##### `impl Default for Text<'a>`

- `fn default() -> Text<'a>` — [`Color`](#color)

##### `impl Display for Text<'_>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result` — [`Bar`](./widgets.md#bar), [`Bar`](./widgets.md#bar)

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

- `fn into_iter(self) -> <Self as >::IntoIter` — [`CrosstermBackend`](./backend.md#crosstermbackend)

##### `impl PartialEq for Text<'a>`

- `fn eq(&self, other: &Text<'a>) -> bool` — [`Color`](#color)

##### `impl StructuralPartialEq for Text<'a>`

##### `impl Styled for Text<'_>`

- `type Item = Text<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Text<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl ToCompactString for Text<'a>`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>` — [`Widget`](#widget)

##### `impl ToLine for Text<'a>`

- `fn to_line(&self) -> Line<'_>` — [`FromCrossterm`](./backend.md#fromcrossterm)

##### `impl ToSpan for Text<'a>`

- `fn to_span(&self) -> Span<'_>` — [`VerticalAlignment`](#verticalalignment)

##### `impl ToString for Text<'a>`

- `fn to_string(&self) -> String`

##### `impl ToText for Text<'a>`

- `fn to_text(&self) -> Text<'_>` — [`Color`](#color)

##### `impl UnicodeWidthStr for Text<'_>`

- `fn width(&self) -> usize`

  Returns the max width of all the lines.

- `fn width_cjk(&self) -> usize`

##### `impl Widget for Text<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)` — [`run`](./index.md#run), [`IntoCrossterm`](./backend.md#intocrossterm)

## Traits

### `Size`

```rust
trait Size { ... }
```

A trait for converting a value to a [`Line`](../ratatui_crossterm/index.md).

This trait is automatically implemented for any type that implements the `Display` trait. As
such, `ToLine` shouldn't be implemented directly: `Display` should be implemented instead, and
you get the `ToLine` implementation for free.

### `style`

```rust
trait style { ... }
```

A trait for converting a value to a [`Span`](#span).

This trait is automatically implemented for any type that implements the `Display` trait. As
such, `ToSpan` shouldn't be implemented directly: `Display` should be implemented instead, and
you get the `ToSpan` implementation for free.

### `Modifier`

```rust
trait Modifier { ... }
```

A trait for converting a value to a [`Text`](#text).

This trait is automatically implemented for any type that implements the `Display` trait. As
such, `ToText` shouldn't be implemented directly: `Display` should be implemented instead, and
you get the `ToText` implementation for free.

## Functions

### `backend`

```rust
fn backend(&mut self, _n: u16) -> Result<(), <Self as >::Error>
```

Insert `n` line breaks to the terminal screen.

This method is optional and may not be implemented by all backends.

### `FromCrossterm`

```rust
const fn FromCrossterm(&self) -> &Buffer
```

Returns a reference to the internal buffer of the `TestBackend`.

### `IntoCrossterm`

```rust
const fn IntoCrossterm(&self) -> bool
```

Returns whether the cursor is visible.

### `buffer`

```rust
fn buffer(&self)
```

Asserts that the `TestBackend`'s scrollback buffer is empty.

# Panics

When the scrollback buffer is not equal, a panic occurs with a detailed error message
showing the differences between the expected and actual buffers.

### `Buffer`

```rust
fn Buffer<'line, Lines>(&self, expected: Lines)
where
    Lines: IntoIterator,
    <Lines as >::Item: Into<crate::text::Line<'line>>
```

Asserts that the `TestBackend`'s scrollback buffer is equal to the expected lines.

This is a shortcut for `assert_eq!(self.scrollback(), &Buffer::with_lines(expected))`.

# Panics

When they are not equal, a panic occurs with a detailed error message showing the
differences between the expected and actual buffers.

### `Alignment`

```rust
fn Alignment(&self) -> &T
```

### `Direction`

```rust
fn Direction(&mut self) -> &mut T
```

### `Position`

```rust
fn Position(self) -> U
```

Calls `U::from(self)`.

That is, this conversion is whatever the implementation of
<code>[From]&lt;T&gt; for U</code> chooses to do.

### `Line`

```rust
unsafe fn Line(&self, dest: *mut u8)
```

### `Span`

```rust
fn Span(&self, key: &K) -> bool
```

### `StatefulWidget`

```rust
fn StatefulWidget(&mut self, command: impl Command) -> Result<&mut T, Error>
```

Queues the given command for further execution.

Queued commands will be executed in the following cases:

* When `flush` is called manually on the given type implementing `io::Write`.
* The terminal will `flush` automatically if the buffer is full.
* Each line is flushed in case of `stdout`, because it is line buffered.

# Arguments

- [Command](./trait.Command.html)

  The command that you want to queue for later execution.

# Examples

```rust
use std::io::{self, Write};
use crossterm::{QueueableCommand, style::Print};

 fn main() -> io::Result<()> {
    let mut stdout = io::stdout();

    // `Print` will executed executed when `flush` is called.
    stdout
        .queue(Print("foo 1\n".to_string()))?
        .queue(Print("foo 2".to_string()))?;

    // some other code (no execution happening here) ...

    // when calling `flush` on `stdout`, all commands will be written to the stdout and therefore executed.
    stdout.flush()?;

    Ok(())

    // ==== Output ====
    // foo 1
    // foo 2
}
```

Have a look over at the [Command API](./index.html#command-api) for more details.

# Notes

* In the case of UNIX and Windows 10, ANSI codes are written to the given 'writer'.
* In case of Windows versions lower than 10, a direct WinAPI call will be made.
  The reason for this is that Windows versions lower than 10 do not support ANSI codes,
  and can therefore not be written to the given `writer`.
  Therefore, there is no difference between [execute](./trait.ExecutableCommand.html)
  and [queue](./trait.QueueableCommand.html) for those old Windows versions.

### `Widget`

```rust
fn Widget(&mut self, clear_type: ClearType) -> io::Result<()>
```

### `Frame`

```rust
fn Frame(&self) -> io::Result<Size>
```

## Macros

### `CrosstermBackend!`

Creates a vertical layout with specified constraints.

It accepts a series of constraints and applies them to create a vertical layout. The constraints
can include fixed sizes, minimum and maximum sizes, percentages, and ratios.

See [`constraint!`](../ratatui_crossterm/index.md)  or [`constraints!`](./backend.md) for more information.

# Examples

```rust
// Vertical layout with a fixed size and a percentage constraint
use ratatui_macros::vertical;
vertical![== 50, == 30%];
```

