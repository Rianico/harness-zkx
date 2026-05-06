*[ratatui_core](../../index.md) / [symbols](../index.md) / [line](index.md)*

---

# Module `line`

## Contents

- [Structs](#structs)
  - [`Set`](#set)
- [Constants](#constants)
  - [`VERTICAL`](#vertical)
  - [`DOUBLE_VERTICAL`](#double-vertical)
  - [`THICK_VERTICAL`](#thick-vertical)
  - [`LIGHT_DOUBLE_DASH_VERTICAL`](#light-double-dash-vertical)
  - [`HEAVY_DOUBLE_DASH_VERTICAL`](#heavy-double-dash-vertical)
  - [`LIGHT_TRIPLE_DASH_VERTICAL`](#light-triple-dash-vertical)
  - [`HEAVY_TRIPLE_DASH_VERTICAL`](#heavy-triple-dash-vertical)
  - [`LIGHT_QUADRUPLE_DASH_VERTICAL`](#light-quadruple-dash-vertical)
  - [`HEAVY_QUADRUPLE_DASH_VERTICAL`](#heavy-quadruple-dash-vertical)
  - [`HORIZONTAL`](#horizontal)
  - [`DOUBLE_HORIZONTAL`](#double-horizontal)
  - [`THICK_HORIZONTAL`](#thick-horizontal)
  - [`LIGHT_DOUBLE_DASH_HORIZONTAL`](#light-double-dash-horizontal)
  - [`HEAVY_DOUBLE_DASH_HORIZONTAL`](#heavy-double-dash-horizontal)
  - [`LIGHT_TRIPLE_DASH_HORIZONTAL`](#light-triple-dash-horizontal)
  - [`HEAVY_TRIPLE_DASH_HORIZONTAL`](#heavy-triple-dash-horizontal)
  - [`LIGHT_QUADRUPLE_DASH_HORIZONTAL`](#light-quadruple-dash-horizontal)
  - [`HEAVY_QUADRUPLE_DASH_HORIZONTAL`](#heavy-quadruple-dash-horizontal)
  - [`TOP_RIGHT`](#top-right)
  - [`ROUNDED_TOP_RIGHT`](#rounded-top-right)
  - [`DOUBLE_TOP_RIGHT`](#double-top-right)
  - [`THICK_TOP_RIGHT`](#thick-top-right)
  - [`TOP_LEFT`](#top-left)
  - [`ROUNDED_TOP_LEFT`](#rounded-top-left)
  - [`DOUBLE_TOP_LEFT`](#double-top-left)
  - [`THICK_TOP_LEFT`](#thick-top-left)
  - [`BOTTOM_RIGHT`](#bottom-right)
  - [`ROUNDED_BOTTOM_RIGHT`](#rounded-bottom-right)
  - [`DOUBLE_BOTTOM_RIGHT`](#double-bottom-right)
  - [`THICK_BOTTOM_RIGHT`](#thick-bottom-right)
  - [`BOTTOM_LEFT`](#bottom-left)
  - [`ROUNDED_BOTTOM_LEFT`](#rounded-bottom-left)
  - [`DOUBLE_BOTTOM_LEFT`](#double-bottom-left)
  - [`THICK_BOTTOM_LEFT`](#thick-bottom-left)
  - [`VERTICAL_LEFT`](#vertical-left)
  - [`DOUBLE_VERTICAL_LEFT`](#double-vertical-left)
  - [`THICK_VERTICAL_LEFT`](#thick-vertical-left)
  - [`VERTICAL_RIGHT`](#vertical-right)
  - [`DOUBLE_VERTICAL_RIGHT`](#double-vertical-right)
  - [`THICK_VERTICAL_RIGHT`](#thick-vertical-right)
  - [`HORIZONTAL_DOWN`](#horizontal-down)
  - [`DOUBLE_HORIZONTAL_DOWN`](#double-horizontal-down)
  - [`THICK_HORIZONTAL_DOWN`](#thick-horizontal-down)
  - [`HORIZONTAL_UP`](#horizontal-up)
  - [`DOUBLE_HORIZONTAL_UP`](#double-horizontal-up)
  - [`THICK_HORIZONTAL_UP`](#thick-horizontal-up)
  - [`CROSS`](#cross)
  - [`DOUBLE_CROSS`](#double-cross)
  - [`THICK_CROSS`](#thick-cross)
  - [`NORMAL`](#normal)
  - [`ROUNDED`](#rounded)
  - [`DOUBLE`](#double)
  - [`THICK`](#thick)
  - [`LIGHT_DOUBLE_DASHED`](#light-double-dashed)
  - [`HEAVY_DOUBLE_DASHED`](#heavy-double-dashed)
  - [`LIGHT_TRIPLE_DASHED`](#light-triple-dashed)
  - [`HEAVY_TRIPLE_DASHED`](#heavy-triple-dashed)
  - [`LIGHT_QUADRUPLE_DASHED`](#light-quadruple-dashed)
  - [`HEAVY_QUADRUPLE_DASHED`](#heavy-quadruple-dashed)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Set`](#set) | struct |  |
| [`VERTICAL`](#vertical) | const |  |
| [`DOUBLE_VERTICAL`](#double-vertical) | const |  |
| [`THICK_VERTICAL`](#thick-vertical) | const |  |
| [`LIGHT_DOUBLE_DASH_VERTICAL`](#light-double-dash-vertical) | const |  |
| [`HEAVY_DOUBLE_DASH_VERTICAL`](#heavy-double-dash-vertical) | const |  |
| [`LIGHT_TRIPLE_DASH_VERTICAL`](#light-triple-dash-vertical) | const |  |
| [`HEAVY_TRIPLE_DASH_VERTICAL`](#heavy-triple-dash-vertical) | const |  |
| [`LIGHT_QUADRUPLE_DASH_VERTICAL`](#light-quadruple-dash-vertical) | const |  |
| [`HEAVY_QUADRUPLE_DASH_VERTICAL`](#heavy-quadruple-dash-vertical) | const |  |
| [`HORIZONTAL`](#horizontal) | const |  |
| [`DOUBLE_HORIZONTAL`](#double-horizontal) | const |  |
| [`THICK_HORIZONTAL`](#thick-horizontal) | const |  |
| [`LIGHT_DOUBLE_DASH_HORIZONTAL`](#light-double-dash-horizontal) | const |  |
| [`HEAVY_DOUBLE_DASH_HORIZONTAL`](#heavy-double-dash-horizontal) | const |  |
| [`LIGHT_TRIPLE_DASH_HORIZONTAL`](#light-triple-dash-horizontal) | const |  |
| [`HEAVY_TRIPLE_DASH_HORIZONTAL`](#heavy-triple-dash-horizontal) | const |  |
| [`LIGHT_QUADRUPLE_DASH_HORIZONTAL`](#light-quadruple-dash-horizontal) | const |  |
| [`HEAVY_QUADRUPLE_DASH_HORIZONTAL`](#heavy-quadruple-dash-horizontal) | const |  |
| [`TOP_RIGHT`](#top-right) | const |  |
| [`ROUNDED_TOP_RIGHT`](#rounded-top-right) | const |  |
| [`DOUBLE_TOP_RIGHT`](#double-top-right) | const |  |
| [`THICK_TOP_RIGHT`](#thick-top-right) | const |  |
| [`TOP_LEFT`](#top-left) | const |  |
| [`ROUNDED_TOP_LEFT`](#rounded-top-left) | const |  |
| [`DOUBLE_TOP_LEFT`](#double-top-left) | const |  |
| [`THICK_TOP_LEFT`](#thick-top-left) | const |  |
| [`BOTTOM_RIGHT`](#bottom-right) | const |  |
| [`ROUNDED_BOTTOM_RIGHT`](#rounded-bottom-right) | const |  |
| [`DOUBLE_BOTTOM_RIGHT`](#double-bottom-right) | const |  |
| [`THICK_BOTTOM_RIGHT`](#thick-bottom-right) | const |  |
| [`BOTTOM_LEFT`](#bottom-left) | const |  |
| [`ROUNDED_BOTTOM_LEFT`](#rounded-bottom-left) | const |  |
| [`DOUBLE_BOTTOM_LEFT`](#double-bottom-left) | const |  |
| [`THICK_BOTTOM_LEFT`](#thick-bottom-left) | const |  |
| [`VERTICAL_LEFT`](#vertical-left) | const |  |
| [`DOUBLE_VERTICAL_LEFT`](#double-vertical-left) | const |  |
| [`THICK_VERTICAL_LEFT`](#thick-vertical-left) | const |  |
| [`VERTICAL_RIGHT`](#vertical-right) | const |  |
| [`DOUBLE_VERTICAL_RIGHT`](#double-vertical-right) | const |  |
| [`THICK_VERTICAL_RIGHT`](#thick-vertical-right) | const |  |
| [`HORIZONTAL_DOWN`](#horizontal-down) | const |  |
| [`DOUBLE_HORIZONTAL_DOWN`](#double-horizontal-down) | const |  |
| [`THICK_HORIZONTAL_DOWN`](#thick-horizontal-down) | const |  |
| [`HORIZONTAL_UP`](#horizontal-up) | const |  |
| [`DOUBLE_HORIZONTAL_UP`](#double-horizontal-up) | const |  |
| [`THICK_HORIZONTAL_UP`](#thick-horizontal-up) | const |  |
| [`CROSS`](#cross) | const |  |
| [`DOUBLE_CROSS`](#double-cross) | const |  |
| [`THICK_CROSS`](#thick-cross) | const |  |
| [`NORMAL`](#normal) | const |  |
| [`ROUNDED`](#rounded) | const |  |
| [`DOUBLE`](#double) | const |  |
| [`THICK`](#thick) | const |  |
| [`LIGHT_DOUBLE_DASHED`](#light-double-dashed) | const |  |
| [`HEAVY_DOUBLE_DASHED`](#heavy-double-dashed) | const |  |
| [`LIGHT_TRIPLE_DASHED`](#light-triple-dashed) | const |  |
| [`HEAVY_TRIPLE_DASHED`](#heavy-triple-dashed) | const |  |
| [`LIGHT_QUADRUPLE_DASHED`](#light-quadruple-dashed) | const |  |
| [`HEAVY_QUADRUPLE_DASHED`](#heavy-quadruple-dashed) | const |  |

## Structs

### `Set<'a>`

```rust
struct Set<'a> {
    pub vertical: &'a str,
    pub horizontal: &'a str,
    pub top_right: &'a str,
    pub top_left: &'a str,
    pub bottom_right: &'a str,
    pub bottom_left: &'a str,
    pub vertical_left: &'a str,
    pub vertical_right: &'a str,
    pub horizontal_down: &'a str,
    pub horizontal_up: &'a str,
    pub cross: &'a str,
}
```

#### Trait Implementations

##### `impl Clone for Set<'a>`

- `fn clone(&self) -> Set<'a>` — [`Set`](#set)

##### `impl Copy for Set<'a>`

##### `impl Debug for Set<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Set<'_>`

- `fn default() -> Self`

##### `impl Eq for Set<'a>`

##### `impl<K> Equivalent for Set<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Set<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Set<'a>`

##### `impl PartialEq for Set<'a>`

- `fn eq(&self, other: &Set<'a>) -> bool` — [`Set`](#set)

##### `impl StructuralPartialEq for Set<'a>`

## Constants

### `VERTICAL`
```rust
const VERTICAL: &str;
```

### `DOUBLE_VERTICAL`
```rust
const DOUBLE_VERTICAL: &str;
```

### `THICK_VERTICAL`
```rust
const THICK_VERTICAL: &str;
```

### `LIGHT_DOUBLE_DASH_VERTICAL`
```rust
const LIGHT_DOUBLE_DASH_VERTICAL: &str;
```

### `HEAVY_DOUBLE_DASH_VERTICAL`
```rust
const HEAVY_DOUBLE_DASH_VERTICAL: &str;
```

### `LIGHT_TRIPLE_DASH_VERTICAL`
```rust
const LIGHT_TRIPLE_DASH_VERTICAL: &str;
```

### `HEAVY_TRIPLE_DASH_VERTICAL`
```rust
const HEAVY_TRIPLE_DASH_VERTICAL: &str;
```

### `LIGHT_QUADRUPLE_DASH_VERTICAL`
```rust
const LIGHT_QUADRUPLE_DASH_VERTICAL: &str;
```

### `HEAVY_QUADRUPLE_DASH_VERTICAL`
```rust
const HEAVY_QUADRUPLE_DASH_VERTICAL: &str;
```

### `HORIZONTAL`
```rust
const HORIZONTAL: &str;
```

### `DOUBLE_HORIZONTAL`
```rust
const DOUBLE_HORIZONTAL: &str;
```

### `THICK_HORIZONTAL`
```rust
const THICK_HORIZONTAL: &str;
```

### `LIGHT_DOUBLE_DASH_HORIZONTAL`
```rust
const LIGHT_DOUBLE_DASH_HORIZONTAL: &str;
```

### `HEAVY_DOUBLE_DASH_HORIZONTAL`
```rust
const HEAVY_DOUBLE_DASH_HORIZONTAL: &str;
```

### `LIGHT_TRIPLE_DASH_HORIZONTAL`
```rust
const LIGHT_TRIPLE_DASH_HORIZONTAL: &str;
```

### `HEAVY_TRIPLE_DASH_HORIZONTAL`
```rust
const HEAVY_TRIPLE_DASH_HORIZONTAL: &str;
```

### `LIGHT_QUADRUPLE_DASH_HORIZONTAL`
```rust
const LIGHT_QUADRUPLE_DASH_HORIZONTAL: &str;
```

### `HEAVY_QUADRUPLE_DASH_HORIZONTAL`
```rust
const HEAVY_QUADRUPLE_DASH_HORIZONTAL: &str;
```

### `TOP_RIGHT`
```rust
const TOP_RIGHT: &str;
```

### `ROUNDED_TOP_RIGHT`
```rust
const ROUNDED_TOP_RIGHT: &str;
```

### `DOUBLE_TOP_RIGHT`
```rust
const DOUBLE_TOP_RIGHT: &str;
```

### `THICK_TOP_RIGHT`
```rust
const THICK_TOP_RIGHT: &str;
```

### `TOP_LEFT`
```rust
const TOP_LEFT: &str;
```

### `ROUNDED_TOP_LEFT`
```rust
const ROUNDED_TOP_LEFT: &str;
```

### `DOUBLE_TOP_LEFT`
```rust
const DOUBLE_TOP_LEFT: &str;
```

### `THICK_TOP_LEFT`
```rust
const THICK_TOP_LEFT: &str;
```

### `BOTTOM_RIGHT`
```rust
const BOTTOM_RIGHT: &str;
```

### `ROUNDED_BOTTOM_RIGHT`
```rust
const ROUNDED_BOTTOM_RIGHT: &str;
```

### `DOUBLE_BOTTOM_RIGHT`
```rust
const DOUBLE_BOTTOM_RIGHT: &str;
```

### `THICK_BOTTOM_RIGHT`
```rust
const THICK_BOTTOM_RIGHT: &str;
```

### `BOTTOM_LEFT`
```rust
const BOTTOM_LEFT: &str;
```

### `ROUNDED_BOTTOM_LEFT`
```rust
const ROUNDED_BOTTOM_LEFT: &str;
```

### `DOUBLE_BOTTOM_LEFT`
```rust
const DOUBLE_BOTTOM_LEFT: &str;
```

### `THICK_BOTTOM_LEFT`
```rust
const THICK_BOTTOM_LEFT: &str;
```

### `VERTICAL_LEFT`
```rust
const VERTICAL_LEFT: &str;
```

### `DOUBLE_VERTICAL_LEFT`
```rust
const DOUBLE_VERTICAL_LEFT: &str;
```

### `THICK_VERTICAL_LEFT`
```rust
const THICK_VERTICAL_LEFT: &str;
```

### `VERTICAL_RIGHT`
```rust
const VERTICAL_RIGHT: &str;
```

### `DOUBLE_VERTICAL_RIGHT`
```rust
const DOUBLE_VERTICAL_RIGHT: &str;
```

### `THICK_VERTICAL_RIGHT`
```rust
const THICK_VERTICAL_RIGHT: &str;
```

### `HORIZONTAL_DOWN`
```rust
const HORIZONTAL_DOWN: &str;
```

### `DOUBLE_HORIZONTAL_DOWN`
```rust
const DOUBLE_HORIZONTAL_DOWN: &str;
```

### `THICK_HORIZONTAL_DOWN`
```rust
const THICK_HORIZONTAL_DOWN: &str;
```

### `HORIZONTAL_UP`
```rust
const HORIZONTAL_UP: &str;
```

### `DOUBLE_HORIZONTAL_UP`
```rust
const DOUBLE_HORIZONTAL_UP: &str;
```

### `THICK_HORIZONTAL_UP`
```rust
const THICK_HORIZONTAL_UP: &str;
```

### `CROSS`
```rust
const CROSS: &str;
```

### `DOUBLE_CROSS`
```rust
const DOUBLE_CROSS: &str;
```

### `THICK_CROSS`
```rust
const THICK_CROSS: &str;
```

### `NORMAL`
```rust
const NORMAL: Set<'_>;
```

### `ROUNDED`
```rust
const ROUNDED: Set<'_>;
```

### `DOUBLE`
```rust
const DOUBLE: Set<'_>;
```

### `THICK`
```rust
const THICK: Set<'_>;
```

### `LIGHT_DOUBLE_DASHED`
```rust
const LIGHT_DOUBLE_DASHED: Set<'_>;
```

### `HEAVY_DOUBLE_DASHED`
```rust
const HEAVY_DOUBLE_DASHED: Set<'_>;
```

### `LIGHT_TRIPLE_DASHED`
```rust
const LIGHT_TRIPLE_DASHED: Set<'_>;
```

### `HEAVY_TRIPLE_DASHED`
```rust
const HEAVY_TRIPLE_DASHED: Set<'_>;
```

### `LIGHT_QUADRUPLE_DASHED`
```rust
const LIGHT_QUADRUPLE_DASHED: Set<'_>;
```

### `HEAVY_QUADRUPLE_DASHED`
```rust
const HEAVY_QUADRUPLE_DASHED: Set<'_>;
```

