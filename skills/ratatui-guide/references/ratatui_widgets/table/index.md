*[ratatui_widgets](../index.md) / [table](index.md)*

---

# Module `table`

The [`Table`](#table) widget is used to display multiple rows and columns in a grid and allows selecting
one or multiple cells.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Cell`](#cell) | struct |  |
| [`Row`](#row) | struct |  |
| [`TableState`](#tablestate) | struct |  |
| [`Table`](#table) | struct | A widget to display data in formatted columns. |
| [`HighlightSpacing`](#highlightspacing) | enum |  |

## Structs

### `Cell<'a>`

```rust
struct Cell<'a> {
    // [REDACTED: Private Fields]
}
```

A [`Cell`](../index.md) contains the [`Text`](../../ratatui_core/index.md) to be displayed in a [`Row`](../index.md) of a [`Table`](#table).

You can apply a [`Style`](../../ratatui_core/style/index.md) to the [`Cell`](../index.md) using `Cell::style`. This will set the style for the
entire area of the cell. Any [`Style`](../../ratatui_core/style/index.md) set on the [`Text`](../../ratatui_core/index.md) content will be combined with the
[`Style`](../../ratatui_core/style/index.md) of the [`Cell`](../index.md) by adding the [`Style`](../../ratatui_core/style/index.md) of the [`Text`](../../ratatui_core/index.md) content to the [`Style`](../../ratatui_core/style/index.md) of
the [`Cell`](../index.md). Styles set on the text content will only affect the content.

You can use `Text::alignment` when creating a cell to align its content.

# Examples

You can create a `Cell` from anything that can be converted to a [`Text`](../../ratatui_core/index.md).

```rust
use std::borrow::Cow;

use ratatui::style::Stylize;
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::Cell;

Cell::from("simple string");
Cell::from(Span::from("span"));
Cell::from(Line::from(vec![
    Span::from("a vec of "),
    Span::from("spans").bold(),
]));
Cell::from(Text::from("a text"));
Cell::from(Text::from(Cow::Borrowed("hello")));
```

`Cell` implements [`Styled`](../../ratatui_core/index.md) which means you can use style shorthands from the `Stylize` trait
to set the style of the cell concisely.

```rust
use ratatui::style::Stylize;
use ratatui::widgets::Cell;

Cell::new("Cell 1").red().italic();
```

#### Implementations

- `fn new<T>(content: T) -> Self`

  Creates a new [`Cell`](../index.md)

  

  The `content` parameter accepts any value that can be converted into a [`Text`](../../ratatui_core/index.md).

  

  # Examples

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::text::{Line, Span, Text};

  use ratatui::widgets::Cell;

  

  Cell::new("simple string");

  Cell::new(Span::from("span"));

  Cell::new(Line::from(vec![

      Span::raw("a vec of "),

      Span::from("spans").bold(),

  ]));

  Cell::new(Text::from("a text"));

  ```

- `fn content<T>(self, content: T) -> Self`

  Set the content of the [`Cell`](../index.md)

  

  The `content` parameter accepts any value that can be converted into a [`Text`](../../ratatui_core/index.md).

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::text::{Line, Span, Text};

  use ratatui::widgets::Cell;

  

  Cell::default().content("simple string");

  Cell::default().content(Span::from("span"));

  Cell::default().content(Line::from(vec![

      Span::raw("a vec of "),

      Span::from("spans").bold(),

  ]));

  Cell::default().content(Text::from("a text"));

  ```

- `const fn column_span(self, column_span: u16) -> Self`

  Set the `column_span` of this cell

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  ```rust

  use ratatui::widgets::{Cell, Row};

  let rows = vec![

      Row::new(vec![Cell::new("12345").column_span(2)]),

      Row::new(vec![Cell::new("xx"), Cell::new("yy")]),

  ];

  // "12345",

  // "xx yy",

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Set the `Style` of this cell

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This `Style` will override the `Style` of the [`Row`](../index.md) and can be overridden by the `Style`

  of the [`Text`](../../ratatui_core/index.md) content.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::Cell;

  

  Cell::new("Cell 1").style(Style::new().red().italic());

  ```

  

  `Cell` also implements the [`Styled`](../../ratatui_core/index.md) trait, which means you can use style shorthands from

  the `Stylize` trait to set the style of the widget more concisely.

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::Cell;

  

  Cell::new("Cell 1").red().italic();

  ```

  

  

#### Trait Implementations

##### `impl Clone for Cell<'a>`

- `fn clone(&self) -> Cell<'a>` — [`Cell`](../index.md#cell)

##### `impl Debug for Cell<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Cell<'a>`

- `fn default() -> Cell<'a>` — [`Cell`](../index.md#cell)

##### `impl Eq for Cell<'a>`

##### `impl<K> Equivalent for Cell<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Cell<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Cell<'a>`

##### `impl PartialEq for Cell<'a>`

- `fn eq(&self, other: &Cell<'a>) -> bool` — [`Cell`](../index.md#cell)

##### `impl StructuralPartialEq for Cell<'a>`

##### `impl Styled for Cell<'_>`

- `type Item = Cell<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Cell<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

### `Row<'a>`

```rust
struct Row<'a> {
    // [REDACTED: Private Fields]
}
```

A single row of data to be displayed in a [`Table`](#table) widget.

A `Row` is a collection of [`Cell`](../index.md)s.

By default, a row has a height of 1 but you can change this using `Row::height`.

You can set the style of the entire row using `Row::style`. This [`Style`](../../ratatui_core/style/index.md) will be combined
with the [`Style`](../../ratatui_core/style/index.md) of each individual [`Cell`](../index.md) by adding the [`Style`](../../ratatui_core/style/index.md) of the [`Cell`](../index.md) to the
[`Style`](../../ratatui_core/style/index.md) of the [`Row`](../index.md).

# Examples

You can create `Row`s from simple strings.

```rust
use ratatui::widgets::Row;

Row::new(vec!["Cell1", "Cell2", "Cell3"]);
```

If you need a bit more control over individual cells, you can explicitly create [`Cell`](../index.md)s:

```rust
use ratatui::style::Stylize;
use ratatui::widgets::{Cell, Row};

Row::new(vec![
    Cell::from("Cell1"),
    Cell::from("Cell2").red().italic(),
]);
```

You can also construct a row from any type that can be converted into `Text`:

```rust
use std::borrow::Cow;

use ratatui::widgets::{Cell, Row};

Row::new(vec![
    Cow::Borrowed("hello"),
    Cow::Owned("world".to_uppercase()),
]);
```

An iterator whose item type is convertible into `Text` can be collected into a row.

```rust
use ratatui::widgets::Row;

(0..10).map(|i| format!("{i}")).collect::<Row>();
```

`Row` implements [`Styled`](../../ratatui_core/index.md) which means you can use style shorthands from the `Stylize` trait
to set the style of the row concisely.

```rust
use ratatui::style::Stylize;
use ratatui::widgets::Row;

let cells = vec!["Cell1", "Cell2", "Cell3"];
Row::new(cells).red().italic();
```

#### Implementations

- `fn new<T>(cells: T) -> Self`

  Creates a new [`Row`](../index.md)

  

  The `cells` parameter accepts any value that can be converted into an iterator of anything

  that can be converted into a [`Cell`](../index.md) (e.g. `Vec<&str>`, `&[Cell<'a>]`, `Vec<String>`, etc.)

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Cell, Row};

  

  let row = Row::new(vec!["Cell 1", "Cell 2", "Cell 3"]);

  let row = Row::new(vec![

      Cell::new("Cell 1"),

      Cell::new("Cell 2"),

      Cell::new("Cell 3"),

  ]);

  ```

- `fn cells<T>(self, cells: T) -> Self`

  Set the cells of the [`Row`](../index.md)

  

  The `cells` parameter accepts any value that can be converted into an iterator of anything

  that can be converted into a [`Cell`](../index.md) (e.g. `Vec<&str>`, `&[Cell<'a>]`, `Vec<String>`, etc.)

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Cell, Row};

  

  let row = Row::default().cells(vec!["Cell 1", "Cell 2", "Cell 3"]);

  let row = Row::default().cells(vec![

      Cell::new("Cell 1"),

      Cell::new("Cell 2"),

      Cell::new("Cell 3"),

  ]);

  ```

- `const fn height(self, height: u16) -> Self`

  Set the fixed height of the [`Row`](../index.md)

  

  Any [`Cell`](../index.md) whose content has more lines than this height will see its content truncated.

  

  By default, the height is `1`.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::Row;

  

  let cells = vec!["Cell 1\nline 2", "Cell 2", "Cell 3"];

  let row = Row::new(cells).height(2);

  ```

- `const fn top_margin(self, margin: u16) -> Self`

  Set the top margin. By default, the top margin is `0`.

  

  The top margin is the number of blank lines to be displayed before the row.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::Row;

  let cells = vec!["Cell 1", "Cell 2", "Cell 3"];

  

  let row = Row::default().top_margin(1);

  ```

- `const fn bottom_margin(self, margin: u16) -> Self`

  Set the bottom margin. By default, the bottom margin is `0`.

  

  The bottom margin is the number of blank lines to be displayed after the row.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::Row;

  

  let cells = vec!["Cell 1", "Cell 2", "Cell 3"];

  let row = Row::default().bottom_margin(1);

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Set the [`Style`](../../ratatui_core/style/index.md) of the entire row

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This [`Style`](../../ratatui_core/style/index.md) can be overridden by the [`Style`](../../ratatui_core/style/index.md) of a any individual [`Cell`](../index.md) or by their

  `Text` content.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::Row;

  let cells = vec!["Cell 1", "Cell 2", "Cell 3"];

  let row = Row::new(cells).style(Style::new().red().italic());

  ```

  

  `Row` also implements the [`Styled`](../../ratatui_core/index.md) trait, which means you can use style shorthands from

  the `Stylize` trait to set the style of the widget more concisely.

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::Row;

  

  let cells = vec!["Cell 1", "Cell 2", "Cell 3"];

  let row = Row::new(cells).red().italic();

  ```

  

  

#### Trait Implementations

##### `impl Clone for Row<'a>`

- `fn clone(&self) -> Row<'a>` — [`Row`](../index.md#row)

##### `impl Debug for Row<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Row<'a>`

- `fn default() -> Row<'a>` — [`Row`](../index.md#row)

##### `impl Eq for Row<'a>`

##### `impl<K> Equivalent for Row<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl<Item> FromIterator for Row<'a>`

- `fn from_iter<IterCells: IntoIterator<Item = Item>>(cells: IterCells) -> Self`

##### `impl Hash for Row<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Row<'a>`

##### `impl PartialEq for Row<'a>`

- `fn eq(&self, other: &Row<'a>) -> bool` — [`Row`](../index.md#row)

##### `impl StructuralPartialEq for Row<'a>`

##### `impl Styled for Row<'_>`

- `type Item = Row<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Row<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

### `TableState`

```rust
struct TableState {
    // [REDACTED: Private Fields]
}
```

State of a [`Table`](#table) widget

This state can be used to scroll through the rows and select one of them. When the table is
rendered as a stateful widget, the selected row, column and cell will be highlighted and the
table will be shifted to ensure that the selected row is visible. This will modify the
[`TableState`](../index.md) object passed to the `Frame::render_stateful_widget` method.

The state consists of two fields:
- `offset`: the index of the first row to be displayed
- `selected`: the index of the selected row, which can be `None` if no row is selected
- `selected_column`: the index of the selected column, which can be `None` if no column is
  selected

See the `table` example and the `recipe` and `traceroute` tabs in the demo2 example in the
[Examples] directory for a more in depth example of the various configuration options and for
how to handle state.

# Example

```rust
use ratatui::Frame;
use ratatui::layout::{Constraint, Rect};
use ratatui::widgets::{Row, Table, TableState};

fn ui(frame: &mut Frame) {
let area = Rect::default();
let rows = [Row::new(vec!["Cell1", "Cell2"])];
let widths = [Constraint::Length(5), Constraint::Length(5)];
let table = Table::new(rows, widths).widths(widths);

// Note: TableState should be stored in your application state (not constructed in your render
// method) so that the selected row is preserved across renders
let mut table_state = TableState::default();
*table_state.offset_mut() = 1; // display the second row and onwards
table_state.select(Some(3)); // select the forth row (0-indexed)
table_state.select_column(Some(2)); // select the third column (0-indexed)

frame.render_stateful_widget(table, area, &mut table_state);
}
```

Note that if `Table::widths` is not called before rendering, the rendered columns will have
equal width.

#### Implementations

- `const fn new() -> Self`

  Creates a new [`TableState`](../index.md)

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let state = TableState::new();

  ```

- `const fn with_offset(self, offset: usize) -> Self`

  Sets the index of the first row to be displayed

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let state = TableState::new().with_offset(1);

  ```

- `fn with_selected<T>(self, selected: T) -> Self`

  Sets the index of the selected row

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let state = TableState::new().with_selected(Some(1));

  ```

- `fn with_selected_column<T>(self, selected: T) -> Self`

  Sets the index of the selected column

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let state = TableState::new().with_selected_column(Some(1));

  ```

- `fn with_selected_cell<T>(self, selected: T) -> Self`

  Sets the indexes of the selected cell

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let state = TableState::new().with_selected_cell(Some((1, 5)));

  ```

- `const fn offset(&self) -> usize`

  Index of the first row to be displayed

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let state = TableState::new();

  assert_eq!(state.offset(), 0);

  ```

- `const fn offset_mut(&mut self) -> &mut usize`

  Mutable reference to the index of the first row to be displayed

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  *state.offset_mut() = 1;

  ```

- `const fn selected(&self) -> Option<usize>`

  Index of the selected row

  

  Returns `None` if no row is selected

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let state = TableState::new();

  assert_eq!(state.selected(), None);

  ```

- `const fn selected_column(&self) -> Option<usize>`

  Index of the selected column

  

  Returns `None` if no column is selected

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let state = TableState::new();

  assert_eq!(state.selected_column(), None);

  ```

- `const fn selected_cell(&self) -> Option<(usize, usize)>`

  Indexes of the selected cell

  

  Returns `None` if no cell is selected

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let state = TableState::new();

  assert_eq!(state.selected_cell(), None);

  ```

- `const fn selected_mut(&mut self) -> &mut Option<usize>`

  Mutable reference to the index of the selected row

  

  Returns `None` if no row is selected

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  *state.selected_mut() = Some(1);

  ```

- `const fn selected_column_mut(&mut self) -> &mut Option<usize>`

  Mutable reference to the index of the selected column

  

  Returns `None` if no column is selected

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  *state.selected_column_mut() = Some(1);

  ```

- `const fn select(&mut self, index: Option<usize>)`

  Sets the index of the selected row

  

  Set to `None` if no row is selected. This will also reset the offset to `0`.

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  state.select(Some(1));

  ```

- `const fn select_column(&mut self, index: Option<usize>)`

  Sets the index of the selected column

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  state.select_column(Some(1));

  ```

- `const fn select_cell(&mut self, indexes: Option<(usize, usize)>)`

  Sets the indexes of the selected cell

  

  Set to `None` if no cell is selected. This will also reset the row offset to `0`.

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  state.select_cell(Some((1, 5)));

  ```

- `fn select_next(&mut self)`

  Selects the next row or the first one if no row is selected

  

  Note: until the table is rendered, the number of rows is not known, so the index is set to

  `0` and will be corrected when the table is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  state.select_next();

  ```

- `fn select_next_column(&mut self)`

  Selects the next column or the first one if no column is selected

  

  Note: until the table is rendered, the number of columns is not known, so the index is set

  to `0` and will be corrected when the table is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  state.select_next_column();

  ```

- `fn select_previous(&mut self)`

  Selects the previous row or the last one if no item is selected

  

  Note: until the table is rendered, the number of rows is not known, so the index is set to

  `usize::MAX` and will be corrected when the table is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  state.select_previous();

  ```

- `fn select_previous_column(&mut self)`

  Selects the previous column or the last one if no column is selected

  

  Note: until the table is rendered, the number of columns is not known, so the index is set

  to `usize::MAX` and will be corrected when the table is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  state.select_previous_column();

  ```

- `const fn select_first(&mut self)`

  Selects the first row

  

  Note: until the table is rendered, the number of rows is not known, so the index is set to

  `0` and will be corrected when the table is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  state.select_first();

  ```

- `const fn select_first_column(&mut self)`

  Selects the first column

  

  Note: until the table is rendered, the number of columns is not known, so the index is set

  to `0` and will be corrected when the table is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  state.select_first_column();

  ```

- `const fn select_last(&mut self)`

  Selects the last row

  

  Note: until the table is rendered, the number of rows is not known, so the index is set to

  `usize::MAX` and will be corrected when the table is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  state.select_last();

  ```

- `const fn select_last_column(&mut self)`

  Selects the last column

  

  Note: until the table is rendered, the number of columns is not known, so the index is set

  to `usize::MAX` and will be corrected when the table is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  state.select_last();

  ```

- `fn scroll_down_by(&mut self, amount: u16)`

  Scrolls down by a specified `amount` in the table.

  

  This method updates the selected index by moving it down by the given `amount`.

  If the `amount` causes the index to go out of bounds (i.e., if the index is greater than

  the number of rows in the table), the last row in the table will be selected.

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  state.scroll_down_by(4);

  ```

- `fn scroll_up_by(&mut self, amount: u16)`

  Scrolls up by a specified `amount` in the table.

  

  This method updates the selected index by moving it up by the given `amount`.

  If the `amount` causes the index to go out of bounds (i.e., less than zero),

  the first row in the table will be selected.

  

  # Examples

  

  ```rust

  use ratatui::widgets::TableState;

  

  let mut state = TableState::default();

  state.scroll_up_by(4);

  ```

- `fn scroll_right_by(&mut self, amount: u16)`

  Scrolls right by a specified `amount` in the table.

  

  This method updates the selected index by moving it right by the given `amount`.

  If the `amount` causes the index to go out of bounds (i.e., if the index is greater than

  the number of columns in the table), the last column in the table will be selected.

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  state.scroll_right_by(4);

  ```

- `fn scroll_left_by(&mut self, amount: u16)`

  Scrolls left by a specified `amount` in the table.

  

  This method updates the selected index by moving it left by the given `amount`.

  If the `amount` causes the index to go out of bounds (i.e., less than zero),

  the first item in the table will be selected.

  

  # Examples

  

  ```rust

  use ratatui::widgets::{TableState};

  let mut state = TableState::default();

  state.scroll_left_by(4);

  ```

#### Trait Implementations

##### `impl Clone for TableState`

- `fn clone(&self) -> TableState` — [`TableState`](../index.md#tablestate)

##### `impl Copy for TableState`

##### `impl Debug for TableState`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for TableState`

- `fn default() -> TableState` — [`TableState`](../index.md#tablestate)

##### `impl Eq for TableState`

##### `impl<K> Equivalent for TableState`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for TableState`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for TableState`

##### `impl PartialEq for TableState`

- `fn eq(&self, other: &TableState) -> bool` — [`TableState`](../index.md#tablestate)

##### `impl StructuralPartialEq for TableState`

### `Table<'a>`

```rust
struct Table<'a> {
    // [REDACTED: Private Fields]
}
```

A widget to display data in formatted columns.

A `Table` is a collection of [`Row`](../index.md)s, each composed of [`Cell`](../index.md)s:

You can construct a [`Table`](#table) using either `Table::new` or `Table::default` and then chain
builder style methods to set the desired properties.

Table cells can be aligned, for more details see [`Cell`](../index.md).

Make sure to call the `Table::widths` method, otherwise the columns will all have a width of 0
and thus not be visible.

[`Table`](#table) implements [`Widget`](../../ratatui_core/index.md) and so it can be drawn using `Frame::render_widget`.

[`Table`](#table) is also a [`StatefulWidget`](../../ratatui_core/index.md), which means you can use it with [`TableState`](../index.md) to allow
the user to scroll through the rows and select one of them. When rendering a [`Table`](#table) with a
[`TableState`](../index.md), the selected row, column and cell will be highlighted. If the selected row is
not visible (based on the offset), the table will be scrolled to make the selected row visible.

Note: if the `widths` field is empty, the table will be rendered with equal widths.
Note: Highlight styles are applied in the following order: Row, Column, Cell.

See the table example and the recipe and traceroute tabs in the demo2 example in the [Examples]
directory for a more in depth example of the various configuration options and for how to handle
state.

# Constructor methods

- `Table::new` creates a new [`Table`](#table) with the given rows.
- `Table::default` creates an empty [`Table`](#table). You can then add rows using `Table::rows`.

# Setter methods

These methods are fluent setters. They return a new `Table` with the specified property set.

- `Table::rows` sets the rows of the [`Table`](#table).
- `Table::header` sets the header row of the [`Table`](#table).
- `Table::footer` sets the footer row of the [`Table`](#table).
- `Table::widths` sets the width constraints of each column.
- `Table::column_spacing` sets the spacing between each column.
- `Table::block` wraps the table in a [`Block`](../block/index.md) widget.
- `Table::style` sets the base style of the widget.
- `Table::row_highlight_style` sets the style of the selected row.
- `Table::column_highlight_style` sets the style of the selected column.
- `Table::cell_highlight_style` sets the style of the selected cell.
- `Table::highlight_symbol` sets the symbol to be displayed in front of the selected row.
- `Table::highlight_spacing` sets when to show the highlight spacing.

# Example

```rust
use ratatui::layout::Constraint;
use ratatui::style::{Style, Stylize};
use ratatui::widgets::{Block, Row, Table};

let rows = [Row::new(vec!["Cell1", "Cell2", "Cell3"])];
// Columns widths are constrained in the same way as Layout...
let widths = [
    Constraint::Length(5),
    Constraint::Length(5),
    Constraint::Length(10),
];
let table = Table::new(rows, widths)
    // ...and they can be separated by a fixed spacing.
    .column_spacing(1)
    // You can set the style of the entire Table.
    .style(Style::new().blue())
    // It has an optional header, which is simply a Row always visible at the top.
    .header(
        Row::new(vec!["Col1", "Col2", "Col3"])
            .style(Style::new().bold())
            // To add space between the header and the rest of the rows, specify the margin
            .bottom_margin(1),
    )
    // It has an optional footer, which is simply a Row always visible at the bottom.
    .footer(Row::new(vec!["Updated on Dec 28"]))
    // As any other widget, a Table can be wrapped in a Block.
    .block(Block::new().title("Table"))
    // The selected row, column, cell and its content can also be styled.
    .row_highlight_style(Style::new().reversed())
    .column_highlight_style(Style::new().red())
    .cell_highlight_style(Style::new().blue())
    // ...and potentially show a symbol in front of the selection.
    .highlight_symbol(">>");
```

Rows can be created from an iterator of [`Cell`](../index.md)s. Each row can have an associated height,
bottom margin, and style. See [`Row`](../index.md) for more details.

```rust
use ratatui::style::{Style, Stylize};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Cell, Row, Table};

// a Row can be created from simple strings.
let row = Row::new(vec!["Row11", "Row12", "Row13"]);

// You can style the entire row.
let row = Row::new(vec!["Row21", "Row22", "Row23"]).style(Style::new().red());

// If you need more control over the styling, create Cells directly
let row = Row::new(vec![
    Cell::from("Row31"),
    Cell::from("Row32").style(Style::new().yellow()),
    Cell::from(Line::from(vec![Span::raw("Row"), Span::from("33").green()])),
]);

// If a Row need to display some content over multiple lines, specify the height.
let row = Row::new(vec![
    Cell::from("Row\n41"),
    Cell::from("Row\n42"),
    Cell::from("Row\n43"),
])
.height(2);
```

Cells can be created from anything that can be converted to [`Text`](../../ratatui_core/index.md). See [`Cell`](../index.md) for more
details.

```rust
use ratatui::style::{Style, Stylize};
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::Cell;

Cell::from("simple string");
Cell::from("simple styled span".red());
Cell::from(Span::raw("raw span"));
Cell::from(Span::styled("styled span", Style::new().red()));
Cell::from(Line::from(vec![
    Span::raw("a vec of "),
    Span::from("spans").bold(),
]));
Cell::from(Text::from("text"));
```

Just as rows can be collected from iterators of `Cell`s, tables can be collected from iterators
of `Row`s.  This will create a table with column widths evenly dividing the space available.
These default columns widths can be overridden using the `Table::widths` method.

```rust
use ratatui::layout::Constraint;
use ratatui::widgets::{Row, Table};

let text = "Mary had a\nlittle lamb.";

let table = text
    .split("\n")
    .map(|line: &str| -> Row { line.split_ascii_whitespace().collect() })
    .collect::<Table>()
    .widths([Constraint::Length(10); 3]);
```

`Table` also implements the [`Styled`](../../ratatui_core/index.md) trait, which means you can use style shorthands from
the `Stylize` trait to set the style of the widget more concisely.

```rust
use ratatui::layout::Constraint;
use ratatui::style::Stylize;
use ratatui::widgets::{Row, Table};

let rows = [Row::new(vec!["Cell1", "Cell2", "Cell3"])];
let widths = [
    Constraint::Length(5),
    Constraint::Length(5),
    Constraint::Length(10),
];
let table = Table::new(rows, widths).red().italic();
```

# Stateful example

`Table` is a [`StatefulWidget`](../../ratatui_core/index.md), which means you can use it with [`TableState`](../index.md) to allow the
user to scroll through the rows and select one of them.

```rust
use ratatui::Frame;
use ratatui::layout::{Constraint, Rect};
use ratatui::style::{Style, Stylize};
use ratatui::widgets::{Block, Row, Table, TableState};

fn ui(frame: &mut Frame) {
let area = Rect::default();
// Note: TableState should be stored in your application state (not constructed in your render
// method) so that the selected row is preserved across renders
let mut table_state = TableState::default();
let rows = [
    Row::new(vec!["Row11", "Row12", "Row13"]),
    Row::new(vec!["Row21", "Row22", "Row23"]),
    Row::new(vec!["Row31", "Row32", "Row33"]),
];
let widths = [
    Constraint::Length(5),
    Constraint::Length(5),
    Constraint::Length(10),
];
let table = Table::new(rows, widths)
    .block(Block::new().title("Table"))
    .row_highlight_style(Style::new().reversed())
    .highlight_symbol(">>");

frame.render_stateful_widget(table, area, &mut table_state);
}
```

#### Implementations

- `fn new<R, C>(rows: R, widths: C) -> Self`

  Creates a new [`Table`](#table) widget with the given rows.

  

  The `rows` parameter accepts any value that can be converted into an iterator of [`Row`](../index.md)s.

  This includes arrays, slices, and `Vec`s.

  

  The `widths` parameter accepts any type that implements `IntoIterator<Item =

  Into<Constraint>>`. This includes arrays, slices, vectors, iterators. `Into<Constraint>` is

  implemented on u16, so you can pass an array, vec, etc. of u16 to this function to create a

  table with fixed width columns.

  

  # Examples

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::{Row, Table};

  

  let rows = [

      Row::new(vec!["Cell1", "Cell2"]),

      Row::new(vec!["Cell3", "Cell4"]),

  ];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths);

  ```

- `fn rows<T>(self, rows: T) -> Self`

  Set the rows

  

  The `rows` parameter accepts any value that can be converted into an iterator of [`Row`](../index.md)s.

  This includes arrays, slices, and `Vec`s.

  

  # Warning

  

  This method does not currently set the column widths. You will need to set them manually by

  calling `Table::widths`.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Row, Table};

  

  let rows = [

      Row::new(vec!["Cell1", "Cell2"]),

      Row::new(vec!["Cell3", "Cell4"]),

  ];

  let table = Table::default().rows(rows);

  ```

- `fn header(self, header: Row<'a>) -> Self` — [`Row`](../index.md#row)

  Sets the header row

  

  The `header` parameter is a [`Row`](../index.md) which will be displayed at the top of the [`Table`](#table)

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Cell, Row, Table};

  

  let header = Row::new(vec![

      Cell::from("Header Cell 1"),

      Cell::from("Header Cell 2"),

  ]);

  let table = Table::default().header(header);

  ```

- `fn footer(self, footer: Row<'a>) -> Self` — [`Row`](../index.md#row)

  Sets the footer row

  

  The `footer` parameter is a [`Row`](../index.md) which will be displayed at the bottom of the [`Table`](#table)

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Cell, Row, Table};

  

  let footer = Row::new(vec![

      Cell::from("Footer Cell 1"),

      Cell::from("Footer Cell 2"),

  ]);

  let table = Table::default().footer(footer);

  ```

- `fn widths<I>(self, widths: I) -> Self`

  Set the widths of the columns.

  

  The `widths` parameter accepts any type that implements `IntoIterator<Item =

  Into<Constraint>>`. This includes arrays, slices, vectors, iterators. `Into<Constraint>` is

  implemented on u16, so you can pass an array, vec, etc. of u16 to this function to create a

  table with fixed width columns.

  

  If the widths are empty, the table will be rendered with equal widths.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::{Cell, Row, Table};

  

  let table = Table::default().widths([Constraint::Length(5), Constraint::Length(5)]);

  let table = Table::default().widths(vec![Constraint::Length(5); 2]);

  

  // widths could also be computed at runtime

  let widths = [10, 10, 20].into_iter().map(|c| Constraint::Length(c));

  let table = Table::default().widths(widths);

  ```

- `const fn column_spacing(self, spacing: u16) -> Self`

  Set the spacing between columns

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::{Row, Table};

  

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).column_spacing(1);

  ```

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](../block/index.md#block)

  Wraps the table with a custom [`Block`](../block/index.md) widget.

  

  The `block` parameter is of type [`Block`](../block/index.md). This holds the specified block to be

  created around the [`Table`](#table)

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::{Block, Cell, Row, Table};

  

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let block = Block::bordered().title("Table");

  let table = Table::new(rows, widths).block(block);

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the base style of the widget

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  All text rendered by the widget will use this style, unless overridden by `Block::style`,

  `Row::style`, `Cell::style`, or the styles of cell's content.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::{Row, Table};

  

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).style(Style::new().red().italic());

  ```

  

  `Table` also implements the [`Styled`](../../ratatui_core/index.md) trait, which means you can use style shorthands from

  the `Stylize` trait to set the style of the widget more concisely.

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::style::Stylize;

  use ratatui::widgets::{Cell, Row, Table};

  

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = vec![Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).red().italic();

  ```

  

- `fn highlight_style<S: Into<Style>>(self, highlight_style: S) -> Self`

  Set the style of the selected row

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This style will be applied to the entire row, including the selection symbol if it is

  displayed, and will override any style set on the row or on the individual cells.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::{Cell, Row, Table};

  

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).highlight_style(Style::new().red().italic());

  ```

- `fn row_highlight_style<S: Into<Style>>(self, highlight_style: S) -> Self`

  Set the style of the selected row

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This style will be applied to the entire row, including the selection symbol if it is

  displayed, and will override any style set on the row or on the individual cells.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::{layout::Constraint, style::{Style, Stylize}, widgets::{Row, Table}};

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).row_highlight_style(Style::new().red().italic());

  ```

- `fn column_highlight_style<S: Into<Style>>(self, highlight_style: S) -> Self`

  Set the style of the selected column

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This style will be applied to the entire column, and will override any style set on the

  row or on the individual cells.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::{layout::Constraint, style::{Style, Stylize}, widgets::{Row, Table}};

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).column_highlight_style(Style::new().red().italic());

  ```

- `fn cell_highlight_style<S: Into<Style>>(self, highlight_style: S) -> Self`

  Set the style of the selected cell

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This style will be applied to the selected cell, and will override any style set on the

  row or on the individual cells.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::{layout::Constraint, style::{Style, Stylize}, widgets::{Row, Table}};

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).cell_highlight_style(Style::new().red().italic());

  ```

- `fn highlight_symbol<T: Into<Text<'a>>>(self, highlight_symbol: T) -> Self`

  Set the symbol to be displayed in front of the selected row

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::{Cell, Row, Table};

  

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).highlight_symbol(">>");

  ```

- `const fn highlight_spacing(self, value: HighlightSpacing) -> Self` — [`HighlightSpacing`](../index.md#highlightspacing)

  Set when to show the highlight spacing

  

  The highlight spacing is the spacing that is allocated for the selection symbol column (if

  enabled) and is used to shift the table when a row is selected. This method allows you to

  configure when this spacing is allocated.

  

  - [`HighlightSpacing::Always`](../index.md) will always allocate the spacing, regardless of whether a row

    is selected or not. This means that the table will never change size, regardless of if a

    row is selected or not.

  - [`HighlightSpacing::WhenSelected`](../index.md) will only allocate the spacing if a row is selected.

    This means that the table will shift when a row is selected. This is the default setting

    for backwards compatibility, but it is recommended to use `HighlightSpacing::Always` for a

    better user experience.

  - [`HighlightSpacing::Never`](../index.md) will never allocate the spacing, regardless of whether a row

    is selected or not. This means that the highlight symbol will never be drawn.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::{HighlightSpacing, Row, Table};

  

  let rows = [Row::new(vec!["Cell1", "Cell2"])];

  let widths = [Constraint::Length(5), Constraint::Length(5)];

  let table = Table::new(rows, widths).highlight_spacing(HighlightSpacing::Always);

  ```

- `const fn flex(self, flex: Flex) -> Self`

  Set how extra space is distributed amongst columns.

  

  This determines how the space is distributed when the constraints are satisfied. By default,

  the extra space is not distributed at all.  But this can be changed to distribute all extra

  space to the last column or to distribute it equally.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  Create a table that needs at least 30 columns to display.  Any extra space will be assigned

  to the last column.

  ```rust

  use ratatui::layout::{Constraint, Flex};

  use ratatui::widgets::{Row, Table};

  

  let widths = [

      Constraint::Min(10),

      Constraint::Min(10),

      Constraint::Min(10),

  ];

  let table = Table::new(Vec::<Row>::new(), widths).flex(Flex::Legacy);

  ```

#### Trait Implementations

##### `impl AsRef for crate::table::Table<'a>`

- `fn as_ref(&self) -> &crate::table::Table<'a>` — [`Table`](#table)

##### `impl Clone for Table<'a>`

- `fn clone(&self) -> Table<'a>` — [`Table`](#table)

##### `impl Debug for Table<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Table<'_>`

- `fn default() -> Self`

##### `impl Eq for Table<'a>`

##### `impl<K> Equivalent for Table<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl<Item> FromIterator for Table<'a>`

- `fn from_iter<Iter: IntoIterator<Item = Item>>(rows: Iter) -> Self`

  Collects an iterator of rows into a table.

  

  When collecting from an iterator into a table, the user must provide the widths using

  `Table::widths` after construction.

##### `impl Hash for Table<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Table<'a>`

##### `impl PartialEq for Table<'a>`

- `fn eq(&self, other: &Table<'a>) -> bool` — [`Table`](#table)

##### `impl StatefulWidget for Table<'_>`

- `type State = TableState`

- `fn render(self, area: Rect, buf: &mut Buffer, state: &mut <Self as >::State)`

##### `impl StructuralPartialEq for Table<'a>`

##### `impl Styled for Table<'_>`

- `type Item = Table<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Table<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for Table<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

## Enums

### `HighlightSpacing`

```rust
enum HighlightSpacing {
    Always,
    WhenSelected,
    Never,
}
```

This option allows the user to configure the "highlight symbol" column width spacing

#### Variants

- **`Always`**

  Always add spacing for the selection symbol column
  
  With this variant, the column for the selection symbol will always be allocated, and so the
  table will never change size, regardless of if a row is selected or not

- **`WhenSelected`**

  Only add spacing for the selection symbol column if a row is selected
  
  With this variant, the column for the selection symbol will only be allocated if there is a
  selection, causing the table to shift if selected / unselected

- **`Never`**

  Never add spacing to the selection symbol column, regardless of whether something is
  selected or not
  
  This means that the highlight symbol will never be drawn

#### Trait Implementations

##### `impl Clone for HighlightSpacing`

- `fn clone(&self) -> HighlightSpacing` — [`HighlightSpacing`](../index.md#highlightspacing)

##### `impl Debug for HighlightSpacing`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for HighlightSpacing`

- `fn default() -> HighlightSpacing` — [`HighlightSpacing`](../index.md#highlightspacing)

##### `impl Display for HighlightSpacing`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for HighlightSpacing`

##### `impl<K> Equivalent for HighlightSpacing`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for HighlightSpacing`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<HighlightSpacing, <Self as ::core::str::FromStr>::Err>` — [`HighlightSpacing`](../index.md#highlightspacing)

##### `impl Hash for HighlightSpacing`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for HighlightSpacing`

##### `impl PartialEq for HighlightSpacing`

- `fn eq(&self, other: &HighlightSpacing) -> bool` — [`HighlightSpacing`](../index.md#highlightspacing)

##### `impl StructuralPartialEq for HighlightSpacing`

##### `impl ToCompactString for HighlightSpacing`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for HighlightSpacing`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for HighlightSpacing`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for HighlightSpacing`

- `fn to_string(&self) -> String`

##### `impl ToText for HighlightSpacing`

- `fn to_text(&self) -> Text<'_>`

