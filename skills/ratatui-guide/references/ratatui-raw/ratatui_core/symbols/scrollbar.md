*[ratatui_core](../index.md) / [symbols](../index.md) / [scrollbar](#)*

---

# Module `scrollbar`

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Set`](#set) | struct | Scrollbar Set ```text <--▮-------> ^  ^   ^   ^ │  │   │   └ end │  │   └──── track │  └──────── thumb └─────────── begin ``` |
| [`DOUBLE_VERTICAL`](#double-vertical) | const |  |
| [`DOUBLE_HORIZONTAL`](#double-horizontal) | const |  |
| [`VERTICAL`](#vertical) | const |  |
| [`HORIZONTAL`](#horizontal) | const |  |

## Structs

### `Set<'a>`

```rust
struct Set<'a> {
    pub track: &'a str,
    pub thumb: &'a str,
    pub begin: &'a str,
    pub end: &'a str,
}
```

Scrollbar Set
```text
<--▮------->
^  ^   ^   ^
│  │   │   └ end
│  │   └──── track
│  └──────── thumb
└─────────── begin
```

#### Trait Implementations

##### `impl Clone for Set<'a>`

- `fn clone(&self) -> Set<'a>` — [`Set`](#set)

##### `impl Debug for Set<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Set<'a>`

- `fn default() -> Set<'a>` — [`Set`](#set)

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

### `DOUBLE_VERTICAL`
```rust
const DOUBLE_VERTICAL: Set<'_>;
```

### `DOUBLE_HORIZONTAL`
```rust
const DOUBLE_HORIZONTAL: Set<'_>;
```

### `VERTICAL`
```rust
const VERTICAL: Set<'_>;
```

### `HORIZONTAL`
```rust
const HORIZONTAL: Set<'_>;
```

