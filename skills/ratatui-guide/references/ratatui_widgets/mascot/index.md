*[ratatui_widgets](../index.md) / [mascot](index.md)*

---

# Module `mascot`

A Ratatui mascot widget

The mascot takes 32x16 cells and is rendered using half block characters.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`RatatuiMascot`](#ratatuimascot) | struct | A widget that renders the Ratatui mascot |
| [`MascotEyeColor`](#mascoteyecolor) | enum | State for the mascot's eye |

## Structs

### `RatatuiMascot`

```rust
struct RatatuiMascot {
    // [REDACTED: Private Fields]
}
```

A widget that renders the Ratatui mascot

#### Implementations

- `fn new() -> Self`

  Create a new Ratatui mascot widget

- `const fn set_eye(self, rat_eye: MascotEyeColor) -> Self` — [`MascotEyeColor`](#mascoteyecolor)

  Set the eye state (open / blinking)

#### Trait Implementations

##### `impl AsRef for crate::mascot::RatatuiMascot`

- `fn as_ref(&self) -> &crate::mascot::RatatuiMascot` — [`RatatuiMascot`](#ratatuimascot)

##### `impl Clone for RatatuiMascot`

- `fn clone(&self) -> RatatuiMascot` — [`RatatuiMascot`](#ratatuimascot)

##### `impl Copy for RatatuiMascot`

##### `impl Debug for RatatuiMascot`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for RatatuiMascot`

- `fn default() -> Self`

##### `impl Eq for RatatuiMascot`

##### `impl<K> Equivalent for RatatuiMascot`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl IntoEither for RatatuiMascot`

##### `impl PartialEq for RatatuiMascot`

- `fn eq(&self, other: &RatatuiMascot) -> bool` — [`RatatuiMascot`](#ratatuimascot)

##### `impl StructuralPartialEq for RatatuiMascot`

##### `impl Widget for RatatuiMascot`

- `fn render(self, area: Rect, buf: &mut Buffer)`

  Use half block characters to render a logo based on the `RATATUI_LOGO` const.

  

  The logo colors are hardcorded in the widget.

  The eye color depends on whether it's open / blinking

## Enums

### `MascotEyeColor`

```rust
enum MascotEyeColor {
    Default,
    Red,
}
```

State for the mascot's eye

#### Variants

- **`Default`**

  The default eye color

- **`Red`**

  The red eye color

#### Trait Implementations

##### `impl Clone for MascotEyeColor`

- `fn clone(&self) -> MascotEyeColor` — [`MascotEyeColor`](#mascoteyecolor)

##### `impl Copy for MascotEyeColor`

##### `impl Debug for MascotEyeColor`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for MascotEyeColor`

- `fn default() -> MascotEyeColor` — [`MascotEyeColor`](#mascoteyecolor)

##### `impl Eq for MascotEyeColor`

##### `impl<K> Equivalent for MascotEyeColor`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl IntoEither for MascotEyeColor`

##### `impl PartialEq for MascotEyeColor`

- `fn eq(&self, other: &MascotEyeColor) -> bool` — [`MascotEyeColor`](#mascoteyecolor)

##### `impl StructuralPartialEq for MascotEyeColor`

