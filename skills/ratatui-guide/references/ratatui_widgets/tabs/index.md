*[ratatui_widgets](../index.md) / [tabs](index.md)*

---

# Module `tabs`

The [`Tabs`](#tabs) widget displays a horizontal set of tabs with a single tab selected.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Tabs`](#tabs) | struct | A widget that displays a horizontal set of Tabs with a single tab selected. |

## Structs

### `Tabs<'a>`

```rust
struct Tabs<'a> {
    // [REDACTED: Private Fields]
}
```

A widget that displays a horizontal set of Tabs with a single tab selected.

Each tab title is stored as a [`Line`](../../ratatui_core/index.md) which can be individually styled. The selected tab is set
using `Tabs::select` and styled using `Tabs::highlight_style`. The divider can be customized
with `Tabs::divider`. Padding can be set with `Tabs::padding` or `Tabs::padding_left` and
`Tabs::padding_right`.

The divider defaults to |, and padding defaults to a singular space on each side.

# Example

```rust
use ratatui::style::{Style, Stylize};
use ratatui::symbols;
use ratatui::widgets::{Block, Tabs};

Tabs::new(vec!["Tab1", "Tab2", "Tab3", "Tab4"])
    .block(Block::bordered().title("Tabs"))
    .style(Style::default().white())
    .highlight_style(Style::default().yellow())
    .select(2)
    .divider(symbols::DOT)
    .padding("->", "<-");
```

In addition to `Tabs::new`, any iterator whose element is convertible to `Line` can be collected
into `Tabs`.

```rust
use ratatui::widgets::Tabs;

(0..5).map(|i| format!("Tab{i}")).collect::<Tabs>();
```

#### Implementations

- `fn new<Iter>(titles: Iter) -> Self`

  Creates new `Tabs` from their titles.

  

  `titles` can be a `Vec` of `&str`, `String` or anything that can be converted into

  [`Line`](../../ratatui_core/index.md). As such, titles can be styled independently.

  

  The selected tab can be set with `Tabs::select`. The first tab has index 0 (this is also

  the default index).

  

  The selected tab can have a different style with `Tabs::highlight_style`. This defaults to

  a style with the `Modifier::REVERSED` modifier added.

  

  The default divider is a pipe (`|`), but it can be customized with `Tabs::divider`.

  

  The entire widget can be styled with `Tabs::style`.

  

  The widget can be wrapped in a [`Block`](../block/index.md) using `Tabs::block`.

  

  # Examples

  

  Basic titles.

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]);

  ```

  

  Styled titles

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1".red(), "Tab 2".blue()]);

  ```

  

- `fn titles<Iter>(self, titles: Iter) -> Self`

  Sets the titles of the tabs.

  

  `titles` is an iterator whose elements can be converted into `Line`.

  

  The selected tab can be set with `Tabs::select`. The first tab has index 0 (this is also

  the default index).

  

  # Examples

  

  Basic titles.

  

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::default().titles(vec!["Tab 1", "Tab 2"]);

  ```

  

  Styled titles.

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::default().titles(vec!["Tab 1".red(), "Tab 2".blue()]);

  ```

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](../block/index.md#block)

  Surrounds the `Tabs` with a [`Block`](../block/index.md).

- `fn select<T: Into<Option<usize>>>(self, selected: T) -> Self`

  Sets the selected tab.

  

  The first tab has index 0 (this is also the default index).

  The selected tab can have a different style with `Tabs::highlight_style`.

  

  # Examples

  

  Select the second tab.

  

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]).select(1);

  ```

  

  Deselect the selected tab.

  

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]).select(None);

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of the tabs.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  This will set the given style on the entire render area.

  More precise style can be applied to the titles by styling the ones given to `Tabs::new`.

  The selected tab can be styled differently using `Tabs::highlight_style`.

- `fn highlight_style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style for the highlighted tab.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

  

  Highlighted tab can be selected with `Tabs::select`.

- `fn divider<T>(self, divider: T) -> Self`

  Sets the string to use as tab divider.

  

  By default, the divider is a pipe (`|`).

  

  # Examples

  

  Use a dot (`•`) as separator.

  ```rust

  use ratatui::symbols;

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]).divider(symbols::DOT);

  ```

  Use dash (`-`) as separator.

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]).divider("-");

  ```

- `fn padding<T, U>(self, left: T, right: U) -> Self`

  Sets the padding between tabs.

  

  Both default to space.

  

  # Examples

  

  A space on either side of the tabs.

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]).padding(" ", " ");

  ```

  Nothing on either side of the tabs.

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]).padding("", "");

  ```

- `fn padding_left<T>(self, padding: T) -> Self`

  Sets the left side padding between tabs.

  

  Defaults to a space.

  

  # Example

  

  An arrow on the left of tabs.

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]).padding_left("->");

  ```

- `fn padding_right<T>(self, padding: T) -> Self`

  Sets the right side padding between tabs.

  

  Defaults to a space.

  

  # Example

  

  An arrow on the right of tabs.

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::new(vec!["Tab 1", "Tab 2"]).padding_right("<-");

  ```

#### Trait Implementations

##### `impl AsRef for crate::tabs::Tabs<'a>`

- `fn as_ref(&self) -> &crate::tabs::Tabs<'a>` — [`Tabs`](#tabs)

##### `impl Clone for Tabs<'a>`

- `fn clone(&self) -> Tabs<'a>` — [`Tabs`](#tabs)

##### `impl Debug for Tabs<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Tabs<'_>`

- `fn default() -> Self`

  Returns a default `Tabs` widget.

  

  The default widget has:

  - No tabs

  - No selected tab

  - The highlight style is set to reversed.

  - The divider is set to a pipe (`|`).

  - The padding on the left and right is set to a space.

  

  This is rarely useful on its own without calling `Tabs::titles`.

  

  # Examples

  

  ```rust

  use ratatui::widgets::Tabs;

  

  let tabs = Tabs::default().titles(["Tab 1", "Tab 2"]);

  ```

##### `impl Eq for Tabs<'a>`

##### `impl<K> Equivalent for Tabs<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl<Item> FromIterator for Tabs<'a>`

- `fn from_iter<Iter: IntoIterator<Item = Item>>(iter: Iter) -> Self`

##### `impl Hash for Tabs<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Tabs<'a>`

##### `impl PartialEq for Tabs<'a>`

- `fn eq(&self, other: &Tabs<'a>) -> bool` — [`Tabs`](#tabs)

##### `impl StructuralPartialEq for Tabs<'a>`

##### `impl Styled for Tabs<'_>`

- `type Item = Tabs<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Tabs<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl UnicodeWidthStr for Tabs<'_>`

- `fn width(&self) -> usize`

  Returns the width of the rendered tabs.

  

  The width includes the titles, dividers, and padding. It does not include any borders added

  by the optional block.

  

  Characters in the Ambiguous category are considered single-width.

  

  ```rust

  use ratatui::widgets::Tabs;

  use unicode_width::UnicodeWidthStr;

  

  let tabs = Tabs::new(vec!["Tab1", "Tab2", "Tab3"]);

  assert_eq!(tabs.width(), 20); // " Tab1 │ Tab2 │ Tab3 "

  ```

- `fn width_cjk(&self) -> usize`

  Returns the width of the rendered tabs, accounting for CJK characters.

  

  This is probably the wrong method to use in most contexts that Ratatui applications care

  about as it doesn't correlate with the visual representation of most terminals. Consider

  using `Tabs::width` instead.

  

  The width includes the titles, dividers, and padding. It does not include any borders added

  by the optional block.

  

  Characters in the Ambiguous category are considered double-width.

  

  ```rust

  use ratatui::widgets::Tabs;

  use unicode_width::UnicodeWidthStr;

  

  let tabs = Tabs::new(vec!["你", "好", "世界"]);

  assert_eq!("你".width_cjk(), 2);

  assert_eq!("好".width_cjk(), 2);

  assert_eq!("世界".width_cjk(), 4);

  assert_eq!("│".width_cjk(), 2); // this is correct for cjk

  assert_eq!(tabs.width_cjk(), 18); // " 你 │ 好 │ 世界 "

  ```

##### `impl Widget for Tabs<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

