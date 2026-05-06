*[ratatui_widgets](../index.md) / [clear](index.md)*

---

# Module `clear`

The [`Clear`](#clear) widget allows you to clear a certain area to allow overdrawing (e.g. for popups).

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Clear`](#clear) | struct | A widget to clear/reset a certain area to allow overdrawing (e.g. for popups). |

## Structs

### `Clear`

```rust
struct Clear;
```

A widget to clear/reset a certain area to allow overdrawing (e.g. for popups).

This widget **cannot be used to clear the terminal on the first render** as `ratatui` assumes
the render area is empty. Use `Terminal::clear` instead.

# Examples

```rust
use ratatui::Frame;
use ratatui::layout::Rect;
use ratatui::widgets::{Block, Clear};

fn draw_on_clear(f: &mut Frame, area: Rect) {
    let block = Block::bordered().title("Block");
    f.render_widget(Clear, area); // <- this will clear/reset the area first
    f.render_widget(block, area); // now render the block widget
}
```

# Popup Example

For a more complete example how to utilize `Clear` to realize popups see
the example `examples/popup.rs`

#### Trait Implementations

##### `impl AsRef for crate::clear::Clear`

- `fn as_ref(&self) -> &crate::clear::Clear` — [`Clear`](#clear)

##### `impl Clone for Clear`

- `fn clone(&self) -> Clear` — [`Clear`](#clear)

##### `impl Debug for Clear`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Clear`

- `fn default() -> Clear` — [`Clear`](#clear)

##### `impl Eq for Clear`

##### `impl<K> Equivalent for Clear`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Clear`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Clear`

##### `impl PartialEq for Clear`

- `fn eq(&self, other: &Clear) -> bool` — [`Clear`](#clear)

##### `impl StructuralPartialEq for Clear`

##### `impl Widget for Clear`

- `fn render(self, area: Rect, buf: &mut Buffer)`

