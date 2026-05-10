*[ratatui_core](../index.md) / [symbols](../index.md) / [bar](#)*

---

# Module `bar`

## Contents

- [Structs](#structs)
  - [`Set`](#set)
- [Constants](#constants)
  - [`FULL`](#full)
  - [`SEVEN_EIGHTHS`](#seven-eighths)
  - [`THREE_QUARTERS`](#three-quarters)
  - [`FIVE_EIGHTHS`](#five-eighths)
  - [`HALF`](#half)
  - [`THREE_EIGHTHS`](#three-eighths)
  - [`ONE_QUARTER`](#one-quarter)
  - [`ONE_EIGHTH`](#one-eighth)
  - [`THREE_LEVELS`](#three-levels)
  - [`NINE_LEVELS`](#nine-levels)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Set`](#set) | struct |  |
| [`FULL`](#full) | const |  |
| [`SEVEN_EIGHTHS`](#seven-eighths) | const |  |
| [`THREE_QUARTERS`](#three-quarters) | const |  |
| [`FIVE_EIGHTHS`](#five-eighths) | const |  |
| [`HALF`](#half) | const |  |
| [`THREE_EIGHTHS`](#three-eighths) | const |  |
| [`ONE_QUARTER`](#one-quarter) | const |  |
| [`ONE_EIGHTH`](#one-eighth) | const |  |
| [`THREE_LEVELS`](#three-levels) | const |  |
| [`NINE_LEVELS`](#nine-levels) | const |  |

## Structs

### `Set<'a>`

```rust
struct Set<'a> {
    pub full: &'a str,
    pub seven_eighths: &'a str,
    pub three_quarters: &'a str,
    pub five_eighths: &'a str,
    pub half: &'a str,
    pub three_eighths: &'a str,
    pub one_quarter: &'a str,
    pub one_eighth: &'a str,
    pub empty: &'a str,
}
```

#### Trait Implementations

##### `impl Clone for Set<'a>`

- `fn clone(&self) -> Set<'a>` — [`Set`](#set)

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

### `FULL`
```rust
const FULL: &str;
```

### `SEVEN_EIGHTHS`
```rust
const SEVEN_EIGHTHS: &str;
```

### `THREE_QUARTERS`
```rust
const THREE_QUARTERS: &str;
```

### `FIVE_EIGHTHS`
```rust
const FIVE_EIGHTHS: &str;
```

### `HALF`
```rust
const HALF: &str;
```

### `THREE_EIGHTHS`
```rust
const THREE_EIGHTHS: &str;
```

### `ONE_QUARTER`
```rust
const ONE_QUARTER: &str;
```

### `ONE_EIGHTH`
```rust
const ONE_EIGHTH: &str;
```

### `THREE_LEVELS`
```rust
const THREE_LEVELS: Set<'_>;
```

### `NINE_LEVELS`
```rust
const NINE_LEVELS: Set<'_>;
```

