*[ratatui_core](../index.md) / [symbols](../index.md) / [marker](#)*

---

# Module `marker`

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Marker`](#marker) | enum | Marker to use when plotting data points |
| [`DOT`](#dot) | const |  |

## Enums

### `Marker`

```rust
enum Marker {
    Dot,
    Block,
    Bar,
    Braille,
    HalfBlock,
    Quadrant,
    Sextant,
    Octant,
    Custom(char),
}
```

Marker to use when plotting data points

#### Variants

- **`Dot`**

  One point per cell in shape of dot (`•`)

- **`Block`**

  One point per cell in shape of a block (`█`)

- **`Bar`**

  One point per cell in the shape of a bar (`▄`)

- **`Braille`**

  Use the [Unicode Braille Patterns](https://en.wikipedia.org/wiki/Braille_Patterns) block to
  represent data points.
  
  This is a 2x4 grid of dots, where each dot can be either on or off.
  
  Note: Support for this marker is limited to terminals and fonts that support Unicode
  Braille Patterns. If your terminal does not support this, you will see unicode replacement
  characters (`�`) instead of Braille dots (`⠓`, `⣇`, `⣿`).

- **`HalfBlock`**

  Use the unicode block and half block characters (`█`, `▄`, and `▀`) to represent points in
  a grid that is double the resolution of the terminal. Because each terminal cell is
  generally about twice as tall as it is wide, this allows for a square grid of pixels.

- **`Quadrant`**

  Use quadrant characters to represent data points.
  
  Quadrant characters display densely packed and regularly spaced pseudo-pixels with a 2x2
  resolution per character, without visible bands between cells.

- **`Sextant`**

  Use sextant characters from the [Unicode Symbols for Legacy Computing
  Supplement](https://en.wikipedia.org/wiki/Symbols_for_Legacy_Computing_Supplement) to
  represent data points.
  
  Sextant characters display densely packed and regularly spaced pseudo-pixels with a 2x3
  resolution per character, without visible bands between cells.
  
  Note: the Symbols for Legacy Computing Supplement block is a relatively recent addition to
  unicode that is less broadly supported than Braille dots. If your terminal does not support
  this, you will see unicode replacement characters (`�`) instead of sextants (`🬌`, `🬲`, `🬑`).

- **`Octant`**

  Use octant characters from the [Unicode Symbols for Legacy Computing
  Supplement](https://en.wikipedia.org/wiki/Symbols_for_Legacy_Computing_Supplement) to
  represent data points.
  
  Octant characters have the same 2x4 resolution as Braille characters but display densely
  packed and regularly spaced pseudo-pixels, without visible bands between cells.
  
  Note: the Symbols for Legacy Computing Supplement block is a relatively recent addition to
  unicode that is less broadly supported than Braille dots. If your terminal does not support
  this, you will see unicode replacement characters (`�`) instead of octants (`𜴇`, `𜷀`, `𜴷`).

- **`Custom`**

  Custom marker where the supplied char is applied once per cell

#### Trait Implementations

##### `impl Clone for Marker`

- `fn clone(&self) -> Marker` — [`Marker`](#marker)

##### `impl Copy for Marker`

##### `impl Debug for Marker`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Marker`

- `fn default() -> Marker` — [`Marker`](#marker)

##### `impl Display for Marker`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for Marker`

##### `impl<K> Equivalent for Marker`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for Marker`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<Marker, <Self as ::core::str::FromStr>::Err>` — [`Marker`](#marker)

##### `impl Hash for Marker`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Marker`

##### `impl PartialEq for Marker`

- `fn eq(&self, other: &Marker) -> bool` — [`Marker`](#marker)

##### `impl StructuralPartialEq for Marker`

##### `impl ToCompactString for Marker`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Marker`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Marker`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Marker`

- `fn to_string(&self) -> String`

##### `impl ToText for Marker`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

## Constants

### `DOT`
```rust
const DOT: &str;
```

