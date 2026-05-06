*[ratatui_core](../../index.md) / [symbols](../index.md) / [border](index.md)*

---

# Module `border`

## Contents

- [Structs](#structs)
  - [`Set`](#set)
- [Constants](#constants)
  - [`PLAIN`](#plain)
  - [`ROUNDED`](#rounded)
  - [`DOUBLE`](#double)
  - [`THICK`](#thick)
  - [`LIGHT_DOUBLE_DASHED`](#light-double-dashed)
  - [`HEAVY_DOUBLE_DASHED`](#heavy-double-dashed)
  - [`LIGHT_TRIPLE_DASHED`](#light-triple-dashed)
  - [`HEAVY_TRIPLE_DASHED`](#heavy-triple-dashed)
  - [`LIGHT_QUADRUPLE_DASHED`](#light-quadruple-dashed)
  - [`HEAVY_QUADRUPLE_DASHED`](#heavy-quadruple-dashed)
  - [`QUADRANT_TOP_LEFT`](#quadrant-top-left)
  - [`QUADRANT_TOP_RIGHT`](#quadrant-top-right)
  - [`QUADRANT_BOTTOM_LEFT`](#quadrant-bottom-left)
  - [`QUADRANT_BOTTOM_RIGHT`](#quadrant-bottom-right)
  - [`QUADRANT_TOP_HALF`](#quadrant-top-half)
  - [`QUADRANT_BOTTOM_HALF`](#quadrant-bottom-half)
  - [`QUADRANT_LEFT_HALF`](#quadrant-left-half)
  - [`QUADRANT_RIGHT_HALF`](#quadrant-right-half)
  - [`QUADRANT_TOP_LEFT_BOTTOM_LEFT_BOTTOM_RIGHT`](#quadrant-top-left-bottom-left-bottom-right)
  - [`QUADRANT_TOP_LEFT_TOP_RIGHT_BOTTOM_LEFT`](#quadrant-top-left-top-right-bottom-left)
  - [`QUADRANT_TOP_LEFT_TOP_RIGHT_BOTTOM_RIGHT`](#quadrant-top-left-top-right-bottom-right)
  - [`QUADRANT_TOP_RIGHT_BOTTOM_LEFT_BOTTOM_RIGHT`](#quadrant-top-right-bottom-left-bottom-right)
  - [`QUADRANT_TOP_LEFT_BOTTOM_RIGHT`](#quadrant-top-left-bottom-right)
  - [`QUADRANT_TOP_RIGHT_BOTTOM_LEFT`](#quadrant-top-right-bottom-left)
  - [`QUADRANT_BLOCK`](#quadrant-block)
  - [`QUADRANT_OUTSIDE`](#quadrant-outside)
  - [`QUADRANT_INSIDE`](#quadrant-inside)
  - [`ONE_EIGHTH_TOP_EIGHT`](#one-eighth-top-eight)
  - [`ONE_EIGHTH_BOTTOM_EIGHT`](#one-eighth-bottom-eight)
  - [`ONE_EIGHTH_LEFT_EIGHT`](#one-eighth-left-eight)
  - [`ONE_EIGHTH_RIGHT_EIGHT`](#one-eighth-right-eight)
  - [`ONE_EIGHTH_WIDE`](#one-eighth-wide)
  - [`ONE_EIGHTH_TALL`](#one-eighth-tall)
  - [`PROPORTIONAL_WIDE`](#proportional-wide)
  - [`PROPORTIONAL_TALL`](#proportional-tall)
  - [`FULL`](#full)
  - [`EMPTY`](#empty)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Set`](#set) | struct |  |
| [`PLAIN`](#plain) | const | Border Set with a single line width |
| [`ROUNDED`](#rounded) | const | Border Set with a single line width and rounded corners |
| [`DOUBLE`](#double) | const | Border Set with a double line width |
| [`THICK`](#thick) | const | Border Set with a thick line width |
| [`LIGHT_DOUBLE_DASHED`](#light-double-dashed) | const | Border Set with light double-dashed border lines |
| [`HEAVY_DOUBLE_DASHED`](#heavy-double-dashed) | const | Border Set with thick double-dashed border lines |
| [`LIGHT_TRIPLE_DASHED`](#light-triple-dashed) | const | Border Set with light triple-dashed border lines |
| [`HEAVY_TRIPLE_DASHED`](#heavy-triple-dashed) | const | Border Set with thick triple-dashed border lines |
| [`LIGHT_QUADRUPLE_DASHED`](#light-quadruple-dashed) | const | Border Set with light quadruple-dashed border lines |
| [`HEAVY_QUADRUPLE_DASHED`](#heavy-quadruple-dashed) | const | Border Set with thick quadruple-dashed border lines |
| [`QUADRANT_TOP_LEFT`](#quadrant-top-left) | const |  |
| [`QUADRANT_TOP_RIGHT`](#quadrant-top-right) | const |  |
| [`QUADRANT_BOTTOM_LEFT`](#quadrant-bottom-left) | const |  |
| [`QUADRANT_BOTTOM_RIGHT`](#quadrant-bottom-right) | const |  |
| [`QUADRANT_TOP_HALF`](#quadrant-top-half) | const |  |
| [`QUADRANT_BOTTOM_HALF`](#quadrant-bottom-half) | const |  |
| [`QUADRANT_LEFT_HALF`](#quadrant-left-half) | const |  |
| [`QUADRANT_RIGHT_HALF`](#quadrant-right-half) | const |  |
| [`QUADRANT_TOP_LEFT_BOTTOM_LEFT_BOTTOM_RIGHT`](#quadrant-top-left-bottom-left-bottom-right) | const |  |
| [`QUADRANT_TOP_LEFT_TOP_RIGHT_BOTTOM_LEFT`](#quadrant-top-left-top-right-bottom-left) | const |  |
| [`QUADRANT_TOP_LEFT_TOP_RIGHT_BOTTOM_RIGHT`](#quadrant-top-left-top-right-bottom-right) | const |  |
| [`QUADRANT_TOP_RIGHT_BOTTOM_LEFT_BOTTOM_RIGHT`](#quadrant-top-right-bottom-left-bottom-right) | const |  |
| [`QUADRANT_TOP_LEFT_BOTTOM_RIGHT`](#quadrant-top-left-bottom-right) | const |  |
| [`QUADRANT_TOP_RIGHT_BOTTOM_LEFT`](#quadrant-top-right-bottom-left) | const |  |
| [`QUADRANT_BLOCK`](#quadrant-block) | const |  |
| [`QUADRANT_OUTSIDE`](#quadrant-outside) | const | Quadrant used for setting a border outside a block by one half cell "pixel". |
| [`QUADRANT_INSIDE`](#quadrant-inside) | const | Quadrant used for setting a border inside a block by one half cell "pixel". |
| [`ONE_EIGHTH_TOP_EIGHT`](#one-eighth-top-eight) | const |  |
| [`ONE_EIGHTH_BOTTOM_EIGHT`](#one-eighth-bottom-eight) | const |  |
| [`ONE_EIGHTH_LEFT_EIGHT`](#one-eighth-left-eight) | const |  |
| [`ONE_EIGHTH_RIGHT_EIGHT`](#one-eighth-right-eight) | const |  |
| [`ONE_EIGHTH_WIDE`](#one-eighth-wide) | const | Wide border set based on McGugan box technique |
| [`ONE_EIGHTH_TALL`](#one-eighth-tall) | const | Tall border set based on McGugan box technique |
| [`PROPORTIONAL_WIDE`](#proportional-wide) | const | Wide proportional (visually equal width and height) border with using set of quadrants. |
| [`PROPORTIONAL_TALL`](#proportional-tall) | const | Tall proportional (visually equal width and height) border with using set of quadrants. |
| [`FULL`](#full) | const | Solid border set |
| [`EMPTY`](#empty) | const | Empty border set |

## Structs

### `Set<'a>`

```rust
struct Set<'a> {
    pub top_left: &'a str,
    pub top_right: &'a str,
    pub bottom_left: &'a str,
    pub bottom_right: &'a str,
    pub vertical_left: &'a str,
    pub vertical_right: &'a str,
    pub horizontal_top: &'a str,
    pub horizontal_bottom: &'a str,
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

### `PLAIN`
```rust
const PLAIN: Set<'_>;
```

Border Set with a single line width

```text
┌─────┐
│xxxxx│
│xxxxx│
└─────┘
```

### `ROUNDED`
```rust
const ROUNDED: Set<'_>;
```

Border Set with a single line width and rounded corners

```text
╭─────╮
│xxxxx│
│xxxxx│
╰─────╯
```

### `DOUBLE`
```rust
const DOUBLE: Set<'_>;
```

Border Set with a double line width

```text
╔═════╗
║xxxxx║
║xxxxx║
╚═════╝
```

### `THICK`
```rust
const THICK: Set<'_>;
```

Border Set with a thick line width

```text
┏━━━━━┓
┃xxxxx┃
┃xxxxx┃
┗━━━━━┛
```

### `LIGHT_DOUBLE_DASHED`
```rust
const LIGHT_DOUBLE_DASHED: Set<'_>;
```

Border Set with light double-dashed border lines

```text
┌╌╌╌╌╌┐
╎xxxxx╎
╎xxxxx╎
└╌╌╌╌╌┘
```

### `HEAVY_DOUBLE_DASHED`
```rust
const HEAVY_DOUBLE_DASHED: Set<'_>;
```

Border Set with thick double-dashed border lines

```text
┏╍╍╍╍╍┓
╏xxxxx╏
╏xxxxx╏
┗╍╍╍╍╍┛
```

### `LIGHT_TRIPLE_DASHED`
```rust
const LIGHT_TRIPLE_DASHED: Set<'_>;
```

Border Set with light triple-dashed border lines

```text
┌┄┄┄┄┄┐
┆xxxxx┆
┆xxxxx┆
└┄┄┄┄┄┘
```

### `HEAVY_TRIPLE_DASHED`
```rust
const HEAVY_TRIPLE_DASHED: Set<'_>;
```

Border Set with thick triple-dashed border lines

```text
┏┅┅┅┅┅┓
┇xxxxx┇
┇xxxxx┇
┗┅┅┅┅┅┛
```

### `LIGHT_QUADRUPLE_DASHED`
```rust
const LIGHT_QUADRUPLE_DASHED: Set<'_>;
```

Border Set with light quadruple-dashed border lines

```text
┌┈┈┈┈┈┐
┊xxxxx┊
┊xxxxx┊
└┈┈┈┈┈┘
```

### `HEAVY_QUADRUPLE_DASHED`
```rust
const HEAVY_QUADRUPLE_DASHED: Set<'_>;
```

Border Set with thick quadruple-dashed border lines

```text
┏┉┉┉┉┉┓
┋xxxxx┋
┋xxxxx┋
┗┉┉┉┉┉┛
```

### `QUADRANT_TOP_LEFT`
```rust
const QUADRANT_TOP_LEFT: &str;
```

### `QUADRANT_TOP_RIGHT`
```rust
const QUADRANT_TOP_RIGHT: &str;
```

### `QUADRANT_BOTTOM_LEFT`
```rust
const QUADRANT_BOTTOM_LEFT: &str;
```

### `QUADRANT_BOTTOM_RIGHT`
```rust
const QUADRANT_BOTTOM_RIGHT: &str;
```

### `QUADRANT_TOP_HALF`
```rust
const QUADRANT_TOP_HALF: &str;
```

### `QUADRANT_BOTTOM_HALF`
```rust
const QUADRANT_BOTTOM_HALF: &str;
```

### `QUADRANT_LEFT_HALF`
```rust
const QUADRANT_LEFT_HALF: &str;
```

### `QUADRANT_RIGHT_HALF`
```rust
const QUADRANT_RIGHT_HALF: &str;
```

### `QUADRANT_TOP_LEFT_BOTTOM_LEFT_BOTTOM_RIGHT`
```rust
const QUADRANT_TOP_LEFT_BOTTOM_LEFT_BOTTOM_RIGHT: &str;
```

### `QUADRANT_TOP_LEFT_TOP_RIGHT_BOTTOM_LEFT`
```rust
const QUADRANT_TOP_LEFT_TOP_RIGHT_BOTTOM_LEFT: &str;
```

### `QUADRANT_TOP_LEFT_TOP_RIGHT_BOTTOM_RIGHT`
```rust
const QUADRANT_TOP_LEFT_TOP_RIGHT_BOTTOM_RIGHT: &str;
```

### `QUADRANT_TOP_RIGHT_BOTTOM_LEFT_BOTTOM_RIGHT`
```rust
const QUADRANT_TOP_RIGHT_BOTTOM_LEFT_BOTTOM_RIGHT: &str;
```

### `QUADRANT_TOP_LEFT_BOTTOM_RIGHT`
```rust
const QUADRANT_TOP_LEFT_BOTTOM_RIGHT: &str;
```

### `QUADRANT_TOP_RIGHT_BOTTOM_LEFT`
```rust
const QUADRANT_TOP_RIGHT_BOTTOM_LEFT: &str;
```

### `QUADRANT_BLOCK`
```rust
const QUADRANT_BLOCK: &str;
```

### `QUADRANT_OUTSIDE`
```rust
const QUADRANT_OUTSIDE: Set<'_>;
```

Quadrant used for setting a border outside a block by one half cell "pixel".

```text
▛▀▀▀▀▀▜
▌xxxxx▐
▌xxxxx▐
▙▄▄▄▄▄▟
```

### `QUADRANT_INSIDE`
```rust
const QUADRANT_INSIDE: Set<'_>;
```

Quadrant used for setting a border inside a block by one half cell "pixel".

```text
▗▄▄▄▄▄▖
▐xxxxx▌
▐xxxxx▌
▝▀▀▀▀▀▘
```

### `ONE_EIGHTH_TOP_EIGHT`
```rust
const ONE_EIGHTH_TOP_EIGHT: &str;
```

### `ONE_EIGHTH_BOTTOM_EIGHT`
```rust
const ONE_EIGHTH_BOTTOM_EIGHT: &str;
```

### `ONE_EIGHTH_LEFT_EIGHT`
```rust
const ONE_EIGHTH_LEFT_EIGHT: &str;
```

### `ONE_EIGHTH_RIGHT_EIGHT`
```rust
const ONE_EIGHTH_RIGHT_EIGHT: &str;
```

### `ONE_EIGHTH_WIDE`
```rust
const ONE_EIGHTH_WIDE: Set<'_>;
```

Wide border set based on McGugan box technique

```text
▁▁▁▁▁▁▁
▏xxxxx▕
▏xxxxx▕
▔▔▔▔▔▔▔
```

### `ONE_EIGHTH_TALL`
```rust
const ONE_EIGHTH_TALL: Set<'_>;
```

Tall border set based on McGugan box technique

```text
▕▔▔▏
▕xx▏
▕xx▏
▕▁▁▏
```

### `PROPORTIONAL_WIDE`
```rust
const PROPORTIONAL_WIDE: Set<'_>;
```

Wide proportional (visually equal width and height) border with using set of quadrants.

The border is created by using half blocks for top and bottom, and full
blocks for right and left sides to make horizontal and vertical borders seem equal.

```text
▄▄▄▄
█xx█
█xx█
▀▀▀▀
```

### `PROPORTIONAL_TALL`
```rust
const PROPORTIONAL_TALL: Set<'_>;
```

Tall proportional (visually equal width and height) border with using set of quadrants.

The border is created by using full blocks for all sides, except for the top and bottom,
which use half blocks to make horizontal and vertical borders seem equal.

```text
▕█▀▀█
▕█xx█
▕█xx█
▕█▄▄█
```

### `FULL`
```rust
const FULL: Set<'_>;
```

Solid border set

The border is created by using full blocks for all sides.

```text
████
█xx█
█xx█
████
```

### `EMPTY`
```rust
const EMPTY: Set<'_>;
```

Empty border set

The border is created by using empty strings for all sides.

This is useful for ensuring that the border style is applied to a border on a block with a title
without actually drawing a border.

░ Example

`░` represents the content in the area not covered by the border to make it easier to see the
blank symbols.

```text
░░░░░░░░
░░    ░░
░░ ░░ ░░
░░ ░░ ░░
░░    ░░
░░░░░░░░
```

