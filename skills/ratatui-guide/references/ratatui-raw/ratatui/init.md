*[ratatui](./index.md) / [init](#)*

---

# Module `init`

Terminal initialization and restoration functions.

This module provides a set of convenience functions for initializing and restoring terminal
state when creating Ratatui applications. These functions handle the common setup and teardown
tasks required for terminal user interfaces.

All functions in this module use the [`CrosstermBackend`](./backend.md) by default, which provides excellent
cross-platform compatibility and is the recommended backend for most applications. The
[`DefaultTerminal`](#defaultterminal) type alias encapsulates this choice, providing a ready-to-use terminal
configuration that works well across different operating systems. For more information about
backend choices and alternatives, see the [`backend`](`crate::backend`) module.

Once you have initialized a terminal using the functions in this module, you can use it to
[draw the UI](`crate#drawing-the-ui`) and [handle events](`crate#handling-events`). For more
information about building widgets for your application, see the [`widgets`](`crate::widgets`)
module.

**Note**: All functions and types in this module are re-exported at the crate root for
convenience, so you can call `ratatui::run()`, `ratatui::init()`, etc. instead of
`ratatui::init::run()`, `ratatui::init::init()`, etc.

# Which function should I start with?

Start with the simplest path that fits your application:

1. Use [`run`](#run) for the normal case: Ratatui owns setup and cleanup around your application
   closure.
2. Move to [`init`](#init) / [`restore`](#restore) when you want explicit control over setup, teardown, or event
   loop structure.
3. Use [`try_init`](#try-init) / [`try_restore`](#try-restore) when you want the same control but need explicit error
   handling instead of panicking or printing cleanup failures.
4. Use [`init_with_options`](#init-with-options) / [`try_init_with_options`](#try-init-with-options) when you need a custom
   [`TerminalOptions`](./index.md) such as inline or fixed viewports.
5. Construct [`Terminal`](./prelude.md) manually only when these helpers do not match the backend or terminal
   lifecycle you need.

# Available Types and Functions

## Types

- [`DefaultTerminal`](#defaultterminal) - A type alias for `Terminal<CrosstermBackend<Stdout>>`, providing a
  reasonable default terminal configuration for most applications. All initialization functions
  return this type.

## Functions

The module provides several related functions that handle different initialization scenarios:

- [`run`](#run) - Initializes a terminal, runs a closure, and automatically restores the terminal
  state. This is the simplest way to run a Ratatui application and handles all setup and cleanup
  automatically.
- [`init`](#init) - Creates a terminal with reasonable defaults including alternate screen and raw
  mode. Panics on failure.
- [`try_init`](#try-init) - Same as [`init`](#init) but returns a `Result` instead of panicking.
- [`init_with_options`](#init-with-options) - Creates a terminal with custom [`TerminalOptions`](./index.md), enabling raw mode
  but not alternate screen. Panics on failure.
- [`try_init_with_options`](#try-init-with-options) - Same as [`init_with_options`](#init-with-options) but returns a `Result` instead of
  panicking.
- [`restore`](#restore) - Restores the terminal to its original state. Prints errors to stderr but does
  not panic.
- [`try_restore`](#try-restore) - Same as [`restore`](#restore) but returns a `Result` instead of printing errors.

# Usage Guide

Start with the normal fullscreen application path:

```rust,no_run
fn main() -> std::io::Result<()> {
    ratatui::run(|terminal| {
        loop {
            terminal.draw(|frame| frame.render_widget("Hello, world!", frame.area()))?;
            if crossterm::event::read()?.is_key_press() {
                break Ok(());
            }
        }
    })
}
```

Then add resize-aware redraws to the event loop:

```rust,no_run
use crossterm::event::{self, Event, KeyCode, KeyEventKind};

fn main() -> std::io::Result<()> {
    ratatui::run(|terminal| {
        loop {
            terminal.draw(|frame| {
                frame.render_widget("Resize the terminal or press q to quit", frame.area());
            })?;

            match event::read()? {
                Event::Resize(_, _) => {
                    // The next `draw` pass re-renders the UI at the new size.
                }
                Event::Key(key)
                    if key.kind == KeyEventKind::Press && key.code == KeyCode::Char('q') =>
                {
                    break Ok(());
                }
                _ => {}
            }
        }
    })
}
```

Reach for [`init`](#init) / [`restore`](#restore) when you want manual control over setup and teardown:

```rust,no_run
// Using init() - panics on failure
let mut terminal = ratatui::init();
// ... app logic ...
ratatui::restore();

// Using try_init() - returns Result for custom error handling
let mut terminal = ratatui::try_init()?;
// ... app logic ...
ratatui::try_restore()?;
Ok::<(), std::io::Error>(())
```

Use [`init_with_options`](#init-with-options) when the UI should not use the normal fullscreen path, for example
for an inline UI that continues to share the terminal with earlier output:

```rust,no_run
use crossterm::event::{self, Event, KeyCode, KeyEventKind};
use ratatui::widgets::Widget;
use ratatui::{TerminalOptions, Viewport};

let options = TerminalOptions {
    viewport: Viewport::Inline(10),
};

let mut terminal = ratatui::init_with_options(options);

terminal.insert_before(1, |buf| {
    "> Ready".render(buf.area, buf);
})?;

loop {
    terminal.draw(|frame| {
        frame.render_widget("Inline UI lives below earlier terminal output", frame.area());
    })?;

    if matches!(
        event::read()?,
        Event::Key(key)
            if key.kind == KeyEventKind::Press && key.code == KeyCode::Char('q')
    ) {
        break;
    }
}

ratatui::restore();

// Using try_init_with_options() - returns Result for custom error handling
let options = TerminalOptions {
    viewport: Viewport::Inline(10),
};
let mut terminal = ratatui::try_init_with_options(options)?;
terminal.draw(|frame| {
    frame.render_widget("Inline UI", frame.area());
})?;
ratatui::try_restore()?;
Ok::<(), std::io::Error>(())
```

These higher-level helpers are the normal application path. Manual [`Terminal`](./prelude.md) construction is
still available for custom backends and specialized integrations, but it is an advanced path.

For cleanup, use [`restore`](#restore) in most cases where you want to attempt restoration but don't need
to handle errors (they are printed to stderr). Use [`try_restore`](#try-restore) when you need to handle
restoration errors, perhaps to retry or provide user feedback.

Once you have a terminal set up, continue with the main loop to [draw the
UI](`crate#drawing-the-ui`) and [handle events](`crate#handling-events`). See the [main crate
documentation](`crate`) for comprehensive examples of complete applications.

# Key Differences

| Function | Alternate Screen | Raw Mode | Error Handling | Use Case |
|----------|------------------|----------|----------------|----------|
| [`run`](#run) | ✓ | ✓ | Auto-cleanup | Simple apps |
| [`init`](#init) | ✓ | ✓ | Panic | Standard full-screen apps |
| [`try_init`](#try-init) | ✓ | ✓ | Result | Standard apps with error handling |
| [`init_with_options`](#init-with-options) | ✗ | ✓ | Panic | Custom viewport apps |
| [`try_init_with_options`](#try-init-with-options) | ✗ | ✓ | Result | Custom viewport with error handling |

# Panic Hook

All initialization functions install a panic hook that automatically restores the terminal
state before panicking. This ensures that even if your application panics, the terminal will
be left in a usable state.

**Important**: Call the initialization functions *after* installing any other panic hooks to
ensure the terminal is restored before other hooks run.

## Contents

- [Functions](#functions)
  - [`run`](#run)
  - [`init`](#init)
  - [`try_init`](#try-init)
  - [`init_with_options`](#init-with-options)
  - [`try_init_with_options`](#try-init-with-options)
  - [`restore`](#restore)
  - [`try_restore`](#try-restore)
- [Type Aliases](#type-aliases)
  - [`DefaultTerminal`](#defaultterminal)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`run`](#run) | fn | Run a closure with a terminal initialized with reasonable defaults for most applications. |
| [`init`](#init) | fn | Initialize a terminal with reasonable defaults for most applications. |
| [`try_init`](#try-init) | fn | Try to initialize a terminal using reasonable defaults for most applications. |
| [`init_with_options`](#init-with-options) | fn | Initialize a terminal with the given options and reasonable defaults. |
| [`try_init_with_options`](#try-init-with-options) | fn | Try to initialize a terminal with the given options and reasonable defaults. |
| [`restore`](#restore) | fn | Restores the terminal to its original state. |
| [`try_restore`](#try-restore) | fn | Restore the terminal to its original state. |
| [`DefaultTerminal`](#defaultterminal) | type | A type alias for the default terminal type. |

## Functions

### `run`

```rust
fn run<F, R>(f: F) -> R
where
    F: FnOnce(&mut DefaultTerminal) -> R
```

Run a closure with a terminal initialized with reasonable defaults for most applications.

This function creates a new [`DefaultTerminal`](#defaultterminal) with [`init`](#init) and then runs the given closure
with a mutable reference to the terminal. After the closure completes, the terminal is restored
to its original state with [`restore`](#restore).

This function is a convenience wrapper around [`init`](#init) and [`restore`](#restore), and is useful for simple
applications that need a terminal with reasonable defaults for the entire lifetime of the
application.

See the [module-level documentation](mod@crate::init) for a comparison of all initialization
functions and guidance on when to use each one.

# Examples

A simple example where the app logic is contained in the closure:

```rust,no_run
use crossterm::event;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    ratatui::run(|terminal| {
        loop {
            terminal.draw(|frame| frame.render_widget("Hello, world!", frame.area()))?;
            if event::read()?.is_key_press() {
                break Ok(());
            }
        }
    })
}
```

A more complex example where the app logic is contained in a separate function:

```rust,no_run
use crossterm::event;

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn main() -> Result<()> {
    ratatui::run(app)
}

fn app(terminal: &mut ratatui::DefaultTerminal) -> Result<()> {
    const GREETING: &str = "Hello, world!";
    loop {
        terminal.draw(|frame| frame.render_widget(format!("{GREETING}"), frame.area()))?;
        if matches!(event::read()?, event::Event::Key(_)) {
            break Ok(());
        }
    }
}
```

Once the app logic becomes more complex, it may be beneficial to move the app logic into a
separate struct. This allows the app logic to be split into multiple methods with each having
access to the state of the app. This can make the app logic easier to understand and maintain.

```rust,no_run
use crossterm::event;

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn main() -> Result<()> {
    let mut app = App::new();
    ratatui::run(|terminal| app.run(terminal))
}

struct App {
    should_quit: bool,
    name: String,
}

impl App {
    fn new() -> Self {
        Self {
            should_quit: false,
            name: "world".to_string(),
        }
    }

    fn run(&mut self, terminal: &mut ratatui::DefaultTerminal) -> Result<()> {
        while !self.should_quit {
            terminal.draw(|frame| frame.render_widget("Hello, world!", frame.area()))?;
            self.handle_events()?;
        }
        Ok(())
    }

    fn render(&mut self, frame: &mut ratatui::Frame) -> Result<()> {
        let greeting = format!("Hello, {}!", self.name);
        frame.render_widget(greeting, frame.area());
        Ok(())
    }

    fn handle_events(&mut self) -> Result<()> {
        if event::read()?.is_key_press() {
            self.should_quit = true;
        }
        Ok(())
    }
}
```

### `init`

```rust
fn init() -> DefaultTerminal
```

Initialize a terminal with reasonable defaults for most applications.

This will create a new [`DefaultTerminal`](#defaultterminal) and initialize it with the following defaults:

- Backend: [`CrosstermBackend`](./backend.md) writing to `Stdout`
- Raw mode is enabled
- Alternate screen buffer enabled
- A panic hook is installed that restores the terminal before panicking. Ensure that this method
  is called after any other panic hooks that may be installed to ensure that the terminal is
  restored before those hooks are called.

For more control over the terminal initialization, use `Terminal::new` or
`Terminal::with_options`.

Ensure that this method is called *after* your app installs any other panic hooks to ensure the
terminal is restored before the other hooks are called.

Generally, use this function instead of [`try_init`](#try-init) to ensure that the terminal is restored
correctly if any of the initialization steps fail. If you need to handle the error yourself, use
[`try_init`](#try-init) instead.

See the [module-level documentation](mod@crate::init) for a comparison of all initialization
functions and guidance on when to use each one.

# Panics

This function will panic if any of the following steps fail:

- Enabling raw mode
- Entering the alternate screen buffer
- Creating the terminal fails due to being unable to calculate the terminal size

# Examples

```rust,no_run
let terminal = ratatui::init();
```

### `try_init`

```rust
fn try_init() -> io::Result<DefaultTerminal>
```

Try to initialize a terminal using reasonable defaults for most applications.

This function will attempt to create a [`DefaultTerminal`](#defaultterminal) and initialize it with the following
defaults:

- Raw mode is enabled
- Alternate screen buffer enabled
- A panic hook is installed that restores the terminal before panicking.
- A [`Terminal`](./prelude.md) is created using [`CrosstermBackend`](./backend.md) writing to `Stdout`

If any of these steps fail, the error is returned.

Ensure that this method is called *after* your app installs any other panic hooks to ensure the
terminal is restored before the other hooks are called.

Generally, you should use [`init`](#init) instead of this function, as the panic hook installed by this
function will ensure that any failures during initialization will restore the terminal before
panicking. This function is provided for cases where you need to handle the error yourself.

See the [module-level documentation](mod@crate::init) for a comparison of all initialization
functions and guidance on when to use each one.

# Examples

```no_run
let terminal = ratatui::try_init()?;
Ok::<(), std::io::Error>(())
```

### `init_with_options`

```rust
fn init_with_options(options: ratatui_core::terminal::TerminalOptions) -> DefaultTerminal
```

Initialize a terminal with the given options and reasonable defaults.

This function allows the caller to specify a custom [`Viewport`](../ratatui_core/index.md) via the [`TerminalOptions`](./index.md). It
will create a new [`DefaultTerminal`](#defaultterminal) and initialize it with the given options and the following
defaults:

- Raw mode is enabled
- A panic hook is installed that restores the terminal before panicking.

Unlike [`init`](#init), this function does not enter the alternate screen buffer as this may not be
desired in all cases. If you need the alternate screen buffer, you should enable it manually
after calling this function.

For more control over the terminal initialization, use `Terminal::with_options`.

Ensure that this method is called *after* your app installs any other panic hooks to ensure the
terminal is restored before the other hooks are called.

Generally, use this function instead of [`try_init_with_options`](#try-init-with-options) to ensure that the terminal is
restored correctly if any of the initialization steps fail. If you need to handle the error
yourself, use [`try_init_with_options`](#try-init-with-options) instead.

See the [module-level documentation](mod@crate::init) for a comparison of all initialization
functions and guidance on when to use each one.

# Panics

This function will panic if any of the following steps fail:

- Enabling raw mode
- Creating the terminal fails due to being unable to calculate the terminal size

# Examples

```rust,no_run
use ratatui::{TerminalOptions, Viewport};

let options = TerminalOptions {
    viewport: Viewport::Inline(5),
};
let terminal = ratatui::init_with_options(options);
```

### `try_init_with_options`

```rust
fn try_init_with_options(options: ratatui_core::terminal::TerminalOptions) -> io::Result<DefaultTerminal>
```

Try to initialize a terminal with the given options and reasonable defaults.

This function allows the caller to specify a custom [`Viewport`](../ratatui_core/index.md) via the [`TerminalOptions`](./index.md). It
will attempt to create a [`DefaultTerminal`](#defaultterminal) and initialize it with the given options and the
following defaults:

- Raw mode is enabled
- A panic hook is installed that restores the terminal before panicking.

Unlike [`try_init`](#try-init), this function does not enter the alternate screen buffer as this may not be
desired in all cases. If you need the alternate screen buffer, you should enable it manually
after calling this function.

If any of these steps fail, the error is returned.

Ensure that this method is called *after* your app installs any other panic hooks to ensure the
terminal is restored before the other hooks are called.

Generally, you should use [`init_with_options`](#init-with-options) instead of this function, as the panic hook
installed by this function will ensure that any failures during initialization will restore the
terminal before panicking. This function is provided for cases where you need to handle the
error yourself.

See the [module-level documentation](mod@crate::init) for a comparison of all initialization
functions and guidance on when to use each one.

# Examples

```no_run
use ratatui::{TerminalOptions, Viewport};

let options = TerminalOptions {
    viewport: Viewport::Inline(5),
};
let terminal = ratatui::try_init_with_options(options)?;
Ok::<(), std::io::Error>(())
```

### `restore`

```rust
fn restore()
```

Restores the terminal to its original state.

This function should be called before the program exits to ensure that the terminal is
restored to its original state.

This function will attempt to restore the terminal to its original state by performing the
following steps:

1. Raw mode is disabled.
2. The alternate screen buffer is left.

If either of these steps fail, the error is printed to stderr and ignored.

Use this function over [`try_restore`](#try-restore) when you don't need to handle the error yourself, as
ignoring the error is generally the correct behavior when cleaning up before exiting. If you
need to handle the error yourself, use [`try_restore`](#try-restore) instead.

See the [module-level documentation](mod@crate::init) for a comparison of all initialization
functions and guidance on when to use each one.

# Examples

```rust,no_run
ratatui::restore();
```

### `try_restore`

```rust
fn try_restore() -> io::Result<()>
```

Restore the terminal to its original state.

This function will attempt to restore the terminal to its original state by performing the
following steps:

1. Raw mode is disabled.
2. The alternate screen buffer is left.

If either of these steps fail, the error is returned.

Use [`restore`](#restore) instead of this function when you don't need to handle the error yourself, as
ignoring the error is generally the correct behavior when cleaning up before exiting. If you
need to handle the error yourself, use this function instead.

See the [module-level documentation](mod@crate::init) for a comparison of all initialization
functions and guidance on when to use each one.

# Examples

```no_run
ratatui::try_restore()?;
Ok::<(), std::io::Error>(())
```

## Type Aliases

### `DefaultTerminal`

```rust
type DefaultTerminal = ratatui_core::terminal::Terminal<ratatui_crossterm::CrosstermBackend<std::io::Stdout>>;
```

A type alias for the default terminal type.

This is a [`Terminal`](./prelude.md) using the [`CrosstermBackend`](./backend.md) which writes to `Stdout`. This is a
reasonable default for most applications. To use a different backend or output stream, instead
use [`Terminal`](./prelude.md) and a [backend][`crate::backend`](./backend.md) of your choice directly.

