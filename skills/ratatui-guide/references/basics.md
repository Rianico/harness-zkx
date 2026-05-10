# Ratatui Basics

> Terminal initialization, backends, event handling, and app structure.

## Key Patterns

### Pattern 1: Hello World with run()

Simplest Ratatui application using the `run()` helper:

```rust
use crossterm::event;

fn main() -> std::io::Result<()> {
    ratatui::run(|terminal| {
        loop {
            terminal.draw(|frame| {
                frame.render_widget("Hello World!", frame.area())
            })?;
            if event::read()?.is_key_press() {
                break Ok(());
            }
        }
    })
}
```

### Pattern 2: App Struct Pattern

Recommended pattern for structured TUI applications:

```rust
use crossterm::event;

fn main() -> std::io::Result<()> {
    let mut app = App::default();
    ratatui::run(|terminal| app.run(terminal))
}

#[derive(Debug, Default)]
pub struct App {
    counter: u8,
    exit: bool,
}

impl App {
    pub fn run(&mut self, terminal: &mut ratatui::DefaultTerminal) -> std::io::Result<()> {
        while !self.exit {
            terminal.draw(|frame| self.draw(frame))?;
            self.handle_events()?;
        }
        Ok(())
    }

    fn draw(&self, frame: &mut ratatui::Frame) {
        frame.render_widget(self, frame.area());
    }

    fn handle_events(&mut self) -> std::io::Result<()> {
        match event::read()? {
            event::Event::Key(key_event) if key_event.kind == crossterm::event::KeyEventKind::Press => {
                self.handle_key_event(key_event)
            }
            _ => {}
        };
        Ok(())
    }

    fn handle_key_event(&mut self, key_event: crossterm::event::KeyEvent) {
        match key_event.code {
            crossterm::event::KeyCode::Char('q') => self.exit = true,
            _ => {}
        }
    }
}
```

### Pattern 3: Terminal Restore on Exit

Always restore terminal state, even on panic:

```rust
fn main() -> std::io::Result<()> {
    let mut terminal = ratatui::init();
    let result = run_app(&mut terminal);
    ratatui::restore();  // Always restore!
    result
}
```

### Pattern 4: Event Handling Pattern

Handle keyboard and resize events:

```rust
use crossterm::event::{Event, KeyCode, KeyEventKind};

fn handle_events() -> std::io::Result<bool> {
    match event::read()? {
        Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
            KeyCode::Char('q') => return Ok(true),
            KeyCode::Left => { /* handle left */ }
            KeyCode::Right => { /* handle right */ }
            _ => {}
        },
        Event::Resize(_, _) => { /* handle resize */ }
        _ => {}
    }
    Ok(false)
}
```

### Pattern 5: Widget Trait Implementation

Implement Widget for custom rendering:

```rust
use ratatui::{
    buffer::Buffer,
    layout::Rect,
    widgets::{Block, Widget},
};

impl Widget for &App {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let title = ratatui::text::Line::from(" Counter App ".bold());
        let block = Block::bordered().title(title);
        ratatui::widgets::Paragraph::new("Content")
            .block(block)
            .render(area, buf);
    }
}
```

## API Reference

| Function/Type | Description | Example |
|---------------|-------------|---------|
| `ratatui::init()` | Initialize terminal with panic hook | `let terminal = ratatui::init();` |
| `ratatui::restore()` | Restore terminal to original state | `ratatui::restore();` |
| `ratatui::run()` | Run app with auto init/restore | `ratatui::run(\|t\| app.run(t))` |
| `DefaultTerminal` | Default terminal type | `&mut ratatui::DefaultTerminal` |
| `Frame` | Rendering context in draw closure | `frame.render_widget(w, area)` |
| `event::read()` | Read next event (blocking) | `event::read()?` |
| `event::poll()` | Check for event without blocking | `event::poll(Duration::from_millis(100))?` |
| `is_key_press()` | Check if event is key press | `event::read()?.is_key_press()` |

## Terminal Initialization

### Overview

Ratatui provides simple helpers for terminal initialization and cleanup.

### Initialization Functions

| Function | Alternate Screen | Raw Mode | Error Handling | Use Case |
|----------|------------------|----------|----------------|----------|
| `run()` | Yes | Yes | Auto-cleanup | Simple apps |
| `init()` | Yes | Yes | Panic | Standard full-screen apps |
| `try_init()` | Yes | Yes | Result | Standard apps with error handling |
| `init_with_options()` | No | Yes | Panic | Custom viewport apps |
| `try_init_with_options()` | No | Yes | Result | Custom viewport with error handling |

### Basic Pattern

```rust
fn main() -> std::io::Result<()> {
    ratatui::run(|terminal| {
        // Your app loop here
    })
}
```

### Manual Init/Restore

```rust
fn main() -> std::io::Result<()> {
    let mut terminal = ratatui::init();
    let result = run_app(&mut terminal);
    ratatui::restore();
    result
}
```

### Which Function Should I Start With?

1. Use `run()` for the normal case: Ratatui owns setup and cleanup around your application closure.
2. Move to `init()` / `restore()` when you want explicit control over setup, teardown, or event loop structure.
3. Use `try_init()` / `try_restore()` when you want the same control but need explicit error handling instead of panicking or printing cleanup failures.
4. Use `init_with_options()` / `try_init_with_options()` when you need a custom `TerminalOptions` such as inline or fixed viewports.
5. Construct `Terminal` manually only when these helpers do not match the backend or terminal lifecycle you need.

### Panic Handling

`ratatui::init()` and `ratatui::run()` automatically install a panic hook that restores the terminal before panicking.

**Important:** Call initialization functions *after* installing any other panic hooks to ensure the terminal is restored before other hooks run.

### Resize-Aware Redraws

```rust
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

### Inline Viewport Example

Use `init_with_options()` when the UI should not use the normal fullscreen path:

```rust
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
```

### Function Signatures

```rust
// run() - wraps init/restore automatically
fn run<F, R>(f: F) -> R
where
    F: FnOnce(&mut DefaultTerminal) -> R

// init() - panics on failure
fn init() -> DefaultTerminal

// try_init() - returns Result
fn try_init() -> io::Result<DefaultTerminal>

// init_with_options() - custom viewport
fn init_with_options(options: TerminalOptions) -> DefaultTerminal

// try_init_with_options() - custom viewport with error handling
fn try_init_with_options(options: TerminalOptions) -> io::Result<DefaultTerminal>

// restore() - prints errors to stderr
fn restore()

// try_restore() - returns Result
fn try_restore() -> io::Result<()>

// DefaultTerminal type alias
type DefaultTerminal = Terminal<CrosstermBackend<Stdout>>;
```

## Backends

### Overview

Ratatui supports multiple backends for terminal operations. The default is Crossterm.

### TestBackend

A `Backend` implementation used for integration testing that renders to a memory buffer:

```rust
use ratatui::backend::{Backend, TestBackend};

let mut backend = TestBackend::new(10, 2);
backend.clear()?;
backend.assert_buffer_lines(["          "; 2]);
```

### TestBackend Methods

| Method | Description |
|--------|-------------|
| `new(width, height)` | Creates a new TestBackend with specified dimensions |
| `with_lines(lines)` | Creates TestBackend with initial screen state |
| `buffer()` | Returns reference to internal buffer |
| `scrollback()` | Returns reference to scrollback buffer |
| `resize(width, height)` | Resizes the backend |
| `assert_buffer(expected)` | Asserts buffer equals expected |
| `assert_buffer_lines(lines)` | Asserts buffer equals expected lines |
| `assert_cursor_position(pos)` | Asserts cursor position |

### Crossterm Backend

The default backend providing cross-platform compatibility:

```rust
use ratatui::Terminal;
use ratatui::backend::CrosstermBackend;

let backend = CrosstermBackend::new(std::io::stdout());
let mut terminal = Terminal::new(backend)?;
```

### Backend Trait

```rust
trait Backend {
    type Error;
    fn draw<'a, I>(&mut self, content: I) -> Result<(), Self::Error>;
    fn hide_cursor(&mut self) -> Result<(), Self::Error>;
    fn show_cursor(&mut self) -> Result<(), Self::Error>;
    fn get_cursor_position(&mut self) -> Result<Position, Self::Error>;
    fn set_cursor_position<P: Into<Position>>(&mut self, position: P) -> Result<(), Self::Error>;
    fn clear(&mut self) -> Result<(), Self::Error>;
    fn size(&self) -> Result<Size, Self::Error>;
    fn flush(&mut self) -> Result<(), Self::Error>;
}
```

## Event Loop

### Overview

Event loops handle terminal input and drive frame rendering.

### Blocking Event Loop

```rust
loop {
    terminal.draw(|frame| {
        // Render widgets
    })?;

    if event::read()?.is_key_press() {
        break;
    }
}
```

### App-Based Event Loop

```rust
impl App {
    pub fn run(&mut self, terminal: &mut ratatui::DefaultTerminal) -> std::io::Result<()> {
        while !self.exit {
            terminal.draw(|frame| self.draw(frame))?;
            self.handle_events()?;
        }
        Ok(())
    }

    fn handle_events(&mut self) -> std::io::Result<()> {
        match event::read()? {
            event::Event::Key(key) if key.kind == KeyEventKind::Press => {
                self.handle_key(key);
            }
            _ => {}
        }
        Ok(())
    }
}
```

### Non-Blocking Poll

```rust
if event::poll(Duration::from_millis(100))? {
    match event::read()? {
        // Handle event
    }
}
```

### Key Event Best Practices

1. Check `KeyEventKind::Press` to avoid duplicate events
2. Handle `Event::Resize` for responsive UIs
3. Use `KeyCode::Char` for printable characters

## App Structure

### Overview

The App struct pattern organizes state, rendering, and event handling.

### Basic Structure

```rust
#[derive(Debug, Default)]
pub struct App {
    // State fields
    counter: u8,
    exit: bool,
}

impl App {
    pub fn run(&mut self, terminal: &mut ratatui::DefaultTerminal) -> std::io::Result<()> {
        while !self.exit {
            terminal.draw(|frame| self.draw(frame))?;
            self.handle_events()?;
        }
        Ok(())
    }

    fn draw(&self, frame: &mut ratatui::Frame) {
        frame.render_widget(self, frame.area());
    }

    fn handle_events(&mut self) -> std::io::Result<()> {
        // Event handling logic
        Ok(())
    }
}
```

### Widget Trait Implementation

```rust
impl Widget for &App {
    fn render(self, area: Rect, buf: &mut Buffer) {
        // Custom rendering
    }
}
```

### Entry Point

```rust
fn main() -> std::io::Result<()> {
    let mut app = App::default();
    ratatui::run(|terminal| app.run(terminal))
}
```

### Benefits

1. Clear separation of state, rendering, and events
2. Easy testing with TestBackend
3. Composable and reusable

## Complete API: Terminal

### Overview

The `Terminal` struct is the main entry point for Ratatui's rendering subsystem. It owns the backend-facing render state: double buffers, viewport bookkeeping, and cursor synchronization for each render pass.

### Terminal Struct

```rust
struct Terminal<B>
where
    B: Backend {
    // private fields
}
```

### Basic Usage

```rust
use ratatui::Terminal;
use ratatui::backend::CrosstermBackend;
use ratatui::widgets::Paragraph;

let backend = CrosstermBackend::new(stdout());
let mut terminal = Terminal::new(backend)?;
terminal.draw(|frame| {
    frame.render_widget(Paragraph::new("Hello world!"), frame.area());
})?;
```

### Rendering Pipeline

A single call to `Terminal::draw` represents one render pass:

1. Checks whether the underlying terminal size changed
2. Creates a `Frame` backed by the current buffer
3. Runs your render callback to populate that buffer
4. Diffs the current buffer against the previous buffer and writes the changes
5. Applies cursor visibility and position requested by the frame
6. Swaps the buffers to prepare for the next render pass
7. Flushes the backend

### Terminal Methods

| Method | Description |
|--------|-------------|
| `backend()` | Returns shared reference to backend |
| `backend_mut()` | Returns mutable reference to backend |
| `size()` | Queries the real size of the backend |

### Frame Struct

A consistent view into the terminal state for rendering a single frame:

```rust
struct Frame<'a> {
    // private fields
}
```

### Frame Methods

| Method | Description |
|--------|-------------|
| `area()` | Returns the area of the current frame |
| `size()` | Alias for `area()` |
| `render_widget(widget, area)` | Render a Widget to the current buffer |
| `render_stateful_widget(widget, area, state)` | Render a StatefulWidget |
| `set_cursor_position(pos)` | Make cursor visible at position |
| `set_cursor(x, y)` | Legacy cursor positioning |
| `buffer_mut()` | Gets mutable buffer reference |
| `count()` | Returns current frame count |

### CompletedFrame Struct

Represents the state of the terminal after the last successful render:

```rust
struct CompletedFrame<'a> {
    pub buffer: &'a Buffer,
    pub area: Rect,
    pub count: usize,
}
```

### Viewport Enum

Controls where Ratatui draws and what `Frame::area` returns:

```rust
enum Viewport {
    Fullscreen,
    Inline(u16),
    Fixed(Rect),
}
```

#### Viewport Variants

- **Fullscreen**: Draw into the entire terminal. Default viewport used by `Terminal::new`. `Frame::area()` starts at (0, 0).

- **Inline(u16)**: Draw inline with terminal output. Viewport spans full width, anchored to cursor row. Height specified in rows. Use for UI inside larger CLI flow.

- **Fixed(Rect)**: Draw into a fixed region. `Frame::area()` returns the rectangle as-is including offset. Not automatically resized.

### Viewport Example

```rust
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
    let [header, body] =
        Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).areas(frame.area());

    frame.render_widget("Fixed panel header", header);
    frame.render_widget("Render the panel body relative to frame.area()", body);
})?;
```

### TerminalOptions

Options to pass to `Terminal::with_options`:

```rust
struct TerminalOptions {
    pub viewport: Viewport,
}
```

### Manual Render Pass

For tests and specialized integrations:

```rust
use ratatui::Terminal;
use ratatui::backend::{Backend, TestBackend};

let backend = TestBackend::new(10, 10);
let mut terminal = Terminal::new(backend)?;

// Manual render pass (roughly what `Terminal::draw` does internally)
{
    let mut frame = terminal.get_frame();
    frame.render_widget("Hello World!", frame.area());
}

terminal.flush()?;
terminal.swap_buffers();
terminal.backend_mut().flush()?;
```

### Inline Viewport Behavior

In `Viewport::Inline`, Ratatui anchors the viewport to the backend cursor row and starts drawing at column 0.

```rust
use ratatui::{TerminalOptions, Viewport};

println!("Some output above the UI");

let options = TerminalOptions {
    viewport: Viewport::Inline(10),
};
let mut terminal = ratatui::try_init_with_options(options)?;

terminal.insert_before(1, |buf| {
    // Render a single line of output into `buf` before the UI.
})?;

terminal.draw(|frame| {
    frame.render_widget("inline ui", frame.area());
})?;
```

### Resize Handling

Applications should redraw after terminal resizes with `Terminal::draw`. Fullscreen and inline viewports resize automatically during render passes; fixed viewports do not.

If your event loop receives a resize event, treat that event as a signal to render again. Use `Frame::area` as the rectangle that Ratatui has actually prepared for drawing.

## When Writing Code

1. Always call `ratatui::restore()` or use `ratatui::run()` to ensure terminal restoration
2. Use `KeyEventKind::Press` to avoid double key events on some terminals
3. Implement the Widget trait for custom components
4. Use `TestBackend` for unit testing widgets without a terminal

## When Answering Questions

1. Answer from patterns first
2. If the question involves custom backends, TestBackend configuration, or obscure event types, consult the raw docs
3. If still insufficient, inform user and answer from built-in knowledge
