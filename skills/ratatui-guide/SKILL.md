---
name: ratatui-guide
description: >-
  |
  Ratatui/Rust TUI framework for terminal UIs with widgets, layouts, and styling. Covers event loops, widget rendering, layout constraints, text styling, custom widgets. TRIGGER: ratatui, TUI, terminal app/interface/UI, hello world, app structure.
argument-hint: >-
  [topic]
---

# Ratatui TUI Library

> **Version:** 0.30.0 | **Last Updated:** 2026-05-10
>
> Check for updates: https://docs.rs/ratatui/

Rust library for building rich terminal user interfaces with widgets, layouts, and styling.

## Code Generation Rules

- Use `edition = "2024"` in Cargo.toml
- Use latest ratatui version: `ratatui = "0.30"`
- Use crossterm backend by default (cross-platform)
- Always call `ratatui::restore()` or use `ratatui::run()` to ensure terminal restoration

## Quick Start

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

## Core Concepts

1. **Terminal** - Main entry point, manages backend and rendering
2. **Frame** - Passed to draw closure, provides rendering context
3. **Widget** - Trait for renderable components (Block, Paragraph, List, etc.)
4. **Layout** - Constraint-based area splitting for responsive UIs
5. **Style** - Colors, modifiers, and text styling

Ratatui uses **immediate rendering with intermediate buffers**: each frame, render all widgets to a buffer; terminal compares current/previous buffers; only changed cells are written.

## App Struct Pattern

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

    fn handle_events(&mut self) -> std::io::Result<()> {
        match event::read()? {
            event::Event::Key(key) if key.kind == crossterm::event::KeyEventKind::Press => {
                match key.code {
                    crossterm::event::KeyCode::Char('q') => self.exit = true,
                    _ => {}
                }
            }
            _ => {}
        }
        Ok(())
    }
}
```

## Layout

```rust
use ratatui::layout::{Constraint, Layout};

// Vertical split (header/body/footer)
let [header, body, footer] = Layout::vertical([
    Constraint::Length(3),
    Constraint::Fill(1),
    Constraint::Length(1),
]).areas(frame.area());

// Horizontal split (sidebar/main)
let [sidebar, main] = Layout::horizontal([
    Constraint::Length(20),
    Constraint::Fill(1),
]).areas(frame.area());

// With spacing
let [left, right] = Layout::horizontal([
    Constraint::Percentage(50),
    Constraint::Percentage(50),
]).spacing(2).areas(frame.area());
```

## Constraint Types

| Constraint | Description |
|------------|-------------|
| `Length(n)` | Exactly n cells |
| `Min(n)` | At least n cells |
| `Max(n)` | At most n cells |
| `Percentage(n)` | n% of available |
| `Ratio(a, b)` | a/b of available |
| `Fill(n)` | Fill with weight n |

## Styled Text

```rust
use ratatui::style::Stylize;
use ratatui::text::{Line, Span};

let style = Style::default().fg(Color::Green).bg(Color::Black).add_modifier(Modifier::BOLD);
let span = Span::styled("Hello", style);
let line = Line::from(vec![
    "Normal ".into(),
    "bold".bold(),
    " and ".into(),
    "red".red(),
]);
```

## Common Widgets

```rust
// Block with borders
let block = Block::bordered().title("My Block");

// Paragraph with wrapping
Paragraph::new("Long text...").block(Block::bordered()).wrap(Wrap { trim: true });

// Selectable list
let list = List::new(items).highlight_style(Style::new().reversed()).highlight_symbol("> ");
frame.render_stateful_widget(list, area, &mut state);

// Table
Table::new(rows, [Constraint::Length(10), Constraint::Length(10)])
    .header(Row::new(vec!["H1", "H2"]).bold());

// Gauge (progress bar)
Gauge::default().percent(75).label("75%");

// Chart
Chart::new(vec![Dataset::default().data(&[(0.0, 1.0), (1.0, 2.0)]).graph_type(GraphType::Line)])
    .x_axis(Axis::default().title("X"))
    .y_axis(Axis::default().title("Y"));
```

## API Reference Table

| Function/Type | Description | Example |
|---------------|-------------|---------|
| `ratatui::init()` | Initialize terminal with panic hook | `let terminal = ratatui::init();` |
| `ratatui::restore()` | Restore terminal to original state | `ratatui::restore();` |
| `ratatui::run(f)` | Run app with auto init/restore | `ratatui::run(\|t\| app.run(t))` |
| `terminal.draw(f)` | Draw a frame | `terminal.draw(\|frame\| { ... })?;` |
| `Layout::vertical([...])` | Create vertical layout | `Layout::vertical([Length(3), Fill(1)])` |
| `Layout::horizontal([...])` | Create horizontal layout | `Layout::horizontal([Percentage(50); 2])` |
| `frame.render_widget(w, a)` | Render widget | `frame.render_widget(para, area);` |
| `frame.render_stateful_widget(w, a, s)` | Render with state | `frame.render_stateful_widget(list, area, &mut state);` |

## Built-in Widgets

| Widget | State Type | Description |
|--------|------------|-------------|
| `Block` | - | Container with borders/title |
| `Paragraph` | - | Text display with wrapping |
| `List` | `ListState` | Selectable list items |
| `Table` | `TableState` | Rows and columns |
| `Tabs` | - | Tab bar |
| `Gauge` | - | Progress bar |
| `Scrollbar` | `ScrollbarState` | Scroll indicator |
| `Chart` | - | Line/scatter charts |
| `BarChart` | - | Bar charts |
| `Canvas` | - | Custom drawing |

## References

For detailed patterns and complete API documentation, read:

| Module | File | Topics |
|--------|------|--------|
| Basics | `$SKILL_DIR/references/basics.md` | Terminal init, app structure, event loop, backends |
| Layout | `$SKILL_DIR/references/layout.md` | Constraints, splitting, flex modes, nesting |
| Styling | `$SKILL_DIR/references/styling.md` | Colors, modifiers, Span/Line/Text, alignment |
| Widgets | `$SKILL_DIR/references/widgets.md` | All widget patterns, stateful widgets, composition |

For edge cases and complete API surface not covered above, read the raw docs at `$SKILL_DIR/references/ratatui-raw/`.

## Trigger Examples

Activate this skill when you see any of these patterns:

- "Build a terminal UI" / "Create a TUI app"
- "ratatui hello world" / "ratatui app structure"
- "Terminal dashboard" / "CLI interface with widgets"
- "Layout for terminal app" / "Split terminal screen"
- "Terminal progress bar" / "Text-based UI"
- "Rust TUI" / "crossterm event loop"
- "Widget rendering" / "Frame drawing"
- Questions about ratatui widgets: List, Table, Gauge, Chart, Block, Paragraph
- Implementing keyboard input handling in terminal
- Terminal restoration and cleanup patterns

## When Writing Code

1. Use `ratatui::run()` for simple apps - handles init/restore automatically
2. Use `KeyEventKind::Press` to avoid double key events on some terminals
3. Use `Layout::vertical/horizontal()` with `areas()` for compile-time known layouts
4. Wrap content widgets with `Block` for borders and titles
5. Use `Fill(1)` for flexible areas, `Length()` for fixed-size headers/footers
6. Chain `.spacing()` to add gaps between layout areas
7. Implement `Widget for &MyWidget` for reusable custom widgets
8. Use `Stylize` trait (`.red()`, `.bold()`) for concise styling

## When Answering Questions

1. Answer from patterns and tables above first
2. If the question involves deeper details, read `$SKILL_DIR/references/<module>.md`
3. For edge cases, obscure parameters, or complete API surface, read `$SKILL_DIR/references/ratatui-raw/`
4. If still insufficient, inform user and answer from built-in knowledge
