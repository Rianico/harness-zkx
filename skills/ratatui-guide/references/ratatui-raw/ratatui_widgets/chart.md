*[ratatui_widgets](./index.md) / [chart](#)*

---

# Module `chart`

The [`Chart`](#chart) widget is used to plot one or more [`Dataset`](#dataset) in a cartesian coordinate system.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Axis`](#axis) | struct | An X or Y axis for the [`Chart`] widget |
| [`Dataset`](#dataset) | struct | A group of data points |
| [`Chart`](#chart) | struct | A widget to plot one or more [`Dataset`] in a cartesian coordinate system |
| [`GraphType`](#graphtype) | enum | Used to determine which style of graphing to use |
| [`LegendPosition`](#legendposition) | enum | Allow users to specify the position of a legend in a [`Chart`] |

## Structs

### `Axis<'a>`

```rust
struct Axis<'a> {
    // [REDACTED: Private Fields]
}
```

An X or Y axis for the [`Chart`](#chart) widget

An axis can have a [title](Axis::title) which will be displayed at the end of the axis. For an
X axis this is the right, for a Y axis, this is the top.

You can also set the bounds and labels on this axis using respectively `Axis::bounds` and
`Axis::labels`.

See `Chart::x_axis` and `Chart::y_axis` to set an axis on a chart.

# Example

```rust
use ratatui::style::{Style, Stylize};
use ratatui::widgets::Axis;

let axis = Axis::default()
    .title("X Axis")
    .style(Style::default().gray())
    .bounds([0.0, 50.0])
    .labels(["0".bold(), "25".into(), "50".bold()]);
```

#### Implementations

- `fn title<T>(self, title: T) -> Self`

  Sets the axis title

  

  It will be displayed at the end of the axis. For an X axis this is the right, for a Y axis,

  this is the top.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn bounds(self, bounds: [f64; 2]) -> Self`

  Sets the bounds of this axis

  

  In other words, sets the min and max value on this axis.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn labels<Labels>(self, labels: Labels) -> Self`

  Sets the axis labels

  

  - For the X axis, the labels are displayed left to right.

  - For the Y axis, the labels are displayed bottom to top.

  

  Currently, you need to give at least two labels or the render will panic. Also, giving

  more than 3 labels is currently broken and the middle labels won't be in the correct

  position, see [issue 334].

  

  `labels` is a vector of any type that can be converted into a [`Line`](../ratatui_core/index.md) (e.g. `&str`,

  `String`, `&Line`, `Span`, ...). This allows you to style the labels using the methods

  provided by [`Line`](../ratatui_core/index.md). Any alignment set on the labels will be ignored as the alignment is

  determined by the axis.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::Axis;

  

  let axis = Axis::default()

      .bounds([0.0, 50.0])

      .labels(["0".bold(), "25".into(), "50".bold()]);

  ```

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the axis style

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

  

  # Example

  

  [`Axis`](#axis) also implements [`Stylize`](ratatui_core::style::Stylize) which mean you can style

  it like so

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::Axis;

  

  let axis = Axis::default().red();

  ```

- `const fn labels_alignment(self, alignment: Alignment) -> Self`

  Sets the labels alignment of the axis

  

  The alignment behaves differently based on the axis:

  - Y axis: The labels are aligned within the area on the left of the axis

  - X axis: The first X-axis label is aligned relative to the Y-axis

  

  On the X axis, this parameter only affects the first label.

#### Trait Implementations

##### `impl Clone for Axis<'a>`

- `fn clone(&self) -> Axis<'a>` — [`Axis`](#axis)

##### `impl Debug for Axis<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Axis<'a>`

- `fn default() -> Axis<'a>` — [`Axis`](#axis)

##### `impl IntoEither for Axis<'a>`

##### `impl PartialEq for Axis<'a>`

- `fn eq(&self, other: &Axis<'a>) -> bool` — [`Axis`](#axis)

##### `impl StructuralPartialEq for Axis<'a>`

##### `impl Styled for Axis<'_>`

- `type Item = Axis<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Axis<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

### `Dataset<'a>`

```rust
struct Dataset<'a> {
    // [REDACTED: Private Fields]
}
```

A group of data points

This is the main element composing a [`Chart`](#chart).

A dataset can be [named](Dataset::name). Only named datasets will be rendered in the legend.

After that, you can pass it data with `Dataset::data`. Data is an array of `f64` tuples
(`(f64, f64)`), the first element being X and the second Y. It's also worth noting that, unlike
the [`Rect`](../ratatui_core/index.md), here the Y axis is bottom to top, as in math.

You can also customize the rendering by using `Dataset::marker` and `Dataset::graph_type`.

# Example

This example draws a red line between two points.

```rust
use ratatui::style::Stylize;
use ratatui::symbols::Marker;
use ratatui::widgets::{Dataset, GraphType};

let dataset = Dataset::default()
    .name("dataset 1")
    .data(&[(1., 1.), (5., 5.)])
    .marker(Marker::Braille)
    .graph_type(GraphType::Line)
    .red();
```

#### Implementations

- `fn name<S>(self, name: S) -> Self`

  Sets the name of the dataset

  

  The dataset's name is used when displaying the chart legend. Datasets don't require a name

  and can be created without specifying one. Once assigned, a name can't be removed, only

  changed

  

  The name can be styled (see [`Line`](../ratatui_core/index.md) for that), but the dataset's style will always have

  precedence.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn data(self, data: &'a [(f64, f64)]) -> Self`

  Sets the data points of this dataset

  

  Points will then either be rendered as scattered points or with lines between them

  depending on `Dataset::graph_type`.

  

  Data consist in an array of `f64` tuples (`(f64, f64)`), the first element being X and the

  second Y. It's also worth noting that, unlike the [`Rect`](../ratatui_core/index.md), here the Y axis is bottom to

  top, as in math.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn marker(self, marker: symbols::Marker) -> Self`

  Sets the kind of character to use to display this dataset

  

  You can use dots (`•`), blocks (`█`), bars (`▄`), braille (`⠓`, `⣇`, `⣿`), half-blocks

  (`█`, `▄`, and `▀`) or if you need custom chars use

  [`Marker::Custom`](symbols::Marker::Custom). See [`symbols::Marker`](../ratatui_core/symbols/marker.md) for more details.

  

  Note [`Marker::Braille`](symbols::Marker::Braille) requires a font that supports Unicode

  Braille Patterns.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `const fn graph_type(self, graph_type: GraphType) -> Self` — [`GraphType`](#graphtype)

  Sets how the dataset should be drawn

  

  [`Chart`](#chart) can draw [scatter](GraphType::Scatter), [line](GraphType::Line) or

  [bar](GraphType::Bar) charts. A scatter chart draws only the points in the dataset, a line

  char draws a line between each point, and a bar chart draws a line from the x axis to the

  point.  See [`GraphType`](#graphtype) for more details

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of this dataset

  

  The given style will be used to draw the legend and the data points. Currently the legend

  will use the entire style whereas the data points will only use the foreground.

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  

  [`Dataset`](#dataset) also implements [`Stylize`](ratatui_core::style::Stylize) which mean you can

  style it like so

  

  ```rust

  use ratatui::style::Stylize;

  use ratatui::widgets::Dataset;

  

  let dataset = Dataset::default().red();

  ```

- `const fn fill_to_y(self, fill_to_y: f64) -> Self`

  Sets the y-coordinate to fill the area to when using [`GraphType::Area`](./index.md)

  

  When the graph type is set to [`GraphType::Area`](./index.md), the area between the data points and the

  specified y-coordinate will be filled with the dataset's style. The default is `0.0`.

  

  This is a fluent setter method which must be chained or used as it consumes self

#### Trait Implementations

##### `impl Clone for Dataset<'a>`

- `fn clone(&self) -> Dataset<'a>` — [`Dataset`](#dataset)

##### `impl Debug for Dataset<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Dataset<'a>`

- `fn default() -> Dataset<'a>` — [`Dataset`](#dataset)

##### `impl IntoEither for Dataset<'a>`

##### `impl PartialEq for Dataset<'a>`

- `fn eq(&self, other: &Dataset<'a>) -> bool` — [`Dataset`](#dataset)

##### `impl StructuralPartialEq for Dataset<'a>`

##### `impl Styled for Dataset<'_>`

- `type Item = Dataset<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Dataset<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

### `Chart<'a>`

```rust
struct Chart<'a> {
    // [REDACTED: Private Fields]
}
```

A widget to plot one or more [`Dataset`](#dataset) in a cartesian coordinate system

To use this widget, start by creating one or more [`Dataset`](#dataset). With it, you can set the
[data points](Dataset::data), the [name](Dataset::name) or the
[chart type](Dataset::graph_type). See [`Dataset`](#dataset) for a complete documentation of what is
possible.

Then, you'll usually want to configure the [`Axis`](#axis). Axis [titles](Axis::title),
[bounds](Axis::bounds) and [labels](Axis::labels) can be configured on both axis. See [`Axis`](#axis)
for a complete documentation of what is possible.

Finally, you can pass all of that to the `Chart` via `Chart::new`, `Chart::x_axis` and
`Chart::y_axis`.

Additionally, `Chart` allows configuring the legend [position](Chart::legend_position) and
[hiding constraints](Chart::hidden_legend_constraints).

# Examples

```rust
use ratatui::style::{Style, Stylize};
use ratatui::symbols;
use ratatui::widgets::{Axis, Block, Chart, Dataset, GraphType};

// Create the datasets to fill the chart with
let datasets = vec![
    // Scatter chart
    Dataset::default()
        .name("data1")
        .marker(symbols::Marker::Dot)
        .graph_type(GraphType::Scatter)
        .style(Style::default().cyan())
        .data(&[(0.0, 5.0), (1.0, 6.0), (1.5, 6.434)]),
    // Line chart
    Dataset::default()
        .name("data2")
        .marker(symbols::Marker::Braille)
        .graph_type(GraphType::Line)
        .style(Style::default().magenta())
        .data(&[(4.0, 5.0), (5.0, 8.0), (7.66, 13.5)]),
];

// Create the X axis and define its properties
let x_axis = Axis::default()
    .title("X Axis".red())
    .style(Style::default().white())
    .bounds([0.0, 10.0])
    .labels(["0.0", "5.0", "10.0"]);

// Create the Y axis and define its properties
let y_axis = Axis::default()
    .title("Y Axis".red())
    .style(Style::default().white())
    .bounds([0.0, 10.0])
    .labels(["0.0", "5.0", "10.0"]);

// Create the chart and link all the parts together
let chart = Chart::new(datasets)
    .block(Block::new().title("Chart"))
    .x_axis(x_axis)
    .y_axis(y_axis);
```

#### Implementations

- `fn new(datasets: Vec<Dataset<'a>>) -> Self` — [`Dataset`](#dataset)

  Creates a chart with the given [datasets](Dataset)

  

  A chart can render multiple datasets.

  

  # Example

  

  This creates a simple chart with one [`Dataset`](#dataset)

  

  ```rust

  use ratatui::widgets::{Chart, Dataset};

  

  let data_points = vec![];

  let chart = Chart::new(vec![Dataset::default().data(&data_points)]);

  ```

  

  This creates a chart with multiple [`Dataset`](#dataset)s

  

  ```rust

  use ratatui::widgets::{Chart, Dataset};

  

  let data_points = vec![];

  let data_points2 = vec![];

  let chart = Chart::new(vec![

      Dataset::default().data(&data_points),

      Dataset::default().data(&data_points2),

  ]);

  ```

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](./block.md#block)

  Wraps the chart with the given [`Block`](./block.md)

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn style<S: Into<Style>>(self, style: S) -> Self`

  Sets the style of the entire chart

  

  `style` accepts any type that is convertible to [`Style`](../ratatui_core/style.md) (e.g. [`Style`](../ratatui_core/style.md), [`Color`](../ratatui_core/index.md), or

  your own type that implements `Into<Style>`).

  

  Styles of [`Axis`](#axis) and [`Dataset`](#dataset) will have priority over this style.

  

  This is a fluent setter method which must be chained or used as it consumes self

- `fn x_axis(self, axis: Axis<'a>) -> Self` — [`Axis`](#axis)

  Sets the X [`Axis`](#axis)

  

  The default is an empty [`Axis`](#axis), i.e. only a line.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  

  ```rust

  use ratatui::widgets::{Axis, Chart};

  

  let chart = Chart::new(vec![]).x_axis(

      Axis::default()

          .title("X Axis")

          .bounds([0.0, 20.0])

          .labels(["0", "20"]),

  );

  ```

- `fn y_axis(self, axis: Axis<'a>) -> Self` — [`Axis`](#axis)

  Sets the Y [`Axis`](#axis)

  

  The default is an empty [`Axis`](#axis), i.e. only a line.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Example

  

  ```rust

  use ratatui::widgets::{Axis, Chart};

  

  let chart = Chart::new(vec![]).y_axis(

      Axis::default()

          .title("Y Axis")

          .bounds([0.0, 20.0])

          .labels(["0", "20"]),

  );

  ```

- `const fn hidden_legend_constraints(self, constraints: (Constraint, Constraint)) -> Self`

  Sets the constraints used to determine whether the legend should be shown or not.

  

  The tuple's first constraint is used for the width and the second for the height. If the

  legend takes more space than what is allowed by any constraint, the legend is hidden.

  `Constraint::Min` is an exception and will always show the legend.

  

  If this is not set, the default behavior is to hide the legend if it is greater than 25% of

  the chart, either horizontally or vertically.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  Hide the legend when either its width is greater than 33% of the total widget width or if

  its height is greater than 25% of the total widget height.

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::Chart;

  

  let constraints = (Constraint::Ratio(1, 3), Constraint::Ratio(1, 4));

  let chart = Chart::new(vec![]).hidden_legend_constraints(constraints);

  ```

  

  Always show the legend, note the second constraint doesn't matter in this case since the

  first one is always true.

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::Chart;

  

  let constraints = (Constraint::Min(0), Constraint::Ratio(1, 4));

  let chart = Chart::new(vec![]).hidden_legend_constraints(constraints);

  ```

  

  Always hide the legend. Note this can be accomplished more explicitly by passing `None` to

  `Chart::legend_position`.

  

  ```rust

  use ratatui::layout::Constraint;

  use ratatui::widgets::Chart;

  

  let constraints = (Constraint::Length(0), Constraint::Ratio(1, 4));

  let chart = Chart::new(vec![]).hidden_legend_constraints(constraints);

  ```

- `const fn legend_position(self, position: Option<LegendPosition>) -> Self` — [`LegendPosition`](#legendposition)

  Sets the position of a legend or hide it

  

  The default is [`LegendPosition::TopRight`](./index.md).

  

  If `None` is given, hide the legend even if `hidden_legend_constraints` determines it

  should be shown. In contrast, if `Some(...)` is given, `hidden_legend_constraints` might

  still decide whether to show the legend or not.

  

  See [`LegendPosition`](#legendposition) for all available positions.

  

  This is a fluent setter method which must be chained or used as it consumes self

  

  # Examples

  

  Show the legend on the top left corner.

  

  ```rust

  use ratatui::widgets::{Chart, LegendPosition};

  

  let chart: Chart = Chart::new(vec![]).legend_position(Some(LegendPosition::TopLeft));

  ```

  

  Hide the legend altogether

  

  ```rust

  use ratatui::widgets::{Chart, LegendPosition};

  

  let chart = Chart::new(vec![]).legend_position(None);

  ```

#### Trait Implementations

##### `impl AsRef for crate::chart::Chart<'a>`

- `fn as_ref(&self) -> &crate::chart::Chart<'a>` — [`Chart`](#chart)

##### `impl Clone for Chart<'a>`

- `fn clone(&self) -> Chart<'a>` — [`Chart`](#chart)

##### `impl Debug for Chart<'a>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for Chart<'a>`

- `fn default() -> Chart<'a>` — [`Chart`](#chart)

##### `impl IntoEither for Chart<'a>`

##### `impl PartialEq for Chart<'a>`

- `fn eq(&self, other: &Chart<'a>) -> bool` — [`Chart`](#chart)

##### `impl StructuralPartialEq for Chart<'a>`

##### `impl Styled for Chart<'_>`

- `type Item = Chart<'_>`

- `fn style(&self) -> Style`

- `fn set_style<S: Into<Style>>(self, style: S) -> <Self as >::Item`

##### `impl<T> Stylize for Chart<'a>`

- `fn bg<C>(self, color: C) -> T`

- `fn fg<C>(self, color: C) -> T`

- `fn add_modifier(self, modifier: Modifier) -> T`

- `fn remove_modifier(self, modifier: Modifier) -> T`

- `fn reset(self) -> T`

##### `impl Widget for Chart<'_>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

## Enums

### `GraphType`

```rust
enum GraphType {
    Scatter,
    Line,
    Bar,
    Area,
}
```

Used to determine which style of graphing to use

#### Variants

- **`Scatter`**

  Draw each point. This is the default.

- **`Line`**

  Draw a line between each following point.
  
  The order of the lines will be the same as the order of the points in the dataset, which
  allows this widget to draw lines both left-to-right and right-to-left

- **`Bar`**

  Draw a bar chart. This will draw a bar for each point in the dataset.

- **`Area`**

  Draw a line chart with the area filled. Like [`Line`](GraphType::Line), this draws a line
  between each following point, but also fills the area between the line and the y-coordinate
  specified by `Dataset::fill_to_y`.

#### Trait Implementations

##### `impl Clone for GraphType`

- `fn clone(&self) -> GraphType` — [`GraphType`](#graphtype)

##### `impl Copy for GraphType`

##### `impl Debug for GraphType`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for GraphType`

- `fn default() -> GraphType` — [`GraphType`](#graphtype)

##### `impl Display for GraphType`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>`

##### `impl Eq for GraphType`

##### `impl<K> Equivalent for GraphType`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for GraphType`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<GraphType, <Self as ::core::str::FromStr>::Err>` — [`GraphType`](#graphtype)

##### `impl Hash for GraphType`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for GraphType`

##### `impl PartialEq for GraphType`

- `fn eq(&self, other: &GraphType) -> bool` — [`GraphType`](#graphtype)

##### `impl StructuralPartialEq for GraphType`

##### `impl ToCompactString for GraphType`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>`

##### `impl ToLine for GraphType`

- `fn to_line(&self) -> Line<'_>`

##### `impl ToSpan for GraphType`

- `fn to_span(&self) -> Span<'_>`

##### `impl ToString for GraphType`

- `fn to_string(&self) -> String`

##### `impl ToText for GraphType`

- `fn to_text(&self) -> Text<'_>`

### `LegendPosition`

```rust
enum LegendPosition {
    Top,
    TopRight,
    TopLeft,
    Left,
    Right,
    Bottom,
    BottomRight,
    BottomLeft,
}
```

Allow users to specify the position of a legend in a [`Chart`](#chart)

See `Chart::legend_position`

#### Variants

- **`Top`**

  Legend is centered on top

- **`TopRight`**

  Legend is in the top-right corner. This is the **default**.

- **`TopLeft`**

  Legend is in the top-left corner

- **`Left`**

  Legend is centered on the left

- **`Right`**

  Legend is centered on the right

- **`Bottom`**

  Legend is centered on the bottom

- **`BottomRight`**

  Legend is in the bottom-right corner

- **`BottomLeft`**

  Legend is in the bottom-left corner

#### Trait Implementations

##### `impl Clone for LegendPosition`

- `fn clone(&self) -> LegendPosition` — [`LegendPosition`](#legendposition)

##### `impl Copy for LegendPosition`

##### `impl Debug for LegendPosition`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for LegendPosition`

- `fn default() -> LegendPosition` — [`LegendPosition`](#legendposition)

##### `impl Eq for LegendPosition`

##### `impl<K> Equivalent for LegendPosition`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl IntoEither for LegendPosition`

##### `impl PartialEq for LegendPosition`

- `fn eq(&self, other: &LegendPosition) -> bool` — [`LegendPosition`](#legendposition)

##### `impl StructuralPartialEq for LegendPosition`

