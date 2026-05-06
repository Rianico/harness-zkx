*[ratatui_core](../index.md) / [backend](index.md)*

---

# Module `backend`

This module provides the backend implementations for different terminal libraries.

It defines the [`Backend`](#backend) trait which is used to abstract over the specific terminal library
being used.

Supported terminal backends:
- [Crossterm]: enable the `crossterm` feature (enabled by default) and use [`CrosstermBackend`](#crosstermbackend)
- [Termion]: enable the `termion` feature and use `TermionBackend`
- [Termwiz]: enable the `termwiz` feature and use `TermwizBackend`

Additionally, a [`TestBackend`](../index.md) is provided for testing purposes.

See the [Backend Comparison] section of the [Ratatui Website] for more details on the different
backends.

Each backend supports a number of features, such as [raw mode](#raw-mode), [alternate
screen](#alternate-screen), and [mouse capture](#mouse-capture). These features are generally
not enabled by default, and must be enabled by the application before they can be used. See the
documentation for each backend for more details.

Note: most applications should use the [`Terminal`](../terminal/index.md) struct instead of directly calling methods
on the backend.

# Example

```rust,ignore
use std::io::stdout;

use ratatui::{backend::CrosstermBackend, Terminal};

let backend = CrosstermBackend::new(stdout());
let mut terminal = Terminal::new(backend)?;
terminal.clear()?;
terminal.draw(|frame| {
    // -- snip --
})?;
std::io::Result::Ok(())
```

See the the [Examples] directory for more examples.

# Raw Mode

Raw mode is a mode where the terminal does not perform any processing or handling of the input
and output. This means that features such as echoing input characters, line buffering, and
special character processing (e.g., CTRL-C for SIGINT) are disabled. This is useful for
applications that want to have complete control over the terminal input and output, processing
each keystroke themselves.

For example, in raw mode, the terminal will not perform line buffering on the input, so the
application will receive each key press as it is typed, instead of waiting for the user to
press enter. This makes it suitable for real-time applications like text editors,
terminal-based games, and more.

Each backend handles raw mode differently, so the behavior may vary depending on the backend
being used. Be sure to consult the backend's specific documentation for exact details on how it
implements raw mode.

# Alternate Screen

The alternate screen is a separate buffer that some terminals provide, distinct from the main
screen. When activated, the terminal will display the alternate screen, hiding the current
content of the main screen. Applications can write to this screen as if it were the regular
terminal display, but when the application exits, the terminal will switch back to the main
screen, and the contents of the alternate screen will be cleared. This is useful for
applications like text editors or terminal games that want to use the full terminal window
without disrupting the command line or other terminal content.

This creates a seamless transition between the application and the regular terminal session, as
the content displayed before launching the application will reappear after the application
exits.

Note that not all terminal emulators support the alternate screen, and even those that do may
handle it differently. As a result, the behavior may vary depending on the backend being used.
Always consult the specific backend's documentation to understand how it implements the
alternate screen.

# Mouse Capture

Mouse capture is a mode where the terminal captures mouse events such as clicks, scrolls, and
movement, and sends them to the application as special sequences or events. This enables the
application to handle and respond to mouse actions, providing a more interactive and graphical
user experience within the terminal. It's particularly useful for applications like
terminal-based games, text editors, or other programs that require more direct interaction from
the user.

Each backend handles mouse capture differently, with variations in the types of events that can
be captured and how they are represented. As such, the behavior may vary depending on the
backend being used, and developers should consult the specific backend's documentation to
understand how it implements mouse capture.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`TestBackend`](#testbackend) | struct |  |
| [`WindowSize`](#windowsize) | struct | The window size in characters (columns / rows) as well as pixels. |
| [`ClearType`](#cleartype) | enum | Defines which region of the terminal's visible display area is cleared. |
| [`Backend`](#backend) | trait | The `Backend` trait provides an abstraction over different terminal libraries. |

## Structs

### `TestBackend`

```rust
struct TestBackend {
    // [REDACTED: Private Fields]
}
```

A [`Backend`](#backend) implementation used for integration testing that renders to an memory buffer.

Note: that although many of the integration and unit tests in ratatui are written using this
backend, it is preferable to write unit tests for widgets directly against the buffer rather
than using this backend. This backend is intended for integration tests that test the entire
terminal UI.

# Example

```rust,ignore
use ratatui::backend::{Backend, TestBackend};

let mut backend = TestBackend::new(10, 2);
backend.clear()?;
backend.assert_buffer_lines(["          "; 2]);
Result::Ok(())
```

#### Implementations

- `fn new(width: u16, height: u16) -> Self`

  Creates a new `TestBackend` with the specified width and height.

- `fn with_lines<'line, Lines>(lines: Lines) -> Self`

  Creates a new `TestBackend` with the specified lines as the initial screen state.

  

  The backend's screen size is determined from the initial lines.

- `const fn buffer(&self) -> &Buffer` — [`Buffer`](../index.md#buffer)

  Returns a reference to the internal buffer of the `TestBackend`.

- `const fn cursor_visible(&self) -> bool`

  Returns whether the cursor is visible.

- `const fn cursor_position(&self) -> Position` — [`Position`](../index.md#position)

  Returns the current cursor position.

- `const fn scrollback(&self) -> &Buffer` — [`Buffer`](../index.md#buffer)

  Returns a reference to the internal scrollback buffer of the `TestBackend`.

  

  The scrollback buffer represents the part of the screen that is currently hidden from view,

  but that could be accessed by scrolling back in the terminal's history. This would normally

  be done using the terminal's scrollbar or an equivalent keyboard shortcut.

  

  The scrollback buffer starts out empty. Lines are appended when they scroll off the top of

  the main buffer. This happens when lines are appended to the bottom of the main buffer

  using `Backend::append_lines`.

  

  The scrollback buffer has a maximum height of `u16::MAX`. If lines are appended to the

  bottom of the scrollback buffer when it is at its maximum height, a corresponding number of

  lines will be removed from the top.

- `fn resize(&mut self, width: u16, height: u16)`

  Resizes the `TestBackend` to the specified width and height.

- `fn assert_buffer(&self, expected: &Buffer)` — [`Buffer`](../index.md#buffer)

  Asserts that the `TestBackend`'s buffer is equal to the expected buffer.

  

  This is a shortcut for `assert_eq!(self.buffer(), &expected)`.

  

  # Panics

  

  When they are not equal, a panic occurs with a detailed error message showing the

  differences between the expected and actual buffers.

- `fn assert_scrollback(&self, expected: &Buffer)` — [`Buffer`](../index.md#buffer)

  Asserts that the `TestBackend`'s scrollback buffer is equal to the expected buffer.

  

  This is a shortcut for `assert_eq!(self.scrollback(), &expected)`.

  

  # Panics

  

  When they are not equal, a panic occurs with a detailed error message showing the

  differences between the expected and actual buffers.

- `fn assert_scrollback_empty(&self)`

  Asserts that the `TestBackend`'s scrollback buffer is empty.

  

  # Panics

  

  When the scrollback buffer is not equal, a panic occurs with a detailed error message

  showing the differences between the expected and actual buffers.

- `fn assert_buffer_lines<'line, Lines>(&self, expected: Lines)`

  Asserts that the `TestBackend`'s buffer is equal to the expected lines.

  

  This is a shortcut for `assert_eq!(self.buffer(), &Buffer::with_lines(expected))`.

  

  # Panics

  

  When they are not equal, a panic occurs with a detailed error message showing the

  differences between the expected and actual buffers.

- `fn assert_scrollback_lines<'line, Lines>(&self, expected: Lines)`

  Asserts that the `TestBackend`'s scrollback buffer is equal to the expected lines.

  

  This is a shortcut for `assert_eq!(self.scrollback(), &Buffer::with_lines(expected))`.

  

  # Panics

  

  When they are not equal, a panic occurs with a detailed error message showing the

  differences between the expected and actual buffers.

- `fn assert_cursor_position<P: Into<Position>>(&mut self, position: P)`

  Asserts that the `TestBackend`'s cursor position is equal to the expected one.

  

  This is a shortcut for `assert_eq!(self.get_cursor_position().unwrap(), expected)`.

  

  # Panics

  

  When they are not equal, a panic occurs with a detailed error message showing the

  differences between the expected and actual position.

#### Trait Implementations

##### `impl Backend for TestBackend`

- `type Error = Infallible`

- `fn draw<'a, I>(&mut self, content: I) -> core::result::Result<(), core::convert::Infallible>`

- `fn hide_cursor(&mut self) -> core::result::Result<(), core::convert::Infallible>`

- `fn show_cursor(&mut self) -> core::result::Result<(), core::convert::Infallible>`

- `fn get_cursor_position(&mut self) -> core::result::Result<Position, core::convert::Infallible>` — [`Position`](../index.md#position)

- `fn set_cursor_position<P: Into<Position>>(&mut self, position: P) -> core::result::Result<(), core::convert::Infallible>`

- `fn clear(&mut self) -> core::result::Result<(), core::convert::Infallible>`

- `fn clear_region(&mut self, clear_type: ClearType) -> core::result::Result<(), core::convert::Infallible>` — [`ClearType`](#cleartype)

- `fn append_lines(&mut self, line_count: u16) -> core::result::Result<(), core::convert::Infallible>`

  Inserts n line breaks at the current cursor position.

  

  After the insertion, the cursor x position will be incremented by 1 (unless it's already

  at the end of line). This is a common behaviour of terminals in raw mode.

  

  If the number of lines to append is fewer than the number of lines in the buffer after the

  cursor y position then the cursor is moved down by n rows.

  

  If the number of lines to append is greater than the number of lines in the buffer after

  the cursor y position then that number of empty lines (at most the buffer's height in this

  case but this limit is instead replaced with scrolling in most backend implementations) will

  be added after the current position and the cursor will be moved to the last row.

- `fn size(&self) -> core::result::Result<Size, core::convert::Infallible>` — [`Size`](../index.md#size)

- `fn window_size(&mut self) -> core::result::Result<WindowSize, core::convert::Infallible>` — [`WindowSize`](#windowsize)

- `fn flush(&mut self) -> core::result::Result<(), core::convert::Infallible>`

##### `impl Clone for TestBackend`

- `fn clone(&self) -> TestBackend` — [`TestBackend`](../index.md#testbackend)

##### `impl Debug for TestBackend`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Display for TestBackend`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

  Formats the `TestBackend` for display by calling the `buffer_view` function

  on its internal buffer.

##### `impl Eq for TestBackend`

##### `impl<K> Equivalent for TestBackend`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for TestBackend`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for TestBackend`

##### `impl PartialEq for TestBackend`

- `fn eq(&self, other: &TestBackend) -> bool` — [`TestBackend`](../index.md#testbackend)

##### `impl StructuralPartialEq for TestBackend`

##### `impl ToCompactString for TestBackend`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for TestBackend`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for TestBackend`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for TestBackend`

- `fn to_string(&self) -> String`

##### `impl ToText for TestBackend`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `WindowSize`

```rust
struct WindowSize {
    pub columns_rows: crate::layout::Size,
    pub pixels: crate::layout::Size,
}
```

The window size in characters (columns / rows) as well as pixels.

#### Fields

- **`columns_rows`**: `crate::layout::Size`

  Size of the window in characters (columns / rows).

- **`pixels`**: `crate::layout::Size`

  Size of the window in pixels.
  
  The `pixels` fields may not be implemented by all terminals and return `0,0`. See
  <https://man7.org/linux/man-pages/man4/tty_ioctl.4.html> under section "Get and set window
  size" / TIOCGWINSZ where the fields are commented as "unused".

#### Trait Implementations

##### `impl Clone for WindowSize`

- `fn clone(&self) -> WindowSize` — [`WindowSize`](#windowsize)

##### `impl Copy for WindowSize`

##### `impl Debug for WindowSize`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for WindowSize`

##### `impl<K> Equivalent for WindowSize`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for WindowSize`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for WindowSize`

##### `impl PartialEq for WindowSize`

- `fn eq(&self, other: &WindowSize) -> bool` — [`WindowSize`](#windowsize)

##### `impl StructuralPartialEq for WindowSize`

## Enums

### `ClearType`

```rust
enum ClearType {
    All,
    AfterCursor,
    BeforeCursor,
    CurrentLine,
    UntilNewLine,
}
```

Defines which region of the terminal's visible display area is cleared.

Clearing operates on character cells in the active display surface. It does not move, hide, or
reset the cursor position. If the cursor lies inside the cleared region, the character cell at
the cursor position is cleared as well.

Clearing applies to the terminal's visible display area, not just content previously drawn by
Ratatui. No guarantees are made about scrollback, history, or off-screen buffers.

#### Variants

- **`All`**

  Clears all character cells in the visible display area.

- **`AfterCursor`**

  Clears all character cells from the cursor position (inclusive) through the end of the
  display area.

- **`BeforeCursor`**

  Clears all character cells from the start of the display area through the cursor position
  (inclusive).

- **`CurrentLine`**

  Clears all character cells in the cursor's current line.

- **`UntilNewLine`**

  Clears all character cells from the cursor position (inclusive) to the end of the current
  line.

#### Trait Implementations

##### `impl Clone for ClearType`

- `fn clone(&self) -> ClearType` — [`ClearType`](#cleartype)

##### `impl Copy for ClearType`

##### `impl Debug for ClearType`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Display for ClearType`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for ClearType`

##### `impl<K> Equivalent for ClearType`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for ClearType`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<ClearType, <Self as ::core::str::FromStr>::Err>` — [`ClearType`](#cleartype)

##### `impl Hash for ClearType`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ClearType`

##### `impl PartialEq for ClearType`

- `fn eq(&self, other: &ClearType) -> bool` — [`ClearType`](#cleartype)

##### `impl StructuralPartialEq for ClearType`

##### `impl ToCompactString for ClearType`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for ClearType`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for ClearType`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for ClearType`

- `fn to_string(&self) -> String`

##### `impl ToText for ClearType`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

## Traits

### `Backend`

```rust
trait Backend { ... }
```

The `Backend` trait provides an abstraction over different terminal libraries. It defines the
methods required to draw content, manipulate the cursor, and clear the terminal screen.

Most applications should not need to interact with the `Backend` trait directly as the
[`Terminal`](../terminal/index.md) struct provides a higher level interface for interacting with the terminal.

#### Associated Types

- `type Error: 1`

#### Required Methods

- `fn draw<'a, I>(&mut self, content: I) -> Result<(), <Self as >::Error>`

  Draw the given content to the terminal screen.

- `fn hide_cursor(&mut self) -> Result<(), <Self as >::Error>`

  Hide the cursor on the terminal screen.

- `fn show_cursor(&mut self) -> Result<(), <Self as >::Error>`

  Show the cursor on the terminal screen.

- `fn get_cursor_position(&mut self) -> Result<Position, <Self as >::Error>`

  Get the current cursor position on the terminal screen.

- `fn set_cursor_position<P: Into<Position>>(&mut self, position: P) -> Result<(), <Self as >::Error>`

  Set the cursor position on the terminal screen to the given x and y coordinates.

- `fn clear(&mut self) -> Result<(), <Self as >::Error>`

  Clears all character cells in the terminal's visible display area.

- `fn clear_region(&mut self, clear_type: ClearType) -> Result<(), <Self as >::Error>`

  Clears a specific region of the terminal's visible display area, as defined by

- `fn size(&self) -> Result<Size, <Self as >::Error>`

  Get the size of the terminal screen in columns/rows as a [`Size`](../index.md).

- `fn window_size(&mut self) -> Result<WindowSize, <Self as >::Error>`

  Get the size of the terminal screen in columns/rows and pixels as a [`WindowSize`](#windowsize).

- `fn flush(&mut self) -> Result<(), <Self as >::Error>`

  Flush any backend-buffered output to the terminal screen.

#### Provided Methods

- `fn append_lines(&mut self, _n: u16) -> Result<(), <Self as >::Error>`

  Insert `n` line breaks to the terminal screen.

- `fn get_cursor(&mut self) -> Result<(u16, u16), <Self as >::Error>`

  Get the current cursor position on the terminal screen.

- `fn set_cursor(&mut self, x: u16, y: u16) -> Result<(), <Self as >::Error>`

  Set the cursor position on the terminal screen to the given x and y coordinates.

#### Implementors

- [`TestBackend`](../index.md#testbackend)

