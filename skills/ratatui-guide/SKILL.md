---
name: ratatui-guide
description: "Ratatui TUI framework domain expertise for building terminal user interfaces in Rust. Use when implementing TUI applications, widgets, layouts, styling, or terminal handling with ratatui. TRIGGER when: code imports ratatui, building terminal apps, implementing custom widgets, handling terminal events, creating layouts with Constraint, styling text with Style/Color/Modifier, working with Buffer/Cell/Frame, or questions about ratatui widgets (Block, Paragraph, List, Table, Chart, Canvas, Gauge, Scrollbar, Tabs, BarChart, Sparkline, Clear, Fill). Covers immediate mode rendering, backend selection (crossterm, termion, termwiz), terminal initialization patterns, event handling, and workspace crate organization (ratatui, ratatui-core, ratatui-widgets)."
argument-hint: "[topic|module]"
---

# Ratatui Guide

Domain expertise for building terminal user interfaces with the Ratatui framework in Rust.

## Quick Start

```bash
cargo add ratatui crossterm
```

```rust
use crossterm::event;

fn main() -> std::io::Result<()> {
    ratatui::run(|mut terminal| {
        loop {
            terminal.draw(|frame| frame.render_widget("Hello World!", frame.area()))?;
            if event::read()?.is_key_press() {
                break Ok(());
            }
        }
    })
}
```

## Core Concepts

### Immediate Mode Rendering

Ratatui uses immediate rendering with intermediate buffers. For each frame, render all widgets that should be visible. This differs from retained mode where widgets persist and auto-redraw.

### Terminal Initialization

| Function | Use Case |
|----------|----------|
| `ratatui::run()` | Normal applications (handles init, cleanup, panic hooks) |
| `init()` / `restore()` | Manual control over terminal lifetime |
| `init_with_options()` | Custom viewport (inline, fixed region) |
| `Terminal::new()` | Custom backend construction |

### Event Handling

Ratatui doesn't include input handling. Use backend events directly:

```rust
use crossterm::event::{self, Event, KeyCode, KeyEventKind};

fn handle_events() -> std::io::Result<bool> {
    match event::read()? {
        Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
            KeyCode::Char('q') => return Ok(true),
            _ => {}
        },
        _ => {}
    }
    Ok(false)
}
```

### Layout

```rust
use ratatui::layout::{Constraint, Layout};

let [title, main, status] = Layout::vertical([
    Constraint::Length(1),
    Constraint::Min(0),
    Constraint::Length(1),
]).areas(frame.area());
```

## Workspace Organization

Starting with 0.30.0, ratatui is modular:

| Crate | Use For |
|-------|---------|
| `ratatui` | Applications (recommended) |
| `ratatui-core` | Widget libraries, custom integrations |
| `ratatui-widgets` | Built-in widgets only |
| `ratatui-crossterm` | Crossterm backend directly |
| `ratatui-termwiz` | Termwiz backend directly |

## Built-in Widgets

| Widget | Purpose |
|--------|---------|
| `Block` | Container with borders, titles |
| `Paragraph` | Styled text with wrapping |
| `List` | Selectable list of items |
| `Table` | Grid with rows/columns, selection |
| `Chart` | Line/scatter graphs |
| `Canvas` | Arbitrary shapes |
| `Gauge` | Progress percentage |
| `BarChart` | Multiple datasets as bars |
| `Scrollbar` | Scroll indicator |
| `Tabs` | Tab bar with selection |
| `Sparkline` | Single dataset sparkline |
| `Clear` | Clear area (overlay) |
| `Fill` | Fill with repeated symbol |

## Styling

```rust
use ratatui::style::{Color, Modifier, Style, Stylize};

// Builder pattern
Style::new().fg(Color::Green).bg(Color::White).add_modifier(Modifier::BOLD);

// Shorthand trait
"Hello".red().on_white().bold();
paragraph.blue().on_yellow();
```

## Common Patterns

### Application Structure

```rust
struct App {
    should_quit: bool,
    // state...
}

impl App {
    fn run(&mut self, terminal: &mut ratatui::DefaultTerminal) -> io::Result<()> {
        while !self.should_quit {
            terminal.draw(|frame| self.render(frame))?;
            self.handle_events()?;
        }
        Ok(())
    }

    fn render(&self, frame: &mut Frame) { /* ... */ }
    fn handle_events(&mut self) -> io::Result<()> { /* ... */ }
}
```

### Custom Widget

Implement `Widget` for stateless, `StatefulWidget` for stateful:

```rust
impl Widget for MyWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        // Draw to buffer
    }
}

impl StatefulWidget for MyStatefulWidget {
    type State = MyState;
    fn render(self, area: Rect, buf: &mut Buffer, state: &mut Self::State) {
        // Draw with state
    }
}
```

## Common Issues

### Terminal not restored on panic

Always use `ratatui::run()` or ensure `restore()` is called. The init functions install panic hooks, but call them after other panic hooks.

### Resize events

Ratatui doesn't auto-redraw on resize. Continue the event loop and call `draw()` again - it checks the backend's current size during render.

### Cursor position conflicts

Don't mix `Frame` cursor methods with direct backend cursor changes. Choose one path consistently.

## Reference Documentation

Full API documentation generated from source:

- `references/ratatui/` — Main crate with init, prelude, widgets
- `references/ratatui_core/` — Core types: Buffer, Cell, Layout, Style, Terminal, Text
- `references/ratatui_widgets/` — All built-in widgets
- `references/ratatui_crossterm/` — Crossterm backend
- `references/SUMMARY.md` — Full documentation index

## External Resources

- [Ratatui Website](https://ratatui.rs) — Concepts, tutorials
- [Examples](https://github.com/ratatui-org/ratatui/tree/main/examples) — Official examples
- [FAQ](https://ratatui.rs/faq/) — Common questions
