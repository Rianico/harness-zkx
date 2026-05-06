*[ratatui_widgets](../index.md) / [borders](index.md)*

---

# Module `borders`

Border related types ([`Borders`](#borders), [`BorderType`](#bordertype)) and a macro to create borders ([`border`](../../ratatui_core/symbols/border/index.md)).

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Borders`](#borders) | struct | Bitflags that can be composed to set the visible borders essentially on the block widget. |
| [`BorderType`](#bordertype) | enum | The type of border of a [`Block`](crate::block::Block). |

## Structs

### `Borders`

```rust
struct Borders();
```

Bitflags that can be composed to set the visible borders essentially on the block widget.

#### Implementations

- `const TOP: Self`

- `const RIGHT: Self`

- `const BOTTOM: Self`

- `const LEFT: Self`

- `const ALL: Self`

#### Trait Implementations

##### `impl Binary for Borders`

- `fn fmt(&self, f: &mut __private::core::fmt::Formatter<'_>) -> __private::core::fmt::Result`

##### `impl BitAnd for Borders`

- `type Output = Borders`

- `fn bitand(self, other: Self) -> Self`

  The bitwise and (`&`) of the bits in `self` and `other`.

##### `impl BitAndAssign for Borders`

- `fn bitand_assign(&mut self, other: Self)`

  The bitwise and (`&`) of the bits in `self` and `other`.

##### `impl BitOr for Borders`

- `type Output = Borders`

- `fn bitor(self, other: Borders) -> Self` — [`Borders`](#borders)

  The bitwise or (`|`) of the bits in `self` and `other`.

##### `impl BitOrAssign for Borders`

- `fn bitor_assign(&mut self, other: Self)`

  The bitwise or (`|`) of the bits in `self` and `other`.

##### `impl BitXor for Borders`

- `type Output = Borders`

- `fn bitxor(self, other: Self) -> Self`

  The bitwise exclusive-or (`^`) of the bits in `self` and `other`.

##### `impl BitXorAssign for Borders`

- `fn bitxor_assign(&mut self, other: Self)`

  The bitwise exclusive-or (`^`) of the bits in `self` and `other`.

##### `impl Clone for Borders`

- `fn clone(&self) -> Borders` — [`Borders`](#borders)

##### `impl Copy for Borders`

##### `impl Debug for Borders`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

  Display the Borders bitflags as a list of names.

  

  `Borders::NONE` is displayed as `NONE` and `Borders::ALL` is displayed as `ALL`. If multiple

  flags are set, they are otherwise displayed separated by a pipe character.

##### `impl Default for Borders`

- `fn default() -> Borders` — [`Borders`](#borders)

##### `impl Eq for Borders`

##### `impl<K> Equivalent for Borders`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Extend for Borders`

- `fn extend<T: __private::core::iter::IntoIterator<Item = Self>>(&mut self, iterator: T)`

  The bitwise or (`|`) of the bits in each flags value.

##### `impl Flags for Borders`

- `const FLAGS: &'static [Flag<Borders>]`

- `type Bits = u8`

- `fn bits(&self) -> u8`

- `fn from_bits_retain(bits: u8) -> Borders` — [`Borders`](#borders)

##### `impl FromIterator for Borders`

- `fn from_iter<T: __private::core::iter::IntoIterator<Item = Self>>(iterator: T) -> Self`

  The bitwise or (`|`) of the bits in each flags value.

##### `impl Hash for Borders`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Borders`

##### `impl IntoIterator for Borders`

- `type Item = Borders`

- `type IntoIter = Iter<Borders>`

- `fn into_iter(self) -> <Self as >::IntoIter`

##### `impl LowerHex for Borders`

- `fn fmt(&self, f: &mut __private::core::fmt::Formatter<'_>) -> __private::core::fmt::Result`

##### `impl Not for Borders`

- `type Output = Borders`

- `fn not(self) -> Self`

  The bitwise negation (`!`) of the bits in `self`, truncating the result.

##### `impl Octal for Borders`

- `fn fmt(&self, f: &mut __private::core::fmt::Formatter<'_>) -> __private::core::fmt::Result`

##### `impl PartialEq for Borders`

- `fn eq(&self, other: &Borders) -> bool` — [`Borders`](#borders)

##### `impl PublicFlags for Borders`

- `type Primitive = u8`

- `type Internal = InternalBitFlags`

##### `impl StructuralPartialEq for Borders`

##### `impl Sub for Borders`

- `type Output = Borders`

- `fn sub(self, other: Self) -> Self`

  The intersection of `self` with the complement of `other` (`&!`).

  

  This method is not equivalent to `self & !other` when `other` has unknown bits set.

  `difference` won't truncate `other`, but the `!` operator will.

##### `impl SubAssign for Borders`

- `fn sub_assign(&mut self, other: Self)`

  The intersection of `self` with the complement of `other` (`&!`).

  

  This method is not equivalent to `self & !other` when `other` has unknown bits set.

  `difference` won't truncate `other`, but the `!` operator will.

##### `impl UpperHex for Borders`

- `fn fmt(&self, f: &mut __private::core::fmt::Formatter<'_>) -> __private::core::fmt::Result`

## Enums

### `BorderType`

```rust
enum BorderType {
    Plain,
    Rounded,
    Double,
    Thick,
    LightDoubleDashed,
    HeavyDoubleDashed,
    LightTripleDashed,
    HeavyTripleDashed,
    LightQuadrupleDashed,
    HeavyQuadrupleDashed,
    QuadrantInside,
    QuadrantOutside,
}
```

The type of border of a [`Block`](crate::block::Block).

See the [`borders`](crate::block::Block::borders) method of `Block` to configure its borders.

#### Variants

- **`Plain`**

  A plain, simple border.
  
  This is the default
  
  # Example
  
  ```plain
  ┌───────┐
  │       │
  └───────┘
  ```

- **`Rounded`**

  A plain border with rounded corners.
  
  # Example
  
  ```plain
  ╭───────╮
  │       │
  ╰───────╯
  ```

- **`Double`**

  A doubled border.
  
  Note this uses one character that draws two lines.
  
  # Example
  
  ```plain
  ╔═══════╗
  ║       ║
  ╚═══════╝
  ```

- **`Thick`**

  A thick border.
  
  # Example
  
  ```plain
  ┏━━━━━━━┓
  ┃       ┃
  ┗━━━━━━━┛
  ```

- **`LightDoubleDashed`**

  A light double-dashed border.
  
  ```plain
  ┌╌╌╌╌╌╌╌┐
  ╎       ╎
  └╌╌╌╌╌╌╌┘
  ```

- **`HeavyDoubleDashed`**

  A heavy double-dashed border.
  
  ```plain
  ┏╍╍╍╍╍╍╍┓
  ╏       ╏
  ┗╍╍╍╍╍╍╍┛
  ```

- **`LightTripleDashed`**

  A light triple-dashed border.
  
  ```plain
  ┌┄┄┄┄┄┄┄┐
  ┆       ┆
  └┄┄┄┄┄┄┄┘
  ```

- **`HeavyTripleDashed`**

  A heavy triple-dashed border.
  
  ```plain
  ┏┅┅┅┅┅┅┅┓
  ┇       ┇
  ┗┅┅┅┅┅┅┅┛
  ```

- **`LightQuadrupleDashed`**

  A light quadruple-dashed border.
  
  ```plain
  ┌┈┈┈┈┈┈┈┐
  ┊       ┊
  └┈┈┈┈┈┈┈┘
  ```

- **`HeavyQuadrupleDashed`**

  A heavy quadruple-dashed border.
  
  ```plain
  ┏┉┉┉┉┉┉┉┓
  ┋       ┋
  ┗┉┉┉┉┉┉┉┛
  ```

- **`QuadrantInside`**

  A border with a single line on the inside of a half block.
  
  # Example
  
  ```plain
  ▗▄▄▄▄▄▄▄▖
  ▐       ▌
  ▐       ▌
  ▝▀▀▀▀▀▀▀▘

- **`QuadrantOutside`**

  A border with a single line on the outside of a half block.
  
  # Example
  
  ```plain
  ▛▀▀▀▀▀▀▀▜
  ▌       ▐
  ▌       ▐
  ▙▄▄▄▄▄▄▄▟

#### Implementations

- `const fn border_symbols<'a>(border_type: Self) -> border::Set<'a>`

  Convert this `BorderType` into the corresponding [`Set`](border::Set) of border symbols.

- `const fn to_border_set<'a>(self) -> border::Set<'a>`

  Convert this `BorderType` into the corresponding [`Set`](border::Set) of border symbols.

#### Trait Implementations

##### `impl Clone for BorderType`

- `fn clone(&self) -> BorderType` — [`BorderType`](#bordertype)

##### `impl Copy for BorderType`

##### `impl Debug for BorderType`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for BorderType`

- `fn default() -> BorderType` — [`BorderType`](#bordertype)

##### `impl Display for BorderType`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for BorderType`

##### `impl<K> Equivalent for BorderType`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for BorderType`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<BorderType, <Self as ::core::str::FromStr>::Err>` — [`BorderType`](#bordertype)

##### `impl Hash for BorderType`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for BorderType`

##### `impl PartialEq for BorderType`

- `fn eq(&self, other: &BorderType) -> bool` — [`BorderType`](#bordertype)

##### `impl StructuralPartialEq for BorderType`

##### `impl ToCompactString for BorderType`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for BorderType`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for BorderType`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for BorderType`

- `fn to_string(&self) -> String`

##### `impl ToText for BorderType`

- `fn to_text(&self) -> Text<'_>`

