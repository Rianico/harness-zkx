*[ratatui_widgets](../index.md) / [list](index.md)*

---

# Module `list`

The [`List`](#list) widget is used to display a list of items and allows selecting one or multiple
items.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`ListItem`](#listitem) | struct |  |
| [`ListState`](#liststate) | struct |  |
| [`List`](#list) | struct | A widget to display several items among which one can be selected (optional) |
| [`ListDirection`](#listdirection) | enum | Defines the direction in which the list will be rendered. |

## Structs

### `ListItem<'a>`

```rust
struct ListItem<'a> {
    // [REDACTED: Private Fields]
}
```

A single item in a [`List`](#list)

The item's height is defined by the number of lines it contains. This can be queried using
`ListItem::height`. Similarly, `ListItem::width` will return the maximum width of all
lines.

You can set the style of an item with `ListItem::style` or using the `Stylize` trait.
This [`Style`](../../ratatui_core/style/index.md) will be combined with the [`Style`](../../ratatui_core/style/index.md) of the inner [`Text`](../../ratatui_core/index.md). The [`Style`](../../ratatui_core/style/index.md)
of the [`Text`](../../ratatui_core/index.md) will be added to the [`Style`](../../ratatui_core/style/index.md) of the [`ListItem`](../index.md).

You can also align a `ListItem` by aligning its underlying [`Text`](../../ratatui_core/index.md) and [`Line`](../index.md)s. For that,
see `Text::alignment` and `Line::alignment`. On a multiline `Text`, one `Line` can override
the alignment by setting it explicitly.

# Examples

You can create [`ListItem`](../index.md)s from simple `&str`

```rust
use ratatui::widgets::ListItem;
let item = ListItem::new("Item 1");
```

Anything that can be converted to [`Text`](../../ratatui_core/index.md) can be a [`ListItem`](../index.md).

```rust
use ratatui::text::Line;
use ratatui::widgets::ListItem;

let item1: ListItem = "Item 1".into();
let item2: ListItem = Line::raw("Item 2").into();
```

A [`ListItem`](../index.md) styled with `Stylize`

```rust
use ratatui::style::Stylize;
use ratatui::widgets::ListItem;

let item = ListItem::new("Item 1").red().on_white();
```

If you need more control over the item's style, you can explicitly style the underlying
[`Text`](../../ratatui_core/index.md)

```rust
use ratatui::style::Stylize;
use ratatui::text::{Span, Text};
use ratatui::widgets::ListItem;

let mut text = Text::default();
text.extend(["Item".blue(), Span::raw(" "), "1".bold().red()]);
let item = ListItem::new(text);
```

A right-aligned `ListItem`

```rust
use ratatui::text::Text;
use ratatui::widgets::ListItem;

ListItem::new(Text::from("foo").right_aligned());
```

#### Implementations

- `fn new<T>(content: T) -> Self`

  Creates a new [`ListItem`](../index.md)

  

  The `content` parameter accepts any value that can be converted into [`Text`](../../ratatui_core/index.md).

  

  # Examples

  

  You can create [`ListItem`](../index.md)s from simple `&str`

  

  ```rust

  use ratatui::widgets::ListItem;

  

  let item = ListItem::new("Item 1");

  ```

  

  Anything that can be converted to [`Text`](../../ratatui_core/index.md) can be a [`ListItem`](../index.md).

  

  ```rust

  use ratatui::text::Line;

  use ratatui::widgets::ListItem;

  

  let item1: ListItem = "Item 1".into();

  let item2: ListItem = Line::raw("Item 2").into();

  ```

  

  You can also create multiline items

  

  ```rust

  use ratatui::widgets::ListItem;

  

  let item = ListItem::new("Multi-line\nitem");

  ```

  

  # See also

  

  - [`List::new`](super::List::new) to create a list of items that can be converted to

    [`ListItem`](../index.md)

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the item style

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This [`Style`](../../ratatui_core/style/index.md) can be overridden by the [`Style`](../../ratatui_core/style/index.md) of the [`Text`](../../ratatui_core/index.md) content.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::ListItem;

  

  let item = ListItem::new("Item 1").style(Style::new().red().italic());

  ```

  

  `ListItem` also implements the `Styled` trait, which means you can use style shorthands

  from the [`Stylize`](ratatui_core::style::Stylize) trait to set the style of the widget more

  concisely.

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::ListItem;

  

  let item = ListItem::new("Item 1").red().italic();

  ```

  

  

- `const fn height(&self) -> usize`

  Returns the item height

  

  # Examples

  

  One line item

  

  ```rust

  use ratatui::widgets::ListItem;

  

  let item = ListItem::new("Item 1");

  assert_eq!(item.height(), 1);

  ```

  

  Two lines item (note the `\n`)

  

  ```rust

  use ratatui::widgets::ListItem;

  

  let item = ListItem::new("Multi-line\nitem");

  assert_eq!(item.height(), 2);

  ```

- `fn width(&self) -> usize`

  Returns the max width of all the lines

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListItem;

  

  let item = ListItem::new("12345");

  assert_eq!(item.width(), 5);

  ```

  

  ```rust

  use ratatui::widgets::ListItem;

  

  let item = ListItem::new("12345\n1234567");

  assert_eq!(item.width(), 7);

  ```

#### Trait Implementations

##### `impl Clone for ListItem<'a>`

- `fn clone(&self) -> ListItem<'a>` — [`ListItem`](../index.md#listitem)

##### `impl Debug for ListItem<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for ListItem<'a>`

##### `impl<K> Equivalent for ListItem<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for ListItem<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ListItem<'a>`

##### `impl PartialEq for ListItem<'a>`

- `fn eq(&self, other: &ListItem<'a>) -> bool` — [`ListItem`](../index.md#listitem)

##### `impl StructuralPartialEq for ListItem<'a>`

##### `impl Styled for ListItem<'_>`

- `type Item = ListItem<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for ListItem<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

### `ListState`

```rust
struct ListState {
    // [REDACTED: Private Fields]
}
```

State of the [`List`](#list) widget

This state can be used to scroll through items and select one. When the list is rendered as a
stateful widget, the selected item will be highlighted and the list will be shifted to ensure
that the selected item is visible. This will modify the [`ListState`](../index.md) object passed to the
`Frame::render_stateful_widget` method.

The state consists of two fields:
- `offset`: the index of the first item to be displayed
- `selected`: the index of the selected item, which can be `None` if no item is selected

See the list in the [Examples] directory for a more in depth example of the various
configuration options and for how to handle state.

# Example

```rust
use ratatui::Frame;
use ratatui::layout::Rect;
use ratatui::widgets::{List, ListState};

fn ui(frame: &mut Frame) {
let area = Rect::default();
let items = ["Item 1"];
let list = List::new(items);

// This should be stored outside of the function in your application state.
let mut state = ListState::default();

*state.offset_mut() = 1; // display the second item and onwards
state.select(Some(3)); // select the forth item (0-indexed)

frame.render_stateful_widget(list, area, &mut state);
}
```

#### Implementations

- `const fn with_offset(self, offset: usize) -> Self`

  Sets the index of the first item to be displayed

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let state = ListState::default().with_offset(1);

  ```

- `const fn with_selected(self, selected: Option<usize>) -> Self`

  Sets the index of the selected item

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let state = ListState::default().with_selected(Some(1));

  ```

- `const fn offset(&self) -> usize`

  Index of the first item to be displayed

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let state = ListState::default();

  assert_eq!(state.offset(), 0);

  ```

- `const fn offset_mut(&mut self) -> &mut usize`

  Mutable reference to the index of the first item to be displayed

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  *state.offset_mut() = 1;

  ```

- `const fn selected(&self) -> Option<usize>`

  Index of the selected item

  

  Returns `None` if no item is selected

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let state = ListState::default();

  assert_eq!(state.selected(), None);

  ```

- `const fn selected_mut(&mut self) -> &mut Option<usize>`

  Mutable reference to the index of the selected item

  

  Returns `None` if no item is selected

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  *state.selected_mut() = Some(1);

  ```

- `const fn select(&mut self, index: Option<usize>)`

  Sets the index of the selected item

  

  Set to `None` if no item is selected. This will also reset the offset to `0`.

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  state.select(Some(1));

  ```

- `fn select_next(&mut self)`

  Selects the next item or the first one if no item is selected

  

  Note: until the list is rendered, the number of items is not known, so the index is set to

  `0` and will be corrected when the list is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  state.select_next();

  ```

- `fn select_previous(&mut self)`

  Selects the previous item or the last one if no item is selected

  

  Note: until the list is rendered, the number of items is not known, so the index is set to

  `usize::MAX` and will be corrected when the list is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  state.select_previous();

  ```

- `const fn select_first(&mut self)`

  Selects the first item

  

  Note: until the list is rendered, the number of items is not known, so the index is set to

  `0` and will be corrected when the list is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  state.select_first();

  ```

- `const fn select_last(&mut self)`

  Selects the last item

  

  Note: until the list is rendered, the number of items is not known, so the index is set to

  `usize::MAX` and will be corrected when the list is rendered

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  state.select_last();

  ```

- `fn scroll_down_by(&mut self, amount: u16)`

  Scrolls down by a specified `amount` in the list.

  

  This method updates the selected index by moving it down by the given `amount`.

  If the `amount` causes the index to go out of bounds (i.e., if the index is greater than

  the length of the list), the last item in the list will be selected.

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  state.scroll_down_by(4);

  ```

- `fn scroll_up_by(&mut self, amount: u16)`

  Scrolls up by a specified `amount` in the list.

  

  This method updates the selected index by moving it up by the given `amount`.

  If the `amount` causes the index to go out of bounds (i.e., less than zero),

  the first item in the list will be selected.

  

  # Examples

  

  ```rust

  use ratatui::widgets::ListState;

  

  let mut state = ListState::default();

  state.scroll_up_by(4);

  ```

#### Trait Implementations

##### `impl Clone for ListState`

- `fn clone(&self) -> ListState` — [`ListState`](../index.md#liststate)

##### `impl Copy for ListState`

##### `impl Debug for ListState`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for ListState`

- `fn default() -> ListState` — [`ListState`](../index.md#liststate)

##### `impl Eq for ListState`

##### `impl<K> Equivalent for ListState`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for ListState`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ListState`

##### `impl PartialEq for ListState`

- `fn eq(&self, other: &ListState) -> bool` — [`ListState`](../index.md#liststate)

##### `impl StructuralPartialEq for ListState`

### `List<'a>`

```rust
struct List<'a> {
    // [REDACTED: Private Fields]
}
```

A widget to display several items among which one can be selected (optional)

A list is a collection of [`ListItem`](../index.md)s.

This is different from a [`Table`](../table/index.md) because it does not handle columns, headers or footers and
the item's height is automatically determined. A `List` can also be put in reverse order (i.e.
*bottom to top*) whereas a [`Table`](../table/index.md) cannot.

List items can be aligned using `Text::alignment`, for more details see [`ListItem`](../index.md).

[`List`](#list) is also a `StatefulWidget`, which means you can use it with [`ListState`](../index.md) to allow
the user to [scroll] through items and [select] one of them.

See the list in the [Examples] directory for a more in depth example of the various
configuration options and for how to handle state.

# Fluent setters

- `List::highlight_style` sets the style of the selected item.
- `List::highlight_symbol` sets the symbol to be displayed in front of the selected item.
- `List::repeat_highlight_symbol` sets whether to repeat the symbol and style over selected
  multi-line items
- `List::direction` sets the list direction

# Examples

```rust
use ratatui::Frame;
use ratatui::layout::Rect;
use ratatui::style::{Style, Stylize};
use ratatui::widgets::{Block, List, ListDirection, ListItem};

fn ui(frame: &mut Frame) {
let area = Rect::default();
let items = ["Item 1", "Item 2", "Item 3"];
let list = List::new(items)
    .block(Block::bordered().title("List"))
    .style(Style::new().white())
    .highlight_style(Style::new().italic())
    .highlight_symbol(">>")
    .repeat_highlight_symbol(true)
    .direction(ListDirection::BottomToTop);

frame.render_widget(list, area);
}
```

# Stateful example

```rust
use ratatui::Frame;
use ratatui::layout::Rect;
use ratatui::style::{Style, Stylize};
use ratatui::widgets::{Block, List, ListState};

fn ui(frame: &mut Frame) {
let area = Rect::default();
// This should be stored outside of the function in your application state.
let mut state = ListState::default();
let items = ["Item 1", "Item 2", "Item 3"];
let list = List::new(items)
    .block(Block::bordered().title("List"))
    .highlight_style(Style::new().reversed())
    .highlight_symbol(">>")
    .repeat_highlight_symbol(true);

frame.render_stateful_widget(list, area, &mut state);
}
```

In addition to `List::new`, any iterator whose element is convertible to `ListItem` can be
collected into `List`.

```rust
use ratatui::widgets::List;

(0..5).map(|i| format!("Item{i}")).collect::<List>();
```

#### Implementations

- `fn new<T>(items: T) -> Self`

  Creates a new list from [`ListItem`](../index.md)s

  

  The `items` parameter accepts any value that can be converted into an iterator of

  `Into<ListItem>`. This includes arrays of `&str` or `Vec`s of `Text`.

  

  # Example

  

  From a slice of `&str`

  

  ```rust

  use ratatui::widgets::List;

  

  let list = List::new(["Item 1", "Item 2"]);

  ```

  

  From `Text`

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::text::Text;

  use ratatui::widgets::List;

  

  let list = List::new([

      Text::styled("Item 1", Style::new().red()),

      Text::styled("Item 2", Style::new().red()),

  ]);

  ```

  

  You can also create an empty list using the [`Default`](../index.md) implementation and use the

  `List::items` fluent setter.

  

  ```rust

  use ratatui::widgets::List;

  

  let empty_list = List::default();

  let filled_list = empty_list.items(["Item 1"]);

  ```

- `fn items<T>(self, items: T) -> Self`

  Set the items

  

  The `items` parameter accepts any value that can be converted into an iterator of

  `Into<ListItem>`. This includes arrays of `&str` or `Vec`s of `Text`.

  

  This is a fluent setter method which must be chained or used as it consumes self.

  

  # Example

  

  ```rust

  use ratatui::widgets::List;

  

  let list = List::default().items(["Item 1", "Item 2"]);

  ```

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](../block/index.md#block)

  Wraps the list with a custom [`Block`](../block/index.md) widget.

  

  The `block` parameter holds the specified [`Block`](../block/index.md) to be created around the [`List`](#list)

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::{Block, List};

  

  let items = ["Item 1"];

  let block = Block::bordered().title("List");

  let list = List::new(items).block(block);

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the base style of the widget

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  All text rendered by the widget will use this style, unless overridden by `Block::style`,

  `ListItem::style`, or the styles of the [`ListItem`](../index.md)'s content.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::List;

  

  let items = ["Item 1"];

  let list = List::new(items).style(Style::new().red().italic());

  ```

  

  `List` also implements the [`Styled`](../../ratatui_core/index.md) trait, which means you can use style shorthands from

  the `Stylize` trait to set the style of the widget more concisely.

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::List;

  

  let items = ["Item 1"];

  let list = List::new(items).red().italic();

  ```

- `fn highlight_symbol<L: Into<Line<'a>>>(self, highlight_symbol: L) -> Self`

  Set the symbol to be displayed in front of the selected item

  

  By default there are no highlight symbol.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::List;

  

  let items = ["Item 1", "Item 2"];

  let list = List::new(items).highlight_symbol(">>");

  ```

- `fn highlight_style<S: Into<Style>>(self, style: S) -> Self`

  Set the style of the selected item

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This style will be applied to the entire item, including the

  [highlight symbol](List::highlight_symbol) if it is displayed, and will override any style

  set on the item or on the individual cells.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::style::{Style, Stylize};

  use ratatui::widgets::List;

  

  let items = ["Item 1", "Item 2"];

  let list = List::new(items).highlight_style(Style::new().red().italic());

  ```

- `const fn repeat_highlight_symbol(self, repeat: bool) -> Self`

  Set whether to repeat the highlight symbol and style over selected multi-line items

  

  This is `false` by default.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn highlight_spacing(self, value: HighlightSpacing) -> Self` — [`HighlightSpacing`](../index.md#highlightspacing)

  Set when to show the highlight spacing

  

  The highlight spacing is the spacing that is allocated for the selection symbol (if enabled)

  and is used to shift the list when an item is selected. This method allows you to configure

  when this spacing is allocated.

  

  - [`HighlightSpacing::Always`](../index.md) will always allocate the spacing, regardless of whether an

    item is selected or not. This means that the table will never change size, regardless of

    if an item is selected or not.

  - [`HighlightSpacing::WhenSelected`](../index.md) will only allocate the spacing if an item is selected.

    This means that the table will shift when an item is selected. This is the default setting

    for backwards compatibility, but it is recommended to use `HighlightSpacing::Always` for a

    better user experience.

  - [`HighlightSpacing::Never`](../index.md) will never allocate the spacing, regardless of whether an item

    is selected or not. This means that the highlight symbol will never be drawn.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::widgets::{HighlightSpacing, List};

  

  let items = ["Item 1"];

  let list = List::new(items).highlight_spacing(HighlightSpacing::Always);

  ```

- `const fn direction(self, direction: ListDirection) -> Self` — [`ListDirection`](#listdirection)

  Defines the list direction (up or down)

  

  Defines if the `List` is displayed *top to bottom* (default) or *bottom to top*.

  If there is too few items to fill the screen, the list will stick to the starting edge.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  

  Bottom to top

  

  ```rust

  use ratatui::widgets::{List, ListDirection};

  

  let items = ["Item 1"];

  let list = List::new(items).direction(ListDirection::BottomToTop);

  ```

- `const fn scroll_padding(self, padding: usize) -> Self`

  Sets the number of items around the currently selected item that should be kept visible

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  

  A padding value of 1 will keep 1 item above and 1 item below visible if possible

  

  ```rust

  use ratatui::widgets::List;

  

  let items = ["Item 1"];

  let list = List::new(items).scroll_padding(1);

  ```

- `const fn len(&self) -> usize`

  Returns the number of [`ListItem`](../index.md)s in the list

- `const fn is_empty(&self) -> bool`

  Returns true if the list contains no elements.

#### Trait Implementations

##### `impl AsRef for crate::list::List<'a>`

- `fn as_ref(&self) -> &crate::list::List<'a>` — [`List`](#list)

##### `impl Clone for List<'a>`

- `fn clone(&self) -> List<'a>` — [`List`](#list)

##### `impl Debug for List<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for List<'a>`

- `fn default() -> List<'a>` — [`List`](#list)

##### `impl Eq for List<'a>`

##### `impl<K> Equivalent for List<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl<Item> FromIterator for List<'a>`

- `fn from_iter<Iter: IntoIterator<Item = Item>>(iter: Iter) -> Self`

##### `impl Hash for List<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for List<'a>`

##### `impl PartialEq for List<'a>`

- `fn eq(&self, other: &List<'a>) -> bool` — [`List`](#list)

##### `impl StatefulWidget for crate::list::List<'_>`

- `type State = ListState`

- `fn render(self, area: Rect, buf: &mut Buffer, state: &mut <Self as >::State)`

##### `impl StructuralPartialEq for List<'a>`

##### `impl Styled for List<'_>`

- `type Item = List<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for List<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for crate::list::List<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

## Enums

### `ListDirection`

```rust
enum ListDirection {
    TopToBottom,
    BottomToTop,
}
```

Defines the direction in which the list will be rendered.

If there are too few items to fill the screen, the list will stick to the starting edge.

See `List::direction`.

#### Variants

- **`TopToBottom`**

  The first value is on the top, going to the bottom

- **`BottomToTop`**

  The first value is on the bottom, going to the top.

#### Trait Implementations

##### `impl Clone for ListDirection`

- `fn clone(&self) -> ListDirection` — [`ListDirection`](#listdirection)

##### `impl Copy for ListDirection`

##### `impl Debug for ListDirection`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for ListDirection`

- `fn default() -> ListDirection` — [`ListDirection`](#listdirection)

##### `impl Display for ListDirection`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for ListDirection`

##### `impl<K> Equivalent for ListDirection`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for ListDirection`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<ListDirection, <Self as ::core::str::FromStr>::Err>` — [`ListDirection`](#listdirection)

##### `impl Hash for ListDirection`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ListDirection`

##### `impl PartialEq for ListDirection`

- `fn eq(&self, other: &ListDirection) -> bool` — [`ListDirection`](#listdirection)

##### `impl StructuralPartialEq for ListDirection`

##### `impl ToCompactString for ListDirection`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for ListDirection`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for ListDirection`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for ListDirection`

- `fn to_string(&self) -> String`

##### `impl ToText for ListDirection`

- `fn to_text(&self) -> Text<'_>`

