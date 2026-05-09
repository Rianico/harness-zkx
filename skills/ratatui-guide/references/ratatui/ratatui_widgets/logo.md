*[ratatui_widgets](./index.md) / [logo](#)*

---

# Module `logo`

The [`RatatuiLogo`](#ratatuilogo) widget renders the Ratatui logo.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`RatatuiLogo`](#ratatuilogo) | struct | A widget that renders the Ratatui logo |
| [`Size`](#size) | enum | The size of the logo |

## Structs

### `RatatuiLogo`

```rust
struct RatatuiLogo {
    // [REDACTED: Private Fields]
}
```

A widget that renders the Ratatui logo

The Ratatui logo takes up two lines of text and comes in two sizes: `Tiny` and `Small`. This may
be used in an application's help or about screen to show that it is powered by Ratatui.

# Examples

The [Ratatui-logo] example demonstrates how to use the `RatatuiLogo` widget. This can be run by
cloning the Ratatui repository and then running the following command with an optional size
argument:

```shell
cargo run --example logo [size]
```

## Tiny (default, 2x15 characters)

```rust
use ratatui::widgets::RatatuiLogo;

fn draw(frame: &mut ratatui::Frame) {
frame.render_widget(RatatuiLogo::tiny(), frame.area());
}
```

Renders:

```text
▛▚▗▀▖▜▘▞▚▝▛▐ ▌▌
▛▚▐▀▌▐ ▛▜ ▌▝▄▘▌
```

## Small (2x27 characters)

```rust
use ratatui::widgets::RatatuiLogo;

fn draw(frame: &mut ratatui::Frame) {
frame.render_widget(RatatuiLogo::small(), frame.area());
}
```

Renders:

```text
█▀▀▄ ▄▀▀▄▝▜▛▘▄▀▀▄▝▜▛▘█  █ █
█▀▀▄ █▀▀█ ▐▌ █▀▀█ ▐▌ ▀▄▄▀ █
```

#### Implementations

- `const fn new(size: Size) -> Self` — [`Size`](#size)

  Create a new Ratatui logo widget

  

  # Examples

  

  ```rust

  use ratatui::widgets::{RatatuiLogo, RatatuiLogoSize};

  

  let logo = RatatuiLogo::new(RatatuiLogoSize::Tiny);

  ```

- `const fn size(self, size: Size) -> Self` — [`Size`](#size)

  Set the size of the logo

  

  # Examples

  

  ```rust

  use ratatui::widgets::{RatatuiLogo, RatatuiLogoSize};

  

  let logo = RatatuiLogo::default().size(RatatuiLogoSize::Small);

  ```

- `const fn tiny() -> Self`

  Create a new Ratatui logo widget with a tiny size

  

  # Examples

  

  ```rust

  use ratatui::widgets::RatatuiLogo;

  

  let logo = RatatuiLogo::tiny();

  ```

- `const fn small() -> Self`

  Create a new Ratatui logo widget with a small size

  

  # Examples

  

  ```rust

  use ratatui::widgets::RatatuiLogo;

  

  let logo = RatatuiLogo::small();

  ```

#### Trait Implementations

##### `impl AsRef for crate::logo::RatatuiLogo`

- `fn as_ref(&self) -> &crate::logo::RatatuiLogo` — [`RatatuiLogo`](#ratatuilogo)

##### `impl Clone for RatatuiLogo`

- `fn clone(&self) -> RatatuiLogo` — [`RatatuiLogo`](#ratatuilogo)

##### `impl Copy for RatatuiLogo`

##### `impl Debug for RatatuiLogo`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for RatatuiLogo`

- `fn default() -> RatatuiLogo` — [`RatatuiLogo`](#ratatuilogo)

##### `impl Eq for RatatuiLogo`

##### `impl<K> Equivalent for RatatuiLogo`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl IntoEither for RatatuiLogo`

##### `impl PartialEq for RatatuiLogo`

- `fn eq(&self, other: &RatatuiLogo) -> bool` — [`RatatuiLogo`](#ratatuilogo)

##### `impl StructuralPartialEq for RatatuiLogo`

##### `impl Widget for RatatuiLogo`

- `fn render(self, area: Rect, buf: &mut Buffer)`

## Enums

### `Size`

```rust
enum Size {
    Tiny,
    Small,
}
```

The size of the logo

#### Variants

- **`Tiny`**

  A tiny logo
  
  The default size of the logo (2x15 characters)
  
  ```text
  ▛▚▗▀▖▜▘▞▚▝▛▐ ▌▌
  ▛▚▐▀▌▐ ▛▜ ▌▝▄▘▌
  ```

- **`Small`**

  A small logo
  
  A slightly larger version of the logo (2x27 characters)
  
  ```text
  █▀▀▄ ▄▀▀▄▝▜▛▘▄▀▀▄▝▜▛▘█  █ █
  █▀▀▄ █▀▀█ ▐▌ █▀▀█ ▐▌ ▀▄▄▀ █
  ```

#### Trait Implementations

##### `impl Clone for Size`

- `fn clone(&self) -> Size` — [`Size`](#size)

##### `impl Copy for Size`

##### `impl Debug for Size`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Size`

- `fn default() -> Size` — [`Size`](#size)

##### `impl Eq for Size`

##### `impl<K> Equivalent for Size`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl IntoEither for Size`

##### `impl PartialEq for Size`

- `fn eq(&self, other: &Size) -> bool` — [`Size`](#size)

##### `impl StructuralPartialEq for Size`

