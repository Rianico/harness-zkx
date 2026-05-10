# Ratatui Widgets

> **Version:** 0.30.0
>
> Check for updates: https://docs.rs/ratatui/

Common and advanced UI widgets for terminal applications.

## Key Patterns

### Pattern 1: Bordered Block

Create a container with borders:

```rust
use ratatui::widgets::{Block, Borders};

let block = Block::bordered()
    .title("My Block")
    .padding(Padding::uniform(1));

frame.render_widget(block, area);
```

### Pattern 2: Paragraph with Wrapping

Display text with word wrap:

```rust
use ratatui::widgets::{Block, Paragraph, Wrap};

let paragraph = Paragraph::new("Long text that will wrap...")
    .block(Block::bordered().title("Content"))
    .wrap(Wrap { trim: true })
    .centered();

frame.render_widget(paragraph, area);
```

### Pattern 3: Selectable List

Create an interactive list:

```rust
use ratatui::widgets::{Block, List, ListItem, ListState};

let items: Vec<ListItem> = ["Item 1", "Item 2", "Item 3"]
    .iter()
    .map(|s| ListItem::new(*s))
    .collect();

let mut state = ListState::default();
state.select(Some(0));

let list = List::new(items)
    .block(Block::bordered().title("List"))
    .highlight_style(Style::default().bg(Color::Blue))
    .highlight_symbol(">> ");

frame.render_stateful_widget(list, area, &mut state);
```

### Pattern 4: Table with Headers

Display tabular data:

```rust
use ratatui::widgets::{Block, Cell, Row, Table};

let rows = [
    Row::new(vec!["Row 1 Col 1", "Row 1 Col 2"]),
    Row::new(vec!["Row 2 Col 1", "Row 2 Col 2"]),
];

let table = Table::new(
    rows,
    [Constraint::Length(10), Constraint::Length(10)],
)
.header(Row::new(vec!["Header 1", "Header 2"]).bold())
.block(Block::bordered().title("Table"));

frame.render_widget(table, area);
```

### Pattern 5: Progress Gauge

Show progress indicator:

```rust
use ratatui::widgets::{Block, Gauge};

let gauge = Gauge::default()
    .block(Block::bordered().title("Progress"))
    .percent(75)
    .label("75%");

frame.render_widget(gauge, area);
```

### Pattern 6: Tabs Navigation

Create tabbed interface:

```rust
use ratatui::widgets::{Block, Tabs};

let tabs = Tabs::new(vec!["Tab 1", "Tab 2", "Tab 3"])
    .block(Block::bordered().title("Tabs"))
    .select(0)
    .highlight_style(Style::default().fg(Color::Yellow));

frame.render_widget(tabs, area);
```

### Pattern 7: Line Chart

Create a line chart with data:

```rust
use ratatui::widgets::{Axis, Chart, Dataset, GraphType};

let datasets = vec![
    Dataset::default()
        .name("Series 1")
        .data(&[(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)])
        .graph_type(GraphType::Line),
];

let chart = Chart::new(datasets)
    .x_axis(Axis::default().title("X"))
    .y_axis(Axis::default().title("Y"));

frame.render_widget(chart, area);
```

### Pattern 8: Bar Chart

Create a bar chart:

```rust
use ratatui::widgets::{Bar, BarChart, BarGroup};

let bars = vec![
    Bar::default().value(10).label("A".into()),
    Bar::default().value(20).label("B".into()),
    Bar::default().value(30).label("C".into()),
];

let barchart = BarChart::default()
    .data(BarGroup::default().bars(&bars))
    .bar_width(3)
    .bar_gap(1);

frame.render_widget(barchart, area);
```

### Pattern 9: Canvas Drawing

Draw shapes on a canvas:

```rust
use ratatui::widgets::canvas::{Canvas, Circle, Line, Rectangle};

let canvas = Canvas::default()
    .x_bounds([0.0, 100.0])
    .y_bounds([0.0, 100.0])
    .paint(|ctx| {
        ctx.draw(&Circle {
            x: 50.0,
            y: 50.0,
            radius: 20.0,
            color: Color::Red,
        });
        ctx.draw(&Rectangle {
            x: 10.0,
            y: 10.0,
            width: 30.0,
            height: 20.0,
            color: Color::Blue,
        });
    });

frame.render_widget(canvas, area);
```

### Pattern 10: Sparkline

Create a mini sparkline chart:

```rust
use ratatui::widgets::Sparkline;

let data: &[u64] = &[0, 2, 5, 3, 8, 12, 10, 15, 20, 18];

let sparkline = Sparkline::default()
    .data(data)
    .max(20);

frame.render_widget(sparkline, area);
```

## API Reference Table

### Common Widgets

| Widget | Description | Key Methods |
|--------|-------------|-------------|
| `Block` | Container with borders/title | `bordered()`, `title()`, `padding()`, `border_type()`, `border_set()` |
| `Paragraph` | Text display | `new()`, `wrap()`, `centered()`, `block()`, `scroll()` |
| `List` | Selectable list | `new()`, `highlight_style()`, `highlight_symbol()`, `direction()` |
| `ListState` | List selection state | `select()`, `selected()`, `select_next()`, `select_previous()` |
| `Table` | Tabular data | `new()`, `header()`, `footer()`, `widths()`, `column_spacing()` |
| `TableState` | Table selection state | `select()`, `select_column()`, `select_cell()`, `scroll_down_by()` |
| `Row` | Table row | `new()`, `height()`, `style()`, `top_margin()`, `bottom_margin()` |
| `Cell` | Table cell | `new()`, `style()`, `column_span()` |
| `Tabs` | Tab navigation | `new()`, `select()`, `highlight_style()` |
| `Gauge` | Progress bar | `percent()`, `ratio()`, `label()`, `gauge_style()` |
| `Scrollbar` | Scroll indicator | `new()`, `begin_symbol()`, `end_symbol()` |
| `ScrollbarState` | Scrollbar position | `position()`, `viewport_content_length()` |
| `Clear` | Clear area | `new()` |

### Advanced Widgets

| Widget | Description | Key Methods |
|--------|-------------|-------------|
| `Chart` | Line/scatter/area charts | `new()`, `x_axis()`, `y_axis()`, `legend_position()` |
| `Dataset` | Chart data series | `name()`, `data()`, `graph_type()`, `marker()`, `fill_to_y()` |
| `Axis` | Chart axis configuration | `title()`, `bounds()`, `labels()`, `labels_alignment()` |
| `GraphType` | Chart style | `Line`, `Scatter`, `Bar`, `Area` |
| `Marker` | Point markers | `Dot`, `Block`, `Braille`, `HalfBlock` |
| `BarChart` | Bar chart visualization | `data()`, `bar_width()`, `bar_gap()`, `direction()` |
| `Bar` | Individual bar | `value()`, `label()`, `style()`, `value_style()` |
| `BarGroup` | Group of bars | `default().bars(&[...])` |
| `Canvas` | Drawing surface | `x_bounds()`, `y_bounds()`, `paint()`, `marker()` |
| `Circle` | Circle primitive | `x`, `y`, `radius`, `color` |
| `Rectangle` | Rectangle primitive | `x`, `y`, `width`, `height`, `color` |
| `Line` | Line primitive | `x1`, `y1`, `x2`, `y2`, `color` |
| `FilledLine` | Filled line | `x1`, `y1`, `x2`, `y2`, `fill_to_y`, `color` |
| `Points` | Scatter points | `coords`, `color` |
| `Map` | World map | `resolution`, `color` |
| `Sparkline` | Mini bar chart | `data()`, `max()`, `style()`, `direction()` |

---

## Block

Container widget with borders, title, and padding.

### Basic Usage

```rust
use ratatui::widgets::Block;

let block = Block::bordered().title(" Title ");
frame.render_widget(block, area);
```

### Border Styles

```rust
use ratatui::widgets::{Block, Borders, border};

// All borders
Block::bordered()

// Specific borders
Block::new().borders(Borders::TOP | Borders::BOTTOM)

// Border sets (predefined)
Block::bordered().border_set(border::THICK)
Block::bordered().border_set(border::ROUNDED)
Block::bordered().border_set(border::DOUBLE)
```

### Title Positioning

```rust
use ratatui::style::Stylize;

Block::bordered()
    .title("Top Left")                    // Default: top-left
    .title("Top Right".right_aligned())
    .title("Bottom".bottom_aligned())
    .title("Center".centered())
```

### Multiple Titles

```rust
Block::bordered()
    .title_top("Left1")
    .title_top(Line::from("Center").centered())
    .title_top(Line::from("Right").right_aligned())
    .title_bottom("Status: OK");
```

### Padding

```rust
use ratatui::layout::Padding;

Block::bordered()
    .padding(Padding::uniform(1))           // All sides: 1
    .padding(Padding::horizontal(2))        // Left and right: 2
    .padding(Padding::proportional(4))      // 2x horizontal, 1x vertical
    .padding(Padding::new(1, 2, 3, 4));     // Left, Right, Top, Bottom
```

### Style

```rust
Block::bordered()
    .style(Style::default().fg(Color::Blue))
    .border_style(Color::Yellow)
    .title_style(Style::default().bold())
```

### Nesting Widgets

```rust
Paragraph::new("Content")
    .block(Block::bordered().title("Wrapped"))
```

### Inner Area Calculation

```rust
let outer_block = Block::bordered().title("Outer");
let inner_block = Block::bordered().title("Inner");

let inner_area = outer_block.inner(area);

frame.render_widget(outer_block, area);
frame.render_widget(inner_block, inner_area);
```

### Border Merge Strategy

```rust
use ratatui::symbols::merge::MergeStrategy;

Block::bordered()
    .border_type(BorderType::Thick)
    .merge_borders(MergeStrategy::Exact);
```

---

## Paragraph

Text display with optional wrapping and alignment.

### Basic Usage

```rust
use ratatui::widgets::Paragraph;

let paragraph = Paragraph::new("Hello, World!");
frame.render_widget(paragraph, area);
```

### With Block

```rust
Paragraph::new("Content")
    .block(Block::bordered().title("Title"))
```

### Text Wrapping

```rust
use ratatui::widgets::Wrap;

Paragraph::new("Long text that wraps...")
    .wrap(Wrap { trim: true })
```

### Alignment

```rust
Paragraph::new("Centered").centered()
Paragraph::new("Left").left_aligned()
Paragraph::new("Right").right_aligned()
```

### Styled Content

```rust
use ratatui::text::Line;

let paragraph = Paragraph::new(Line::from(vec![
    "Status: ".into(),
    "OK".green().bold(),
]));
```

### Scrolling

```rust
Paragraph::new("Very long content...")
    .scroll((offset_y, offset_x))
```

---

## List

Selectable items with optional highlighting.

### Basic Usage

```rust
use ratatui::widgets::{List, ListItem};

let items: Vec<ListItem> = ["Apple", "Banana", "Cherry"]
    .iter()
    .map(|s| ListItem::new(*s))
    .collect();

let list = List::new(items);
frame.render_widget(list, area);
```

### With Block and Highlighting

```rust
List::new(items)
    .block(Block::bordered().title("Fruits"))
    .highlight_style(Style::default().bg(Color::Blue))
    .highlight_symbol(">> ")
    .repeat_highlight_symbol(true)  // For multi-line items
```

### ListState Methods

```rust
use ratatui::widgets::ListState;

let mut state = ListState::default();

// Selection
state.select(Some(0));
state.select_next();
state.select_previous();
state.select_first();
state.select_last();

// Scrolling
state.scroll_down_by(4);
state.scroll_up_by(4);

// Query
let selected: Option<usize> = state.selected();
let offset: usize = state.offset();
```

### Styled Items

```rust
let items = vec![
    ListItem::new("Normal".white()),
    ListItem::new("Important".red().bold()),
    ListItem::new(Line::from(vec!["Mixed ".into(), "Style".yellow()])),
];
```

### List Direction

```rust
use ratatui::widgets::ListDirection;

List::new(items)
    .direction(ListDirection::BottomToTop)
```

### Scroll Padding

```rust
List::new(items)
    .scroll_padding(1)  // Keep 1 item visible above/below selection
```

---

## Table

Tabular data with rows and columns.

### Basic Usage

```rust
use ratatui::widgets::{Table, Row, Cell};

let table = Table::new(
    vec![
        Row::new(vec!["Alice", "30"]),
        Row::new(vec!["Bob", "25"]),
    ],
    [Constraint::Length(10), Constraint::Length(5)],
);

frame.render_widget(table, area);
```

### With Header and Footer

```rust
Table::new(rows, widths)
    .header(Row::new(vec!["Name", "Age"]).bold())
    .footer(Row::new(vec!["Total", "55"]))
    .block(Block::bordered().title("Users"))
```

### Styled Cells

```rust
let rows = vec![
    Row::new(vec![
        Cell::from("Alice"),
        Cell::from("30").green(),
    ]),
    Row::new(vec![
        Cell::from("Bob"),
        Cell::from("25").yellow(),
    ]),
];
```

### Column Widths

```rust
[
    Constraint::Length(10),     // Fixed 10 cells
    Constraint::Fill(1),        // Fill remaining
    Constraint::Percentage(30), // 30% of available
    Constraint::Min(5),         // At least 5 cells
]
```

### Row Height and Margins

```rust
Row::new(cells)
    .height(2)           // Multi-line rows
    .top_margin(1)
    .bottom_margin(1)
```

### Cell Column Span

```rust
Row::new(vec![
    Cell::new("Spans 2 columns").column_span(2),
])
```

### TableState Methods

```rust
use ratatui::widgets::TableState;

let mut state = TableState::default();

// Row selection
state.select(Some(0));
state.select_next();
state.select_previous();
state.select_first();
state.select_last();
state.scroll_down_by(4);
state.scroll_up_by(4);

// Column selection
state.select_column(Some(1));
state.select_next_column();
state.select_previous_column();
state.select_first_column();
state.select_last_column();
state.scroll_right_by(2);
state.scroll_left_by(2);

// Cell selection
state.select_cell(Some((row, col)));
```

### Highlight Styles

```rust
Table::new(rows, widths)
    .row_highlight_style(Style::new().reversed())
    .column_highlight_style(Style::new().red())
    .cell_highlight_style(Style::new().blue())
    .highlight_symbol(">>")
    .highlight_spacing(HighlightSpacing::Always)
```

---

## Tabs, Gauge, Scrollbar

### Tabs

```rust
use ratatui::widgets::Tabs;

let tabs = Tabs::new(vec!["Tab 1", "Tab 2", "Tab 3"])
    .block(Block::bordered().title("Tabs"))
    .select(0)
    .highlight_style(Style::default().fg(Color::Yellow))
    .padding(" ", " ")
    .divider(symbols::line::VERTICAL);
```

### Gauge

```rust
use ratatui::widgets::Gauge;

let gauge = Gauge::default()
    .block(Block::bordered().title("Progress"))
    .percent(75)
    .ratio(3, 4)          // Alternative: numerator/denominator
    .label("75 of 100")
    .gauge_style(Style::default().fg(Color::Green))
    .use_unicode(true);   // Smoother appearance

// Line Gauge (horizontal bar)
use ratatui::widgets::LineGauge;

let line_gauge = LineGauge::default()
    .ratio(0.5)
    .line_set(symbols::line::THICK);
```

### Scrollbar

```rust
use ratatui::widgets::{Scrollbar, ScrollbarOrientation, ScrollbarState};

let mut state = ScrollbarState::new(total_items)
    .position(current_position)
    .viewport_content_length(visible_items);

let scrollbar = Scrollbar::new(ScrollbarOrientation::VerticalRight)
    .begin_symbol(Some("up"))
    .end_symbol(Some("down"))
    .track_symbol(Some("│"))
    .thumb_symbol("█");

frame.render_stateful_widget(scrollbar, area, &mut state);
```

---

## Chart

Line, scatter, bar, and area charts.

### Basic Usage

```rust
use ratatui::widgets::{Chart, Dataset, Axis};

let data = [(0.0, 0.0), (1.0, 1.0), (2.0, 4.0)];

let chart = Chart::new(vec![
    Dataset::default().data(&data)
])
.x_axis(Axis::default().title("X"))
.y_axis(Axis::default().title("Y"));

frame.render_widget(chart, area);
```

### Multiple Datasets

```rust
Chart::new(vec![
    Dataset::default()
        .name("Series A")
        .data(&data_a)
        .marker(Marker::Dot)
        .graph_type(GraphType::Line),
    Dataset::default()
        .name("Series B")
        .data(&data_b)
        .marker(Marker::Block)
        .graph_type(GraphType::Scatter),
])
```

### Graph Types

```rust
Dataset::default()
    .graph_type(GraphType::Line)     // Connected lines
    .graph_type(GraphType::Scatter)  // Individual points
    .graph_type(GraphType::Bar)      // Vertical bars from axis
    .graph_type(GraphType::Area)     // Filled area under line
    .fill_to_y(0.0)                  // For Area: fill to y-coordinate
```

### Axis Configuration

```rust
Axis::default()
    .title("X Axis")
    .bounds([0.0, 100.0])
    .labels(vec!["0".into(), "50".into(), "100".into()])
    .labels_alignment(Alignment::Center)
    .style(Style::default().gray())
```

### Markers

```rust
Marker::Dot       // Single character
Marker::Block     // Block character
Marker::Braille   // High-resolution (2x4 per cell)
Marker::HalfBlock // Foreground/background colors
```

### Legend Position

```rust
use ratatui::widgets::LegendPosition;

Chart::new(datasets)
    .legend_position(Some(LegendPosition::TopLeft))
    .hidden_legend_constraints((Constraint::Ratio(1, 3), Constraint::Ratio(1, 4)))
```

---

## BarChart

Vertical or horizontal bar visualization.

### Basic Usage

```rust
use ratatui::widgets::BarChart;

let barchart = BarChart::default()
    .data(&[("A", 10), ("B", 20), ("C", 15)])
    .bar_width(3)
    .bar_gap(1);

frame.render_widget(barchart, area);
```

### With Block

```rust
BarChart::default()
    .data(&data)
    .block(Block::bordered().title("Chart"))
```

### Styling

```rust
BarChart::default()
    .data(&data)
    .bar_style(Style::default().fg(Color::Green))
    .value_style(Style::default().fg(Color::Yellow))
    .label_style(Style::default().fg(Color::White))
```

### Individual Bars

```rust
use ratatui::widgets::{Bar, BarGroup};

let bars = vec![
    Bar::default()
        .value(100)
        .label("Label".into())
        .style(Style::default().fg(Color::Red))
        .value_style(Style::default().fg(Color::White)),
];

let group = BarGroup::default()
    .label("Q1".into())
    .bars(&bars);

let chart = BarChart::default().data(group);
```

### Direction

```rust
use ratatui::widgets::BarDirection;

BarChart::default()
    .direction(BarDirection::Vertical)    // Default
    .direction(BarDirection::Horizontal)  // Horizontal bars
```

---

## Canvas

Coordinate system for drawing shapes.

### Basic Usage

```rust
use ratatui::widgets::Canvas;

let canvas = Canvas::default()
    .x_bounds([0.0, 100.0])
    .y_bounds([0.0, 100.0])
    .paint(|ctx| {
        // Draw shapes here
    });

frame.render_widget(canvas, area);
```

### Drawing Primitives

```rust
use ratatui::widgets::canvas::{Circle, Rectangle, Line, Points, FilledLine};

// Circle
ctx.draw(&Circle {
    x: 50.0, y: 50.0, radius: 20.0, color: Color::Red
});

// Rectangle
ctx.draw(&Rectangle {
    x: 10.0, y: 10.0, width: 30.0, height: 20.0, color: Color::Blue
});

// Line
ctx.draw(&Line {
    x1: 0.0, y1: 0.0, x2: 100.0, y2: 100.0, color: Color::Green
});

// Filled Line (area under line)
ctx.draw(&FilledLine {
    x1: 0.0, y1: 50.0, x2: 100.0, y2: 50.0,
    fill_to_y: 0.0, color: Color::Cyan
});

// Points
ctx.draw(&Points {
    coords: &[(10.0, 20.0), (30.0, 40.0)],
    color: Color::Yellow
});

// World Map
use ratatui::widgets::canvas::{Map, MapResolution};

ctx.draw(&Map {
    resolution: MapResolution::High,
    color: Color::White,
});
```

### Coordinate System

- Bounds define the visible area
- Origin is bottom-left (mathematical, not terminal top-left)
- Coordinates are floating point
- Canvas automatically scales to terminal area

### Markers

```rust
Canvas::default()
    .marker(Marker::Dot)       // Default
    .marker(Marker::Block)
    .marker(Marker::Braille)   // Higher resolution (2x4 per cell)
    .marker(Marker::HalfBlock) // Supports fg/bg colors
```

### Layers

```rust
Canvas::default()
    .paint(|ctx| {
        ctx.draw(&shape1);
        ctx.layer();           // Save current layer, start fresh
        ctx.draw(&shape2);     // Drawn on new layer
    });
```

### Print Text on Canvas

```rust
Canvas::default()
    .paint(|ctx| {
        ctx.print(10.0, 20.0, Line::from("Label"));
    });
```

### Background Color

```rust
Canvas::default()
    .background_color(Color::Black)
```

---

## Sparkline

Compact inline bar charts for showing trends.

### Basic Usage

```rust
use ratatui::widgets::Sparkline;

let sparkline = Sparkline::default()
    .data(&[1, 3, 2, 5, 4, 6, 3, 2, 7, 5]);

frame.render_widget(sparkline, area);
```

### With Block

```rust
Sparkline::default()
    .data(&data)
    .block(Block::bordered().title("Trend"))
```

### Styling

```rust
Sparkline::default()
    .data(&data)
    .style(Style::default().fg(Color::Green))
```

### Max Value

```rust
Sparkline::default()
    .data(&data)
    .max(100)  // Set explicit max for consistent scaling
```

### Direction

```rust
use ratatui::widgets::RenderDirection;

Sparkline::default()
    .data(&data)
    .direction(RenderDirection::RightToLeft)  // Reverse direction
```

### Use Cases

- CPU/memory usage over time
- Request rates
- Any time-series trend in compact form

---

## When Writing Code

1. Use `Block::bordered()` as the most common block pattern
2. Use stateful widgets (List, Table, Scrollbar) with `render_stateful_widget`
3. Chain `.block()` to wrap widgets in borders
4. Use `Wrap { trim: true }` for clean text wrapping
5. Use `GraphType::Line` for line charts, `GraphType::Scatter` for scatter plots
6. Canvas coordinates use mathematical convention (origin bottom-left)
7. Sparklines are efficient for showing trends in small spaces
8. BarChart groups allow multiple bar sets side by side

## When Answering Questions

1. Answer from patterns first
2. If the question involves custom border sets, complex cell formatting, canvas coordinate transformations, custom markers, or niche widget options, consult the raw docs
3. If still insufficient, inform user and answer from built-in knowledge
