*[ratatui_widgets](../index.md) / [fill](index.md)*

---

# Module `fill`

The [`Fill`](#fill) widget paints every cell in its area with a single symbol and style.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Fill`](#fill) | struct | A widget that fills its render area with a single repeated symbol and style. |

## Structs

### `Fill<'a>`

```rust
struct Fill<'a> {
    // [REDACTED: Private Fields]
}
```

A widget that fills its render area with a single repeated symbol and style.

[`Fill`](#fill) is a small building block for painting solid blocks of one symbol — backgrounds,
separators, scrollbar tracks, custom borders, etc. — without writing the nested loop
yourself. It composes naturally with the `Stylize` trait so the typical call site is
a one-liner.

# Examples

```rust
use ratatui::layout::Rect;
use ratatui::style::Stylize;
use ratatui::widgets::{Fill, Widget};

let mut buf = ratatui::buffer::Buffer::empty(Rect::new(0, 0, 10, 5));
let fill = Fill::new("X").blue().bold();
fill.render(Rect::new(0, 0, 10, 3), &mut buf);
```

This renders as:

```plain
XXXXXXXXXX
XXXXXXXXXX
XXXXXXXXXX
```

[`Fill`](#fill) accepts anything that converts into a `Cow<str>`, so both string literals and
owned [`String`](alloc::string::String)s work:

```rust
use ratatui::widgets::Fill;

let _ = Fill::new("•");
let _ = Fill::new(String::from("•"));
```

Cells outside the buffer are silently clipped, mirroring the behavior of other widgets
such as [`Clear`](crate::clear::Clear).

#### Implementations

- `fn new<S: Into<Cow<'a, str>>>(symbol: S) -> Self`

  Create a new [`Fill`](#fill) widget that paints `symbol` into every cell of its render area.

  

  The style defaults to `Style::default`; use the `Stylize` shorthands or

  `Fill::style` to customize it.

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Set the style used to paint each cell.

  

  `style` accepts any value convertible into a [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md),

  [`Color`](ratatui_core::style::Color), or your own type implementing

  `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn symbol<S: Into<Cow<'a, str>>>(self, symbol: S) -> Self`

  Set the symbol painted into each cell.

  

  This is a fluent setter method which must be chained or used as it consumes self

#### Trait Implementations

##### `impl Clone for Fill<'a>`

- `fn clone(&self) -> Fill<'a>` — [`Fill`](#fill)

##### `impl Debug for Fill<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Fill<'a>`

- `fn default() -> Fill<'a>` — [`Fill`](#fill)

##### `impl Eq for Fill<'a>`

##### `impl<K> Equivalent for Fill<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Fill<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Fill<'a>`

##### `impl PartialEq for Fill<'a>`

- `fn eq(&self, other: &Fill<'a>) -> bool` — [`Fill`](#fill)

##### `impl StructuralPartialEq for Fill<'a>`

##### `impl Styled for Fill<'_>`

- `type Item = Fill<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Fill<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for Fill<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

