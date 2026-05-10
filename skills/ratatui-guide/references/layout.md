# Ratatui Layout

> **Version:** 0.30.0
>
> Constraint-based layout system for splitting terminal areas.

## Key Patterns

### Pattern 1: Vertical Layout Split

Split area into vertical sections (header/body/footer):

```rust
use ratatui::layout::{Constraint, Layout};

let [header, body, footer] = Layout::vertical([
    Constraint::Length(3),
    Constraint::Fill(1),
    Constraint::Length(1),
]).areas(frame.area());
```

### Pattern 2: Horizontal Layout Split

Split area into horizontal sections (sidebar/main):

```rust
use ratatui::layout::{Constraint, Layout};

let [sidebar, main] = Layout::horizontal([
    Constraint::Length(20),
    Constraint::Fill(1),
]).areas(frame.area());
```

### Pattern 3: Nested Layout

Combine vertical and horizontal layouts for complex UIs:

```rust
use ratatui::layout::{Constraint, Layout};
use ratatui::widgets::Block;

let [header, body, footer] = Layout::vertical([
    Constraint::Length(3),
    Constraint::Fill(1),
    Constraint::Length(1),
]).areas(frame.area());

let [sidebar, main_content] = Layout::horizontal([
    Constraint::Length(20),
    Constraint::Fill(1),
]).areas(body);

frame.render_widget(Block::bordered().title("Header"), header);
frame.render_widget(Block::bordered().title("Sidebar"), sidebar);
frame.render_widget(Block::bordered().title("Content"), main_content);
frame.render_widget(Block::bordered().title("Footer"), footer);
```

### Pattern 4: Constraint Types

All available constraint types:

```rust
use ratatui::layout::Constraint;

// Fixed length in cells
Constraint::Length(10),

// Fill remaining space (weight 1)
Constraint::Fill(1),

// Percentage of available space
Constraint::Percentage(50),

// Minimum size
Constraint::Min(5),

// Maximum size
Constraint::Max(20),

// Ratio (e.g., 1:2)
Constraint::Ratio(1, 2),
```

### Pattern 5: Spacing Between Areas

Add gaps between layout areas:

```rust
use ratatui::layout::{Constraint, Layout};

let [left, right] = Layout::horizontal([
    Constraint::Percentage(50),
    Constraint::Percentage(50),
])
.spacing(2)  // 2-cell gap between areas
.areas(frame.area());
```

## API Reference Table

| Function/Type | Description | Example |
|---------------|-------------|---------|
| `Layout::vertical()` | Create vertical layout | `Layout::vertical([constraints])` |
| `Layout::horizontal()` | Create horizontal layout | `Layout::horizontal([constraints])` |
| `Layout::areas()` | Split area into array | `let [a, b] = layout.areas(area)` |
| `Layout::split()` | Split into Vec | `let areas = layout.split(area)` |
| `Layout::spacing()` | Add gaps between areas | `Layout::horizontal([...]).spacing(2)` |
| `Constraint::Length(n)` | Fixed size in cells | `Constraint::Length(10)` |
| `Constraint::Fill(w)` | Fill remaining with weight | `Constraint::Fill(1)` |
| `Constraint::Percentage(p)` | Percentage of available | `Constraint::Percentage(50)` |
| `Constraint::Min(n)` | Minimum size | `Constraint::Min(5)` |
| `Constraint::Max(n)` | Maximum size | `Constraint::Max(20)` |
| `Constraint::Ratio(n, d)` | Ratio-based size | `Constraint::Ratio(1, 2)` |
| `Rect` | Area with x, y, width, height | `area.x`, `area.width` |

## Constraints

Constraints define how Layout splits available space.

### Constraint Types

| Constraint | Description | Example |
|------------|-------------|---------|
| `Length(n)` | Fixed size in cells | Header with 3 lines |
| `Fill(w)` | Fill remaining with weight | Body fills rest |
| `Percentage(p)` | Percentage of available | 50% for each half |
| `Min(n)` | Minimum size | At least 5 cells |
| `Max(n)` | Maximum size | No more than 20 cells |
| `Ratio(n, d)` | Ratio-based | 1:2 split |

### Constraint Priority

Constraints are resolved in priority order:

1. `Constraint::Min` - Highest priority
2. `Constraint::Max`
3. `Constraint::Length`
4. `Constraint::Percentage`
5. `Constraint::Ratio`
6. `Constraint::Fill` - Lowest priority

### Common Patterns

#### Fixed Header/Footer with Flexible Body

```rust
let [header, body, footer] = Layout::vertical([
    Constraint::Length(3),    // Fixed 3 lines
    Constraint::Fill(1),      // Remaining space
    Constraint::Length(1),    // Fixed 1 line
]).areas(frame.area());
```

#### Sidebar with Main Content

```rust
let [sidebar, main] = Layout::horizontal([
    Constraint::Length(20),   // Fixed 20 columns
    Constraint::Fill(1),      // Remaining width
]).areas(frame.area());
```

#### Equal Split

```rust
let [left, right] = Layout::horizontal([
    Constraint::Percentage(50),
    Constraint::Percentage(50),
]).areas(frame.area());
```

#### Weighted Fill

```rust
// 1:2 ratio using Fill
let [small, large] = Layout::horizontal([
    Constraint::Fill(1),
    Constraint::Fill(2),
]).areas(frame.area());
```

### Constraint Enum

```rust
enum Constraint {
    Min(u16),       // Minimum size
    Max(u16),       // Maximum size
    Length(u16),    // Fixed size in cells
    Percentage(u16), // Percentage of available
    Ratio(u32, u32), // Ratio-based (numerator, denominator)
    Fill(u16),      // Fill remaining with weight
}
```

#### Constraint Methods

- `Constraint::from_lengths([10, 20, 10])` - Create length constraints
- `Constraint::from_ratios([(1, 4), (1, 2), (1, 4)])` - Create ratio constraints
- `Constraint::from_percentages([25, 50, 25])` - Create percentage constraints
- `Constraint::from_mins([0, 100, 0])` - Create minimum constraints
- `Constraint::from_maxes([30, 170])` - Create maximum constraints
- `Constraint::from_fills([1, 2, 1])` - Create fill constraints

## Splitting and Nesting

Layout splits areas into regions using constraints.

### Basic Splitting

#### Vertical Split

```rust
let [top, bottom] = Layout::vertical([
    Constraint::Length(5),
    Constraint::Fill(1),
]).areas(frame.area());
```

#### Horizontal Split

```rust
let [left, right] = Layout::horizontal([
    Constraint::Length(20),
    Constraint::Fill(1),
]).areas(frame.area());
```

### Nested Layouts

```rust
// First split vertically
let [header, body, footer] = Layout::vertical([
    Constraint::Length(3),
    Constraint::Fill(1),
    Constraint::Length(1),
]).areas(frame.area());

// Then split body horizontally
let [sidebar, content] = Layout::horizontal([
    Constraint::Length(20),
    Constraint::Fill(1),
]).areas(body);
```

### Adding Spacing

```rust
let [left, right] = Layout::horizontal([
    Constraint::Percentage(50),
    Constraint::Percentage(50),
])
.spacing(2)  // 2-cell gap
.areas(frame.area());
```

### Destructuring vs Vec

```rust
// Destructuring (preferred for known count)
let [a, b, c] = layout.areas(frame.area());

// Vec (dynamic count)
let areas = layout.split(frame.area());
```

### Layout Struct

```rust
struct Layout {
    // direction, constraints, margin, flex, spacing
}
```

The primary layout engine for dividing terminal space using constraints.

#### Construction

- `Layout::default()` - Create with defaults (vertical, no constraints, no margin)
- `Layout::new(direction, constraints)` - Create with direction and constraints
- `Layout::vertical(constraints)` - Create vertical layout
- `Layout::horizontal(constraints)` - Create horizontal layout

#### Configuration

- `.direction(Direction)` - Set layout direction
- `.constraints(constraints)` - Set constraints
- `.margin(u16)` - Set uniform margin on all sides
- `.horizontal_margin(u16)` - Set horizontal margin only
- `.vertical_margin(u16)` - Set vertical margin only
- `.flex(Flex)` - Control space distribution
- `.spacing(u16)` - Set gap between segments (also accepts negative for overlap)

#### Layout Operations

- `.areas(area)` - Split into fixed-size array `[Rect; N]`
- `.try_areas(area)` - Split into array, returns `Result`
- `.split(area)` - Split into `Rc<[Rect]>` for runtime count
- `.spacers(area)` - Get spacer rectangles between areas
- `.split_with_spacers(area)` - Split and return both areas and spacers

#### Cache Management

- `Layout::init_cache(size)` - Initialize layout cache with custom size

## Flex Distribution

The `Flex` enum controls how extra space is distributed when constraints are satisfied.

### Flex Variants

```rust
enum Flex {
    Legacy,        // Last element gets excess space (default behavior)
    Start,         // Align items to start, excess at end
    End,           // Align items to end, excess at start
    Center,        // Center items, excess on both sides
    SpaceBetween,  // Distribute excess between elements
    SpaceAround,   // Distribute space around each element
    SpaceEvenly,   // Equal spacing everywhere including edges
}
```

### Flex Examples

#### Flex::Start

```rust
// Items aligned to start, excess space at end
Layout::horizontal([Length(20), Length(20), Length(20)])
    .flex(Flex::Start);
```

#### Flex::Center

```rust
// Items centered within container
Layout::horizontal([Length(20), Length(20)])
    .flex(Flex::Center);
```

#### Flex::SpaceBetween

```rust
// Space distributed between elements, none at edges
Layout::horizontal([Length(20), Length(20), Length(20)])
    .flex(Flex::SpaceBetween);
```

#### Flex::SpaceEvenly

```rust
// Equal spacing before, between, and after elements
Layout::horizontal([Length(20), Length(20)])
    .flex(Flex::SpaceEvenly);
```

### Spacing Interaction with Flex

Note: `spacing()` is not applied for `SpaceAround`, `SpaceEvenly`, and `SpaceBetween` flex modes.

## Direction

```rust
enum Direction {
    Horizontal,  // Side by side (left to right)
    Vertical,    // Top to bottom (default)
}
```

### Direction Methods

- `.perpendicular()` - Returns the perpendicular direction (Horizontal <-> Vertical)

## Rect, Margin, Padding

### Rect

A rectangular area in the terminal.

```rust
struct Rect {
    pub x: u16,       // Left edge coordinate
    pub y: u16,       // Top edge coordinate
    pub width: u16,   // Width in columns
    pub height: u16,  // Height in rows
}
```

#### Construction

- `Rect::new(x, y, width, height)` - Create new rect (clamped to u16 bounds)
- `Rect::default()` - Zero-sized rect at origin
- `Rect::from((Position, Size))` - Create from position and size

#### Properties

- `.area()` - Total area in cells (u32)
- `.is_empty()` - True if zero area
- `.left()`, `.right()` - Edge coordinates
- `.top()`, `.bottom()` - Edge coordinates

#### Spatial Operations

- `.inner(Margin)` - Shrink by margin
- `.outer(Margin)` - Expand by margin
- `.offset(Offset)` - Move by offset
- `.resize(Size)` - Resize keeping position
- `.union(other)` - Bounding box containing both
- `.intersection(other)` - Overlapping area
- `.clamp(other)` - Constrain to fit inside other

#### Centering

- `.centered_horizontally(Constraint)` - Center horizontally
- `.centered_vertically(Constraint)` - Center vertically
- `.centered(h_constraint, v_constraint)` - Center both ways

#### Testing and Iteration

- `.contains(Position)` - Check if position inside
- `.intersects(other)` - Check if overlaps
- `.rows()` - Iterator over horizontal rows
- `.columns()` - Iterator over vertical columns
- `.positions()` - Iterator over all cell positions

#### Layout Method on Rect

```rust
// Split rect directly
let [top, bottom] = area.layout(&layout);
let areas = area.layout_vec(&layout);  // Returns Vec
let result = area.try_layout(&layout); // Returns Result
```

### Margin

Spacing around rectangular areas.

```rust
struct Margin {
    pub horizontal: u16,  // Applied to left and right
    pub vertical: u16,    // Applied to top and bottom
}
```

#### Construction

- `Margin::new(horizontal, vertical)` - Create margin
- `Margin::default()` - Zero margin

#### Usage

```rust
// Apply margin to rect
let inner = area.inner(Margin::new(2, 1));

// Margin on layout
let layout = Layout::vertical([...]).margin(2);
```

### Position

A point in the terminal coordinate system.

```rust
struct Position {
    pub x: u16,  // Column (left edge = 0)
    pub y: u16,  // Row (top edge = 0)
}
```

#### Constants

- `Position::ORIGIN` - (0, 0)
- `Position::MIN` - Minimum position
- `Position::MAX` - Maximum position

#### Construction

- `Position::new(x, y)` - Create position
- `Position::from((u16, u16))` - Create from tuple
- `Position::from(Rect)` - Top-left corner of rect

#### Movement

- `.offset(Offset)` - Move by offset (clamped to u16 bounds)
- `position + Offset` - Add offset
- `position - Offset` - Subtract offset

### Size

Dimensions in the terminal.

```rust
struct Size {
    pub width: u16,   // Columns
    pub height: u16,  // Rows
}
```

#### Methods

- `Size::new(width, height)` - Create size
- `.area()` - Total cells (u32)

### Offset

Relative movement in the coordinate system.

```rust
struct Offset {
    pub x: i32,  // Positive = right, negative = left
    pub y: i32,  // Positive = down, negative = up
}
```

#### Constants

- `Offset::ZERO` - (0, 0)
- `Offset::MIN` - Minimum offset
- `Offset::MAX` - Maximum offset

### Spacing

Spacing between segments in a layout.

```rust
enum Spacing {
    Space(u16),   // Positive: gap between segments
    Overlap(u16), // Negative: overlap segments
}
```

Can be created from integers: positive becomes `Space`, negative becomes `Overlap`.

```rust
.spacing(2)      // 2-cell gap
.spacing(-1)     // 1-cell overlap (borders merge)
```

## Alignment

### HorizontalAlignment

```rust
enum HorizontalAlignment {
    Left,
    Center,
    Right,
}
```

Alias: `Alignment` (for backwards compatibility)

### VerticalAlignment

```rust
enum VerticalAlignment {
    Top,
    Center,
    Bottom,
}
```

## Iterators

### Rows

Iterator over horizontal rows within a Rect.

```rust
for (i, row) in area.rows().enumerate() {
    // row is a Rect with height 1
    format!("Row {i}").render(row, buf);
}
```

### Columns

Iterator over vertical columns within a Rect.

```rust
for (i, col) in area.columns().enumerate() {
    // col is a Rect with width 1
    format!("{}", i % 10).render(col, buf);
}
```

### Positions

Iterator over all positions within a Rect (row-major order).

```rust
for (i, pos) in area.positions().enumerate() {
    buf[pos].set_symbol(&format!("{}", i % 10));
}
```

## Best Practices

1. Use `Fill(1)` for flexible areas that expand to fill space
2. Prefer `Length()` for fixed-size headers/footers
3. Chain `.spacing()` to add gaps between areas
4. Use destructuring for cleaner code: `let [a, b, c] = layout.areas(area)`
5. Prefer `Layout::vertical()` / `Layout::horizontal()` over `Layout::new()` with direction
6. Use `.flex(Flex::Center)` for centering content
7. Remember constraint priority when mixing types: Min > Max > Length > Percentage > Ratio > Fill
