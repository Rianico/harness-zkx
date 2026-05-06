*[ratatui_core](../index.md) / [style](index.md)*

---

# Module `style`

`style` contains the primitives used to control how your user interface will look.

There are two ways to set styles:
- Creating and using the [`Style`](#style) struct. (e.g. `Style::new().fg(Color::Red)`).
- Using style shorthands. (e.g. `"hello".red()`).

# Using the `Style` struct

This is the original approach to styling and likely the most common. This is useful when
creating style variables to reuse, however the shorthands are often more convenient and
readable for most use cases.

## Example

```rust
use ratatui_core::style::{Color, Modifier, Style};
use ratatui_core::text::Span;

let heading_style = Style::new()
    .fg(Color::Black)
    .bg(Color::Green)
    .add_modifier(Modifier::ITALIC | Modifier::BOLD);
let span = Span::styled("hello", heading_style);
```

# Using style shorthands

Originally Ratatui only had the ability to set styles using the `Style` struct. This is still
supported, but there are now shorthands for all the styles that can be set. These save you from
having to create a `Style` struct every time you want to set a style.

The shorthands are implemented in the [`Stylize`](../index.md) trait which is automatically implemented for
many types via the [`Styled`](../index.md) trait. This means that you can use the shorthands on any type
that implements [`Styled`](../index.md). E.g.:
- Strings and string slices when styled return a [`Span`](../index.md)
- [`Span`](../index.md)s can be styled again, which will merge the styles.
- Many widget types can be styled directly rather than calling their `style()` method.

See the [`Stylize`](../index.md) and [`Styled`](../index.md) traits for more information.

## Example

```rust
use ratatui_core::style::{Color, Modifier, Style, Stylize};
use ratatui_core::text::{Span, Text};

assert_eq!(
    "hello".red().on_blue().bold(),
    Span::styled(
        "hello",
        Style::default()
            .fg(Color::Red)
            .bg(Color::Blue)
            .add_modifier(Modifier::BOLD)
    )
);

assert_eq!(
    Text::from("hello").red().on_blue().bold(),
    Text::from("hello").style(
        Style::default()
            .fg(Color::Red)
            .bg(Color::Blue)
            .add_modifier(Modifier::BOLD)
    )
);
```

## Contents

- [Modules](#modules)
  - [`palette`](#palette)
- [Structs](#structs)
  - [`ParseColorError`](#parsecolorerror)
  - [`Modifier`](#modifier)
  - [`Style`](#style)
- [Enums](#enums)
  - [`Color`](#color)
- [Traits](#traits)
  - [`Styled`](#styled)
  - [`Stylize`](#stylize)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`palette`](#palette) | mod | A module for defining color palettes. |
| [`ParseColorError`](#parsecolorerror) | struct |  |
| [`Modifier`](#modifier) | struct | Modifier changes the way a piece of text is displayed. |
| [`Style`](#style) | struct | Style lets you control the main characteristics of the displayed elements. |
| [`Color`](#color) | enum |  |
| [`Styled`](#styled) | trait |  |
| [`Stylize`](#stylize) | trait |  |

## Modules

- [`palette`](palette/index.md) — A module for defining color palettes.

## Structs

### `ParseColorError`

```rust
struct ParseColorError;
```

Error type indicating a failure to parse a color string.

#### Trait Implementations

##### `impl Clone for ParseColorError`

- `fn clone(&self) -> ParseColorError` — [`ParseColorError`](../index.md#parsecolorerror)

##### `impl Copy for ParseColorError`

##### `impl Debug for ParseColorError`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Display for ParseColorError`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for ParseColorError`

##### `impl<K> Equivalent for ParseColorError`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Error for ParseColorError`

##### `impl Hash for ParseColorError`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ParseColorError`

##### `impl PartialEq for ParseColorError`

- `fn eq(&self, other: &ParseColorError) -> bool` — [`ParseColorError`](../index.md#parsecolorerror)

##### `impl StructuralPartialEq for ParseColorError`

##### `impl ToCompactString for ParseColorError`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for ParseColorError`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for ParseColorError`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for ParseColorError`

- `fn to_string(&self) -> String`

##### `impl ToText for ParseColorError`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

### `Modifier`

```rust
struct Modifier();
```

Modifier changes the way a piece of text is displayed.

They are bitflags so they can easily be composed.

`From<Modifier> for Style` is implemented so you can use `Modifier` anywhere that accepts
`Into<Style>`.

## Examples

```rust
use ratatui_core::style::Modifier;

let m = Modifier::BOLD | Modifier::ITALIC;
```

#### Implementations

- `const BOLD: Self`

- `const DIM: Self`

- `const ITALIC: Self`

- `const UNDERLINED: Self`

- `const SLOW_BLINK: Self`

- `const RAPID_BLINK: Self`

- `const REVERSED: Self`

- `const HIDDEN: Self`

- `const CROSSED_OUT: Self`

#### Trait Implementations

##### `impl Binary for Modifier`

- `fn fmt(&self, f: &mut __private::core::fmt::Formatter<'_>) -> __private::core::fmt::Result`

##### `impl BitAnd for Modifier`

- `type Output = Modifier`

- `fn bitand(self, other: Self) -> Self`

  The bitwise and (`&`) of the bits in `self` and `other`.

##### `impl BitAndAssign for Modifier`

- `fn bitand_assign(&mut self, other: Self)`

  The bitwise and (`&`) of the bits in `self` and `other`.

##### `impl BitOr for Modifier`

- `type Output = Modifier`

- `fn bitor(self, other: Modifier) -> Self` — [`Modifier`](#modifier)

  The bitwise or (`|`) of the bits in `self` and `other`.

##### `impl BitOrAssign for Modifier`

- `fn bitor_assign(&mut self, other: Self)`

  The bitwise or (`|`) of the bits in `self` and `other`.

##### `impl BitXor for Modifier`

- `type Output = Modifier`

- `fn bitxor(self, other: Self) -> Self`

  The bitwise exclusive-or (`^`) of the bits in `self` and `other`.

##### `impl BitXorAssign for Modifier`

- `fn bitxor_assign(&mut self, other: Self)`

  The bitwise exclusive-or (`^`) of the bits in `self` and `other`.

##### `impl Clone for Modifier`

- `fn clone(&self) -> Modifier` — [`Modifier`](#modifier)

##### `impl Copy for Modifier`

##### `impl Debug for Modifier`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

  Format the modifier as `NONE` if the modifier is empty or as a list of flags separated by

  `|` otherwise.

##### `impl Default for Modifier`

- `fn default() -> Modifier` — [`Modifier`](#modifier)

##### `impl Eq for Modifier`

##### `impl<K> Equivalent for Modifier`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Extend for Modifier`

- `fn extend<T: __private::core::iter::IntoIterator<Item = Self>>(&mut self, iterator: T)`

  The bitwise or (`|`) of the bits in each flags value.

##### `impl Flags for Modifier`

- `const FLAGS: &'static [Flag<Modifier>]`

- `type Bits = u16`

- `fn bits(&self) -> u16`

- `fn from_bits_retain(bits: u16) -> Modifier` — [`Modifier`](#modifier)

##### `impl FromCrossterm for ratatui_core::style::Modifier`

##### `impl FromIterator for Modifier`

- `fn from_iter<T: __private::core::iter::IntoIterator<Item = Self>>(iterator: T) -> Self`

  The bitwise or (`|`) of the bits in each flags value.

##### `impl FromTermwiz for ratatui_core::style::Modifier`

##### `impl Hash for Modifier`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Modifier`

##### `impl IntoIterator for Modifier`

- `type Item = Modifier`

- `type IntoIter = Iter<Modifier>`

- `fn into_iter(self) -> <Self as >::IntoIter`

##### `impl LowerHex for Modifier`

- `fn fmt(&self, f: &mut __private::core::fmt::Formatter<'_>) -> __private::core::fmt::Result`

##### `impl Not for Modifier`

- `type Output = Modifier`

- `fn not(self) -> Self`

  The bitwise negation (`!`) of the bits in `self`, truncating the result.

##### `impl Octal for Modifier`

- `fn fmt(&self, f: &mut __private::core::fmt::Formatter<'_>) -> __private::core::fmt::Result`

##### `impl PartialEq for Modifier`

- `fn eq(&self, other: &Modifier) -> bool` — [`Modifier`](#modifier)

##### `impl PublicFlags for Modifier`

- `type Primitive = u16`

- `type Internal = InternalBitFlags`

##### `impl StructuralPartialEq for Modifier`

##### `impl Sub for Modifier`

- `type Output = Modifier`

- `fn sub(self, other: Self) -> Self`

  The intersection of `self` with the complement of `other` (`&!`).

  

  This method is not equivalent to `self & !other` when `other` has unknown bits set.

  `difference` won't truncate `other`, but the `!` operator will.

##### `impl SubAssign for Modifier`

- `fn sub_assign(&mut self, other: Self)`

  The intersection of `self` with the complement of `other` (`&!`).

  

  This method is not equivalent to `self & !other` when `other` has unknown bits set.

  `difference` won't truncate `other`, but the `!` operator will.

##### `impl UpperHex for Modifier`

- `fn fmt(&self, f: &mut __private::core::fmt::Formatter<'_>) -> __private::core::fmt::Result`

### `Style`

```rust
struct Style {
    pub fg: Option<Color>,
    pub bg: Option<Color>,
    pub underline_color: Option<Color>,
    pub add_modifier: Modifier,
    pub sub_modifier: Modifier,
}
```

Style lets you control the main characteristics of the displayed elements.

```rust
use ratatui_core::style::{Color, Modifier, Style};

Style::default()
    .fg(Color::Black)
    .bg(Color::Green)
    .add_modifier(Modifier::ITALIC | Modifier::BOLD);
```

Styles can also be created with a [shorthand notation](crate::style#using-style-shorthands).

```rust
use ratatui_core::style::{Style, Stylize};

Style::new().black().on_green().italic().bold();
```

For more information about the style shorthands, see the [`Stylize`](../index.md) trait.

We implement conversions from [`Color`](../index.md) and [`Modifier`](#modifier) to [`Style`](#style) so you can use them
anywhere that accepts `Into<Style>`.

```rust
use ratatui_core::style::{Color, Modifier, Style};
use ratatui_core::text::Line;

Line::styled("hello", Style::new().fg(Color::Red));
// simplifies to
Line::styled("hello", Color::Red);

Line::styled("hello", Style::new().add_modifier(Modifier::BOLD));
// simplifies to
Line::styled("hello", Modifier::BOLD);
```

Styles represents an incremental change. If you apply the styles S1, S2, S3 to a cell of the
terminal buffer, the style of this cell will be the result of the merge of S1, S2 and S3, not
just S3.

```rust
use ratatui_core::buffer::Buffer;
use ratatui_core::layout::Rect;
use ratatui_core::style::{Color, Modifier, Style};

let styles = [
    Style::default()
        .fg(Color::Blue)
        .add_modifier(Modifier::BOLD | Modifier::ITALIC),
    Style::default()
        .bg(Color::Red)
        .add_modifier(Modifier::UNDERLINED),
    #[cfg(feature = "underline-color")]
    Style::default().underline_color(Color::Green),
    Style::default()
        .fg(Color::Yellow)
        .remove_modifier(Modifier::ITALIC),
];
let mut buffer = Buffer::empty(Rect::new(0, 0, 1, 1));
for style in &styles {
    buffer[(0, 0)].set_style(*style);
}
assert_eq!(
    Style {
        fg: Some(Color::Yellow),
        bg: Some(Color::Red),
        #[cfg(feature = "underline-color")]
        underline_color: Some(Color::Green),
        add_modifier: Modifier::BOLD | Modifier::UNDERLINED,
        sub_modifier: Modifier::empty(),
    },
    buffer[(0, 0)].style(),
);
```

The default implementation returns a `Style` that does not modify anything. If you wish to
reset all properties until that point use `Style::reset`.

```rust
use ratatui_core::buffer::Buffer;
use ratatui_core::layout::Rect;
use ratatui_core::style::{Color, Modifier, Style};

let styles = [
    Style::default()
        .fg(Color::Blue)
        .add_modifier(Modifier::BOLD | Modifier::ITALIC),
    Style::reset().fg(Color::Yellow),
];
let mut buffer = Buffer::empty(Rect::new(0, 0, 1, 1));
for style in &styles {
    buffer[(0, 0)].set_style(*style);
}
assert_eq!(
    Style {
        fg: Some(Color::Yellow),
        bg: Some(Color::Reset),
        #[cfg(feature = "underline-color")]
        underline_color: Some(Color::Reset),
        add_modifier: Modifier::empty(),
        sub_modifier: Modifier::empty(),
    },
    buffer[(0, 0)].style(),
);
```

#### Fields

- **`fg`**: `Option<Color>`

  The foreground color.

- **`bg`**: `Option<Color>`

  The background color.

- **`underline_color`**: `Option<Color>`

  The underline color.

- **`add_modifier`**: `Modifier`

  The modifiers to add.

- **`sub_modifier`**: `Modifier`

  The modifiers to remove.

#### Implementations

- `const fn new() -> Self`

  Returns a `Style` with default properties.

- `const fn reset() -> Self`

  Returns a `Style` resetting all properties.

- `const fn fg(self, color: Color) -> Self` — [`Color`](../index.md#color)

  Changes the foreground color.

  

  ## Examples

  

  ```rust

  use ratatui_core::style::{Color, Style};

  

  let style = Style::default().fg(Color::Blue);

  let diff = Style::default().fg(Color::Red);

  assert_eq!(style.patch(diff), Style::default().fg(Color::Red));

  ```

- `const fn bg(self, color: Color) -> Self` — [`Color`](../index.md#color)

  Changes the background color.

  

  ## Examples

  

  ```rust

  use ratatui_core::style::{Color, Style};

  

  let style = Style::default().bg(Color::Blue);

  let diff = Style::default().bg(Color::Red);

  assert_eq!(style.patch(diff), Style::default().bg(Color::Red));

  ```

- `const fn underline_color(self, color: Color) -> Self` — [`Color`](../index.md#color)

  Changes the underline color. The text must be underlined with a modifier for this to work.

  

  This uses a non-standard ANSI escape sequence. It is supported by most terminal emulators,

  but is only implemented in the crossterm backend and enabled by the `underline-color`

  feature flag.

  

  See

  [Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters)

  code `58` and `59` for more information.

  

  ## Examples

  

  ```rust

  use ratatui_core::style::{Color, Modifier, Style};

  

  let style = Style::default()

      .underline_color(Color::Blue)

      .add_modifier(Modifier::UNDERLINED);

  let diff = Style::default()

      .underline_color(Color::Red)

      .add_modifier(Modifier::UNDERLINED);

  assert_eq!(

      style.patch(diff),

      Style::default()

          .underline_color(Color::Red)

          .add_modifier(Modifier::UNDERLINED)

  );

  ```

- `const fn add_modifier(self, modifier: Modifier) -> Self` — [`Modifier`](#modifier)

  Changes the text emphasis.

  

  When applied, it adds the given modifier to the `Style` modifiers.

  

  ## Examples

  

  ```rust

  use ratatui_core::style::{Modifier, Style};

  

  let style = Style::default().add_modifier(Modifier::BOLD);

  let diff = Style::default().add_modifier(Modifier::ITALIC);

  let patched = style.patch(diff);

  assert_eq!(patched.add_modifier, Modifier::BOLD | Modifier::ITALIC);

  assert_eq!(patched.sub_modifier, Modifier::empty());

  ```

- `const fn remove_modifier(self, modifier: Modifier) -> Self` — [`Modifier`](#modifier)

  Changes the text emphasis.

  

  When applied, it removes the given modifier from the `Style` modifiers.

  

  ## Examples

  

  ```rust

  use ratatui_core::style::{Modifier, Style};

  

  let style = Style::default().add_modifier(Modifier::BOLD | Modifier::ITALIC);

  let diff = Style::default().remove_modifier(Modifier::ITALIC);

  let patched = style.patch(diff);

  assert_eq!(patched.add_modifier, Modifier::BOLD);

  assert_eq!(patched.sub_modifier, Modifier::ITALIC);

  ```

- `const fn has_modifier(self, modifier: Modifier) -> bool` — [`Modifier`](#modifier)

  Returns `true` if the style has the given modifier set.

  

  ## Examples

  

  ```rust

  use ratatui_core::style::{Modifier, Style};

  

  let style = Style::default().add_modifier(Modifier::BOLD | Modifier::ITALIC);

  assert!(style.has_modifier(Modifier::BOLD));

  assert!(style.has_modifier(Modifier::ITALIC));

  assert!(!style.has_modifier(Modifier::UNDERLINED));

  ```

- `fn patch<S: Into<Self>>(self, other: S) -> Self`

  Results in a combined style that is equivalent to applying the two individual styles to

  a style one after the other.

  

  `style` accepts any type that is convertible to [`Style`](#style) (e.g. [`Style`](#style), [`Color`](../index.md), or

  your own type that implements `Into<Style>`).

  

  ## Examples

  ```rust

  use ratatui_core::style::{Color, Modifier, Style};

  

  let style_1 = Style::default().fg(Color::Yellow);

  let style_2 = Style::default().bg(Color::Red);

  let combined = style_1.patch(style_2);

  assert_eq!(

      Style::default().patch(style_1).patch(style_2),

      Style::default().patch(combined)

  );

  ```

- `const fn black(self) -> Self`

  Sets the foreground color to [`black`](Color::Black).

- `const fn on_black(self) -> Self`

  Sets the background color to [`black`](Color::Black).

- `const fn red(self) -> Self`

  Sets the foreground color to [`red`](Color::Red).

- `const fn on_red(self) -> Self`

  Sets the background color to [`red`](Color::Red).

- `const fn green(self) -> Self`

  Sets the foreground color to [`green`](Color::Green).

- `const fn on_green(self) -> Self`

  Sets the background color to [`green`](Color::Green).

- `const fn yellow(self) -> Self`

  Sets the foreground color to [`yellow`](Color::Yellow).

- `const fn on_yellow(self) -> Self`

  Sets the background color to [`yellow`](Color::Yellow).

- `const fn blue(self) -> Self`

  Sets the foreground color to [`blue`](Color::Blue).

- `const fn on_blue(self) -> Self`

  Sets the background color to [`blue`](Color::Blue).

- `const fn magenta(self) -> Self`

  Sets the foreground color to [`magenta`](Color::Magenta).

- `const fn on_magenta(self) -> Self`

  Sets the background color to [`magenta`](Color::Magenta).

- `const fn cyan(self) -> Self`

  Sets the foreground color to [`cyan`](Color::Cyan).

- `const fn on_cyan(self) -> Self`

  Sets the background color to [`cyan`](Color::Cyan).

- `const fn gray(self) -> Self`

  Sets the foreground color to [`gray`](Color::Gray).

- `const fn on_gray(self) -> Self`

  Sets the background color to [`gray`](Color::Gray).

- `const fn dark_gray(self) -> Self`

  Sets the foreground color to [`dark_gray`](Color::DarkGray).

- `const fn on_dark_gray(self) -> Self`

  Sets the background color to [`dark_gray`](Color::DarkGray).

- `const fn light_red(self) -> Self`

  Sets the foreground color to [`light_red`](Color::LightRed).

- `const fn on_light_red(self) -> Self`

  Sets the background color to [`light_red`](Color::LightRed).

- `const fn light_green(self) -> Self`

  Sets the foreground color to [`light_green`](Color::LightGreen).

- `const fn on_light_green(self) -> Self`

  Sets the background color to [`light_green`](Color::LightGreen).

- `const fn light_yellow(self) -> Self`

  Sets the foreground color to [`light_yellow`](Color::LightYellow).

- `const fn on_light_yellow(self) -> Self`

  Sets the background color to [`light_yellow`](Color::LightYellow).

- `const fn light_blue(self) -> Self`

  Sets the foreground color to [`light_blue`](Color::LightBlue).

- `const fn on_light_blue(self) -> Self`

  Sets the background color to [`light_blue`](Color::LightBlue).

- `const fn light_magenta(self) -> Self`

  Sets the foreground color to [`light_magenta`](Color::LightMagenta).

- `const fn on_light_magenta(self) -> Self`

  Sets the background color to [`light_magenta`](Color::LightMagenta).

- `const fn light_cyan(self) -> Self`

  Sets the foreground color to [`light_cyan`](Color::LightCyan).

- `const fn on_light_cyan(self) -> Self`

  Sets the background color to [`light_cyan`](Color::LightCyan).

- `const fn white(self) -> Self`

  Sets the foreground color to [`white`](Color::White).

- `const fn on_white(self) -> Self`

  Sets the background color to [`white`](Color::White).

- `const fn bold(self) -> Self`

  Adds the [`bold`](Modifier::BOLD) modifier.

- `const fn not_bold(self) -> Self`

  Removes the [`bold`](Modifier::BOLD) modifier.

- `const fn dim(self) -> Self`

  Adds the [`dim`](Modifier::DIM) modifier.

- `const fn not_dim(self) -> Self`

  Removes the [`dim`](Modifier::DIM) modifier.

- `const fn italic(self) -> Self`

  Adds the [`italic`](Modifier::ITALIC) modifier.

- `const fn not_italic(self) -> Self`

  Removes the [`italic`](Modifier::ITALIC) modifier.

- `const fn underlined(self) -> Self`

  Adds the [`underlined`](Modifier::UNDERLINED) modifier.

- `const fn not_underlined(self) -> Self`

  Removes the [`underlined`](Modifier::UNDERLINED) modifier.

- `const fn slow_blink(self) -> Self`

  Adds the [`slow_blink`](Modifier::SLOW_BLINK) modifier.

- `const fn not_slow_blink(self) -> Self`

  Removes the [`slow_blink`](Modifier::SLOW_BLINK) modifier.

- `const fn rapid_blink(self) -> Self`

  Adds the [`rapid_blink`](Modifier::RAPID_BLINK) modifier.

- `const fn not_rapid_blink(self) -> Self`

  Removes the [`rapid_blink`](Modifier::RAPID_BLINK) modifier.

- `const fn reversed(self) -> Self`

  Adds the [`reversed`](Modifier::REVERSED) modifier.

- `const fn not_reversed(self) -> Self`

  Removes the [`reversed`](Modifier::REVERSED) modifier.

- `const fn hidden(self) -> Self`

  Adds the [`hidden`](Modifier::HIDDEN) modifier.

- `const fn not_hidden(self) -> Self`

  Removes the [`hidden`](Modifier::HIDDEN) modifier.

- `const fn crossed_out(self) -> Self`

  Adds the [`crossed_out`](Modifier::CROSSED_OUT) modifier.

- `const fn not_crossed_out(self) -> Self`

  Removes the [`crossed_out`](Modifier::CROSSED_OUT) modifier.

#### Trait Implementations

##### `impl Clone for Style`

- `fn clone(&self) -> Style` — [`Style`](#style)

##### `impl Copy for Style`

##### `impl Debug for Style`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Style`

- `fn default() -> Style` — [`Style`](#style)

##### `impl Eq for Style`

##### `impl<K> Equivalent for Style`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromCrossterm for ratatui_core::style::Style`

##### `impl FromTermwiz for ratatui_core::style::Style`

- `type Owned = T`

##### `impl Hash for Style`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoCrossterm for ratatui_core::style::Style`

##### `impl IntoEither for Style`

##### `impl PartialEq for Style`

- `fn eq(&self, other: &Style) -> bool` — [`Style`](#style)

##### `impl StructuralPartialEq for Style`

## Enums

### `Color`

```rust
enum Color {
    Reset,
    Black,
    Red,
    Green,
    Yellow,
    Blue,
    Magenta,
    Cyan,
    Gray,
    DarkGray,
    LightRed,
    LightGreen,
    LightYellow,
    LightBlue,
    LightMagenta,
    LightCyan,
    White,
    Rgb(u8, u8, u8),
    Indexed(u8),
}
```

ANSI Color

All colors from the [ANSI color table] are supported (though some names are not exactly the
same).

| Color Name     | Color                   | Foreground | Background |
|----------------|-------------------------|------------|------------|
| `black`        | [`Color::Black`](../index.md)        | 30         | 40         |
| `red`          | [`Color::Red`](../index.md)          | 31         | 41         |
| `green`        | [`Color::Green`](../index.md)        | 32         | 42         |
| `yellow`       | [`Color::Yellow`](../index.md)       | 33         | 43         |
| `blue`         | [`Color::Blue`](../index.md)         | 34         | 44         |
| `magenta`      | [`Color::Magenta`](../index.md)      | 35         | 45         |
| `cyan`         | [`Color::Cyan`](../index.md)         | 36         | 46         |
| `gray`*        | [`Color::Gray`](../index.md)         | 37         | 47         |
| `darkgray`*    | [`Color::DarkGray`](../index.md)     | 90         | 100        |
| `lightred`     | [`Color::LightRed`](../index.md)     | 91         | 101        |
| `lightgreen`   | [`Color::LightGreen`](../index.md)   | 92         | 102        |
| `lightyellow`  | [`Color::LightYellow`](../index.md)  | 93         | 103        |
| `lightblue`    | [`Color::LightBlue`](../index.md)    | 94         | 104        |
| `lightmagenta` | [`Color::LightMagenta`](../index.md) | 95         | 105        |
| `lightcyan`    | [`Color::LightCyan`](../index.md)    | 96         | 106        |
| `white`*       | [`Color::White`](../index.md)        | 97         | 107        |

- `gray` is sometimes called `white` - this is not supported as we use `white` for bright white
- `gray` is sometimes called `silver` - this is supported
- `darkgray` is sometimes called `light black` or `bright black` (both are supported)
- `white` is sometimes called `light white` or `bright white` (both are supported)
- we support `bright` and `light` prefixes for all colors
- we support `-` and `_` and ` ` as separators for all colors
- we support both `gray` and `grey` spellings

`From<Color> for Style` is implemented by creating a style with the foreground color set to the
given color. This allows you to use colors anywhere that accepts `Into<Style>`.

# Example

```rust
use std::str::FromStr;

use ratatui_core::style::Color;

assert_eq!(Color::from_str("red"), Ok(Color::Red));
assert_eq!("red".parse(), Ok(Color::Red));
assert_eq!("lightred".parse(), Ok(Color::LightRed));
assert_eq!("light red".parse(), Ok(Color::LightRed));
assert_eq!("light-red".parse(), Ok(Color::LightRed));
assert_eq!("light_red".parse(), Ok(Color::LightRed));
assert_eq!("lightRed".parse(), Ok(Color::LightRed));
assert_eq!("bright red".parse(), Ok(Color::LightRed));
assert_eq!("bright-red".parse(), Ok(Color::LightRed));
assert_eq!("silver".parse(), Ok(Color::Gray));
assert_eq!("dark-grey".parse(), Ok(Color::DarkGray));
assert_eq!("dark gray".parse(), Ok(Color::DarkGray));
assert_eq!("light-black".parse(), Ok(Color::DarkGray));
assert_eq!("white".parse(), Ok(Color::White));
assert_eq!("bright white".parse(), Ok(Color::White));
```

#### Variants

- **`Reset`**

  Resets the foreground or background color

- **`Black`**

  ANSI Color: Black. Foreground: 30, Background: 40

- **`Red`**

  ANSI Color: Red. Foreground: 31, Background: 41

- **`Green`**

  ANSI Color: Green. Foreground: 32, Background: 42

- **`Yellow`**

  ANSI Color: Yellow. Foreground: 33, Background: 43

- **`Blue`**

  ANSI Color: Blue. Foreground: 34, Background: 44

- **`Magenta`**

  ANSI Color: Magenta. Foreground: 35, Background: 45

- **`Cyan`**

  ANSI Color: Cyan. Foreground: 36, Background: 46

- **`Gray`**

  ANSI Color: White. Foreground: 37, Background: 47
  
  Note that this is sometimes called `silver` or `white` but we use `white` for bright white

- **`DarkGray`**

  ANSI Color: Bright Black. Foreground: 90, Background: 100
  
  Note that this is sometimes called `light black` or `bright black` but we use `dark gray`

- **`LightRed`**

  ANSI Color: Bright Red. Foreground: 91, Background: 101

- **`LightGreen`**

  ANSI Color: Bright Green. Foreground: 92, Background: 102

- **`LightYellow`**

  ANSI Color: Bright Yellow. Foreground: 93, Background: 103

- **`LightBlue`**

  ANSI Color: Bright Blue. Foreground: 94, Background: 104

- **`LightMagenta`**

  ANSI Color: Bright Magenta. Foreground: 95, Background: 105

- **`LightCyan`**

  ANSI Color: Bright Cyan. Foreground: 96, Background: 106

- **`White`**

  ANSI Color: Bright White. Foreground: 97, Background: 107
  Sometimes called `bright white` or `light white` in some terminals

- **`Rgb`**

  An RGB color.
  
  Note that only terminals that support 24-bit true color will display this correctly.
  Notably versions of Windows Terminal prior to Windows 10 and macOS Terminal.app do not
  support this.
  
  If the terminal does not support true color, code using the  `TermwizBackend` will
  fallback to the default text color. Crossterm and Termion do not have this capability and
  the display will be unpredictable (e.g. Terminal.app may display glitched blinking text).
  See <https://github.com/ratatui/ratatui/issues/475> for an example of this problem.
  
  See also: <https://en.wikipedia.org/wiki/ANSI_escape_code#24-bit>

- **`Indexed`**

  An 8-bit 256 color.
  
  See also <https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit>

#### Implementations

- `const fn from_u32(u: u32) -> Self`

  Convert a u32 to a Color

  

  The u32 should be in the format 0x00RRGGBB.

#### Trait Implementations

##### `impl Clone for Color`

- `fn clone(&self) -> Color` — [`Color`](../index.md#color)

##### `impl Copy for Color`

##### `impl Debug for Color`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Color`

- `fn default() -> Color` — [`Color`](../index.md#color)

##### `impl Display for Color`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Color`

##### `impl<K> Equivalent for Color`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromCrossterm for ratatui_core::style::Color`

- `fn flush(&mut self) -> core::result::Result<(), core::convert::Infallible>`

##### `impl FromStr for Color`

- `type Err = ParseColorError`

- `fn from_str(s: &str) -> Result<Self, <Self as >::Err>`

##### `impl FromTermwiz for ratatui_core::style::Color`

##### `impl Hash for Color`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoCrossterm for ratatui_core::style::Color`

- `fn get_cursor_position(&mut self) -> core::result::Result<Position, core::convert::Infallible>` — [`Position`](../index.md#position)

##### `impl IntoEither for Color`

##### `impl IntoTermwiz for ratatui_core::style::Color`

##### `impl PartialEq for Color`

- `fn eq(&self, other: &Color) -> bool` — [`Color`](../index.md#color)

##### `impl StructuralPartialEq for Color`

##### `impl ToCompactString for Color`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Color`

- `fn to_line(&self) -> Line<'_>` — [`Line`](../index.md#line)

##### `impl ToSpan for Color`

- `fn to_span(&self) -> Span<'_>` — [`Span`](../index.md#span)

##### `impl ToString for Color`

- `fn to_string(&self) -> String`

##### `impl ToText for Color`

- `fn to_text(&self) -> Text<'_>` — [`Text`](../index.md#text)

## Traits

### `Styled`

```rust
trait Styled { ... }
```

A trait for objects that have a `Style`.

This trait enables generic code to be written that can interact with any object that has a
`Style`. This is used by the `Stylize` trait to allow generic code to be written that can
interact with any object that can be styled.

#### Associated Types

- `type Item`

#### Required Methods

- `fn style(&self) -> Style`

  Returns the style of the object.

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

  Sets the style of the object.

#### Implementors

- [`Line`](../index.md#line)
- [`Span`](../index.md#span)
- [`StyledGrapheme`](../index.md#styledgrapheme)
- [`Text`](../index.md#text)
- `&'a str`
- `alloc::borrow::Cow<'a, str>`
- `alloc::string::String`
- `bool`
- `char`
- `f32`
- `f64`
- `i128`
- `i16`
- `i32`
- `i64`
- `i8`
- `isize`
- `u128`
- `u16`
- `u32`
- `u64`
- `u8`
- `usize`

### `Stylize<'a, T>`

```rust
trait Stylize<'a, T>: Sized { ... }
```

An extension trait for styling objects.

For any type that implements `Stylize`, the provided methods in this trait can be used to style
the type further. This trait is automatically implemented for any type that implements the
[`Styled`](../index.md) trait which e.g.: `String`, `&str`, [`Span`](../index.md), [`Style`](#style) and many Widget types.

This results in much more ergonomic styling of text and widgets. For example, instead of
writing:

```rust,ignore
let text = Span::styled("Hello", Style::default().fg(Color::Red).bg(Color::Blue));
```

You can write:

```rust,ignore
let text = "Hello".red().on_blue();
```

This trait implements a provided method for every color as both foreground and background
(prefixed by `on_`), and all modifiers as both an additive and subtractive modifier (prefixed
by `not_`). The `reset()` method is also provided to reset the style.

# Examples
```ignore
use ratatui_core::{
    style::{Color, Modifier, Style, Stylize},
    text::Line,
    widgets::{Block, Paragraph},
};

let span = "hello".red().on_blue().bold();
let line = Line::from(vec![
    "hello".red().on_blue().bold(),
    "world".green().on_yellow().not_bold(),
]);
let paragraph = Paragraph::new(line).italic().underlined();
let block = Block::bordered().title("Title").on_white().bold();
```

#### Required Methods

- `fn bg<C: Into<Color>>(self, color: C) -> T`

- `fn fg<C: Into<Color>>(self, color: C) -> T`

- `fn reset(self) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

#### Provided Methods

- `fn black(self) -> T`

  Sets the foreground color to [`black`](Color::Black).

- `fn on_black(self) -> T`

  Sets the background color to [`black`](Color::Black).

- `fn red(self) -> T`

  Sets the foreground color to [`red`](Color::Red).

- `fn on_red(self) -> T`

  Sets the background color to [`red`](Color::Red).

- `fn green(self) -> T`

  Sets the foreground color to [`green`](Color::Green).

- `fn on_green(self) -> T`

  Sets the background color to [`green`](Color::Green).

- `fn yellow(self) -> T`

  Sets the foreground color to [`yellow`](Color::Yellow).

- `fn on_yellow(self) -> T`

  Sets the background color to [`yellow`](Color::Yellow).

- `fn blue(self) -> T`

  Sets the foreground color to [`blue`](Color::Blue).

- `fn on_blue(self) -> T`

  Sets the background color to [`blue`](Color::Blue).

- `fn magenta(self) -> T`

  Sets the foreground color to [`magenta`](Color::Magenta).

- `fn on_magenta(self) -> T`

  Sets the background color to [`magenta`](Color::Magenta).

- `fn cyan(self) -> T`

  Sets the foreground color to [`cyan`](Color::Cyan).

- `fn on_cyan(self) -> T`

  Sets the background color to [`cyan`](Color::Cyan).

- `fn gray(self) -> T`

  Sets the foreground color to [`gray`](Color::Gray).

- `fn on_gray(self) -> T`

  Sets the background color to [`gray`](Color::Gray).

- `fn dark_gray(self) -> T`

  Sets the foreground color to [`dark_gray`](Color::DarkGray).

- `fn on_dark_gray(self) -> T`

  Sets the background color to [`dark_gray`](Color::DarkGray).

- `fn light_red(self) -> T`

  Sets the foreground color to [`light_red`](Color::LightRed).

- `fn on_light_red(self) -> T`

  Sets the background color to [`light_red`](Color::LightRed).

- `fn light_green(self) -> T`

  Sets the foreground color to [`light_green`](Color::LightGreen).

- `fn on_light_green(self) -> T`

  Sets the background color to [`light_green`](Color::LightGreen).

- `fn light_yellow(self) -> T`

  Sets the foreground color to [`light_yellow`](Color::LightYellow).

- `fn on_light_yellow(self) -> T`

  Sets the background color to [`light_yellow`](Color::LightYellow).

- `fn light_blue(self) -> T`

  Sets the foreground color to [`light_blue`](Color::LightBlue).

- `fn on_light_blue(self) -> T`

  Sets the background color to [`light_blue`](Color::LightBlue).

- `fn light_magenta(self) -> T`

  Sets the foreground color to [`light_magenta`](Color::LightMagenta).

- `fn on_light_magenta(self) -> T`

  Sets the background color to [`light_magenta`](Color::LightMagenta).

- `fn light_cyan(self) -> T`

  Sets the foreground color to [`light_cyan`](Color::LightCyan).

- `fn on_light_cyan(self) -> T`

  Sets the background color to [`light_cyan`](Color::LightCyan).

- `fn white(self) -> T`

  Sets the foreground color to [`white`](Color::White).

- `fn on_white(self) -> T`

  Sets the background color to [`white`](Color::White).

- `fn bold(self) -> T`

  Adds the [`bold`](Modifier::BOLD) modifier.

- `fn not_bold(self) -> T`

  Removes the [`bold`](Modifier::BOLD) modifier.

- `fn dim(self) -> T`

  Adds the [`dim`](Modifier::DIM) modifier.

- `fn not_dim(self) -> T`

  Removes the [`dim`](Modifier::DIM) modifier.

- `fn italic(self) -> T`

  Adds the [`italic`](Modifier::ITALIC) modifier.

- `fn not_italic(self) -> T`

  Removes the [`italic`](Modifier::ITALIC) modifier.

- `fn underlined(self) -> T`

  Adds the [`underlined`](Modifier::UNDERLINED) modifier.

- `fn not_underlined(self) -> T`

  Removes the [`underlined`](Modifier::UNDERLINED) modifier.

- `fn slow_blink(self) -> T`

  Adds the [`slow_blink`](Modifier::SLOW_BLINK) modifier.

- `fn not_slow_blink(self) -> T`

  Removes the [`slow_blink`](Modifier::SLOW_BLINK) modifier.

- `fn rapid_blink(self) -> T`

  Adds the [`rapid_blink`](Modifier::RAPID_BLINK) modifier.

- `fn not_rapid_blink(self) -> T`

  Removes the [`rapid_blink`](Modifier::RAPID_BLINK) modifier.

- `fn reversed(self) -> T`

  Adds the [`reversed`](Modifier::REVERSED) modifier.

- `fn not_reversed(self) -> T`

  Removes the [`reversed`](Modifier::REVERSED) modifier.

- `fn hidden(self) -> T`

  Adds the [`hidden`](Modifier::HIDDEN) modifier.

- `fn not_hidden(self) -> T`

  Removes the [`hidden`](Modifier::HIDDEN) modifier.

- `fn crossed_out(self) -> T`

  Adds the [`crossed_out`](Modifier::CROSSED_OUT) modifier.

- `fn not_crossed_out(self) -> T`

  Removes the [`crossed_out`](Modifier::CROSSED_OUT) modifier.

#### Implementors

- `U`

