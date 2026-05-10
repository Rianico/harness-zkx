*[ratatui_core](./index.md) / [buffer](#)*

---

# Module `buffer`

A module for the [`Buffer`](./index.md) and [`Cell`](./index.md) types.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Buffer`](#buffer) | struct |  |
| [`Cell`](#cell) | struct |  |
| [`BufferDiff`](#bufferdiff) | struct |  |
| [`CellDiffOption`](#celldiffoption) | enum |  |
| [`CellWidth`](#cellwidth) | trait |  |

## Structs

### `Buffer`

```rust
struct Buffer {
    pub area: crate::layout::Rect,
    pub content: alloc::vec::Vec<crate::buffer::Cell>,
}
```

A buffer that maps to the desired content of the terminal after the draw call

No widget in the library interacts directly with the terminal. Instead each of them is required
to draw their state to an intermediate buffer. It is basically a grid where each cell contains
a grapheme, a foreground color and a background color. This grid will then be used to output
the appropriate escape sequences and characters to draw the UI as the user has defined it.

# Examples:

```rust
use ratatui_core::buffer::{Buffer, Cell};
use ratatui_core::layout::{Position, Rect};
use ratatui_core::style::{Color, Style};

fn main() -> Result<(), Box<dyn std::error::Error>> {
let mut buf = Buffer::empty(Rect {
    x: 0,
    y: 0,
    width: 10,
    height: 5,
});

// indexing using Position
buf[Position { x: 0, y: 0 }].set_symbol("A");
assert_eq!(buf[Position { x: 0, y: 0 }].symbol(), "A");

// indexing using (x, y) tuple (which is converted to Position)
buf[(0, 1)].set_symbol("B");
assert_eq!(buf[(0, 1)].symbol(), "B");

// getting an Option instead of panicking if the position is outside the buffer
let cell = buf
    .cell_mut(Position { x: 0, y: 2 })
    .ok_or("cell not found")?;
cell.set_symbol("C");

let cell = buf.cell(Position { x: 0, y: 2 }).ok_or("cell not found")?;
assert_eq!(cell.symbol(), "C");

buf.set_string(
    3,
    0,
    "string",
    Style::default().fg(Color::Red).bg(Color::White),
);
let cell = &buf[(5, 0)]; // cannot move out of buf, so we borrow it
assert_eq!(cell.symbol(), "r");
assert_eq!(cell.fg, Color::Red);
assert_eq!(cell.bg, Color::White);
Ok(())
}
```

#### Fields

- **`area`**: `crate::layout::Rect`

  The area represented by this buffer

- **`content`**: `alloc::vec::Vec<crate::buffer::Cell>`

  The content of the buffer. The length of this Vec should always be equal to area.width *
  area.height

#### Implementations

- `fn empty(area: Rect) -> Self` — [`Rect`](./index.md#rect)

  Returns a Buffer with all cells set to the default one

- `fn filled(area: Rect, cell: Cell) -> Self` — [`Rect`](./index.md#rect), [`Cell`](./index.md#cell)

  Returns a Buffer with all cells initialized with the attributes of the given Cell

- `fn with_lines<'a, Iter>(lines: Iter) -> Self`

  Returns a Buffer containing the given lines

- `fn content(&self) -> &[Cell]` — [`Cell`](./index.md#cell)

  Returns the content of the buffer as a slice

- `const fn area(&self) -> &Rect` — [`Rect`](./index.md#rect)

  Returns the area covered by this buffer

- `fn get(&self, x: u16, y: u16) -> &Cell` — [`Cell`](./index.md#cell)

  Returns a reference to the [`Cell`](./index.md) at the given coordinates

  

  Callers should use [`Buffer[]`](Self::index) or `Buffer::cell` instead of this method.

  

  Note: idiomatically methods named `get` usually return `Option<&T>`, but this method panics

  instead. This is kept for backwards compatibility. See [`cell`](Self::cell) for a safe

  alternative.

  

  # Panics

  

  Panics if the index is out of bounds.

- `fn get_mut(&mut self, x: u16, y: u16) -> &mut Cell` — [`Cell`](./index.md#cell)

  Returns a mutable reference to the [`Cell`](./index.md) at the given coordinates.

  

  Callers should use [`Buffer[]`](Self::index_mut) or `Buffer::cell_mut` instead of this

  method.

  

  Note: idiomatically methods named `get_mut` usually return `Option<&mut T>`, but this method

  panics instead. This is kept for backwards compatibility. See [`cell_mut`](Self::cell_mut)

  for a safe alternative.

  

  # Panics

  

  Panics if the position is outside the `Buffer`'s area.

- `fn cell<P: Into<Position>>(&self, position: P) -> Option<&Cell>` — [`Cell`](./index.md#cell)

  Returns a reference to the [`Cell`](./index.md) at the given position or [`None`](./index.md) if the position is

  outside the `Buffer`'s area.

  

  This method accepts any value that can be converted to [`Position`](./index.md) (e.g. `(x, y)` or

  `Position::new(x, y)`).

  

  For a method that panics when the position is outside the buffer instead of returning

  `None`, use [`Buffer[]`](Self::index).

  

  # Examples

  

  ```rust

  use ratatui_core::buffer::{Buffer, Cell};

  use ratatui_core::layout::{Position, Rect};

  

  let mut buffer = Buffer::empty(Rect::new(0, 0, 10, 10));

  

  assert_eq!(buffer.cell(Position::new(0, 0)), Some(&Cell::default()));

  assert_eq!(buffer.cell(Position::new(10, 10)), None);

  assert_eq!(buffer.cell((0, 0)), Some(&Cell::default()));

  assert_eq!(buffer.cell((10, 10)), None);

  ```

- `fn cell_mut<P: Into<Position>>(&mut self, position: P) -> Option<&mut Cell>` — [`Cell`](./index.md#cell)

  Returns a mutable reference to the [`Cell`](./index.md) at the given position or [`None`](./index.md) if the

  position is outside the `Buffer`'s area.

  

  This method accepts any value that can be converted to [`Position`](./index.md) (e.g. `(x, y)` or

  `Position::new(x, y)`).

  

  For a method that panics when the position is outside the buffer instead of returning

  `None`, use [`Buffer[]`](Self::index_mut).

  

  # Examples

  

  ```rust

  use ratatui_core::buffer::{Buffer, Cell};

  use ratatui_core::layout::{Position, Rect};

  use ratatui_core::style::{Color, Style};

  let mut buffer = Buffer::empty(Rect::new(0, 0, 10, 10));

  

  if let Some(cell) = buffer.cell_mut(Position::new(0, 0)) {

      cell.set_symbol("A");

  }

  if let Some(cell) = buffer.cell_mut((0, 0)) {

      cell.set_style(Style::default().fg(Color::Red));

  }

  ```

- `fn index_of(&self, x: u16, y: u16) -> usize`

  Returns the index in the `Vec<Cell>` for the given global (x, y) coordinates.

  

  Global coordinates are offset by the Buffer's area offset (`x`/`y`).

  

  Usage discouraged, as it exposes `self.content` as a linearly indexable array, which limits

  potential future abstractions. See <https://github.com/ratatui/ratatui/issues/1122>.

  

  # Examples

  

  ```rust

  use ratatui_core::buffer::Buffer;

  use ratatui_core::layout::Rect;

  

  let buffer = Buffer::empty(Rect::new(200, 100, 10, 10));

  // Global coordinates to the top corner of this buffer's area

  assert_eq!(buffer.index_of(200, 100), 0);

  ```

  

  # Panics

  

  Panics when given an coordinate that is outside of this Buffer's area.

  

  ```should_panic

  use ratatui_core::buffer::Buffer;

  use ratatui_core::layout::Rect;

  

  let buffer = Buffer::empty(Rect::new(200, 100, 10, 10));

  // Top coordinate is outside of the buffer in global coordinate space, as the Buffer's area

  // starts at (200, 100).

  buffer.index_of(0, 0); // Panics

  ```

- `fn pos_of(&self, index: usize) -> (u16, u16)`

  Returns the (global) coordinates of a cell given its index.

  

  Global coordinates are offset by the Buffer's area offset (`x`/`y`).

  

  Usage discouraged, as it exposes `self.content` as a linearly indexable array, which limits

  potential future abstractions. See <https://github.com/ratatui/ratatui/issues/1122>.

  

  # Examples

  

  ```rust

  use ratatui_core::buffer::Buffer;

  use ratatui_core::layout::Rect;

  

  let rect = Rect::new(200, 100, 10, 10);

  let buffer = Buffer::empty(rect);

  assert_eq!(buffer.pos_of(0), (200, 100));

  assert_eq!(buffer.pos_of(14), (204, 101));

  ```

  

  # Panics

  

  Panics when given an index that is outside the Buffer's content.

  

  ```should_panic

  use ratatui_core::buffer::Buffer;

  use ratatui_core::layout::Rect;

  

  let rect = Rect::new(0, 0, 10, 10); // 100 cells in total

  let buffer = Buffer::empty(rect);

  // Index 100 is the 101th cell, which lies outside of the area of this Buffer.

  buffer.pos_of(100); // Panics

  ```

- `fn set_string<T, S>(&mut self, x: u16, y: u16, string: T, style: S)`

  Print a string, starting at the position (x, y)

- `fn set_stringn<T, S>(&mut self, x: u16, y: u16, string: T, max_width: usize, style: S) -> (u16, u16)`

  Print at most the first n characters of a string if enough space is available

  until the end of the line. Skips zero-width graphemes and control characters.

  

  Use `Buffer::set_string` when the maximum amount of characters can be printed.

- `fn set_line(&mut self, x: u16, y: u16, line: &Line<'_>, max_width: u16) -> (u16, u16)` — [`Line`](./index.md#line)

  Print a line, starting at the position (x, y)

- `fn set_span(&mut self, x: u16, y: u16, span: &Span<'_>, max_width: u16) -> (u16, u16)` — [`Span`](./index.md#span)

  Print a span, starting at the position (x, y)

- `fn set_style<S: Into<Style>>(&mut self, area: Rect, style: S)` — [`Rect`](./index.md#rect)

  Set the style of all cells in the given area.

  

  `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

- `fn resize(&mut self, area: Rect)` — [`Rect`](./index.md#rect)

  Resize the buffer so that the mapped area matches the given area and that the buffer

  length is equal to area.width * area.height

- `fn reset(&mut self)`

  Reset all cells in the buffer

- `fn merge(&mut self, other: &Self)`

  Merge an other buffer into this one

- `fn diff<'a>(&self, other: &'a Self) -> Vec<(u16, u16, &'a Cell)>` — [`Cell`](./index.md#cell)

  Collects the diff between `self` and `other` into a `Vec`.

  

  This is a convenience wrapper around [`diff_iter`](Self::diff_iter) that collects the

  results. Prefer `diff_iter` to avoid the intermediate allocation.

  

  # Panics

  

  Panics if the two buffers have different `x`, `y`, or `width` values.

- `fn diff_iter<'prev, 'next>(self: &'prev Self, other: &'next Self) -> BufferDiff<'prev, 'next>` — [`BufferDiff`](./index.md#bufferdiff)

  Builds a minimal sequence of coordinates and Cells necessary to update the UI from

  self to other.

  

  We're assuming that buffers are well-formed, that is no double-width cell is followed by

  a non-blank cell.

  

  # Multi-width characters handling:

  

  ```text

  (Index:) `01`

  Prev:    `コ`

  Next:    `aa`

  Updates: `0: a, 1: a'

  ```

  

  ```text

  (Index:) `01`

  Prev:    `a `

  Next:    `コ`

  Updates: `0: コ` (double width symbol at index 0 - skip index 1)

  ```

  

  ```text

  (Index:) `012`

  Prev:    `aaa`

  Next:    `aコ`

  Updates: `0: a, 1: コ` (double width symbol at index 1 - skip index 2)

  ```

  # Panics

  

  Panics if the two buffers have different `x`, `y`, or `width` values.

#### Trait Implementations

##### `impl Clone for Buffer`

- `fn clone(&self) -> Buffer` — [`Buffer`](./index.md#buffer)

##### `impl Debug for Buffer`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

  Writes a debug representation of the buffer to the given formatter.

  

  The format is like a pretty printed struct, with the following fields:

  * `area`: displayed as `Rect { x: 1, y: 2, width: 3, height: 4 }`

  * `content`: displayed as a list of strings representing the content of the buffer

  * `styles`: displayed as a list of: `{ x: 1, y: 2, fg: Color::Red, bg: Color::Blue,

    modifier: Modifier::BOLD }` only showing a value when there is a change in style.

##### `impl Default for Buffer`

- `fn default() -> Buffer` — [`Buffer`](./index.md#buffer)

##### `impl Eq for Buffer`

##### `impl<K> Equivalent for Buffer`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Buffer`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl<P: Into<crate::layout::Position>> Index for Buffer`

- `type Output = Cell`

- `fn index(&self, position: P) -> &<Self as >::Output`

  Returns a reference to the [`Cell`](./index.md) at the given position.

  

  This method accepts any value that can be converted to [`Position`](./index.md) (e.g. `(x, y)` or

  `Position::new(x, y)`).

  

  # Panics

  

  May panic if the given position is outside the buffer's area. For a method that returns

  `None` instead of panicking, use [`Buffer::cell`](Self::cell).

  

  # Examples

  

  ```rust

  use ratatui_core::buffer::{Buffer, Cell};

  use ratatui_core::layout::{Position, Rect};

  

  let buf = Buffer::empty(Rect::new(0, 0, 10, 10));

  let cell = &buf[(0, 0)];

  let cell = &buf[Position::new(0, 0)];

  ```

##### `impl<P: Into<crate::layout::Position>> IndexMut for Buffer`

- `fn index_mut(&mut self, position: P) -> &mut <Self as >::Output`

  Returns a mutable reference to the [`Cell`](./index.md) at the given position.

  

  This method accepts any value that can be converted to [`Position`](./index.md) (e.g. `(x, y)` or

  `Position::new(x, y)`).

  

  # Panics

  

  May panic if the given position is outside the buffer's area. For a method that returns

  `None` instead of panicking, use [`Buffer::cell_mut`](Self::cell_mut).

  

  # Examples

  

  ```rust

  use ratatui_core::buffer::{Buffer, Cell};

  use ratatui_core::layout::{Position, Rect};

  

  let mut buf = Buffer::empty(Rect::new(0, 0, 10, 10));

  buf[(0, 0)].set_symbol("A");

  buf[Position::new(0, 0)].set_symbol("B");

  ```

##### `impl IntoEither for Buffer`

##### `impl PartialEq for Buffer`

- `fn eq(&self, other: &Buffer) -> bool` — [`Buffer`](./index.md#buffer)

##### `impl StructuralPartialEq for Buffer`

### `Cell`

```rust
struct Cell {
    pub fg: crate::style::Color,
    pub bg: crate::style::Color,
    pub underline_color: crate::style::Color,
    pub modifier: crate::style::Modifier,
    pub diff_option: CellDiffOption,
    pub skip: bool,
    // [REDACTED: Private Fields]
}
```

A buffer cell

#### Fields

- **`fg`**: `crate::style::Color`

  The foreground color of the cell.

- **`bg`**: `crate::style::Color`

  The background color of the cell.

- **`underline_color`**: `crate::style::Color`

  The underline color of the cell.

- **`modifier`**: `crate::style::Modifier`

  The modifier of the cell.

- **`diff_option`**: `CellDiffOption`

  Special option applied when copying (diffing) the buffer to the screen (or another buffer).

- **`skip`**: `bool`

  Whether the cell should be skipped when copying (diffing) the buffer to the screen.
  
  Use [`CellDiffOption::Skip`](./index.md) via [`set_diff_option`](Self::set_diff_option) instead.

#### Implementations

- `const EMPTY: Self`

- `const fn new(symbol: &'static str) -> Self`

  Creates a new `Cell` with the given symbol.

  

  This works at compile time and puts the symbol onto the stack. Fails to build when the

  symbol doesn't fit onto the stack and requires to be placed on the heap. Use

  `Self::default().set_symbol()` in that case. See `CompactString::const_new` for more

  details on this.

- `fn symbol(&self) -> &str`

  Gets the symbol of the cell.

  

  If the cell has no symbol, returns a single space character.

- `fn merge_symbol(&mut self, symbol: &str, strategy: MergeStrategy) -> &mut Self` — [`MergeStrategy`](./symbols/merge.md#mergestrategy)

  Merges the symbol of the cell with the one already on the cell, using the provided

  [`MergeStrategy`](./symbols/merge.md).

  

  Merges [Box Drawing Unicode block] characters to create a single character representing

  their combination, useful for [border collapsing]. Currently limited to box drawing

  characters, with potential future support for others.

  

  Merging may not be perfect due to Unicode limitations; some symbol combinations might not

  produce a valid character. [`MergeStrategy`](./symbols/merge.md) defines how to handle such cases, e.g.,

  `Exact` for valid merges only, or `Fuzzy` for close matches.

  

  If the cell has no symbol set, it will set the symbol to the provided one rather than

  merging.

  

  # Example

  

  ```rust

  use ratatui_core::buffer::Cell;

  use ratatui_core::symbols::merge::MergeStrategy;

  

  assert_eq!(

      Cell::new("┘")

          .merge_symbol("┏", MergeStrategy::Exact)

          .symbol(),

      "╆",

  );

  

  assert_eq!(

      Cell::new("╭")

          .merge_symbol("┘", MergeStrategy::Fuzzy)

          .symbol(),

      "┼",

  );

  ```

  

- `fn set_symbol(&mut self, symbol: &str) -> &mut Self`

  Sets the symbol of the cell.

- `fn set_char(&mut self, ch: char) -> &mut Self`

  Sets the symbol of the cell to a single character.

- `const fn set_fg(&mut self, color: Color) -> &mut Self` — [`Color`](./index.md#color)

  Sets the foreground color of the cell.

- `const fn set_bg(&mut self, color: Color) -> &mut Self` — [`Color`](./index.md#color)

  Sets the background color of the cell.

- `fn set_style<S: Into<Style>>(&mut self, style: S) -> &mut Self`

  Sets the style of the cell.

  

   `style` accepts any type that is convertible to [`Style`](./style.md) (e.g. [`Style`](./style.md), [`Color`](./index.md), or

  your own type that implements `Into<Style>`).

- `const fn style(&self) -> Style` — [`Style`](./style.md#style)

  Returns the style of the cell.

- `const fn set_skip(&mut self, skip: bool) -> &mut Self`

  Sets the cell to be skipped when copying (diffing) the buffer to the screen.

  

  This is helpful when it is necessary to prevent the buffer from overwriting a cell that is

  covered by an image from some terminal graphics protocol (Sixel / iTerm / Kitty ...).

- `const fn set_diff_option(&mut self, diff_option: CellDiffOption) -> &mut Self` — [`CellDiffOption`](./index.md#celldiffoption)

  Sets cell [`CellDiffOption`](./index.md).

  

  The diff options are for dealing with cells that are wider than a unit, that should always

  be updated, or that should not be updated at all (skip output due to preceding wider

  cells).

- `fn reset(&mut self)`

  Resets the cell to the empty state.

#### Trait Implementations

##### `impl CellWidth for Cell`

- `fn cell_width(&self) -> u16`

  Returns [`CellDiffOption::ForcedWidth`](./index.md) when set, otherwise computes the width from the

  cell's symbol.

##### `impl Clone for Cell`

- `fn clone(&self) -> Cell` — [`Cell`](./index.md#cell)

##### `impl Debug for Cell`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Cell`

- `fn default() -> Cell` — [`Cell`](./index.md#cell)

##### `impl Eq for Cell`

##### `impl<K> Equivalent for Cell`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Cell`

- `fn hash<H: core::hash::Hasher>(&self, state: &mut H)`

  Hashes the cell.

  

  This treats symbols with Some(" ") as equal to None, so that empty cells are

  treated uniformly, regardless of how they were created.

##### `impl IntoEither for Cell`

##### `impl PartialEq for Cell`

- `fn eq(&self, other: &Self) -> bool`

  Compares two `Cell`s for equality.

  

  Note that cells with no symbol (i.e., `Cell::EMPTY`) are considered equal to cells with a

  single space symbol. This is to ensure that empty cells are treated uniformly,

  regardless of how they were created

### `BufferDiff<'prev, 'next>`

```rust
struct BufferDiff<'prev, 'next> {
    // [REDACTED: Private Fields]
}
```

A zero-allocation iterator over the differences between two buffers of the same width.

Yields `(x, y, &Cell)` tuples for each cell in `next` that differs from the corresponding cell
in `prev`. Handles multi-width characters (including VS16 emoji trailing cells) and
[`CellDiffOption`](./index.md) directives.

#### Trait Implementations

##### `impl Debug for BufferDiff<'prev, 'next>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl IntoEither for BufferDiff<'prev, 'next>`

##### `impl IntoIterator for BufferDiff<'prev, 'next>`

- `type Item = <I as Iterator>::Item`

- `type IntoIter = I`

- `fn into_iter(self) -> I`

##### `impl Iterator for BufferDiff<'_, 'next>`

- `type Item = (u16, u16, &'next Cell)`

- `fn next(&mut self) -> Option<<Self as >::Item>`

##### `impl Itertools for BufferDiff<'prev, 'next>`

##### `impl<FromA, FromB, FromC> MultiUnzip for BufferDiff<'prev, 'next>`

- `fn multiunzip(self) -> (FromA, FromB, FromC)`

## Enums

### `CellDiffOption`

```rust
enum CellDiffOption {
    None,
    Skip,
    AlwaysUpdate,
    ForcedWidth(core::num::NonZeroU16),
}
```

Cell diffing options

#### Variants

- **`None`**

  No special option.

- **`Skip`**

  Skip this cell when diffing.
  
  This is helpful when it is necessary to prevent the buffer from overwriting a cell that is
  covered by something from an escape sequence, such as graphics or links.

- **`AlwaysUpdate`**

  Always update this cell when diffing.
  
  This bypasses the equality check against the previous buffer. Use it when another
  renderer may draw over the same area, such as an external image pipeline, so Ratatui can
  redraw text there on the next render.

- **`ForcedWidth`**

  Force a width regardless of the symbol text width.
  
  Escape sequences will have some computed width that does match what is written to the
  screen.

#### Trait Implementations

##### `impl Clone for CellDiffOption`

- `fn clone(&self) -> CellDiffOption` — [`CellDiffOption`](./index.md#celldiffoption)

##### `impl Copy for CellDiffOption`

##### `impl Debug for CellDiffOption`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for CellDiffOption`

- `fn default() -> CellDiffOption` — [`CellDiffOption`](./index.md#celldiffoption)

##### `impl Eq for CellDiffOption`

##### `impl<K> Equivalent for CellDiffOption`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for CellDiffOption`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for CellDiffOption`

##### `impl PartialEq for CellDiffOption`

- `fn eq(&self, other: &CellDiffOption) -> bool` — [`CellDiffOption`](./index.md#celldiffoption)

##### `impl StructuralPartialEq for CellDiffOption`

## Traits

### `CellWidth`

```rust
trait CellWidth { ... }
```

Returns the display width of a value in terminal cells.

This trait provides a unified way to compute cell widths for both string content
and [`Cell`](super::Cell)s:

- **`str`**: width is derived from `UnicodeWidthStr`, with a fast path for single-byte ASCII
  characters and a terminal-compatibility adjustment for halfwidth katakana dakuten/handakuten
  (`U+FF9E`/`U+FF9F`).
- **[`Cell`](super::Cell)**: returns the
  [`CellDiffOption::ForcedWidth`](super::CellDiffOption::ForcedWidth) when set, otherwise falls
  back to the width of the cell's symbol.

#### Required Methods

- `fn cell_width(&self) -> u16`

  Returns the display width in terminal cells.

#### Implementors

- [`Cell`](./index.md#cell)
- `str`

