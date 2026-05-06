*[ratatui](../index.md) / [backend](index.md)*

---

# Module `backend`

Re-exports for the backend implementations.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`TestBackend`](#testbackend) | struct |  |
| [`WindowSize`](#windowsize) | fn |  |
| [`FromCrossterm`](#fromcrossterm) | fn |  |
| [`IntoCrossterm`](#intocrossterm) | fn |  |
| [`CrosstermBackend!`](#crosstermbackend) | macro |  |

## Structs

### `TestBackend`

```rust
struct TestBackend {
    // [REDACTED: Private Fields]
}
```

*Re-exported from `ratatui_core`*

A [`Backend`](../../ratatui_core/index.md) implementation used for integration testing that renders to an memory buffer.

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

- `const fn buffer(&self) -> &Buffer` — [`IntoCrossterm`](#intocrossterm)

  Returns a reference to the internal buffer of the `TestBackend`.

- `const fn cursor_visible(&self) -> bool`

  Returns whether the cursor is visible.

- `const fn cursor_position(&self) -> Position` — [`backend`](../prelude/index.md#backend)

  Returns the current cursor position.

- `const fn scrollback(&self) -> &Buffer` — [`IntoCrossterm`](#intocrossterm)

  Returns a reference to the internal scrollback buffer of the `TestBackend`.

  

  The scrollback buffer represents the part of the screen that is currently hidden from view,

  but that could be accessed by scrolling back in the terminal's history. This would normally

  be done using the terminal's scrollbar or an equivalent keyboard shortcut.

  

  The scrollback buffer starts out empty. Lines are appended when they scroll off the top of

  the main buffer. This happens when lines are appended to the bottom of the main buffer

  using [`Backend::append_lines`](../prelude/index.md).

  

  The scrollback buffer has a maximum height of [`u16::MAX`](../../ratatui_core/backend/index.md). If lines are appended to the

  bottom of the scrollback buffer when it is at its maximum height, a corresponding number of

  lines will be removed from the top.

- `fn resize(&mut self, width: u16, height: u16)`

  Resizes the `TestBackend` to the specified width and height.

- `fn assert_buffer(&self, expected: &Buffer)` — [`IntoCrossterm`](#intocrossterm)

  Asserts that the `TestBackend`'s buffer is equal to the expected buffer.

  

  This is a shortcut for `assert_eq!(self.buffer(), &expected)`.

  

  # Panics

  

  When they are not equal, a panic occurs with a detailed error message showing the

  differences between the expected and actual buffers.

- `fn assert_scrollback(&self, expected: &Buffer)` — [`IntoCrossterm`](#intocrossterm)

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

- `fn draw<'a, I>(&mut self, content: I) -> core::result::Result<(), core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Terminal`](../prelude/index.md#terminal)

- `fn hide_cursor(&mut self) -> core::result::Result<(), core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Terminal`](../prelude/index.md#terminal)

- `fn show_cursor(&mut self) -> core::result::Result<(), core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Terminal`](../prelude/index.md#terminal)

- `fn get_cursor_position(&mut self) -> core::result::Result<Position, core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`backend`](../prelude/index.md#backend), [`Terminal`](../prelude/index.md#terminal)

- `fn set_cursor_position<P: Into<Position>>(&mut self, position: P) -> core::result::Result<(), core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Terminal`](../prelude/index.md#terminal)

- `fn clear(&mut self) -> core::result::Result<(), core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Terminal`](../prelude/index.md#terminal)

- `fn clear_region(&mut self, clear_type: ClearType) -> core::result::Result<(), core::convert::Infallible>` — [`canvas`](../widgets/index.md#canvas), [`Widget`](../prelude/index.md#widget), [`Terminal`](../prelude/index.md#terminal)

- `fn append_lines(&mut self, line_count: u16) -> core::result::Result<(), core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Terminal`](../prelude/index.md#terminal)

  Inserts n line breaks at the current cursor position.

  

  After the insertion, the cursor x position will be incremented by 1 (unless it's already

  at the end of line). This is a common behaviour of terminals in raw mode.

  

  If the number of lines to append is fewer than the number of lines in the buffer after the

  cursor y position then the cursor is moved down by n rows.

  

  If the number of lines to append is greater than the number of lines in the buffer after

  the cursor y position then that number of empty lines (at most the buffer's height in this

  case but this limit is instead replaced with scrolling in most backend implementations) will

  be added after the current position and the cursor will be moved to the last row.

- `fn size(&self) -> core::result::Result<Size, core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Chart`](../widgets/index.md#chart), [`Terminal`](../prelude/index.md#terminal)

- `fn window_size(&mut self) -> core::result::Result<WindowSize, core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Dataset`](../widgets/index.md#dataset), [`Terminal`](../prelude/index.md#terminal)

- `fn flush(&mut self) -> core::result::Result<(), core::convert::Infallible>` — [`Widget`](../prelude/index.md#widget), [`Terminal`](../prelude/index.md#terminal)

##### `impl Clone for TestBackend`

- `fn clone(&self) -> TestBackend` — [`TestBackend`](#testbackend)

##### `impl Debug for TestBackend`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result` — [`Bar`](../widgets/index.md#bar), [`Bar`](../widgets/index.md#bar)

##### `impl Display for TestBackend`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result` — [`Bar`](../widgets/index.md#bar), [`Bar`](../widgets/index.md#bar)

  Formats the `TestBackend` for display by calling the `buffer_view` function

  on its internal buffer.

##### `impl Eq for TestBackend`

##### `impl<K> Equivalent for TestBackend`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for TestBackend`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for TestBackend`

##### `impl PartialEq for TestBackend`

- `fn eq(&self, other: &TestBackend) -> bool` — [`TestBackend`](#testbackend)

##### `impl StructuralPartialEq for TestBackend`

##### `impl ToCompactString for TestBackend`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>` — [`Widget`](../prelude/index.md#widget)

##### `impl ToLine for TestBackend`

- `fn to_line(&self) -> Line<'_>` — [`FromCrossterm`](#fromcrossterm)

##### `impl ToSpan for TestBackend`

- `fn to_span(&self) -> Span<'_>` — [`VerticalAlignment`](../prelude/index.md#verticalalignment)

##### `impl ToString for TestBackend`

- `fn to_string(&self) -> String`

##### `impl ToText for TestBackend`

- `fn to_text(&self) -> Text<'_>` — [`Color`](../prelude/index.md#color)

## Functions

### `WindowSize`

```rust
fn WindowSize<'line, Lines>(lines: Lines) -> Self
where
    Lines: IntoIterator,
    <Lines as >::Item: Into<crate::text::Line<'line>>
```

Creates a new `TestBackend` with the specified lines as the initial screen state.

The backend's screen size is determined from the initial lines.

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

## Macros

### `CrosstermBackend!`

Creates a vertical layout with specified constraints.

It accepts a series of constraints and applies them to create a vertical layout. The constraints
can include fixed sizes, minimum and maximum sizes, percentages, and ratios.

See [`constraint!`](../../ratatui_crossterm/index.md)  or [`constraints!`](#constraints) for more information.

# Examples

```rust
// Vertical layout with a fixed size and a percentage constraint
use ratatui_macros::vertical;
vertical![== 50, == 30%];
```

