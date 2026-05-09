# Crate `ratatui_macros`

`ratatui-macros` is a Rust crate that provides easy-to-use macros for simplifying boilerplate
associated with creating UI using [Ratatui].

This is an experimental playground for us to explore macros that would be useful to have in
Ratatui proper.

# Features

- [Text macros](#text-macros) for easily defining styled [`Text`](#text)s, [`Line`](#line)s, and [`Span`](#span)s.
- [Layout macros](#layout-macros) for defining [`Layout`](#layout)s with [`Constraint`](#constraint)s and directions.
- [Table macros](#table-macros) for creating [`Row`](#row)s and [`Cell`](#cell)s.

# Getting Started

Add `ratatui-macros` as a dependency in your `Cargo.toml`:

```shell
cargo add ratatui-macros
```

Then, import the macros in your Rust file:

```rust
use ratatui_macros::{constraint, constraints, horizontal, line, row, span, text, vertical};
```

# Text Macros

The [`span!`](#span) macro creates raw or styled [`Span`](#span)s.

```rust
use ratatui_core::style::{Color, Modifier, Style, Stylize};
use ratatui_macros::span;
let name = "world!";
let raw_greeting = span!("hello {name}");
let styled_greeting = span!(Style::new().green(); "hello {name}");
let colored_greeting = span!(Color::Green; "hello {name}");
let modified_greeting = span!(Modifier::BOLD; "hello {name}");
```

The [`line!`](#line) macro creates a [`Line`](#line) that contains a sequence of [`Span`](#span)s. It is similar to
the `vec!` macro. Each element is converted into a [`Span`](#span) using `Into::into`.

```rust
use ratatui_core::style::{Color, Stylize};
use ratatui_macros::{line, span};
let name = "world!";
let line = line!["hello", format!("{name}")];
let line = line!["hello ", span!(Color::Green; "{name}")];
let line = line!["Name: ".bold(), "Remy".italic()];
let line = line!["bye"; 2];
```

The [`text!`](#text) macro creates a [`Text`](#text) that contains a sequence of [`Line`](#line). It is similar to
the `vec!` macro. Each element is converted to a [`Line`](#line) using `Into::into`.

```rust
use ratatui_core::style::{Modifier, Stylize};
use ratatui_macros::{span, line, text};
let name = "world!";
let text = text!["hello", format!("{name}")];
let text = text!["bye"; 2];
let name = "Bye!!!";
let text = text![line!["hello", "world".bold()], span!(Modifier::BOLD; "{name}")];
```

# Layout Macros

If you are new to Ratatui, check out the [Layout concepts] article on the Ratatui website before
proceeding.

The [`constraints!`](#constraints) macro defines an array of [`Constraint`](#constraint)s:

```rust
use ratatui_core::layout::Layout;
use ratatui_macros::constraints;
let layout = Layout::horizontal(constraints![==50, ==30%, >=3, <=1, ==1/2, *=1]);
```

The [`constraint!`](#constraint) macro defines individual [`Constraint`](#constraint)s:

```rust
use ratatui_core::layout::Layout;
use ratatui_macros::constraint;
let layout = Layout::horizontal([constraint!(==50)]);
```

The [`vertical!`](#vertical) and [`horizontal!`](#horizontal) macros are a shortcut to defining a [`Layout`](#layout):

```rust
use ratatui_core::layout::Rect;
use ratatui_macros::{vertical, horizontal};
let area = Rect { x: 0, y: 0, width: 10, height: 10 };
let [top, main, bottom] = vertical![==1, *=1, >=3].areas(area);
let [left, main, right] = horizontal![>=20, *=1, >=20].areas(main);
```

# Table Macros

The [`row!`](#row) macro creates a [`Row`](#row) for a [`Table`](#table) that contains a sequence of [`Cell`](#cell)s. It
is similar to the `vec!` macro.

```rust
use ratatui_core::style::{Modifier, Stylize};
use ratatui_macros::{constraints, line, row, span, text};
use ratatui_widgets::table::Table;
let rows = [
    row!["hello", "world"],
    row!["goodbye", "world"],
    row![
        text!["line 1", line!["Line", "2".bold()]],
        span!(Modifier::BOLD; "Cell 2"),
    ],
];
let table = Table::new(rows, constraints![==20, *=1]);
```

# Contributing

Contributions to `ratatui-macros` are welcome! Whether it's submitting a bug report, a feature
request, or a pull request, all forms of contributions are valued and appreciated.

# Crate Organization

`ratatui-macros` is part of the Ratatui workspace that was modularized in version 0.30.0.
This crate provides declarative macros to reduce boilerplate when working with
Ratatui.

**When to use `ratatui-macros`:**

- You want to reduce boilerplate when creating styled text, layouts, or tables
- You prefer macro-based syntax for creating UI elements
- You need compile-time generation of repetitive UI code

**When to use the main [`ratatui`](#ratatui) crate:**

- Building applications (recommended - includes macros when the `macros` feature is enabled)
- You want the convenience of having everything available

For detailed information about the workspace organization, see [ARCHITECTURE.md].

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`constraint!`](#constraint) | macro | Creates a single constraint. |
| [`constraints!`](#constraints) | macro | Creates an array of constraints. |
| [`vertical!`](#vertical) | macro | Creates a vertical layout with specified constraints. |
| [`horizontal!`](#horizontal) | macro | Creates a horizontal layout with specified constraints. |
| [`line!`](#line) | macro | A macro for creating a [`Line`] using vec! syntax. |
| [`row!`](#row) | macro | A macro for creating a [`Row`] using vec! syntax. |
| [`span!`](#span) | macro | A macro for creating a [`Span`] using formatting syntax. |
| [`text!`](#text) | macro | A macro for creating a [`Text`] using vec! syntax. |

## Macros

### `constraint!`

Creates a single constraint.

If creating an array of constraints, you probably want to use
`constraints!` instead.

# Examples

```rust
use ratatui_core::layout::Constraint;
use ratatui_macros::constraint;
assert_eq!(constraint!(>= 3 + 4), Constraint::Min(7));
assert_eq!(constraint!(<= 3 + 4), Constraint::Max(7));
assert_eq!(constraint!(== 1 / 3), Constraint::Ratio(1, 3));
assert_eq!(constraint!(== 3), Constraint::Length(3));
assert_eq!(constraint!(== 10 %), Constraint::Percentage(10));
assert_eq!(constraint!(*= 1), Constraint::Fill(1));
```

### `constraints!`

Creates an array of constraints.

See `constraint!` for more information.

If you want to solve the constraints, see
`vertical!` and `horizontal!` macros.

# Examples

```rust
use ratatui_macros::constraints;
assert_eq!(constraints![==5, ==30%, >=3, <=1, ==1/2].len(), 5);
assert_eq!(constraints![==5; 5].len(), 5);
```

```rust
use ratatui_core::layout::Constraint;
use ratatui_macros::constraints;
assert_eq!(
    constraints![==50, ==30%, >=3, <=1, ==1/2, *=1],
    [
        Constraint::Length(50),
        Constraint::Percentage(30),
        Constraint::Min(3),
        Constraint::Max(1),
        Constraint::Ratio(1, 2),
        Constraint::Fill(1),
    ]
)
```

### `vertical!`

Creates a vertical layout with specified constraints.

It accepts a series of constraints and applies them to create a vertical layout. The constraints
can include fixed sizes, minimum and maximum sizes, percentages, and ratios.

See [`constraint!`](#constraint)  or [`constraints!`](#constraints) for more information.

# Examples

```rust
// Vertical layout with a fixed size and a percentage constraint
use ratatui_macros::vertical;
vertical![== 50, == 30%];
```

### `horizontal!`

Creates a horizontal layout with specified constraints.

It takes a series of constraints and applies them to create a horizontal layout. The constraints
can include fixed sizes, minimum and maximum sizes, percentages, and ratios.

See [`constraint!`](#constraint)  or [`constraints!`](#constraints) for more information.

# Examples

```rust
// Horizontal layout with a ratio constraint and a minimum size constraint
use ratatui_macros::horizontal;
horizontal![== 1/3, >= 100];
```

### `line!`

A macro for creating a [`Line`](#line) using vec! syntax.

`line!` is similar to the `vec!` macro, but it returns a [`Line`](#line) instead of a `Vec`.

# Examples

* Create a [`Line`](#line) containing a vector of [`Span`](#span)s:

```rust
use ratatui_core::style::Stylize;
use ratatui_macros::line;

let line = line!["hello", "world"];
let line = line!["hello".red(), "world".red().bold()];
```

* Create a [`Line`](#line) from a given [`Span`](#span) repeated some amount of times:

```rust
use ratatui_macros::line;
let line = line!["hello"; 2];
```

* Use `span!` macro inside [`line!`](../ratatui_core/symbols/line.md) macro for formatting.

```rust
use ratatui_core::style::Modifier;
use ratatui_macros::{line, span};

let line = line![span!("hello {}", "world"), span!(Modifier::BOLD; "goodbye {}", "world")];
```

### `row!`

A macro for creating a [`Row`](#row) using vec! syntax.

`row!` is similar to the `vec!` macro, but it returns a [`Row`](#row) instead of a `Vec`.

# Examples

* Create a [`Row`](#row) containing a vector of [`Cell`](#cell)s:

```rust
use ratatui_core::style::Stylize;
use ratatui_macros::row;

let row = row!["hello", "world"];
let row = row!["hello".red(), "world".red().bold()];
```

* Create an empty [`Row`](#row):

```rust
use ratatui_macros::row;
let empty_row = row![];
```

* Create a [`Row`](#row) from a given [`Cell`](#cell) repeated some amount of times:

```rust
use ratatui_macros::row;
let row = row!["hello"; 2];
```

* Use `text!`, `line!` or `span!` macro inside `row!` macro.

```rust
use ratatui_core::style::{Modifier};
use ratatui_macros::{row, line, text, span};

let row = row![
    line!["hello", "world"], span!(Modifier::BOLD; "goodbye {}", "world"),
    text!["hello", "world"],
];
```

### `span!`

A macro for creating a [`Span`](#span) using formatting syntax.

`span!` is similar to the `format!` macro, but it returns a [`Span`](#span) instead of a `String`. In
addition, it also accepts an expression for the first argument, which will be converted to a
string using the `format!` macro.

If semicolon follows the first argument, then the first argument is a [`Style`](#style) and a styled
[`Span`](#span) will be created. Otherwise, the [`Span`](#span) will be created as a raw span (i.e. with style
set to `Style::default()`).

# Examples

```rust
use ratatui_core::style::{Color, Modifier, Style, Stylize};
use ratatui_macros::span;

let content = "content";

// expression
let span = span!(content);

// format string
let span = span!("test content");
let span = span!("test {}", "content");
let span = span!("{} {}", "test", "content");
let span = span!("test {content}");
let span = span!("test {content}", content = "content");

// with format specifiers
let span = span!("test {:4}", 123);
let span = span!("test {:04}", 123);

let style = Style::new().green();

// styled expression
let span = span!(style; content);

// styled format string
let span = span!(style; "test content");
let span = span!(style; "test {}", "content");
let span = span!(style; "{} {}", "test", "content");
let span = span!(style; "test {content}");
let span = span!(style; "test {content}", content = "content");

// accepts any type that is convertible to Style
let span = span!(Style::new().green(); "test {content}");
let span = span!(Color::Green; "test {content}");
let span = span!(Modifier::BOLD; "test {content}");

// with format specifiers
let span = span!(style; "test {:4}", 123);
let span = span!(style; "test {:04}", 123);
```

# Note

The first parameter must be a formatting specifier followed by a comma OR anything that can be
converted into a [`Style`](#style) followed by a semicolon.

For example, the following will fail to compile:

```compile_fail
use ratatui::prelude::*;
use ratatui_macros::span;
let span = span!(Modifier::BOLD, "hello world");
```

But this will work:

```rust
use ratatui_core::style::{Modifier};
use ratatui_macros::span;
let span = span!(Modifier::BOLD; "hello world");
```

The following will fail to compile:

```compile_fail
use ratatui::prelude::*;
use ratatui_macros::span;
let span = span!("hello", "world");
```

But this will work:

```rust
use ratatui_macros::span;
let span = span!("hello {}", "world");
```

### `text!`

A macro for creating a [`Text`](#text) using vec! syntax.

`text!` is similar to the `vec!` macro, but it returns a [`Text`](#text) instead of a `Vec`.

# Examples

* Create a [`Text`](#text) containing a vector of [`Line`](#line)s:

```rust
use ratatui_core::style::Stylize;
use ratatui_macros::text;

let text = text!["hello", "world"];
let text = text!["hello".red(), "world".red().bold()];
```

* Create a [`text`](#text) from a given [`Line`](#line) repeated some amount of times:

```rust
use ratatui_macros::text;
let text = text!["hello"; 2];
```

* Use [`line!`](../ratatui_core/symbols/line.md) or `span!` macro inside `text!` macro.

```rust
use ratatui_core::style::{Modifier};
use ratatui_macros::{line, text, span};

let text = text![line!["hello", "world"], span!(Modifier::BOLD; "goodbye {}", "world")];
```

