# Crate `ratatui_termwiz`

This module provides the [`TermwizBackend`](#termwizbackend) implementation for the `Backend` trait. It uses
the [Termwiz] crate to interact with the terminal.

Most application authors should start with the main [`ratatui`](#ratatui) crate and only depend on
`ratatui-termwiz` directly when they specifically want the Termwiz backend or its advanced
terminal capabilities. This crate is the backend layer, not the primary docs.rs entry point for
building applications.

# Crate Organization

`ratatui-termwiz` is part of the Ratatui workspace that was modularized in version 0.30.0.
This crate provides the [Termwiz] backend implementation for Ratatui.

**When to use `ratatui-termwiz`:**

- You want to depend on the Termwiz backend crate directly
- You need Termwiz's advanced terminal capabilities

**When to use the main [`ratatui`](#ratatui) crate:**

- Building applications
- You want backend selection to stay behind Ratatui's re-exports

For detailed information about the workspace organization, see [ARCHITECTURE.md].

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`TermwizBackend`](#termwizbackend) | struct | A [`Backend`] implementation that uses [Termwiz] to render to the terminal. |
| [`FromTermwiz`](#fromtermwiz) | trait | A trait for converting types from Termwiz to Ratatui. |
| [`IntoTermwiz`](#intotermwiz) | trait | A trait for converting types from Ratatui to Termwiz. |

## Structs

### `TermwizBackend`

```rust
struct TermwizBackend {
    // [REDACTED: Private Fields]
}
```

A `Backend` implementation that uses [Termwiz] to render to the terminal.

The `TermwizBackend` struct is a wrapper around a `BufferedTerminal`, which is used to send
commands to the terminal. It provides methods for drawing content, manipulating the cursor, and
clearing the terminal screen.

Most applications should not call the methods on `TermwizBackend` directly, but will instead
use the [`Terminal`](#terminal) struct, which provides a more ergonomic interface.

This backend automatically enables raw mode and switches to the alternate screen when it is
created using the `TermwizBackend::new` method (and disables raw mode and returns to the main
screen when dropped). Use the `TermwizBackend::with_buffered_terminal` to create a new
instance with a custom `BufferedTerminal` if this is not desired.

# Example

```rust,no_run
use ratatui::Terminal;
use ratatui::backend::TermwizBackend;

let backend = TermwizBackend::new()?;
let mut terminal = Terminal::new(backend)?;

terminal.clear()?;
terminal.draw(|frame| {
    // -- snip --
})?;
std::result::Result::Ok::<(), Box<dyn std::error::Error>>(())
```

See the the [Examples] directory for more examples. See the `backend` module documentation
for more details on raw mode and alternate screen.

#### Implementations

- `fn new() -> Result<Self, Box<dyn Error>>`

  Creates a new Termwiz backend instance.

  

  The backend will automatically enable raw mode and enter the alternate screen.

  

  # Errors

  

  Returns an error if unable to do any of the following:

  - query the terminal capabilities.

  - enter raw mode.

  - enter the alternate screen.

  - create the system or buffered terminal.

  

  # Example

  

  ```rust,no_run

  use ratatui::backend::TermwizBackend;

  

  let backend = TermwizBackend::new()?;

  Ok::<(), Box<dyn std::error::Error>>(())

  ```

- `const fn with_buffered_terminal(instance: BufferedTerminal<SystemTerminal>) -> Self`

  Creates a new Termwiz backend instance with the given buffered terminal.

- `const fn buffered_terminal(&self) -> &BufferedTerminal<SystemTerminal>`

  Returns a reference to the buffered terminal used by the backend.

- `const fn buffered_terminal_mut(&mut self) -> &mut BufferedTerminal<SystemTerminal>`

  Returns a mutable reference to the buffered terminal used by the backend.

#### Trait Implementations

##### `impl Backend for TermwizBackend`

- `type Error = Error`

- `fn draw<'a, I>(&mut self, content: I) -> io::Result<()>`

- `fn hide_cursor(&mut self) -> io::Result<()>`

- `fn show_cursor(&mut self) -> io::Result<()>`

- `fn get_cursor_position(&mut self) -> io::Result<Position>`

- `fn set_cursor_position<P: Into<Position>>(&mut self, position: P) -> io::Result<()>`

- `fn clear(&mut self) -> io::Result<()>`

- `fn clear_region(&mut self, clear_type: ClearType) -> io::Result<()>`

- `fn size(&self) -> io::Result<Size>`

- `fn window_size(&mut self) -> io::Result<WindowSize>`

- `fn flush(&mut self) -> io::Result<()>`

##### `impl IntoEither for TermwizBackend`

##### `impl Same for TermwizBackend`

- `type Output = T`

## Traits

### `FromTermwiz<T>`

```rust
trait FromTermwiz<T> { ... }
```

A trait for converting types from Termwiz to Ratatui.

This trait replaces the `From` trait for converting types from Termwiz to Ratatui. It is
necessary because the `From` trait is not implemented for types defined in external crates.

#### Required Methods

- `fn from_termwiz(termwiz: T) -> Self`

  Converts the given Termwiz type to the Ratatui type.

#### Implementors

- `ratatui_core::style::Color`
- `ratatui_core::style::Modifier`
- `ratatui_core::style::Style`

### `IntoTermwiz<T>`

```rust
trait IntoTermwiz<T> { ... }
```

A trait for converting types from Ratatui to Termwiz.

This trait replaces the `Into` trait for converting types from Ratatui to Termwiz. It is
necessary because the `Into` trait is not implemented for types defined in external crates.

#### Required Methods

- `fn into_termwiz(self) -> T`

  Converts the given Ratatui type to the Termwiz type.

#### Implementors

- `ratatui_core::style::Color`

