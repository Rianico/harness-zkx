*[ratatui_core](../../../index.md) / [style](../../index.md) / [palette](../index.md) / [material](index.md)*

---

# Module `material`

Material design color palettes.

Represents the colors from the 2014 [Material design color palettes][palettes] by Google.

There are 16 palettes with accent colors, and 3 palettes without accent colors. Each palette
has 10 colors, with variants from 50 to 900. The accent palettes also have 4 accent colors
with variants from 100 to 700. Black and White are also included for completeness and to avoid
being affected by any terminal theme that might be in use.

This module exists to provide a convenient way to use the colors from the
[`matdesign-color` crate] in your application.

<style>
.color { display: flex; align-items: center; }
.color > div { width: 2rem; height: 2rem; }
.color > div.name { width: 150px; !important; }
</style>
<div style="overflow-x: auto">
<div style="display: flex; flex-direction:column; text-align: left">
<div class="color" style="font-size:0.8em">
    <div class="name"></div>
    <div>C50</div>
    <div>C100</div>
    <div>C200</div>
    <div>C300</div>
    <div>C400</div>
    <div>C500</div>
    <div>C600</div>
    <div>C700</div>
    <div>C800</div>
    <div>C900</div>
    <div>A100</div>
    <div>A200</div>
    <div>A400</div>
    <div>A700</div>
</div>
<div class="color">
    <div class="name">

[`RED`](#red)</div>
    <div style="background-color: #FFEBEE"></div>
    <div style="background-color: #FFCDD2"></div>
    <div style="background-color: #EF9A9A"></div>
    <div style="background-color: #E57373"></div>
    <div style="background-color: #EF5350"></div>
    <div style="background-color: #F44336"></div>
    <div style="background-color: #E53935"></div>
    <div style="background-color: #D32F2F"></div>
    <div style="background-color: #C62828"></div>
    <div style="background-color: #B71C1C"></div>
    <div style="background-color: #FF8A80"></div>
    <div style="background-color: #FF5252"></div>
    <div style="background-color: #FF1744"></div>
    <div style="background-color: #D50000"></div>
</div>
<div class="color">
    <div class="name">

[`PINK`](#pink)</div>
    <div style="background-color: #FCE4EC"></div>
    <div style="background-color: #F8BBD0"></div>
    <div style="background-color: #F48FB1"></div>
    <div style="background-color: #F06292"></div>
    <div style="background-color: #EC407A"></div>
    <div style="background-color: #E91E63"></div>
    <div style="background-color: #D81B60"></div>
    <div style="background-color: #C2185B"></div>
    <div style="background-color: #AD1457"></div>
    <div style="background-color: #880E4F"></div>
    <div style="background-color: #FF80AB"></div>
    <div style="background-color: #FF4081"></div>
    <div style="background-color: #F50057"></div>
    <div style="background-color: #C51162"></div>
</div>
<div class="color">
    <div class="name">

[`PURPLE`](#purple)</div>
    <div style="background-color: #F3E5F5"></div>
    <div style="background-color: #E1BEE7"></div>
    <div style="background-color: #CE93D8"></div>
    <div style="background-color: #BA68C8"></div>
    <div style="background-color: #AB47BC"></div>
    <div style="background-color: #9C27B0"></div>
    <div style="background-color: #8E24AA"></div>
    <div style="background-color: #7B1FA2"></div>
    <div style="background-color: #6A1B9A"></div>
    <div style="background-color: #4A148C"></div>
    <div style="background-color: #EA80FC"></div>
    <div style="background-color: #E040FB"></div>
    <div style="background-color: #D500F9"></div>
    <div style="background-color: #AA00FF"></div>
</div>
<div class="color">
    <div class="name">

[`DEEP_PURPLE`](#deep-purple)</div>
    <div style="background-color: #EDE7F6"></div>
    <div style="background-color: #D1C4E9"></div>
    <div style="background-color: #B39DDB"></div>
    <div style="background-color: #9575CD"></div>
    <div style="background-color: #7E57C2"></div>
    <div style="background-color: #673AB7"></div>
    <div style="background-color: #5E35B1"></div>
    <div style="background-color: #512DA8"></div>
    <div style="background-color: #4527A0"></div>
    <div style="background-color: #311B92"></div>
    <div style="background-color: #B388FF"></div>
    <div style="background-color: #7C4DFF"></div>
    <div style="background-color: #651FFF"></div>
    <div style="background-color: #6200EA"></div>
</div>
<div class="color">
    <div class="name">

[`INDIGO`](#indigo)</div>
    <div style="background-color: #E8EAF6"></div>
    <div style="background-color: #C5CAE9"></div>
    <div style="background-color: #9FA8DA"></div>
    <div style="background-color: #7986CB"></div>
    <div style="background-color: #5C6BC0"></div>
    <div style="background-color: #3F51B5"></div>
    <div style="background-color: #3949AB"></div>
    <div style="background-color: #303F9F"></div>
    <div style="background-color: #283593"></div>
    <div style="background-color: #1A237E"></div>
    <div style="background-color: #8C9EFF"></div>
    <div style="background-color: #536DFE"></div>
    <div style="background-color: #3D5AFE"></div>
    <div style="background-color: #304FFE"></div>
</div>
<div class="color">
    <div class="name">

[`BLUE`](#blue)</div>
    <div style="background-color: #E3F2FD"></div>
    <div style="background-color: #BBDEFB"></div>
    <div style="background-color: #90CAF9"></div>
    <div style="background-color: #64B5F6"></div>
    <div style="background-color: #42A5F5"></div>
    <div style="background-color: #2196F3"></div>
    <div style="background-color: #1E88E5"></div>
    <div style="background-color: #1976D2"></div>
    <div style="background-color: #1565C0"></div>
    <div style="background-color: #0D47A1"></div>
    <div style="background-color: #82B1FF"></div>
    <div style="background-color: #448AFF"></div>
    <div style="background-color: #2979FF"></div>
    <div style="background-color: #2962FF"></div>
</div>
<div class="color">
    <div class="name">

[`LIGHT_BLUE`](#light-blue)</div>
    <div style="background-color: #E1F5FE"></div>
    <div style="background-color: #B3E5FC"></div>
    <div style="background-color: #81D4FA"></div>
    <div style="background-color: #4FC3F7"></div>
    <div style="background-color: #29B6F6"></div>
    <div style="background-color: #03A9F4"></div>
    <div style="background-color: #039BE5"></div>
    <div style="background-color: #0288D1"></div>
    <div style="background-color: #0277BD"></div>
    <div style="background-color: #01579B"></div>
    <div style="background-color: #80D8FF"></div>
    <div style="background-color: #40C4FF"></div>
    <div style="background-color: #00B0FF"></div>
    <div style="background-color: #0091EA"></div>
</div>
<div class="color">
    <div class="name">

[`CYAN`](#cyan)</div>
    <div style="background-color: #E0F7FA"></div>
    <div style="background-color: #B2EBF2"></div>
    <div style="background-color: #80DEEA"></div>
    <div style="background-color: #4DD0E1"></div>
    <div style="background-color: #26C6DA"></div>
    <div style="background-color: #00BCD4"></div>
    <div style="background-color: #00ACC1"></div>
    <div style="background-color: #0097A7"></div>
    <div style="background-color: #00838F"></div>
    <div style="background-color: #006064"></div>
    <div style="background-color: #84FFFF"></div>
    <div style="background-color: #18FFFF"></div>
    <div style="background-color: #00E5FF"></div>
    <div style="background-color: #00B8D4"></div>
</div>
<div class="color">
    <div class="name">

[`TEAL`](#teal)</div>
    <div style="background-color: #E0F2F1"></div>
    <div style="background-color: #B2DFDB"></div>
    <div style="background-color: #80CBC4"></div>
    <div style="background-color: #4DB6AC"></div>
    <div style="background-color: #26A69A"></div>
    <div style="background-color: #009688"></div>
    <div style="background-color: #00897B"></div>
    <div style="background-color: #00796B"></div>
    <div style="background-color: #00695C"></div>
    <div style="background-color: #004D40"></div>
    <div style="background-color: #A7FFEB"></div>
    <div style="background-color: #64FFDA"></div>
    <div style="background-color: #1DE9B6"></div>
    <div style="background-color: #00BFA5"></div>
</div>
<div class="color">
    <div class="name">

[`GREEN`](#green)</div>
    <div style="background-color: #E8F5E9"></div>
    <div style="background-color: #C8E6C9"></div>
    <div style="background-color: #A5D6A7"></div>
    <div style="background-color: #81C784"></div>
    <div style="background-color: #66BB6A"></div>
    <div style="background-color: #4CAF50"></div>
    <div style="background-color: #43A047"></div>
    <div style="background-color: #388E3C"></div>
    <div style="background-color: #2E7D32"></div>
    <div style="background-color: #1B5E20"></div>
    <div style="background-color: #B9F6CA"></div>
    <div style="background-color: #69F0AE"></div>
    <div style="background-color: #00E676"></div>
    <div style="background-color: #00C853"></div>
</div>
<div class="color">
    <div class="name">

[`LIGHT_GREEN`](#light-green)</div>
    <div style="background-color: #F1F8E9"></div>
    <div style="background-color: #DCEDC8"></div>
    <div style="background-color: #C5E1A5"></div>
    <div style="background-color: #AED581"></div>
    <div style="background-color: #9CCC65"></div>
    <div style="background-color: #8BC34A"></div>
    <div style="background-color: #7CB342"></div>
    <div style="background-color: #689F38"></div>
    <div style="background-color: #558B2F"></div>
    <div style="background-color: #33691E"></div>
    <div style="background-color: #CCFF90"></div>
    <div style="background-color: #B2FF59"></div>
    <div style="background-color: #76FF03"></div>
    <div style="background-color: #64DD17"></div>
</div>
<div class="color">
    <div class="name">

[`LIME`](#lime)</div>
    <div style="background-color: #F9FBE7"></div>
    <div style="background-color: #F0F4C3"></div>
    <div style="background-color: #E6EE9C"></div>
    <div style="background-color: #DCE775"></div>
    <div style="background-color: #D4E157"></div>
    <div style="background-color: #CDDC39"></div>
    <div style="background-color: #C0CA33"></div>
    <div style="background-color: #AFB42B"></div>
    <div style="background-color: #9E9D24"></div>
    <div style="background-color: #827717"></div>
    <div style="background-color: #F4FF81"></div>
    <div style="background-color: #EEFF41"></div>
    <div style="background-color: #C6FF00"></div>
    <div style="background-color: #AEEA00"></div>
</div>
<div class="color">
    <div class="name">

[`YELLOW`](#yellow)</div>
    <div style="background-color: #FFFDE7"></div>
    <div style="background-color: #FFF9C4"></div>
    <div style="background-color: #FFF59D"></div>
    <div style="background-color: #FFF176"></div>
    <div style="background-color: #FFEE58"></div>
    <div style="background-color: #FFEB3B"></div>
    <div style="background-color: #FDD835"></div>
    <div style="background-color: #FBC02D"></div>
    <div style="background-color: #F9A825"></div>
    <div style="background-color: #F57F17"></div>
    <div style="background-color: #FFFF8D"></div>
    <div style="background-color: #FFFF00"></div>
    <div style="background-color: #FFEA00"></div>
    <div style="background-color: #FFD600"></div>
</div>
<div class="color">
    <div class="name">

[`AMBER`](#amber)</div>
    <div style="background-color: #FFF8E1"></div>
    <div style="background-color: #FFECB3"></div>
    <div style="background-color: #FFE082"></div>
    <div style="background-color: #FFD54F"></div>
    <div style="background-color: #FFCA28"></div>
    <div style="background-color: #FFC107"></div>
    <div style="background-color: #FFB300"></div>
    <div style="background-color: #FFA000"></div>
    <div style="background-color: #FF8F00"></div>
    <div style="background-color: #FF6F00"></div>
    <div style="background-color: #FFE57F"></div>
    <div style="background-color: #FFD740"></div>
    <div style="background-color: #FFC400"></div>
    <div style="background-color: #FFAB00"></div>
</div>
<div class="color">
    <div class="name">

[`ORANGE`](#orange)</div>
    <div style="background-color: #FFF3E0"></div>
    <div style="background-color: #FFE0B2"></div>
    <div style="background-color: #FFCC80"></div>
    <div style="background-color: #FFB74D"></div>
    <div style="background-color: #FFA726"></div>
    <div style="background-color: #FF9800"></div>
    <div style="background-color: #FB8C00"></div>
    <div style="background-color: #F57C00"></div>
    <div style="background-color: #EF6C00"></div>
    <div style="background-color: #E65100"></div>
    <div style="background-color: #FFD180"></div>
    <div style="background-color: #FFAB40"></div>
    <div style="background-color: #FF9100"></div>
    <div style="background-color: #FF6D00"></div>
</div>
<div class="color">
    <div class="name">

[`DEEP_ORANGE`](#deep-orange)</div>
    <div style="background-color: #FBE9E7"></div>
    <div style="background-color: #FFCCBC"></div>
    <div style="background-color: #FFAB91"></div>
    <div style="background-color: #FF8A65"></div>
    <div style="background-color: #FF7043"></div>
    <div style="background-color: #FF5722"></div>
    <div style="background-color: #F4511E"></div>
    <div style="background-color: #E64A19"></div>
    <div style="background-color: #D84315"></div>
    <div style="background-color: #BF360C"></div>
    <div style="background-color: #FF9E80"></div>
    <div style="background-color: #FF6E40"></div>
    <div style="background-color: #FF3D00"></div>
    <div style="background-color: #DD2C00"></div>
</div>
<div class="color">
    <div class="name">

[`BROWN`](#brown)</div>
    <div style="background-color: #EFEBE9"></div>
    <div style="background-color: #D7CCC8"></div>
    <div style="background-color: #BCAAA4"></div>
    <div style="background-color: #A1887F"></div>
    <div style="background-color: #8D6E63"></div>
    <div style="background-color: #795548"></div>
    <div style="background-color: #6D4C41"></div>
    <div style="background-color: #5D4037"></div>
    <div style="background-color: #4E342E"></div>
    <div style="background-color: #3E2723"></div>
</div>
<div class="color">
    <div class="name">

[`GRAY`](#gray)</div>
    <div style="background-color: #FAFAFA"></div>
    <div style="background-color: #F5F5F5"></div>
    <div style="background-color: #EEEEEE"></div>
    <div style="background-color: #E0E0E0"></div>
    <div style="background-color: #BDBDBD"></div>
    <div style="background-color: #9E9E9E"></div>
    <div style="background-color: #757575"></div>
    <div style="background-color: #616161"></div>
    <div style="background-color: #424242"></div>
    <div style="background-color: #212121"></div>
</div>
<div class="color">
    <div class="name">

[`BLUE_GRAY`](#blue-gray)</div>
    <div style="background-color: #ECEFF1"></div>
    <div style="background-color: #CFD8DC"></div>
    <div style="background-color: #B0BEC5"></div>
    <div style="background-color: #90A4AE"></div>
    <div style="background-color: #78909C"></div>
    <div style="background-color: #607D8B"></div>
    <div style="background-color: #546E7A"></div>
    <div style="background-color: #455A64"></div>
    <div style="background-color: #37474F"></div>
    <div style="background-color: #263238"></div>
</div>
<div class="color">
    <div class="name">

[`BLACK`](#black)</div>
    <div class="bw" style="width: 350px; background-color: #000000"></div>
</div>
<div class="color">
    <div class="name">

[`WHITE`](#white)</div>
    <div style="width: 350px; background-color: #FFFFFF"></div>
</div>
</div>
</div>

# Example

```rust
use ratatui_core::style::Color;
use ratatui_core::style::palette::material::{BLUE, RED};

assert_eq!(RED.c500, Color::Rgb(244, 67, 54));
assert_eq!(BLUE.c500, Color::Rgb(33, 150, 243));
```

## Contents

- [Structs](#structs)
  - [`AccentedPalette`](#accentedpalette)
  - [`NonAccentedPalette`](#nonaccentedpalette)
- [Constants](#constants)
  - [`RED`](#red)
  - [`PINK`](#pink)
  - [`PURPLE`](#purple)
  - [`DEEP_PURPLE`](#deep-purple)
  - [`INDIGO`](#indigo)
  - [`BLUE`](#blue)
  - [`LIGHT_BLUE`](#light-blue)
  - [`CYAN`](#cyan)
  - [`TEAL`](#teal)
  - [`GREEN`](#green)
  - [`LIGHT_GREEN`](#light-green)
  - [`LIME`](#lime)
  - [`YELLOW`](#yellow)
  - [`AMBER`](#amber)
  - [`ORANGE`](#orange)
  - [`DEEP_ORANGE`](#deep-orange)
  - [`BROWN`](#brown)
  - [`GRAY`](#gray)
  - [`BLUE_GRAY`](#blue-gray)
  - [`BLACK`](#black)
  - [`WHITE`](#white)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`AccentedPalette`](#accentedpalette) | struct | A palette of colors for use in Material design with accent colors |
| [`NonAccentedPalette`](#nonaccentedpalette) | struct | A palette of colors for use in Material design without accent colors |
| [`RED`](#red) | const |  |
| [`PINK`](#pink) | const |  |
| [`PURPLE`](#purple) | const |  |
| [`DEEP_PURPLE`](#deep-purple) | const |  |
| [`INDIGO`](#indigo) | const |  |
| [`BLUE`](#blue) | const |  |
| [`LIGHT_BLUE`](#light-blue) | const |  |
| [`CYAN`](#cyan) | const |  |
| [`TEAL`](#teal) | const |  |
| [`GREEN`](#green) | const |  |
| [`LIGHT_GREEN`](#light-green) | const |  |
| [`LIME`](#lime) | const |  |
| [`YELLOW`](#yellow) | const |  |
| [`AMBER`](#amber) | const |  |
| [`ORANGE`](#orange) | const |  |
| [`DEEP_ORANGE`](#deep-orange) | const |  |
| [`BROWN`](#brown) | const |  |
| [`GRAY`](#gray) | const |  |
| [`BLUE_GRAY`](#blue-gray) | const |  |
| [`BLACK`](#black) | const |  |
| [`WHITE`](#white) | const |  |

## Structs

### `AccentedPalette`

```rust
struct AccentedPalette {
    pub c50: crate::style::Color,
    pub c100: crate::style::Color,
    pub c200: crate::style::Color,
    pub c300: crate::style::Color,
    pub c400: crate::style::Color,
    pub c500: crate::style::Color,
    pub c600: crate::style::Color,
    pub c700: crate::style::Color,
    pub c800: crate::style::Color,
    pub c900: crate::style::Color,
    pub a100: crate::style::Color,
    pub a200: crate::style::Color,
    pub a400: crate::style::Color,
    pub a700: crate::style::Color,
}
```

A palette of colors for use in Material design with accent colors

This is a collection of colors that are used in Material design. They consist of a set of
colors from 50 to 900, and a set of accent colors from 100 to 700.

#### Implementations

- `const fn from_variants(variants: [u32; 14]) -> Self`

  Create a new `AccentedPalette` from the given variants

  

  The variants should be in the format [0x00RRGGBB, ...]

#### Trait Implementations

##### `impl Clone for AccentedPalette`

- `fn clone(&self) -> AccentedPalette` — [`AccentedPalette`](#accentedpalette)

##### `impl Copy for AccentedPalette`

##### `impl Debug for AccentedPalette`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for AccentedPalette`

##### `impl<K> Equivalent for AccentedPalette`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for AccentedPalette`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for AccentedPalette`

##### `impl PartialEq for AccentedPalette`

- `fn eq(&self, other: &AccentedPalette) -> bool` — [`AccentedPalette`](#accentedpalette)

##### `impl StructuralPartialEq for AccentedPalette`

### `NonAccentedPalette`

```rust
struct NonAccentedPalette {
    pub c50: crate::style::Color,
    pub c100: crate::style::Color,
    pub c200: crate::style::Color,
    pub c300: crate::style::Color,
    pub c400: crate::style::Color,
    pub c500: crate::style::Color,
    pub c600: crate::style::Color,
    pub c700: crate::style::Color,
    pub c800: crate::style::Color,
    pub c900: crate::style::Color,
}
```

A palette of colors for use in Material design without accent colors

This is a collection of colors that are used in Material design. They consist of a set of
colors from 50 to 900.

#### Implementations

- `const fn from_variants(variants: [u32; 10]) -> Self`

  Create a new `NonAccented` from the given variants

  

  The variants should be in the format [0x00RRGGBB, ...]

#### Trait Implementations

##### `impl Clone for NonAccentedPalette`

- `fn clone(&self) -> NonAccentedPalette` — [`NonAccentedPalette`](#nonaccentedpalette)

##### `impl Copy for NonAccentedPalette`

##### `impl Debug for NonAccentedPalette`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for NonAccentedPalette`

##### `impl<K> Equivalent for NonAccentedPalette`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for NonAccentedPalette`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for NonAccentedPalette`

##### `impl PartialEq for NonAccentedPalette`

- `fn eq(&self, other: &NonAccentedPalette) -> bool` — [`NonAccentedPalette`](#nonaccentedpalette)

##### `impl StructuralPartialEq for NonAccentedPalette`

## Constants

### `RED`
```rust
const RED: AccentedPalette;
```

### `PINK`
```rust
const PINK: AccentedPalette;
```

### `PURPLE`
```rust
const PURPLE: AccentedPalette;
```

### `DEEP_PURPLE`
```rust
const DEEP_PURPLE: AccentedPalette;
```

### `INDIGO`
```rust
const INDIGO: AccentedPalette;
```

### `BLUE`
```rust
const BLUE: AccentedPalette;
```

### `LIGHT_BLUE`
```rust
const LIGHT_BLUE: AccentedPalette;
```

### `CYAN`
```rust
const CYAN: AccentedPalette;
```

### `TEAL`
```rust
const TEAL: AccentedPalette;
```

### `GREEN`
```rust
const GREEN: AccentedPalette;
```

### `LIGHT_GREEN`
```rust
const LIGHT_GREEN: AccentedPalette;
```

### `LIME`
```rust
const LIME: AccentedPalette;
```

### `YELLOW`
```rust
const YELLOW: AccentedPalette;
```

### `AMBER`
```rust
const AMBER: AccentedPalette;
```

### `ORANGE`
```rust
const ORANGE: AccentedPalette;
```

### `DEEP_ORANGE`
```rust
const DEEP_ORANGE: AccentedPalette;
```

### `BROWN`
```rust
const BROWN: NonAccentedPalette;
```

### `GRAY`
```rust
const GRAY: NonAccentedPalette;
```

### `BLUE_GRAY`
```rust
const BLUE_GRAY: NonAccentedPalette;
```

### `BLACK`
```rust
const BLACK: crate::style::Color;
```

### `WHITE`
```rust
const WHITE: crate::style::Color;
```

