# Crate `ratatui_crossterm`

This crate provides [`CrosstermBackend`](#crosstermbackend), an implementation of the `Backend` trait for the
[Ratatui] library. It uses the [Crossterm] library for all terminal manipulation.

Most application authors should start with the main [`ratatui`](#ratatui) crate, which re-exports this
backend and provides higher-level setup helpers. Reach for `ratatui-crossterm` directly when
you need to depend on the backend crate itself, choose the Crossterm version explicitly, or
integrate with Crossterm APIs beyond Ratatui's higher-level surface.

# Crossterm Version and Re-export

`ratatui-crossterm` requires you to specify a version of the [Crossterm] library to be used.
This is managed via feature flags. The highest enabled feature flag of the available
`crossterm_0_xx` features (e.g., `crossterm_0_28`, `crossterm_0_29`) takes precedence. These
features determine which version of Crossterm is compiled and used by the backend. Feature
unification may mean that any crate in your dependency graph that chooses to depend on a
specific version of Crossterm may be affected by the feature flags you enable.

Ratatui will support at least the two most recent versions of Crossterm (though we may increase
this if crossterm release cadence increases). We will remove support for older versions in major
(0.x) releases of `ratatui-crossterm`, and we may add support for newer versions in minor
(0.x.y) releases.

To promote interoperability within the [Ratatui] ecosystem, the selected Crossterm crate is
re-exported as `ratatui_crossterm::crossterm`. This re-export is essential for authors of widget
libraries or any applications that need to perform direct Crossterm operations while ensuring
compatibility with the version used by `ratatui-crossterm`. By using
`ratatui_crossterm::crossterm` for such operations, developers can avoid version conflicts and
ensure that all parts of their application use a consistent set of Crossterm types and
functions.

For example, if your application's `Cargo.toml` enables the `crossterm_0_29` feature for
`ratatui-crossterm`, then any code using `ratatui_crossterm::crossterm` will refer to the 0.29
version of Crossterm.

For more information on how to use the backend, see the documentation for the
[`CrosstermBackend`](#crosstermbackend) struct.

# Crate Organization

`ratatui-crossterm` is part of the Ratatui workspace that was modularized in version 0.30.0.
This crate provides the [Crossterm] backend implementation for Ratatui.

**When to use `ratatui-crossterm`:**

- You want to depend on the Crossterm backend crate directly
- You need fine-grained control over the selected Crossterm version
- You integrate with Crossterm APIs alongside Ratatui and want the re-exported
  `ratatui_crossterm::crossterm` path

**When to use the main [`ratatui`](#ratatui) crate:**

- Building applications
- You want the common Ratatui path that already includes the Crossterm backend by default
- You want the backend and higher-level terminal setup in one crate

For detailed information about the workspace organization, see [ARCHITECTURE.md].

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`CrosstermBackend`](#crosstermbackend) | struct | A [`Backend`] implementation that uses [Crossterm] to render to the terminal. |
| [`IntoCrossterm`](#intocrossterm) | trait | A trait for converting a Ratatui type to a Crossterm type. |
| [`FromCrossterm`](#fromcrossterm) | trait | A trait for converting a Crossterm type to a Ratatui type. |

## Structs

### `CrosstermBackend<W: Write>`

```rust
struct CrosstermBackend<W: Write> {
    // [REDACTED: Private Fields]
}
```

A `Backend` implementation that uses [Crossterm] to render to the terminal.

The `CrosstermBackend` struct is a wrapper around a writer implementing `Write`, which is
used to send commands to the terminal. It provides methods for drawing content, manipulating
the cursor, and clearing the terminal screen.

Most applications should not call the methods on `CrosstermBackend` directly, but will instead
use the `Terminal` struct, which provides a more ergonomic interface.

Usually applications will enable raw mode and switch to alternate screen mode after creating
a `CrosstermBackend`. This is done by calling `crossterm::terminal::enable_raw_mode` and
`crossterm::terminal::EnterAlternateScreen` (and the corresponding disable/leave functions
when the application exits). This is not done automatically by the backend because it is
possible that the application may want to use the terminal for other purposes (like showing
help text) before entering alternate screen mode.

# Example

```rust,ignore
use std::io::{stderr, stdout};

use crossterm::ExecutableCommand;
use crossterm::terminal::{
    EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode,
};
use ratatui::Terminal;
use ratatui::backend::CrosstermBackend;

let mut backend = CrosstermBackend::new(stdout());
// or
let backend = CrosstermBackend::new(stderr());
let mut terminal = Terminal::new(backend)?;

enable_raw_mode()?;
stdout().execute(EnterAlternateScreen)?;

terminal.clear()?;
terminal.draw(|frame| {
    // -- snip --
})?;

stdout().execute(LeaveAlternateScreen)?;
disable_raw_mode()?;

std::io::Result::Ok(())
```

See the the [Examples] directory for more examples. See the `backend` module documentation
for more details on raw mode and alternate screen.

#### Implementations

- `const fn new(writer: W) -> Self`

  Creates a new `CrosstermBackend` with the given writer.

  

  Most applications will use either [`stdout`](std::io::stdout) or

  [`stderr`](std::io::stderr) as writer. See the [FAQ] to determine which one to use.

  

  # Example

  

  ```rust,ignore

  use std::io::stdout;

  

  use ratatui::backend::CrosstermBackend;

  

  let backend = CrosstermBackend::new(stdout());

  ```

- `const fn writer(&self) -> &W`

   Gets the writer.

  # Stability

  

  **This API is marked as unstable** and is only available when the `unstable-backend-writer`

  crate feature is enabled. This comes with no stability guarantees, and could be changed

  or removed at any time.

  The tracking issue is: `https://github.com/ratatui/ratatui/pull/991`.

- `const fn writer_mut(&mut self) -> &mut W`

   Gets the writer as a mutable reference.

  

   Note: writing to the writer may cause incorrect output after the write. This is due to the

   way that the Terminal implements diffing Buffers.

  # Stability

  

  **This API is marked as unstable** and is only available when the `unstable-backend-writer`

  crate feature is enabled. This comes with no stability guarantees, and could be changed

  or removed at any time.

  The tracking issue is: `https://github.com/ratatui/ratatui/pull/991`.

#### Trait Implementations

##### `impl<W> Backend for CrosstermBackend<W>`

- `type Error = Error`

- `fn draw<'a, I>(&mut self, content: I) -> io::Result<()>`

- `fn hide_cursor(&mut self) -> io::Result<()>`

- `fn show_cursor(&mut self) -> io::Result<()>`

- `fn get_cursor_position(&mut self) -> io::Result<Position>`

- `fn set_cursor_position<P: Into<Position>>(&mut self, position: P) -> io::Result<()>`

- `fn clear(&mut self) -> io::Result<()>`

- `fn clear_region(&mut self, clear_type: ClearType) -> io::Result<()>`

- `fn append_lines(&mut self, n: u16) -> io::Result<()>`

- `fn size(&self) -> io::Result<Size>`

- `fn window_size(&mut self) -> io::Result<WindowSize>`

- `fn flush(&mut self) -> io::Result<()>`

##### `impl<W: clone::Clone + Write> Clone for CrosstermBackend<W>`

- `fn clone(&self) -> CrosstermBackend<W>` — [`CrosstermBackend`](#crosstermbackend)

##### `impl<W: fmt::Debug + Write> Debug for CrosstermBackend<W>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl<W: default::Default + Write> Default for CrosstermBackend<W>`

- `fn default() -> CrosstermBackend<W>` — [`CrosstermBackend`](#crosstermbackend)

##### `impl<W: cmp::Eq + Write> Eq for CrosstermBackend<W>`

##### `impl<K> Equivalent for CrosstermBackend<W>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl ExecutableCommand for CrosstermBackend<W>`

- `fn execute(&mut self, command: impl Command) -> Result<&mut T, Error>`

  Executes the given command directly.

  

  The given command its ANSI escape code will be written and flushed onto `Self`.

  

  # Arguments

  

  - [Command](./trait.Command.html)

  

    The command that you want to execute directly.

  

  # Example

  

  ```rust

  use std::io;

  use crossterm::{ExecutableCommand, style::Print};

  

  fn main() -> io::Result<()> {

       // will be executed directly

        io::stdout()

          .execute(Print("sum:\n".to_string()))?

          .execute(Print(format!("1 + 1= {} ", 1 + 1)))?;

  

        Ok(())

  

       // ==== Output ====

       // sum:

       // 1 + 1 = 2

  }

  ```

  

  Have a look over at the [Command API](./index.html#command-api) for more details.

  

  # Notes

  

  * In the case of UNIX and Windows 10, ANSI codes are written to the given 'writer'.

  * In case of Windows versions lower than 10, a direct WinAPI call will be made.

    The reason for this is that Windows versions lower than 10 do not support ANSI codes,

    and can therefore not be written to the given `writer`.

    Therefore, there is no difference between [execute](./trait.ExecutableCommand.html)

    and [queue](./trait.QueueableCommand.html) for those old Windows versions.

##### `impl<W: hash::Hash + Write> Hash for CrosstermBackend<W>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for CrosstermBackend<W>`

##### `impl<W: cmp::PartialEq + Write> PartialEq for CrosstermBackend<W>`

- `fn eq(&self, other: &CrosstermBackend<W>) -> bool` — [`CrosstermBackend`](#crosstermbackend)

##### `impl QueueableCommand for CrosstermBackend<W>`

- `fn queue(&mut self, command: impl Command) -> Result<&mut T, Error>`

  Queues the given command for further execution.

  

  Queued commands will be executed in the following cases:

  

  * When `flush` is called manually on the given type implementing `io::Write`.

  * The terminal will `flush` automatically if the buffer is full.

  * Each line is flushed in case of `stdout`, because it is line buffered.

  

  # Arguments

  

  - [Command](./trait.Command.html)

  

    The command that you want to queue for later execution.

  

  # Examples

  

  ```rust

  use std::io::{self, Write};

  use crossterm::{QueueableCommand, style::Print};

  

   fn main() -> io::Result<()> {

      let mut stdout = io::stdout();

  

      // `Print` will executed executed when `flush` is called.

      stdout

          .queue(Print("foo 1\n".to_string()))?

          .queue(Print("foo 2".to_string()))?;

  

      // some other code (no execution happening here) ...

  

      // when calling `flush` on `stdout`, all commands will be written to the stdout and therefore executed.

      stdout.flush()?;

  

      Ok(())

  

      // ==== Output ====

      // foo 1

      // foo 2

  }

  ```

  

  Have a look over at the [Command API](./index.html#command-api) for more details.

  

  # Notes

  

  * In the case of UNIX and Windows 10, ANSI codes are written to the given 'writer'.

  * In case of Windows versions lower than 10, a direct WinAPI call will be made.

    The reason for this is that Windows versions lower than 10 do not support ANSI codes,

    and can therefore not be written to the given `writer`.

    Therefore, there is no difference between [execute](./trait.ExecutableCommand.html)

    and [queue](./trait.QueueableCommand.html) for those old Windows versions.

##### `impl<W: Write> StructuralPartialEq for CrosstermBackend<W>`

##### `impl<W> SynchronizedUpdate for CrosstermBackend<W>`

- `fn sync_update<T>(&mut self, operations: impl FnOnce(&mut W) -> T) -> Result<T, Error>`

  Performs a set of actions within a synchronous update.

  

  Updates will be suspended in the terminal, the function will be executed against self,

  updates will be resumed, and a flush will be performed.

  

  # Arguments

  

  - Function

  

      A function that performs the operations that must execute in a synchronized update.

  

  # Examples

  

  ```rust

  use std::io;

  use crossterm::{ExecutableCommand, SynchronizedUpdate, style::Print};

  

  fn main() -> io::Result<()> {

      let mut stdout = io::stdout();

  

      stdout.sync_update(|stdout| {

          stdout.execute(Print("foo 1\n".to_string()))?;

          stdout.execute(Print("foo 2".to_string()))?;

          // The effects of the print command will not be present in the terminal

          // buffer, but not visible in the terminal.

          std::io::Result::Ok(())

      })?;

  

      // The effects of the commands will be visible.

  

      Ok(())

  

      // ==== Output ====

      // foo 1

      // foo 2

  }

  ```

  

  # Notes

  

  This command is performed only using ANSI codes, and will do nothing on terminals that do not support ANSI

  codes, or this specific extension.

  

  When rendering the screen of the terminal, the Emulator usually iterates through each visible grid cell and

  renders its current state. With applications updating the screen a at higher frequency this can cause tearing.

  

  This mode attempts to mitigate that.

  

  When the synchronization mode is enabled following render calls will keep rendering the last rendered state.

  The terminal Emulator keeps processing incoming text and sequences. When the synchronized update mode is disabled

  again the renderer may fetch the latest screen buffer state again, effectively avoiding the tearing effect

  by unintentionally rendering in the middle a of an application screen update.

##### `impl<W> Write for CrosstermBackend<W>`

- `fn write(&mut self, buf: &[u8]) -> io::Result<usize>`

  Writes a buffer of bytes to the underlying buffer.

- `fn flush(&mut self) -> io::Result<()>`

  Flushes the underlying buffer.

## Traits

### `IntoCrossterm<C>`

```rust
trait IntoCrossterm<C> { ... }
```

A trait for converting a Ratatui type to a Crossterm type.

This trait is needed for avoiding the orphan rule when implementing `From` for crossterm types
once these are moved to a separate crate.

#### Required Methods

- `fn into_crossterm(self) -> C`

  Converts the ratatui type to a crossterm type.

#### Implementors

- `ratatui_core::style::Color`
- `ratatui_core::style::Style`

### `FromCrossterm<C>`

```rust
trait FromCrossterm<C> { ... }
```

A trait for converting a Crossterm type to a Ratatui type.

This trait is needed for avoiding the orphan rule when implementing `From` for crossterm types
once these are moved to a separate crate.

#### Required Methods

- `fn from_crossterm(value: C) -> Self`

  Converts the crossterm type to a ratatui type.

#### Implementors

- `ratatui_core::style::Color`
- `ratatui_core::style::Modifier`
- `ratatui_core::style::Style`

