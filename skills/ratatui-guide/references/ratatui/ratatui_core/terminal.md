*[ratatui_core](./index.md) / [terminal](#)*

---

# Module `terminal`

Provides the [`Terminal`](#terminal), [`Frame`](./index.md), [`CompletedFrame`](./index.md), and [`Viewport`](./index.md) types.

This module contains Ratatui's rendering surface abstraction. [`Terminal`](#terminal) ties together a
backend, a viewport, and a double-buffered renderer. In a typical application you create a
`Terminal`, render by calling `Terminal::draw` or `Terminal::try_draw` in a loop, and let
Ratatui diff successive frames so only changed cells are sent to the backend.

[`Frame`](./index.md) is the mutable view used during one render pass. Widgets write into the current
buffer through it, and cursor state for the end of the pass is requested through
`Frame::set_cursor_position`. After rendering completes, Ratatui applies the buffer diff,
updates the cursor, swaps buffers, and flushes any buffered backend output.

This module focuses on rendering contracts. Process-wide terminal setup such as raw mode,
alternate screen handling, and panic restoration lives in the higher-level `ratatui` crate.

# Example

```rust,no_run
#![allow(unexpected_cfgs)]
#[cfg(feature = "crossterm")]
{
use std::io::stdout;

use ratatui::Terminal;
use ratatui::backend::CrosstermBackend;
use ratatui::widgets::Paragraph;

let backend = CrosstermBackend::new(stdout());
let mut terminal = Terminal::new(backend)?;
terminal.draw(|frame| {
    frame.render_widget(Paragraph::new("Hello world!"), frame.area());
})?;
}
Ok::<(), Box<dyn std::error::Error>>(())
```

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`CompletedFrame`](#completedframe) | struct |  |
| [`Frame`](#frame) | struct |  |
| [`Terminal`](#terminal) | struct | An interface to interact and draw [`Frame`]s on the user's terminal. |
| [`TerminalOptions`](#terminaloptions) | struct | Options to pass to [`Terminal::with_options`] |
| [`Viewport`](#viewport) | enum |  |

## Structs

### `CompletedFrame<'a>`

```rust
struct CompletedFrame<'a> {
    pub buffer: &'a crate::buffer::Buffer,
    pub area: crate::layout::Rect,
    pub count: usize,
}
```

`CompletedFrame` represents the state of the terminal after the last successful
`Terminal::draw` / `Terminal::try_draw` render pass has been applied. Therefore, it is only
valid until the next successful draw call.

This lifetime follows Ratatui's double-buffering model: the next render pass swaps buffers via
`Terminal::swap_buffers`, so the previously completed buffer is no longer the current output.

#### Fields

- **`buffer`**: `&'a crate::buffer::Buffer`

  The buffer that was used to draw the last frame.

- **`area`**: `crate::layout::Rect`

  The size of the last frame.

- **`count`**: `usize`

  The frame count indicating the sequence number of this frame.

#### Trait Implementations

##### `impl Clone for CompletedFrame<'a>`

- `fn clone(&self) -> CompletedFrame<'a>` — [`CompletedFrame`](./index.md#completedframe)

##### `impl Debug for CompletedFrame<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for CompletedFrame<'a>`

##### `impl<K> Equivalent for CompletedFrame<'a>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for CompletedFrame<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for CompletedFrame<'a>`

##### `impl PartialEq for CompletedFrame<'a>`

- `fn eq(&self, other: &CompletedFrame<'a>) -> bool` — [`CompletedFrame`](./index.md#completedframe)

##### `impl StructuralPartialEq for CompletedFrame<'a>`

### `Frame<'a>`

```rust
struct Frame<'a> {
    // [REDACTED: Private Fields]
}
```

A consistent view into the terminal state for rendering a single frame.

You usually get a `Frame` from the closure argument of `Terminal::draw` /
`Terminal::try_draw`. For manual rendering, use
[`Terminal::get_frame`](crate::terminal::Terminal::get_frame).

A `Frame` is used to render widgets into Ratatui's current buffer and request the cursor state
for the end of the render pass.

The changes drawn to the frame are applied only to the current [`Buffer`](./index.md). After the closure
returns, the current buffer is compared to the previous buffer and only the changed cells are
sent to the backend. This avoids drawing redundant cells.

#### Implementations

- `const fn area(&self) -> Rect` — [`Rect`](./index.md#rect)

  Returns the area of the current frame.

  

  This is guaranteed not to change during rendering, so may be called multiple times.

  

  If your app listens for a resize event from the backend, ignore that event's dimensions for

  calculations performed during the current render callback and use this value instead. It is

  the area of the buffer that is actually being rendered for this pass.

- `const fn size(&self) -> Rect` — [`Rect`](./index.md#rect)

  Returns the area of the current frame.

  

  This is guaranteed not to change during rendering, so may be called multiple times.

  

  If your app listens for a resize event from the backend, ignore that event's dimensions for

  calculations performed during the current render callback and use this value instead. It is

  the area of the buffer that is actually being rendered for this pass.

- `fn render_widget<W: Widget>(&mut self, widget: W, area: Rect)` — [`Rect`](./index.md#rect)

  Render a [`Widget`](./index.md) to the current buffer using `Widget::render`.

  

  Usually the area argument is the size of the current frame or a sub-area of the current

  frame (which can be obtained using [`Layout`](./index.md) to split the total area).

  

  Rendering writes directly into the current frame buffer. If multiple widgets cover the same

  cells, later renders win for those cells.

  

  # Example

  

  ```rust

  use ratatui_core::{backend::TestBackend, terminal::Terminal};

  let backend = TestBackend::new(5, 5);

  let mut terminal = Terminal::new(backend).unwrap();

  let mut frame = terminal.get_frame();

  use ratatui_core::layout::Rect;

  

  let area = Rect::new(0, 0, 5, 5);

  frame.render_widget("Hello", area);

  ```

- `fn render_stateful_widget<W>(&mut self, widget: W, area: Rect, state: &mut <W as >::State)` — [`Rect`](./index.md#rect), [`StatefulWidget`](./index.md#statefulwidget)

  Render a [`StatefulWidget`](./index.md) to the current buffer using `StatefulWidget::render`.

  

  Usually the area argument is the size of the current frame or a sub-area of the current

  frame (which can be obtained using [`Layout`](./index.md) to split the total area).

  

  The last argument should be an instance of the `StatefulWidget::State` associated to the

  given [`StatefulWidget`](./index.md).

  

  Like `Frame::render_widget`, this writes directly into the current frame buffer. The

  widget owns how it interprets and mutates the provided state.

  

  # Example

  

  ```rust

  use ratatui_core::{backend::TestBackend, buffer::Buffer, layout::Rect, terminal::Terminal};

  let backend = TestBackend::new(5, 5);

  let mut terminal = Terminal::new(backend).unwrap();

  let mut frame = terminal.get_frame();

  use ratatui_core::widgets::StatefulWidget;

  

  struct DemoWidget;

  

  impl StatefulWidget for DemoWidget {

      type State = bool;

  

      fn render(self, area: Rect, buf: &mut Buffer, state: &mut Self::State) {

          let symbol = if *state { "Y" } else { "N" };

          buf[(area.x, area.y)].set_symbol(symbol);

      }

  }

  

  let mut state = true;

  let area = Rect::new(0, 0, 5, 5);

  frame.render_stateful_widget(DemoWidget, area, &mut state);

  ```

- `fn set_cursor_position<P: Into<Position>>(&mut self, position: P)`

  After this frame is rendered, make the cursor visible and put it at the specified `(x, y)`

  coordinates. If this method is not called, the cursor will be hidden.

  

  The cursor is applied after Ratatui flushes the frame's buffer diff to the backend.

  

  Note that this will interfere with calls to `Terminal::hide_cursor`,

  `Terminal::show_cursor`, and `Terminal::set_cursor_position`. Pick one of the APIs and

  stick with it.

  

  

- `fn set_cursor(&mut self, x: u16, y: u16)`

  After this frame is rendered, make the cursor visible and put it at the specified `(x, y)`

  coordinates. If this method is not called, the cursor will be hidden.

  

  Note that this will interfere with calls to `Terminal::hide_cursor`,

  `Terminal::show_cursor`, and `Terminal::set_cursor_position`. Pick one of the APIs and

  stick with it.

  

  

- `const fn buffer_mut(&mut self) -> &mut Buffer` — [`Buffer`](./index.md#buffer)

  Gets the buffer that this `Frame` draws into as a mutable reference.

  

  This is an escape hatch for direct buffer manipulation. Normal applications should prefer

  the widget rendering methods so layout and rendering intent stay visible at the call site.

  

  Use this when tests, custom widgets, or specialized integrations need direct cell access

  during a render pass.

  

  Changes written here are not visible on the backend until the render pass is applied by

  [`Terminal::flush`](crate::terminal::Terminal::flush) or a full

  [`Terminal::draw`](crate::terminal::Terminal::draw) /

  [`Terminal::try_draw`](crate::terminal::Terminal::try_draw) pass.

  

  # Example

  

  ```rust

  use ratatui_core::{backend::TestBackend, terminal::Terminal};

  let backend = TestBackend::new(5, 1);

  let mut terminal = Terminal::new(backend).unwrap();

  let mut frame = terminal.get_frame();

  frame.buffer_mut()[(0, 0)].set_symbol("h");

  ```

- `const fn count(&self) -> usize`

  Returns the current frame count.

  

  This method provides access to the frame count, which is a sequence number indicating

  how many frames have been rendered up to (but not including) this one. It can be used

  for purposes such as animation, performance tracking, or debugging.

  

  Each time a frame has been rendered, this count is incremented,

  providing a consistent way to reference the order and number of frames processed by the

  terminal. When count reaches its maximum value (`usize::MAX`), it wraps around to zero.

  

  This count is particularly useful when dealing with dynamic content or animations where the

  state of the display changes over time. By tracking the frame count, developers can

  synchronize updates or changes to the content with the rendering process.

  

  # Examples

  

  ```rust

  use ratatui_core::{backend::TestBackend, terminal::Terminal};

  let backend = TestBackend::new(5, 5);

  let mut terminal = Terminal::new(backend).unwrap();

  let mut frame = terminal.get_frame();

  let current_count = frame.count();

  println!("Current frame count: {}", current_count);

  ```

#### Trait Implementations

##### `impl Debug for Frame<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl FrameExt for ratatui_core::terminal::Frame<'_>`

##### `impl Hash for Frame<'a>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Frame<'a>`

### `Terminal<B>`

```rust
struct Terminal<B>
where
    B: Backend {
    // [REDACTED: Private Fields]
}
```

An interface to interact and draw [`Frame`](./index.md)s on the user's terminal.

This is the main entry point for Ratatui's rendering subsystem. It owns the backend-facing
render state: double buffers, viewport bookkeeping, and cursor synchronization for each render
pass.

If you're building a fullscreen application with the `ratatui` crate's default backend
([Crossterm]), prefer `ratatui::run` (or `ratatui::init` + `ratatui::restore`) over
constructing `Terminal` directly. These helpers enable common terminal modes (raw mode +
alternate screen) and restore them on exit and on panic.

```rust,no_run
#![allow(unexpected_cfgs)]
#[cfg(feature = "crossterm")]
{
ratatui::run(|terminal| {
    let mut should_quit = false;
    while !should_quit {
        terminal.draw(|frame| {
            frame.render_widget("Hello, World!", frame.area());
        })?;

        // Handle events, update application state, and set `should_quit = true` to exit.
    }
    Ok(())
})?;
}
Ok::<(), Box<dyn std::error::Error>>(())
```

# Typical Usage

In a typical application, the flow is: set up a terminal, run an event loop, update state, and
draw each frame.

1. Choose a setup path for a `Terminal`. Most apps call `ratatui::run`, which passes a
   preconfigured `Terminal` into your callback. If you need more control, use `ratatui::init`
   and `ratatui::restore`, or construct a `Terminal` manually via `Terminal::new`
   (fullscreen) or `Terminal::with_options` (select a [`Viewport`](./index.md)).
2. Enter your application's event loop and call `Terminal::draw` (or `Terminal::try_draw`)
   to render the current UI state into a [`Frame`](./index.md).
3. Handle input and application state updates between draw calls.
4. If the terminal is resized, call `Terminal::draw` again. Ratatui automatically resizes
   fullscreen and inline viewports during `draw`; fixed viewports require an explicit call to
   `Terminal::resize` if you want the region to change.

The normal mental model is: redraw the whole UI each pass, let Ratatui compute the diff, and
treat `Frame::area` as the source of truth for where this pass can render. Most application
code can stay entirely within that model.

# Rendering Pipeline

A single call to `Terminal::draw` (or `Terminal::try_draw`) represents one render pass. In
broad strokes, Ratatui:

1. Checks whether the underlying terminal size changed (see `Terminal::autoresize`).
2. Creates a [`Frame`](./index.md) backed by the current buffer (see `Terminal::get_frame`).
3. Runs your render callback to populate that buffer.
4. Diffs the current buffer against the previous buffer and writes the changes (see
   `Terminal::flush`).
5. Applies cursor visibility and position requested by the frame (see
   `Frame::set_cursor_position`).
6. Swaps the buffers to prepare for the next render pass (see `Terminal::swap_buffers`).
7. Flushes the backend (see `Backend::flush`).

Each render pass starts with an empty buffer for the current viewport. Your render callback
should render everything that should be visible in `Frame::area`, even if it is unchanged
from the previous frame. Ratatui diffs the current and previous buffers and only writes the
changes; anything you don't render is treated as empty and may clear previously drawn content.

If the viewport size changes between render passes (for example via `Terminal::autoresize` or
an explicit `Terminal::resize`), Ratatui clears the viewport and resets the previous buffer so
the next `draw` is treated as a full redraw.

If `Terminal::try_draw` returns an error, the render pass ends early. Depending on where the
failure happened, Ratatui may have already resized internal buffers, written part of the diff,
or left cursor state unapplied. In most applications, treat that error as fatal for the current
terminal session and let higher-level setup code restore terminal state before continuing.

Most applications should use `Terminal::draw` / `Terminal::try_draw`. Manual rendering is a
separate, lower-level path intended primarily for tests and specialized integrations. In that
mode you build a frame with `Terminal::get_frame`, apply the current buffer diff with
`Terminal::flush`, then call `Terminal::swap_buffers`. If your backend buffers output, also
call `Backend::flush`.

`Terminal::flush` only knows about Ratatui's two screen buffers. It does not know whether
you have changed terminal modes or switched display surfaces (for example by leaving the
alternate screen). If you call it after such a change, Ratatui may replay a diff computed for
the old surface onto the new one. When you need a complete draw pass that stays synchronized
with cursor updates and backend flushing, prefer `Terminal::draw` / `Terminal::try_draw`.

The same caution applies to direct backend mutation and direct cursor manipulation. If you
write to the backend or move the cursor outside Ratatui's normal render pass, the next draw may
overwrite those changes or may diff against stale assumptions. Use those escape hatches only
when you intentionally manage resynchronization yourself, typically by calling
`Terminal::clear` or performing a full render pass afterward.

```rust,no_run
mod ratatui {
    pub use ratatui_core::backend;
    pub use ratatui_core::terminal::Terminal;
}
use ratatui::Terminal;
use ratatui::backend::{Backend, TestBackend};

let backend = TestBackend::new(10, 10);
let mut terminal = Terminal::new(backend)?;

// Manual render pass (roughly what `Terminal::draw` does internally).
{
    let mut frame = terminal.get_frame();
    frame.render_widget("Hello World!", frame.area());
}

terminal.flush()?;
terminal.swap_buffers();
terminal.backend_mut().flush()?;
Ok::<(), Box<dyn std::error::Error>>(())
```

# Viewports

The viewport controls *where* Ratatui draws and therefore what `Frame::area` represents.
Most applications use [`Viewport::Fullscreen`](./index.md), but Ratatui also supports [`Viewport::Inline`](./index.md)
and [`Viewport::Fixed`](./index.md).

Choose a viewport based on how the app should fit into the terminal:

- [`Viewport::Fullscreen`](./index.md): the standard TUI case where Ratatui owns the whole terminal window.
- [`Viewport::Inline`](./index.md): embed the UI into a larger CLI flow with normal terminal output above
  it.
- [`Viewport::Fixed`](./index.md): render into one region of a larger terminal layout managed elsewhere.

Choose a viewport at initialization time with `Terminal::with_options` and
[`TerminalOptions`](#terminaloptions).

`Frame::area` depends on the active viewport. In fullscreen mode it starts at (0, 0); in fixed
and inline mode it may have a non-zero origin, so prefer using `frame.area()` as your root
layout rectangle. The variant docs on [`Viewport`](./index.md) describe each mode in more detail, and
inline-specific behavior is covered in the "Inline Viewport" section below.

```rust,no_run
#![allow(unexpected_cfgs)]
#[cfg(feature = "crossterm")]
{
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::{Terminal, TerminalOptions, Viewport};

// Fullscreen (most common):
let fullscreen = Terminal::new(CrosstermBackend::new(std::io::stdout()))?;

// Fixed region (your app manages the coordinates):
let viewport = Viewport::Fixed(Rect::new(0, 0, 30, 10));
let fixed = Terminal::with_options(
    CrosstermBackend::new(std::io::stdout()),
    TerminalOptions { viewport },
)?;

fixed.draw(|frame| {
    // Split the fixed viewport itself instead of assuming the viewport starts at `(0, 0)`.
    let [header, body] =
        Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).areas(frame.area());

    frame.render_widget("Fixed panel header", header);
    frame.render_widget("Render the panel body relative to frame.area()", body);
})?;
}
Ok::<(), Box<dyn std::error::Error>>(())
```

Applications should redraw after terminal resizes with `Terminal::draw` /
`Terminal::try_draw`. Fullscreen and inline viewports resize automatically during those render
passes; fixed viewports do not.

If your event loop receives a resize event, treat that event as a signal to render again rather
than as a complete source of truth for layout. During a render pass, use `Frame::area` as the
rectangle that Ratatui has actually prepared for drawing. Ratatui checks the backend's current
size during `draw` / `try_draw` so layout reflects the terminal size that exists at render
time, even if resize events were coalesced, missed, or arrived before your app handled them.

# Inline Viewport

Inline mode is designed for applications that want to embed a UI into a larger CLI flow. In
[`Viewport::Inline`](./index.md), Ratatui anchors the viewport to the backend cursor row and always starts
drawing at column 0.

To reserve vertical space for the requested height, Ratatui may append lines. When the cursor is
near the bottom edge, terminals scroll; Ratatui accounts for that scrolling by shifting the
computed viewport origin upward so the viewport stays fully visible.

While running in inline mode, `Terminal::insert_before` can be used to print output above the
viewport without disturbing the UI's logical position. When Ratatui is built with the
`scrolling-regions` feature, `insert_before` can do this without clearing and redrawing the
viewport.

```rust,no_run
#![allow(unexpected_cfgs)]
#[cfg(feature = "crossterm")]
{
use ratatui::{TerminalOptions, Viewport};

println!("Some output above the UI");

let options = TerminalOptions {
    viewport: Viewport::Inline(10),
};
let mut terminal = ratatui::try_init_with_options(options)?;

terminal.insert_before(1, |buf| {
    // Render a single line of output into `buf` before the UI.
    // (For example: logs, status updates, or command output.)
})?;

terminal.draw(|frame| {
    // Continue rendering the inline UI relative to the inline viewport.
    frame.render_widget("inline ui", frame.area());
})?;
}
Ok::<(), Box<dyn std::error::Error>>(())
```

# More Information

- Choosing a viewport: `Terminal::with_options`, [`TerminalOptions`](#terminaloptions), and [`Viewport`](./index.md)
- The rendering pipeline: `Terminal::draw` and `Terminal::try_draw`
- Resize handling: `Terminal::autoresize` and `Terminal::resize`
- Cursor behavior: `Frame::set_cursor_position`, `Terminal::set_cursor_position`, and
  `Terminal::show_cursor`
- Manual rendering and testing: `Terminal::get_frame`, `Terminal::flush`, and
  `Terminal::swap_buffers`
- Printing above an inline UI: `Terminal::insert_before`

# Initialization

Most interactive TUIs need process-wide terminal setup (for example: raw mode and an alternate
screen) and matching teardown on exit and on panic. In Ratatui, that setup lives in the
`ratatui` crate; `Terminal` itself focuses on rendering and does not implicitly change those
modes.

If you're using the `ratatui` crate with its default backend ([Crossterm]), there are three
common entry points:

- `ratatui::run`: recommended for most applications. Provides a `ratatui::DefaultTerminal`,
  runs your closure, and restores terminal state on exit and on panic.
- `ratatui::init` + `ratatui::restore`: like `run`, but you control the event loop and
  decide when to restore.
- `Terminal::new` / `Terminal::with_options`: manual construction (for example: custom
  backends such as [Termion] / [Termwiz], inline UIs, or fixed viewports). You are responsible
  for terminal mode setup and teardown.

`ratatui::run` was introduced in Ratatui 0.30, so older tutorials may use `init`/`restore` or
manual construction.

Some applications install a custom panic hook to log a crash report, print a friendlier error,
or integrate with error reporting. If you do, install it before calling `ratatui::init` /
`ratatui::run`. Ratatui wraps the current hook so it can restore terminal state first (for
example: leaving the alternate screen and disabling raw mode) and then delegate to your hook.

Crossterm is cross-platform and is what most Ratatui applications use by default. Ratatui also
supports other backends such as [Termion] and [Termwiz], and third-party backends can integrate
by implementing [`Backend`](./backend.md).

# How it works

`Terminal` ties together a [`Backend`](./backend.md), a [`Viewport`](./index.md), and a double-buffered diffing renderer.
The high-level flow is described in the "Rendering Pipeline" section above; this section focuses
on how that pipeline is implemented.

`Terminal` is generic over a [`Backend`](./backend.md) implementation and does not depend on a particular
terminal library. It relies on the backend to:

- report the current screen size (used by `Terminal::autoresize`)
- draw cell updates (used by `Terminal::flush`)
- clear regions (used by `Terminal::clear` and `Terminal::resize`)
- move and show/hide the cursor (used by `Terminal::try_draw`)
- optionally append lines (used by inline viewports and by `Terminal::insert_before`)

## Buffers and diffing

The `Terminal` maintains two [`Buffer`](./index.md)s sized to the current viewport. During a render pass,
widgets draw into the "current" buffer via the [`Frame`](./index.md) passed to your callback. At the end of
the pass, `Terminal::flush` diffs the current buffer against the previous buffer and sends
only the changed cells to the backend.

After flushing, `Terminal::swap_buffers` flips which buffer is considered "current" and resets
the next buffer. This is why each render pass starts from an empty buffer: your callback is
expected to fully redraw the viewport every time.

The [`CompletedFrame`](./index.md) returned from `Terminal::draw` / `Terminal::try_draw` provides a
reference to the buffer that was just rendered, which can be useful for assertions in tests.

## Viewport state and resizing

The active [`Viewport`](./index.md) controls how the viewport area is computed:

- Fullscreen: `Frame::area` covers the full backend size.
- Fixed: `Frame::area` is the exact rectangle you provided in terminal coordinates.
- Inline: `Frame::area` is a rectangle anchored to the backend cursor row.

For fullscreen and inline viewports, `Terminal::autoresize` checks the backend size during
every render pass and calls `Terminal::resize` when it changes. Resizing updates the internal
buffer sizes and clears the affected region; it also resets the previous buffer so the next draw
is treated as a full redraw.

## Cursor tracking

The cursor position requested by `Frame::set_cursor_position` is applied after
`Terminal::flush` so the cursor ends up on top of the rendered UI. `Terminal` also tracks a
"last known cursor position" as a best-effort record of where it last wrote, and uses that
information when recomputing inline viewports on resize.

## Inline-specific behavior

Inline viewports reserve vertical space by calling `Backend::append_lines`. If the cursor is
close enough to the bottom edge, terminals scroll as lines are appended. Ratatui accounts for
that scrolling by shifting the computed viewport origin upward so the viewport remains fully
visible. On resize, Ratatui recomputes the inline origin while trying to keep the cursor at the
same relative row inside the viewport.

When Ratatui is built with the `scrolling-regions` feature, `Terminal::insert_before` uses
terminal scrolling regions to insert content above an inline viewport without clearing and
redrawing it.

#### Implementations

- `const fn backend(&self) -> &B`

  Returns a shared reference to the backend.

  

  This is primarily useful for backend-specific inspection in tests (e.g. reading

  [`TestBackend`](./index.md)'s buffer) or for backend-specific APIs that Ratatui does not model.

  

  Reading from the backend does not desynchronize Ratatui, but values observed here may lag

  behind the current render callback because Ratatui does not apply a frame to the backend

  until the end of `Terminal::draw` / `Terminal::try_draw`.

- `const fn backend_mut(&mut self) -> &mut B`

  Returns a mutable reference to the backend.

  

  This is an advanced escape hatch. Normal applications should render through

  `Terminal::draw` / `Terminal::try_draw` instead of mutating the backend directly.

  

  Use this when integrating with backend-specific APIs that Ratatui does not model, or when

  tests need direct control over backend state.

  

  Mutating the backend directly can desynchronize Ratatui's internal buffers, cursor

  tracking, or viewport assumptions from what's on-screen. If you do this, call

  `Terminal::clear` or perform a full draw pass before relying on Ratatui's view of the

  terminal again.

  

  

- `fn size(&self) -> Result<Size, <B as >::Error>` — [`Size`](./index.md#size), [`Backend`](./backend.md#backend)

  Queries the real size of the backend.

  

  This returns the backend's current terminal size and does not update Ratatui's internal

  viewport bookkeeping by itself. The current renderable area depends on the configured

  [`Viewport`](./index.md); use `Frame::area` inside `Terminal::draw` / `Terminal::try_draw` if you

  want the area you should render into for the current pass.

  

  To make Ratatui observe backend size changes for fullscreen or inline viewports, see

  `Terminal::autoresize`.

  

  

  

  

#### Trait Implementations

##### `impl<B> Clone for Terminal<B>`

- `fn clone(&self) -> Terminal<B>` — [`Terminal`](#terminal)

##### `impl<B> Debug for Terminal<B>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl<B> Default for Terminal<B>`

- `fn default() -> Terminal<B>` — [`Terminal`](#terminal)

##### `impl<B> Drop for Terminal<B>`

- `fn drop(&mut self)`

##### `impl<B> Eq for Terminal<B>`

##### `impl<K> Equivalent for Terminal<B>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl<B> Hash for Terminal<B>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Terminal<B>`

##### `impl<B> PartialEq for Terminal<B>`

- `fn eq(&self, other: &Terminal<B>) -> bool` — [`Terminal`](#terminal)

##### `impl<B> StructuralPartialEq for Terminal<B>`

### `TerminalOptions`

```rust
struct TerminalOptions {
    pub viewport: Viewport,
}
```

Options to pass to `Terminal::with_options`

Most applications can use `Terminal::new`. Use `TerminalOptions` when you need to configure a
non-default [`Viewport`](./index.md) at initialization time (see [`Terminal`](#terminal) for an overview).

#### Fields

- **`viewport`**: `Viewport`

  Viewport used to draw to the terminal.
  
  See [`Terminal`](#terminal) for a higher-level overview, and [`Viewport`](./index.md) for the per-variant
  definition.

#### Trait Implementations

##### `impl Clone for TerminalOptions`

- `fn clone(&self) -> TerminalOptions` — [`TerminalOptions`](#terminaloptions)

##### `impl Debug for TerminalOptions`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for TerminalOptions`

- `fn default() -> TerminalOptions` — [`TerminalOptions`](#terminaloptions)

##### `impl Eq for TerminalOptions`

##### `impl<K> Equivalent for TerminalOptions`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for TerminalOptions`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for TerminalOptions`

##### `impl PartialEq for TerminalOptions`

- `fn eq(&self, other: &TerminalOptions) -> bool` — [`TerminalOptions`](#terminaloptions)

##### `impl StructuralPartialEq for TerminalOptions`

## Enums

### `Viewport`

```rust
enum Viewport {
    Fullscreen,
    Inline(u16),
    Fixed(crate::layout::Rect),
}
```

The area of the terminal that Ratatui draws into.

A [`Viewport`](./index.md) controls where widgets render and what `Frame::area` returns.

For a higher-level overview of viewports in the context of an application (including
examples), see [`Terminal`](#terminal).

Choose a viewport based on how the Ratatui UI should fit into the terminal:

- [`Viewport::Fullscreen`](./index.md) for the standard case: your app owns the whole terminal surface.
- [`Viewport::Inline`](./index.md) when the UI should live inside a larger CLI flow, with normal terminal
  output above it.
- [`Viewport::Fixed`](./index.md) when Ratatui should render into one region of a terminal layout managed
  elsewhere.

In fullscreen mode, the viewport starts at (0, 0). In inline and fixed mode, the viewport may
have a non-zero `x`/`y` origin; prefer using `Frame::area()` as your root layout rectangle.
Code that assumes `(0, 0)` as the origin is therefore only correct for fullscreen viewports.

See `Terminal::with_options` for how to select a viewport, and `Terminal::resize` /
`Terminal::autoresize` for resize behavior.

# Example

```rust,no_run
#![allow(unexpected_cfgs)]
#[cfg(feature = "crossterm")]
{
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::{Terminal, TerminalOptions, Viewport};

let mut terminal = Terminal::with_options(
    CrosstermBackend::new(std::io::stdout()),
    TerminalOptions {
        viewport: Viewport::Fixed(Rect::new(10, 5, 20, 4)),
    },
)?;

terminal.draw(|frame| {
    // `frame.area()` is `Rect::new(10, 5, 20, 4)`, not `(0, 0, 20, 4)`.
    let [title, body] =
        Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).areas(frame.area());

    frame.render_widget("panel title", title);
    frame.render_widget("render the body relative to the fixed viewport", body);
})?;
}
Ok::<(), Box<dyn std::error::Error>>(())
```

#### Variants

- **`Fullscreen`**

  Draw into the entire terminal.
  
  This is the default viewport used by `Terminal::new`.
  
  Choose this when the Ratatui app should own the whole terminal window.
  
  When the terminal size changes, Ratatui automatically resizes internal buffers during
  `Terminal::draw` / `Terminal::try_draw`.
  
  `Frame::area()` always starts at (0, 0).
  
  
  

- **`Inline`**

  Draw the application inline with the rest of the terminal output.
  
  Choose this when the UI should appear inside a larger command-line flow instead of taking
  over the entire terminal.
  
  The viewport spans the full terminal width and its top-left corner is anchored to column 0
  of the current cursor row when the terminal is created and whenever it is recomputed during
  resize. Ratatui reserves space for the requested height; if the cursor is near the bottom
  of the screen, this may scroll the terminal so the viewport remains fully visible.
  
  The height is specified in rows and is clamped to the current terminal height.
  
  Inline viewports always span the full terminal width.
  
  For the full inline rendering model, including output inserted above the UI, see the
  "Inline Viewport" section on [`Terminal`](crate::terminal::Terminal) and
  [`Terminal::insert_before`](crate::terminal::Terminal::insert_before).
  
  

- **`Fixed`**

  Draw into a fixed region of the terminal.
  
  Choose this when Ratatui is responsible for only part of the screen, for example a panel in
  a larger terminal layout managed by another renderer or by surrounding application code.
  
  Fixed viewports are not automatically resized. If the region should change (for example, on
  terminal resize), call `Terminal::resize` yourself.
  
  The area is specified as a [`Rect`](./index.md) in terminal coordinates.
  
  `Frame::area()` returns this rectangle as-is (including its `x`/`y` offset).
  Ratatui does not keep this rectangle synchronized with backend resizes unless you call
  `Terminal::resize` yourself.
  
  See also `Terminal::with_options` for initialization behavior.
  
  

#### Trait Implementations

##### `impl Clone for Viewport`

- `fn clone(&self) -> Viewport` — [`Viewport`](./index.md#viewport)

##### `impl Debug for Viewport`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Viewport`

- `fn default() -> Viewport` — [`Viewport`](./index.md#viewport)

##### `impl Display for Viewport`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Eq for Viewport`

##### `impl<K> Equivalent for Viewport`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Viewport`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Viewport`

##### `impl PartialEq for Viewport`

- `fn eq(&self, other: &Viewport) -> bool` — [`Viewport`](./index.md#viewport)

##### `impl StructuralPartialEq for Viewport`

##### `impl ToCompactString for Viewport`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for Viewport`

- `fn to_line(&self) -> Line<'_>` — [`Line`](./index.md#line)

##### `impl ToSpan for Viewport`

- `fn to_span(&self) -> Span<'_>` — [`Span`](./index.md#span)

##### `impl ToString for Viewport`

- `fn to_string(&self) -> String`

##### `impl ToText for Viewport`

- `fn to_text(&self) -> Text<'_>` — [`Text`](./index.md#text)

