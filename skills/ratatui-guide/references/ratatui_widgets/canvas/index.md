*[ratatui_widgets](../index.md) / [canvas](index.md)*

---

# Module `canvas`

A [`Canvas`](#canvas) and a collection of [`Shape`](#shape)s.

The [`Canvas`](#canvas) is a blank space on which you can draw anything manually or use one of the
predefined [`Shape`](#shape)s.

The available shapes are:

- [`Circle`](../index.md): A basic circle
- [`Line`](../index.md): A line between two points
- [`Map`](../index.md): A world map
- [`Points`](../index.md): A scatter of points
- [`Rectangle`](../index.md): A basic rectangle

You can also implement your own custom [`Shape`](#shape)s.

## Contents

- [Structs](#structs)
  - [`Circle`](#circle)
  - [`FilledLine`](#filledline)
  - [`Line`](#line)
  - [`Map`](#map)
  - [`Points`](#points)
  - [`Rectangle`](#rectangle)
  - [`Label`](#label)
  - [`Painter`](#painter)
  - [`Context`](#context)
  - [`Canvas`](#canvas)
- [Enums](#enums)
  - [`MapResolution`](#mapresolution)
- [Traits](#traits)
  - [`Shape`](#shape)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Circle`](#circle) | struct |  |
| [`FilledLine`](#filledline) | struct |  |
| [`Line`](#line) | struct |  |
| [`Map`](#map) | struct |  |
| [`Points`](#points) | struct |  |
| [`Rectangle`](#rectangle) | struct |  |
| [`Label`](#label) | struct | Label to draw some text on the canvas |
| [`Painter`](#painter) | struct | Painter is an abstraction over the [`Context`] that allows to draw shapes on the grid. |
| [`Context`](#context) | struct | Holds the state of the [`Canvas`] when painting to it. |
| [`Canvas`](#canvas) | struct | The Canvas widget provides a means to draw shapes (Lines, Rectangles, Circles, etc.) on a grid. |
| [`MapResolution`](#mapresolution) | enum |  |
| [`Shape`](#shape) | trait | Something that can be drawn on a [`Canvas`]. |

## Structs

### `Circle`

```rust
struct Circle {
    pub x: f64,
    pub y: f64,
    pub radius: f64,
    pub color: ratatui_core::style::Color,
}
```

A circle with a given center and radius and with a given color

#### Fields

- **`x`**: `f64`

  `x` coordinate of the circle's center

- **`y`**: `f64`

  `y` coordinate of the circle's center

- **`radius`**: `f64`

  Radius of the circle

- **`color`**: `ratatui_core::style::Color`

  Color of the circle

#### Implementations

- `const fn new(x: f64, y: f64, radius: f64, color: Color) -> Self`

  Create a new circle with the given center, radius, and color

#### Trait Implementations

##### `impl Clone for Circle`

- `fn clone(&self) -> Circle` — [`Circle`](../index.md#circle)

##### `impl Debug for Circle`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Circle`

- `fn default() -> Circle` — [`Circle`](../index.md#circle)

##### `impl IntoEither for Circle`

##### `impl PartialEq for Circle`

- `fn eq(&self, other: &Circle) -> bool` — [`Circle`](../index.md#circle)

##### `impl Shape for Circle`

- `fn draw(&self, painter: &mut Painter<'_, '_>)` — [`Painter`](#painter)

##### `impl StructuralPartialEq for Circle`

### `FilledLine`

```rust
struct FilledLine {
    pub x1: f64,
    pub y1: f64,
    pub x2: f64,
    pub y2: f64,
    pub fill_to_y: f64,
    pub color: ratatui_core::style::Color,
}
```

A filled line from `(x1, y1)` to `(x2, y2)` that fills the area under/over the line
to `fill_to_y` with the given color.

This is useful for creating area charts or filling the space under a line graph.

#### Fields

- **`x1`**: `f64`

  `x` of the starting point

- **`y1`**: `f64`

  `y` of the starting point

- **`x2`**: `f64`

  `x` of the ending point

- **`y2`**: `f64`

  `y` of the ending point

- **`fill_to_y`**: `f64`

  Y-coordinate to fill to (fills area between the line and this Y value)

- **`color`**: `ratatui_core::style::Color`

  Color of the line and filled area

#### Implementations

- `const fn new(x1: f64, y1: f64, x2: f64, y2: f64, fill_to_y: f64, color: Color) -> Self`

  Create a new filled line from `(x1, y1)` to `(x2, y2)` that fills to `fill_to_y`

#### Trait Implementations

##### `impl Clone for FilledLine`

- `fn clone(&self) -> FilledLine` — [`FilledLine`](../index.md#filledline)

##### `impl Debug for FilledLine`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl IntoEither for FilledLine`

##### `impl PartialEq for FilledLine`

- `fn eq(&self, other: &FilledLine) -> bool` — [`FilledLine`](../index.md#filledline)

##### `impl Shape for FilledLine`

- `fn draw(&self, painter: &mut Painter<'_, '_>)` — [`Painter`](#painter)

##### `impl StructuralPartialEq for FilledLine`

### `Line`

```rust
struct Line {
    pub x1: f64,
    pub y1: f64,
    pub x2: f64,
    pub y2: f64,
    pub color: ratatui_core::style::Color,
}
```

A line from `(x1, y1)` to `(x2, y2)` with the given color

# Examples

```rust
use ratatui_core::style::Color;
use ratatui_widgets::canvas::{Canvas, Line};
Canvas::default().paint(|ctx| {
    ctx.draw(&Line::new(0.0, 0.0, 1.0, 0.0, Color::Red));
    ctx.draw(&Line::new(1.0, 0.0, 0.5, 1.0, Color::Red));
    ctx.draw(&Line::new(0.5, 1.0, 0.0, 0.0, Color::Red));
});
```

#### Fields

- **`x1`**: `f64`

  `x` of the starting point

- **`y1`**: `f64`

  `y` of the starting point

- **`x2`**: `f64`

  `x` of the ending point

- **`y2`**: `f64`

  `y` of the ending point

- **`color`**: `ratatui_core::style::Color`

  Color of the line

#### Implementations

- `const fn new(x1: f64, y1: f64, x2: f64, y2: f64, color: Color) -> Self`

  Create a new line from `(x1, y1)` to `(x2, y2)` with the given color

#### Trait Implementations

##### `impl Clone for Line`

- `fn clone(&self) -> Line` — [`Line`](../index.md#line)

##### `impl Debug for Line`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Line`

- `fn default() -> Line` — [`Line`](../index.md#line)

##### `impl IntoEither for Line`

##### `impl PartialEq for Line`

- `fn eq(&self, other: &Line) -> bool` — [`Line`](../index.md#line)

##### `impl Shape for Line`

- `fn draw(&self, painter: &mut Painter<'_, '_>)` — [`Painter`](#painter)

##### `impl StructuralPartialEq for Line`

### `Map`

```rust
struct Map {
    pub resolution: MapResolution,
    pub color: ratatui_core::style::Color,
}
```

A world map. It represents the world using the [EPSG:4326 coordinate reference system](https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset).

A world map can be rendered with different [resolutions](MapResolution) and [colors](Color).

#### Fields

- **`resolution`**: `MapResolution`

  The resolution of the map.
  
  This is the number of points used to draw the map.

- **`color`**: `ratatui_core::style::Color`

  Map color
  
  This is the color of the points of the map.

#### Trait Implementations

##### `impl Clone for Map`

- `fn clone(&self) -> Map` — [`Map`](../index.md#map)

##### `impl Debug for Map`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Map`

- `fn default() -> Map` — [`Map`](../index.md#map)

##### `impl Eq for Map`

##### `impl<K> Equivalent for Map`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for Map`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Map`

##### `impl PartialEq for Map`

- `fn eq(&self, other: &Map) -> bool` — [`Map`](../index.md#map)

##### `impl Shape for Map`

- `fn draw(&self, painter: &mut Painter<'_, '_>)` — [`Painter`](#painter)

##### `impl StructuralPartialEq for Map`

### `Points<'a>`

```rust
struct Points<'a> {
    pub coords: &'a [(f64, f64)],
    pub color: ratatui_core::style::Color,
}
```

A group of points with a given color

#### Fields

- **`coords`**: `&'a [(f64, f64)]`

  List of points to draw

- **`color`**: `ratatui_core::style::Color`

  Color of the points

#### Implementations

- `const fn new(coords: &'a [(f64, f64)], color: Color) -> Self`

  Create a new Points shape with the given coordinates and color

#### Trait Implementations

##### `impl Clone for Points<'a>`

- `fn clone(&self) -> Points<'a>` — [`Points`](../index.md#points)

##### `impl Debug for Points<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Points<'a>`

- `fn default() -> Points<'a>` — [`Points`](../index.md#points)

##### `impl IntoEither for Points<'a>`

##### `impl PartialEq for Points<'a>`

- `fn eq(&self, other: &Points<'a>) -> bool` — [`Points`](../index.md#points)

##### `impl Shape for Points<'_>`

- `fn draw(&self, painter: &mut Painter<'_, '_>)` — [`Painter`](#painter)

##### `impl StructuralPartialEq for Points<'a>`

### `Rectangle`

```rust
struct Rectangle {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
    pub color: ratatui_core::style::Color,
}
```

A rectangle to draw on a [`Canvas`](crate::canvas::Canvas)

Sizes used here are **not** in terminal cell. This is much more similar to the
mathematic coordinate system.

#### Fields

- **`x`**: `f64`

  The `x` position of the rectangle.
  
  The rectangle is positioned from its bottom left corner.

- **`y`**: `f64`

  The `y` position of the rectangle.
  
  The rectangle is positioned from its bottom left corner.

- **`width`**: `f64`

  The width of the rectangle.

- **`height`**: `f64`

  The height of the rectangle.

- **`color`**: `ratatui_core::style::Color`

  The color of the rectangle.

#### Implementations

- `const fn new(x: f64, y: f64, width: f64, height: f64, color: Color) -> Self`

  Create a new rectangle with the given position, size, and color

#### Trait Implementations

##### `impl Clone for Rectangle`

- `fn clone(&self) -> Rectangle` — [`Rectangle`](../index.md#rectangle)

##### `impl Debug for Rectangle`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Rectangle`

- `fn default() -> Rectangle` — [`Rectangle`](../index.md#rectangle)

##### `impl IntoEither for Rectangle`

##### `impl PartialEq for Rectangle`

- `fn eq(&self, other: &Rectangle) -> bool` — [`Rectangle`](../index.md#rectangle)

##### `impl Shape for Rectangle`

- `fn draw(&self, painter: &mut Painter<'_, '_>)` — [`Painter`](#painter)

##### `impl StructuralPartialEq for Rectangle`

### `Label<'a>`

```rust
struct Label<'a> {
    // [REDACTED: Private Fields]
}
```

Label to draw some text on the canvas

#### Trait Implementations

##### `impl Clone for Label<'a>`

- `fn clone(&self) -> Label<'a>` — [`Label`](#label)

##### `impl Debug for Label<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Label<'a>`

- `fn default() -> Label<'a>` — [`Label`](#label)

##### `impl IntoEither for Label<'a>`

##### `impl PartialEq for Label<'a>`

- `fn eq(&self, other: &Label<'a>) -> bool` — [`Label`](#label)

##### `impl StructuralPartialEq for Label<'a>`

### `Painter<'a, 'b>`

```rust
struct Painter<'a, 'b> {
    // [REDACTED: Private Fields]
}
```

Painter is an abstraction over the [`Context`](#context) that allows to draw shapes on the grid.

It is used by the [`Shape`](#shape) trait to draw shapes on the grid. It can be useful to think of this
as similar to the [`Buffer`](../../ratatui_core/index.md) struct that is used to draw widgets on the terminal.

#### Implementations

- `fn get_point(&self, x: f64, y: f64) -> Option<(usize, usize)>`

  Convert the `(x, y)` coordinates to location of a point on the grid

  

  `(x, y)` coordinates are expressed in the coordinate system of the canvas. The origin is in

  the lower left corner of the canvas (unlike most other coordinates in `Ratatui` where the

  origin is the upper left corner). The `x` and `y` bounds of the canvas define the specific

  area of some coordinate system that will be drawn on the canvas. The resolution of the grid

  is used to convert the `(x, y)` coordinates to the location of a point on the grid.

  

  The grid coordinates are expressed in the coordinate system of the grid. The origin is in

  the top left corner of the grid. The x and y bounds of the grid are always `[0, width - 1]`

  and `[0, height - 1]` respectively. The resolution of the grid is used to convert the

  `(x, y)` coordinates to the location of a point on the grid.

  

  Points are rounded to the nearest grid cell (with points exactly in the center of a cell

  rounding up).

  

  # Examples

  

  ```rust

  use ratatui::symbols;

  use ratatui::widgets::canvas::{Context, Painter};

  

  let mut ctx = Context::new(2, 2, [1.0, 2.0], [0.0, 2.0], symbols::Marker::Braille);

  let mut painter = Painter::from(&mut ctx);

  

  let point = painter.get_point(1.0, 0.0);

  assert_eq!(point, Some((0, 7)));

  

  let point = painter.get_point(1.5, 1.0);

  assert_eq!(point, Some((2, 4)));

  

  let point = painter.get_point(0.0, 0.0);

  assert_eq!(point, None);

  

  let point = painter.get_point(2.0, 2.0);

  assert_eq!(point, Some((3, 0)));

  

  let point = painter.get_point(1.0, 2.0);

  assert_eq!(point, Some((0, 0)));

  ```

- `fn paint(&mut self, x: usize, y: usize, color: Color)`

  Paint a point of the grid

  

  # Example

  

  ```rust

  use ratatui::style::Color;

  use ratatui::symbols;

  use ratatui::widgets::canvas::{Context, Painter};

  

  let mut ctx = Context::new(1, 1, [0.0, 2.0], [0.0, 2.0], symbols::Marker::Braille);

  let mut painter = Painter::from(&mut ctx);

  painter.paint(1, 3, Color::Red);

  ```

- `const fn bounds(&self) -> (&[f64; 2], &[f64; 2])`

  Canvas context bounds by axis.

  

  # Example

  

  ```rust

  use ratatui::style::Color;

  use ratatui::symbols;

  use ratatui::widgets::canvas::{Context, Painter};

  

  let mut ctx = Context::new(1, 1, [0.0, 2.0], [0.0, 2.0], symbols::Marker::Braille);

  let mut painter = Painter::from(&mut ctx);

  assert_eq!(painter.bounds(), (&[0.0, 2.0], &[0.0, 2.0]));

  ```

#### Trait Implementations

##### `impl Debug for Painter<'a, 'b>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl IntoEither for Painter<'a, 'b>`

### `Context<'a>`

```rust
struct Context<'a> {
    // [REDACTED: Private Fields]
}
```

Holds the state of the [`Canvas`](#canvas) when painting to it.

This is used by the [`Canvas`](#canvas) widget to draw shapes on the grid. It can be useful to think of
this as similar to the `Frame` struct that is used to draw widgets on the terminal.

#### Implementations

- `fn new(width: u16, height: u16, x_bounds: [f64; 2], y_bounds: [f64; 2], marker: Marker) -> Self`

  Create a new Context with the given width and height measured in terminal columns and rows

  respectively. The `x` and `y` bounds define the specific area of some coordinate system that

  will be drawn on the canvas. The marker defines the type of points used to draw the shapes.

  

  Applications should not use this directly but rather use the [`Canvas`](#canvas) widget. This will be

  created by the `Canvas::paint` method and passed to the closure that is used to draw on

  the canvas.

  

  The `x` and `y` bounds should be specified as left/right and bottom/top respectively. For

  example, if you want to draw a map of the world, you might want to use the following bounds:

  

  ```rust

  use ratatui::symbols;

  use ratatui::widgets::canvas::Context;

  

  let ctx = Context::new(

      100,

      100,

      [-180.0, 180.0],

      [-90.0, 90.0],

      symbols::Marker::Braille,

  );

  ```

- `fn marker(&mut self, marker: Marker)`

  Change the marker being used in this context.

  

  This will save the last layer if necessary and reset the grid to use the new marker.

- `fn draw<S>(&mut self, shape: &S)`

  Draw the given [`Shape`](#shape) in this context

- `fn layer(&mut self)`

  Save the existing state of the grid as a layer.

  

  Save the existing state as a layer to be rendered and reset the grid to its initial

  state for the next layer.

  

  This allows the canvas to be drawn in multiple layers. This is useful if you want to

  draw multiple shapes on the [`Canvas`](#canvas) in specific order.

- `fn print<T>(&mut self, x: f64, y: f64, line: T)`

  Print a `Text` on the [`Canvas`](#canvas) at the given position.

  

  Note that the text is always printed on top of the canvas and is **not** affected by the

  layers.

#### Trait Implementations

##### `impl Debug for Context<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl IntoEither for Context<'a>`

### `Canvas<'a, F>`

```rust
struct Canvas<'a, F>
where
    F: Fn(&mut Context<'_>) {
    // [REDACTED: Private Fields]
}
```

The Canvas widget provides a means to draw shapes (Lines, Rectangles, Circles, etc.) on a grid.

By default the grid is made of Braille patterns but you may change the marker to use a different
set of symbols. If your terminal or font does not support this unicode block, you will see
unicode replacement characters (�) instead of braille dots. The Braille patterns (as well the
octant character patterns) provide a more fine grained result with a 2x4 resolution per
character, but you might want to use a simple dot, block, or bar instead by calling the
`marker` method if your target environment does not support those symbols.

See [Unicode Braille Patterns](https://en.wikipedia.org/wiki/Braille_Patterns) for more info.

The `Octant` marker is similar to the `Braille` marker but, instead of sparse dots, displays
densely packed and regularly spaced pseudo-pixels, without visible bands between rows and
columns. However, it uses characters that are not yet as widely supported as the Braille
unicode block.

The `Quadrant` and `Sextant` markers are in turn akin to the `Octant` marker, but with a 2x2
and 2x3 resolution, respectively.

The `HalfBlock` marker is useful when you want to draw shapes with a higher resolution than a
`CharGrid` but lower than a `PatternGrid`. This grid type supports a foreground and background
color for each terminal cell. This allows for more flexibility than the `PatternGrid` which
only supports a single foreground color for each 2x4 dots cell.

The Canvas widget is used by calling the `Canvas::paint` method and passing a closure that
will be used to draw on the canvas. The closure will be passed a [`Context`](#context) object that can be
used to draw shapes on the canvas.

The [`Context`](#context) object provides a `Context::draw` method that can be used to draw shapes on
the canvas. The `Context::layer` method can be used to save the current state of the canvas
and start a new layer. This is useful if you want to draw multiple shapes on the canvas in
specific order. The [`Context`](#context) object also provides a `Context::print` method that can be
used to print text on the canvas. Note that the text is always printed on top of the canvas and
is not affected by the layers.

# Examples

```rust
use ratatui::style::Color;
use ratatui::widgets::Block;
use ratatui::widgets::canvas::{Canvas, Line, Map, MapResolution, Rectangle};

Canvas::default()
    .block(Block::bordered().title("Canvas"))
    .x_bounds([-180.0, 180.0])
    .y_bounds([-90.0, 90.0])
    .paint(|ctx| {
        ctx.draw(&Map {
            resolution: MapResolution::High,
            color: Color::White,
        });
        ctx.layer();
        ctx.draw(&Line {
            x1: 0.0,
            y1: 10.0,
            x2: 10.0,
            y2: 10.0,
            color: Color::White,
        });
        ctx.draw(&Rectangle {
            x: 10.0,
            y: 20.0,
            width: 10.0,
            height: 10.0,
            color: Color::Red,
        });
    });
```

#### Implementations

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](../block/index.md#block)

  Wraps the canvas with a custom [`Block`](../block/index.md) widget.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn x_bounds(self, bounds: [f64; 2]) -> Self`

  Define the viewport of the canvas.

  

  If you were to "zoom" to a certain part of the world you may want to choose different

  bounds.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn y_bounds(self, bounds: [f64; 2]) -> Self`

  Define the viewport of the canvas.

  

  If you were to "zoom" to a certain part of the world you may want to choose different

  bounds.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn paint(self, f: F) -> Self`

  Store the closure that will be used to draw to the [`Canvas`](#canvas)

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn background_color(self, color: Color) -> Self`

  Change the background [`Color`](../../ratatui_core/index.md) of the entire canvas

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn marker(self, marker: Marker) -> Self`

  Change the type of points used to draw the shapes.

  

  By default the `Braille` patterns are used as they provide a more fine grained result,

  but you might want to use the simple `Dot` or [`Block`](../block/index.md) instead if the targeted terminal

  does not support those symbols.

  

  The `HalfBlock` marker is useful when you want to draw shapes with a higher resolution

  than with a grid of characters (e.g. with [`Block`](../block/index.md) or `Dot`) but lower than with

  `Braille`. This grid type supports a foreground and background color for each terminal

  cell. This allows for more flexibility than the `PatternGrid` which only supports a single

  foreground color for each 2x4 dots cell.

  

  

  

  

  # Examples

  

  ```rust

  use ratatui::symbols;

  use ratatui::widgets::canvas::Canvas;

  

  Canvas::default()

      .marker(symbols::Marker::Braille)

      .paint(|ctx| {});

  

  Canvas::default()

      .marker(symbols::Marker::HalfBlock)

      .paint(|ctx| {});

  

  Canvas::default()

      .marker(symbols::Marker::Dot)

      .paint(|ctx| {});

  

  Canvas::default()

      .marker(symbols::Marker::Block)

      .paint(|ctx| {});

  ```

#### Trait Implementations

##### `impl<F> AsRef for crate::canvas::Canvas<'a, F>`

- `fn as_ref(&self) -> &crate::canvas::Canvas<'a, F>` — [`Canvas`](#canvas)

##### `impl<F> Clone for Canvas<'a, F>`

- `fn clone(&self) -> Canvas<'a, F>` — [`Canvas`](#canvas)

##### `impl<F> Debug for Canvas<'a, F>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl<F> Default for Canvas<'_, F>`

- `fn default() -> Self`

##### `impl IntoEither for Canvas<'a, F>`

##### `impl<F> PartialEq for Canvas<'a, F>`

- `fn eq(&self, other: &Canvas<'a, F>) -> bool` — [`Canvas`](#canvas)

##### `impl<F> StructuralPartialEq for Canvas<'a, F>`

##### `impl<F> Widget for Canvas<'_, F>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

## Enums

### `MapResolution`

```rust
enum MapResolution {
    Low,
    High,
}
```

Defines how many points are going to be used to draw a [`Map`](../index.md).

You generally want a [high](MapResolution::High) resolution map.

#### Variants

- **`Low`**

  A lesser resolution for the [`Map`](../index.md) [`Shape`](#shape).
  
  Contains about 1000 points.

- **`High`**

  A higher resolution for the [`Map`](../index.md) [`Shape`](#shape).
  
  Contains about 5000 points, you likely want to use `Marker::Braille` with this.
  

#### Trait Implementations

##### `impl Clone for MapResolution`

- `fn clone(&self) -> MapResolution` — [`MapResolution`](../index.md#mapresolution)

##### `impl Copy for MapResolution`

##### `impl Debug for MapResolution`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for MapResolution`

- `fn default() -> MapResolution` — [`MapResolution`](../index.md#mapresolution)

##### `impl Display for MapResolution`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for MapResolution`

##### `impl<K> Equivalent for MapResolution`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for MapResolution`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<MapResolution, <Self as ::core::str::FromStr>::Err>` — [`MapResolution`](../index.md#mapresolution)

##### `impl Hash for MapResolution`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for MapResolution`

##### `impl PartialEq for MapResolution`

- `fn eq(&self, other: &MapResolution) -> bool` — [`MapResolution`](../index.md#mapresolution)

##### `impl StructuralPartialEq for MapResolution`

##### `impl ToCompactString for MapResolution`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for MapResolution`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for MapResolution`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for MapResolution`

- `fn to_string(&self) -> String`

##### `impl ToText for MapResolution`

- `fn to_text(&self) -> Text<'_>`

## Traits

### `Shape`

```rust
trait Shape { ... }
```

Something that can be drawn on a [`Canvas`](#canvas).

You may implement your own canvas custom widgets by implementing this trait.

#### Required Methods

- `fn draw(&self, painter: &mut Painter<'_, '_>)`

  Draws this [`Shape`](#shape) using the given [`Painter`](#painter).

#### Implementors

- [`Circle`](../index.md#circle)
- [`FilledLine`](../index.md#filledline)
- [`Line`](../index.md#line)
- [`Map`](../index.md#map)
- [`Points`](../index.md#points)
- [`Rectangle`](../index.md#rectangle)

