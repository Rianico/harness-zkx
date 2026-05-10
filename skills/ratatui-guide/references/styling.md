# Ratatui Styling

> Colors, modifiers, and text styling for terminal UIs.
>
> **Version:** 0.30.0

## Key Patterns

### Basic Style Application

Apply style to text:

```rust
use ratatui::style::{Color, Modifier, Style};

let style = Style::default()
    .fg(Color::Green)
    .bg(Color::Black)
    .add_modifier(Modifier::BOLD);
```

### Styled Span

Create styled text segments:

```rust
use ratatui::style::{Color, Stylize};
use ratatui::text::Span;

let span = Span::styled("Hello", Style::default().fg(Color::Red));

// Or using Stylize trait:
let span = "Hello".red().bold();
```

### Multiple Styles in Line

Combine multiple styled spans:

```rust
use ratatui::text::{Line, Span};
use ratatui::style::Stylize;

let line = Line::from(vec![
    "Status: ".into(),
    "OK".green().bold(),
    " | ".into(),
    "Errors: ".into(),
    "0".yellow(),
]);
```

### Color Types

Available color options:

```rust
use ratatui::style::Color;

// Named colors
Color::Red
Color::Green
Color::Blue
Color::Black
Color::White

// 256-color palette (0-255)
Color::Indexed(196)  // Bright red

// True color (RGB)
Color::Rgb(255, 0, 0)  // Red

// Reset to default
Color::Reset
```

### Modifiers

Text modifiers for emphasis:

```rust
use ratatui::style::Modifier;

Modifier::BOLD
Modifier::DIM
Modifier::ITALIC
Modifier::UNDERLINED
Modifier::SLOW_BLINK
Modifier::RAPID_BLINK
Modifier::REVERSED
Modifier::HIDDEN
Modifier::CROSSED_OUT
```

### Stylize Trait

Convenience methods for styling:

```rust
use ratatui::style::Stylize;

let text = "Hello".red().bold().on_white();
let line = "World".green().italic();
let span = "!".yellow().underlined();
```

### Alignment

Text alignment options:

```rust
use ratatui::layout::Alignment;
use ratatui::widgets::Paragraph;

Paragraph::new("Left aligned").left_aligned();
Paragraph::new("Centered").centered();
Paragraph::new("Right aligned").right_aligned();

// Or in Block title
Block::bordered().title("Title".centered());
```

## API Reference Table

| Function/Type | Description | Example |
|---------------|-------------|---------|
| `Style::default()` | Create new style | `Style::default().fg(Color::Red)` |
| `Style::fg()` | Set foreground color | `.fg(Color::Green)` |
| `Style::bg()` | Set background color | `.bg(Color::Black)` |
| `Style::add_modifier()` | Add modifier | `.add_modifier(Modifier::BOLD)` |
| `Style::remove_modifier()` | Remove modifier | `.remove_modifier(Modifier::DIM)` |
| `Span::styled()` | Create styled span | `Span::styled("text", style)` |
| `Line::from()` | Create line from spans | `Line::from(vec![span1, span2])` |
| `.red()`, `.green()`, etc. | Stylize trait colors | `"text".red().bold()` |
| `Alignment::Left` | Left alignment | `Paragraph::new("text").left_aligned()` |
| `Alignment::Center` | Center alignment | `Paragraph::new("text").centered()` |
| `Alignment::Right` | Right alignment | `Paragraph::new("text").right_aligned()` |

---

## Colors

Ratatui supports multiple color formats for terminal styling.

### Color Types

| Type | Description | Example |
|------|-------------|---------|
| Named | Built-in color names | `Color::Red` |
| Indexed | 256-color palette | `Color::Indexed(196)` |
| RGB | True color (24-bit) | `Color::Rgb(255, 0, 0)` |
| Reset | Terminal default | `Color::Reset` |

### Named Colors

```rust
use ratatui::style::Color;

Color::Black
Color::Red
Color::Green
Color::Yellow
Color::Blue
Color::Magenta
Color::Cyan
Color::Gray       // Bright black (ANSI 37)
Color::DarkGray   // Bright black (ANSI 90)
Color::LightRed
Color::LightGreen
Color::LightYellow
Color::LightBlue
Color::LightMagenta
Color::LightCyan
Color::White      // Bright white (ANSI 97)
```

### ANSI Color Reference

| Color Name | Foreground | Background |
|------------|------------|------------|
| `Black` | 30 | 40 |
| `Red` | 31 | 41 |
| `Green` | 32 | 42 |
| `Yellow` | 33 | 43 |
| `Blue` | 34 | 44 |
| `Magenta` | 35 | 45 |
| `Cyan` | 36 | 46 |
| `Gray` | 37 | 47 |
| `DarkGray` | 90 | 100 |
| `LightRed` | 91 | 101 |
| `LightGreen` | 92 | 102 |
| `LightYellow` | 93 | 103 |
| `LightBlue` | 94 | 104 |
| `LightMagenta` | 95 | 105 |
| `LightCyan` | 96 | 106 |
| `White` | 97 | 107 |

### 256-Color Palette

```rust
// 0-15: Standard colors
// 16-231: 216-color cube
// 232-255: Grayscale

Color::Indexed(196)  // Bright red
Color::Indexed(21)   // Bright blue
Color::Indexed(232)  // Darkest gray
Color::Indexed(255)  // Lightest gray
```

### True Color (RGB)

```rust
Color::Rgb(255, 128, 64)  // Custom orange
Color::Rgb(0, 255, 0)     // Green
```

Note: Only terminals that support 24-bit true color will display RGB correctly. Windows Terminal prior to Windows 10 and macOS Terminal.app do not support this.

### Color Parsing

Colors can be parsed from strings:

```rust
use std::str::FromStr;
use ratatui::style::Color;

assert_eq!(Color::from_str("red"), Ok(Color::Red));
assert_eq!("light red".parse(), Ok(Color::LightRed));
assert_eq!("light-red".parse(), Ok(Color::LightRed));
assert_eq!("bright red".parse(), Ok(Color::LightRed));
assert_eq!("silver".parse(), Ok(Color::Gray));
assert_eq!("dark-gray".parse(), Ok(Color::DarkGray));
```

Supported formats:
- `bright` and `light` prefixes for all colors
- `-`, `_`, or space as separators
- Both `gray` and `grey` spellings

---

## Styles and Modifiers

Styles combine foreground color, background color, and text modifiers.

### Creating Styles

```rust
use ratatui::style::{Style, Color, Modifier};

let style = Style::default()
    .fg(Color::Green)
    .bg(Color::Black)
    .add_modifier(Modifier::BOLD);
```

### Style Struct

```rust
struct Style {
    pub fg: Option<Color>,
    pub bg: Option<Color>,
    pub underline_color: Option<Color>,
    pub add_modifier: Modifier,
    pub sub_modifier: Modifier,
}
```

### Available Modifiers

| Modifier | Effect |
|----------|--------|
| `BOLD` | Bold text |
| `DIM` | Dimmed text |
| `ITALIC` | Italic text |
| `UNDERLINED` | Underlined text |
| `SLOW_BLINK` | Slow blinking |
| `RAPID_BLINK` | Fast blinking |
| `REVERSED` | Swap fg/bg colors |
| `HIDDEN` | Hidden/invisible |
| `CROSSED_OUT` | Strikethrough |

### Combining Modifiers

Modifiers are bitflags and can be combined with `|`:

```rust
let style = Style::default()
    .add_modifier(Modifier::BOLD | Modifier::ITALIC);
```

### Style Methods

```rust
// Create new style
let style = Style::new();  // Same as Style::default()

// Reset all properties
let style = Style::reset();

// Set colors
let style = Style::default().fg(Color::Red).bg(Color::Blue);

// Underline color (requires UNDERLINED modifier)
let style = Style::default()
    .underline_color(Color::Green)
    .add_modifier(Modifier::UNDERLINED);

// Modifiers
let style = Style::default()
    .add_modifier(Modifier::BOLD)
    .remove_modifier(Modifier::DIM);

// Check for modifier
if style.has_modifier(Modifier::BOLD) { /* ... */ }

// Merge styles
let merged = base_style.patch(overlay_style);
```

### Color Shorthands

Style provides shorthand methods for all named colors:

```rust
// Foreground colors
style.red().green().blue().yellow().magenta().cyan()
style.black().white().gray().dark_gray()
style.light_red().light_green().light_blue() /* etc. */

// Background colors (prefixed with `on_`)
style.on_red().on_green().on_blue() /* etc. */
```

### Modifier Shorthands

```rust
// Add modifiers
style.bold().dim().italic().underlined()
style.slow_blink().rapid_blink().reversed()
style.hidden().crossed_out()

// Remove modifiers (prefixed with `not_`)
style.not_bold().not_dim().not_italic() /* etc. */
```

### Merging Styles

```rust
let base = Style::default().fg(Color::Red);
let overlay = Style::default().bg(Color::Blue);
let merged = base.patch(overlay);
// Result: fg=Red, bg=Blue
```

`patch()` merges styles incrementally. The overlay's properties replace the base's where specified.

### Style from Color/Modifier

Colors and Modifiers convert to Style:

```rust
// These are equivalent:
Line::styled("hello", Style::new().fg(Color::Red));
Line::styled("hello", Color::Red);

// These are equivalent:
Line::styled("hello", Style::new().add_modifier(Modifier::BOLD));
Line::styled("hello", Modifier::BOLD);
```

---

## Text: Span, Line, Text

Text types for building styled terminal output.

### Hierarchy

```
Text (multiple lines)
  Line (multiple spans)
    Span (styled text fragment)
```

### Span

A styled text fragment where all characters share the same style.

```rust
use ratatui::text::Span;
use ratatui::style::{Style, Stylize};

// With Style
let span = Span::styled("Hello", Style::default().fg(Color::Red));

// With Stylize trait
let span = "Hello".red().bold();

// Raw content
let span = Span::raw("Hello");

// From string
let span: Span = "Hello".into();
```

#### Span Methods

```rust
// Set content
let span = Span::default().content("text");

// Set style
let span = Span::raw("text").style(Style::new().green());

// Patch style (merge)
let span = Span::styled("text", Style::new().green().italic())
    .patch_style(Style::new().red().bold());
// Result: red, italic, bold

// Reset style
let span = span.reset_style();

// Get width (unicode-aware)
let width = span.width();

// Convert to aligned Line
let line = span.into_left_aligned_line();
let line = span.into_centered_line();
let line = span.into_right_aligned_line();
```

### Line

A collection of spans representing a single line of text.

```rust
use ratatui::text::Line;
use ratatui::style::Stylize;

let line = Line::from(vec![
    "Status: ".into(),
    "OK".green().bold(),
    " | ".into(),
    "Count: ".into(),
    "42".yellow(),
]);
```

#### Creating Lines

```rust
// From string
let line = Line::from("Hello, world!");
let line = Line::from(String::from("Hello, world!"));

// From spans
let line = Line::from(vec![
    Span::styled("Hello", Style::new().blue()),
    Span::raw(" world!"),
]);

// Raw (default style)
let line = Line::raw("content");

// Styled
let line = Line::styled("content", Style::new().yellow());
let line = Line::styled("content", (Color::Yellow, Modifier::BOLD));
```

#### Line Methods

```rust
// Set spans
let line = Line::default().spans(vec!["Hello".blue(), " world!".green()]);

// Set style
let line = Line::from("text").style(Style::new().red());

// Alignment
let line = Line::from("text").left_aligned();
let line = Line::from("text").centered();
let line = Line::from("text").right_aligned();
let line = Line::from("text").alignment(Alignment::Center);

// Get width
let width = line.width();

// Add span
let mut line = Line::from("Hello, ");
line.push_span(Span::raw("world!"));
line.push_span(" How are you?");

// Iterate spans
for span in line.iter() { /* ... */ }
for span in line.iter_mut() { /* ... */ }

// Patch style
let line = line.patch_style(Color::Yellow);

// Reset style
let line = line.reset_style();
```

### Text

Multiple lines of styled text.

```rust
use ratatui::text::Text;

let text = Text::from(vec![
    Line::from("Line 1"),
    Line::from("Line 2"),
]);

// From string with newlines
let text = Text::from("First line\nSecond line");
```

#### Creating Text

```rust
// From string
let text = Text::from("First line\nSecond line");
let text = Text::from(String::from("content"));

// From lines
let text = Text::from(vec![
    Line::from("Line 1"),
    Line::from("Line 2"),
]);

// From span
let text = Text::from(Span::styled("content", Style::new().green()));

// Raw (no style)
let text = Text::raw("First line\nSecond line");

// Styled
let text = Text::styled("content", Style::new().yellow());
let text = Text::styled("content", (Color::Yellow, Modifier::ITALIC));
```

#### Text Methods

```rust
// Set style
let text = Text::from("content").style(Style::new().red());

// Alignment
let text = Text::from("content").left_aligned();
let text = Text::from("content").centered();
let text = Text::from("content").right_aligned();

// Dimensions
let width = text.width();   // Max width of all lines
let height = text.height(); // Number of lines

// Add content
let mut text = Text::default();
text.push_line("New line");
text.push_line(Line::from("Styled line").yellow());
text.push_span("Added to last line");

// Extend
text.extend(vec![Line::from("More lines")]);
text.extend(Text::from("Even more"));

// Iterate
for line in text.iter() { /* ... */ }
for line in text.iter_mut() { /* ... */ }

// Patch/reset style
let text = text.patch_style(Color::Yellow);
let text = text.reset_style();
```

### Widget Usage

Text types can be rendered directly or via widgets:

```rust
// Direct render (Line and Text implement Widget)
line.render(area, buf);
text.render(area, buf);

// Via Paragraph (recommended for wrapping, scrolling)
Paragraph::new(text)
    .wrap(Wrap { trim: true })
    .render(area, buf);

// Any widget accepting text
Block::bordered().title(Line::from(vec![
    "[".dim(),
    "INFO".blue().bold(),
    "] ".dim(),
]));
```

---

## Stylize Trait

Extension trait for styling objects. Automatically implemented for types that implement `Styled`.

### Color Methods

```rust
// Foreground colors
fn black(self) -> T
fn red(self) -> T
fn green(self) -> T
fn yellow(self) -> T
fn blue(self) -> T
fn magenta(self) -> T
fn cyan(self) -> T
fn gray(self) -> T
fn dark_gray(self) -> T
fn light_red(self) -> T
fn light_green(self) -> T
fn light_yellow(self) -> T
fn light_blue(self) -> T
fn light_magenta(self) -> T
fn light_cyan(self) -> T
fn white(self) -> T

// Background colors (prefixed with `on_`)
fn on_black(self) -> T
fn on_red(self) -> T
fn on_green(self) -> T
// ... all colors have `on_` variants
```

### Modifier Methods

```rust
// Add modifiers
fn bold(self) -> T
fn dim(self) -> T
fn italic(self) -> T
fn underlined(self) -> T
fn slow_blink(self) -> T
fn rapid_blink(self) -> T
fn reversed(self) -> T
fn hidden(self) -> T
fn crossed_out(self) -> T

// Remove modifiers (prefixed with `not_`)
fn not_bold(self) -> T
fn not_dim(self) -> T
fn not_italic(self) -> T
fn not_underlined(self) -> T
// ... all modifiers have `not_` variants
```

### Core Methods

```rust
// Set foreground/background with any Color
fn fg<C: Into<Color>>(self, color: C) -> T
fn bg<C: Into<Color>>(self, color: C) -> T

// Modifier control
fn add_modifier(self, modifier: Modifier) -> T
fn remove_modifier(self, modifier: Modifier) -> T

// Reset to default
fn reset(self) -> T
```

### Usage Examples

```rust
use ratatui::style::Stylize;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};

// Strings return Span
let span: Span = "hello".red().on_blue().bold();

// Spans can be restyled
let span = span.green().italic();

// Lines can be styled
let line = Line::from("text").yellow().italic();

// Widgets can be styled
let paragraph = Paragraph::new("text").italic().underlined();
let block = Block::bordered().title("Title").on_white().bold();

// Chaining
let styled = "text".red().bold().on_white().italic().not_underlined();
```

### Implementors

Types that implement `Styled`:
- `Span`, `Line`, `Text`
- `String`, `&str`
- `char`, `bool`
- Numeric types (`i32`, `u8`, `f64`, etc.)
- `Style` itself
- Many widget types

---

## When Writing Code

1. Use Stylize trait methods (`.red()`, `.bold()`) for concise styling
2. Use `Style::default()` when building complex styles programmatically
3. Chain modifiers: `.bold().italic().underlined()`
4. Use `Color::Reset` to restore default terminal colors
5. Use `Line` for multi-span content, `Text` for multi-line content

## Common Patterns

### Log-Style Output

```rust
let log_line = Line::from(vec![
    "[".dim(),
    "INFO".blue().bold(),
    "] ".dim(),
    "Application started".into(),
]);
```

### Status Line

```rust
let status = Line::from(vec![
    "Status: ".into(),
    if connected { "Connected".green() } else { "Disconnected".red() },
]);
```

### Highlighted Text

```rust
let highlight = "important".yellow().bold().on_blue();
```

### Conditional Styling

```rust
let style = if error {
    Style::default().fg(Color::Red)
} else {
    Style::default().fg(Color::Green)
};
let span = Span::styled(message, style);
```
