*[ratatui_widgets](./index.md) / [paragraph](#)*

---

# Module `paragraph`

The [`Paragraph`](#paragraph) widget and related types allows displaying a block of text with optional
wrapping, alignment, and block styling.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Paragraph`](#paragraph) | struct | A widget to display some text. |
| [`Wrap`](#wrap) | struct | Describes how to wrap text across lines. |

## Structs

### `Paragraph<'a>`

```rust
struct Paragraph<'a> {
    // [REDACTED: Private Fields]
}
```

A widget to display some text.

It is used to display a block of text. The text can be styled and aligned. It can also be
wrapped to the next line if it is too long to fit in the given area.

The text can be any type that can be converted into a [`Text`](../ratatui_core/index.md). By default, the text is styled
with `Style::default()`, not wrapped, and aligned to the left.

The text can be wrapped to the next line if it is too long to fit in the given area. The
wrapping can be configured with the `wrap` method. For more complex wrapping, consider using
the [Textwrap crate].

The text can be aligned to the left, right, or center. The alignment can be configured with the
`alignment` method or with the `left_aligned`, `right_aligned`, and `centered` methods.

The text can be scrolled to show a specific part of the text. The scroll offset can be set with
the `scroll` method.

The text can be surrounded by a [`Block`](./block.md) with a title and borders. The block can be configured
with the [`block`](./block.md) method.

The style of the text can be set with the `style` method. This style will be applied to the
entire widget, including the block if one is present. Any style set on the block or text will be
added to this style. See the `Style` type for more information on how styles are combined.

Note: If neither wrapping or a block is needed, consider rendering the [`Text`](../ratatui_core/index.md), [`Line`](../ratatui_core/index.md), or
`Span` widgets directly.

# Example

```rust
use ratatui::layout::Alignment;
use ratatui::style::{Style, Stylize};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Wrap};

let text = vec![
    Line::from(vec![
        Span::raw("First"),
        Span::styled("line", Style::new().green().italic()),
        ".".into(),
    ]),
    Line::from("Second line".red()),
    "Third line".into(),
];
Paragraph::new(text)
    .block(Block::bordered().title("Paragraph"))
    .style(Style::new().white().on_black())
    .alignment(Alignment::Center)
    .wrap(Wrap { trim: true });
```

#### Implementations

- `fn new<T>(text: T) -> Self`

  Creates a new [`Paragraph`](#paragraph) widget with the given text.

  

  The `text` parameter can be a [`Text`](../ratatui_core/index.md) or any type that can be converted into a [`Text`](../ratatui_core/index.md). By

  default, the text is styled with `Style::default()`, not wrapped, and aligned to the left.

  

  # Examples

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::text::{Line, Text};

  use ratatui::widgets::Paragraph;

  

  let paragraph = Paragraph::new("Hello, world!");

  let paragraph = Paragraph::new(String::from("Hello, world!"));

  let paragraph = Paragraph::new(Text::raw("Hello, world!"));

  let paragraph = Paragraph::new(Text::styled("Hello, world!", Style::default()));

  let paragraph = Paragraph::new(Line::from(vec!["Hello, ".into(), "world!".red()]));

  ```

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](./block.md#block)

  Surrounds the [`Paragraph`](#paragraph) widget with a [`Block`](./block.md).

  

  # Example

  

  ```rust

  use ratatui::widgets::{Block, Paragraph};

  

  let paragraph = Paragraph::new("Hello, world!").block(Block::bordered().title("Paragraph"));

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of the entire widget.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This applies to the entire widget, including the block if one is present. Any style set on

  the block or text will be added to this style.

  

  # Example

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::Paragraph;

  

  let paragraph = Paragraph::new("Hello, world!").style(Style::new().red().on_white());

  ```

- `const fn wrap(self, wrap: Wrap) -> Self` — [`Wrap`](#wrap)

  Sets the wrapping configuration for the widget.

  

  See [`Wrap`](#wrap) for more information on the different options.

  

  # Example

  

  ```rust

  use ratatui::widgets::{Paragraph, Wrap};

  

  let paragraph = Paragraph::new("Hello, world!").wrap(Wrap { trim: true });

  ```

- `const fn scroll(self, offset: (u16, u16)) -> Self`

  Set the scroll offset for the given paragraph

  

  The scroll offset is a tuple of (y, x) offset. The y offset is the number of lines to

  scroll, and the x offset is the number of characters to scroll. The scroll offset is applied

  after the text is wrapped and aligned.

  

  Note: the order of the tuple is (y, x) instead of (x, y), which is different from general

  convention across the crate.

  

  For more information about future scrolling design and concerns, see [RFC: Design of

  Scrollable Widgets](https://github.com/ratatui/ratatui/discussions/1924) on GitHub.

- `const fn alignment(self, alignment: Alignment) -> Self`

  Set the text alignment for the given paragraph

  

  The alignment is a variant of the [`Alignment`](../ratatui_core/index.md) enum which can be one of Left, Right, or

  Center. If no alignment is specified, the text in a paragraph will be left-aligned.

  

  # Example

  

  ```rust

  use ratatui::layout::Alignment;

  use ratatui::widgets::Paragraph;

  

  let paragraph = Paragraph::new("Hello World").alignment(Alignment::Center);

  ```

- `const fn left_aligned(self) -> Self`

  Left-aligns the text in the given paragraph.

  

  Convenience shortcut for `Paragraph::alignment(Alignment::Left)`.

  

  # Examples

  

  ```rust

  use ratatui::widgets::Paragraph;

  

  let paragraph = Paragraph::new("Hello World").left_aligned();

  ```

- `const fn centered(self) -> Self`

  Center-aligns the text in the given paragraph.

  

  Convenience shortcut for `Paragraph::alignment(Alignment::Center)`.

  

  # Examples

  

  ```rust

  use ratatui::widgets::Paragraph;

  

  let paragraph = Paragraph::new("Hello World").centered();

  ```

- `const fn right_aligned(self) -> Self`

  Right-aligns the text in the given paragraph.

  

  Convenience shortcut for `Paragraph::alignment(Alignment::Right)`.

  

  # Examples

  

  ```rust

  use ratatui::widgets::Paragraph;

  

  let paragraph = Paragraph::new("Hello World").right_aligned();

  ```

- `fn line_count(&self, width: u16) -> usize`

   Calculates the number of lines needed to fully render.

  

   Given a max line width, this method calculates the number of lines that a paragraph will

   need in order to be fully rendered. For paragraphs that do not use wrapping, this count is

   simply the number of lines present in the paragraph.

  

   This method will also account for the [`Block`](./block.md) if one is set through `Self::block`.

  

   Note: The design for text wrapping is not stable and might affect this API.

  

   # Example

  

   ```ignore

   use ratatui::{widgets::{Paragraph, Wrap}};

  

   let paragraph = Paragraph::new("Hello World")

       .wrap(Wrap { trim: false });

   assert_eq!(paragraph.line_count(20), 1);

   assert_eq!(paragraph.line_count(10), 2);

   ```

  # Stability

  

  **This API is marked as unstable** and is only available when the `unstable-rendered-line-info`

  crate feature is enabled. This comes with no stability guarantees, and could be changed

  or removed at any time.

  The tracking issue is: `https://github.com/ratatui/ratatui/issues/293`.

- `fn line_width(&self) -> usize`

   Calculates the shortest line width needed to avoid any word being wrapped or truncated.

  

   Accounts for the [`Block`](./block.md) if a block is set through `Self::block`.

  

   Note: The design for text wrapping is not stable and might affect this API.

  

   # Example

  

   ```ignore

   use ratatui::{widgets::Paragraph};

  

   let paragraph = Paragraph::new("Hello World");

   assert_eq!(paragraph.line_width(), 11);

  

   let paragraph = Paragraph::new("Hello World\nhi\nHello World!!!");

   assert_eq!(paragraph.line_width(), 14);

   ```

  # Stability

  

  **This API is marked as unstable** and is only available when the `unstable-rendered-line-info`

  crate feature is enabled. This comes with no stability guarantees, and could be changed

  or removed at any time.

  The tracking issue is: `https://github.com/ratatui/ratatui/issues/293`.

#### Trait Implementations

##### `impl AsRef for crate::paragraph::Paragraph<'a>`

- `fn as_ref(&self) -> &crate::paragraph::Paragraph<'a>` — [`Paragraph`](#paragraph)

##### `impl Clone for Paragraph<'a>`

- `fn clone(&self) -> Paragraph<'a>` — [`Paragraph`](#paragraph)

##### `impl Debug for Paragraph<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Paragraph<'a>`

- `fn default() -> Paragraph<'a>` — [`Paragraph`](#paragraph)

##### `impl Eq for Paragraph<'a>`

##### `impl<K> Equivalent for Paragraph<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Paragraph<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Paragraph<'a>`

##### `impl PartialEq for Paragraph<'a>`

- `fn eq(&self, other: &Paragraph<'a>) -> bool` — [`Paragraph`](#paragraph)

##### `impl StructuralPartialEq for Paragraph<'a>`

##### `impl Styled for Paragraph<'_>`

- `type Item = Paragraph<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Paragraph<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for Paragraph<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

### `Wrap`

```rust
struct Wrap {
    pub trim: bool,
}
```

Describes how to wrap text across lines.

## Examples

```rust
use ratatui::text::Text;
use ratatui::widgets::{Paragraph, Wrap};

let bullet_points = Text::from(
    r#"Some indented points:
    - First thing goes here and is long so that it wraps
    - Here is another point that is long enough to wrap"#,
);

// With leading spaces trimmed (window width of 30 chars):
Paragraph::new(bullet_points.clone()).wrap(Wrap { trim: true });
// Some indented points:
// - First thing goes here and is
// long so that it wraps
// - Here is another point that
// is long enough to wrap

// But without trimming, indentation is preserved:
Paragraph::new(bullet_points).wrap(Wrap { trim: false });
// Some indented points:
//     - First thing goes here
// and is long so that it wraps
//     - Here is another point
// that is long enough to wrap
```

#### Fields

- **`trim`**: `bool`

  Should leading whitespace be trimmed

#### Trait Implementations

##### `impl Clone for Wrap`

- `fn clone(&self) -> Wrap` — [`Wrap`](#wrap)

##### `impl Copy for Wrap`

##### `impl Debug for Wrap`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Wrap`

- `fn default() -> Wrap` — [`Wrap`](#wrap)

##### `impl Eq for Wrap`

##### `impl<K> Equivalent for Wrap`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Wrap`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Wrap`

##### `impl PartialEq for Wrap`

- `fn eq(&self, other: &Wrap) -> bool` — [`Wrap`](#wrap)

##### `impl StructuralPartialEq for Wrap`

