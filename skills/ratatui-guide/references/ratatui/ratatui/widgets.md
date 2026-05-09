*[ratatui](./index.md) / [widgets](#)*

---

# Module `widgets`

Widgets are the building blocks of user interfaces in Ratatui.

They are used to create and manage the layout and style of the terminal interface. Widgets can
be combined and nested to create complex UIs, and can be easily customized to suit the needs of
your application.

Ratatui provides a wide variety of built-in widgets that can be used to quickly create UIs.
Additionally, `String`, `&str`, [`Span`](../ratatui_core/index.md), [`Line`](../ratatui_core/index.md), and [`Text`](../ratatui_core/index.md) can be used as widgets
(though often [`Paragraph`](#paragraph) is used instead of these directly as it allows wrapping and
surrounding the text with a block).

# Crate Organization

Starting with Ratatui 0.30.0, the project was split into multiple crates for better modularity:

- **`ratatui-core`**: Contains the core widget traits ([`Widget`](./prelude.md), [`StatefulWidget`](./prelude.md)) and
  text-related types (`String`, `&str`, [`Span`](../ratatui_core/index.md), [`Line`](../ratatui_core/index.md), [`Text`](../ratatui_core/index.md))
- **`ratatui-widgets`**: Contains all the built-in widget implementations ([`Block`](#block),
  [`Paragraph`](#paragraph), [`List`](#list), etc.)
- **[`ratatui`](crate)**: The main crate that re-exports everything for convenience. The
  unstable [`WidgetRef`](./index.md) and [`StatefulWidgetRef`](./index.md) traits are defined in the main `ratatui`
  crate as they are experimental.

This split serves different user needs:

- **App Authors**: Most application developers should use the main [`ratatui`](crate) crate,
  which provides everything needed to build terminal applications with widgets, backends, and
  layout systems
- **Widget Library Authors**: When creating third-party widget libraries, consider depending
  only on `ratatui-core` to avoid pulling in unnecessary built-in widgets and reduce
  compilation time for your users
- **Minimalist Projects**: Use `ratatui-core` directly if you only need the fundamental traits
  and text types without any built-in widgets

The modular structure allows widget library authors to create lightweight dependencies while
still being compatible with the broader Ratatui ecosystem.

# Built-in Widgets

Ratatui provides a comprehensive set of built-in widgets:

- [`Block`](#block): a basic widget that draws a block with optional borders, titles and styles.
- [`BarChart`](#barchart): displays multiple datasets as bars with optional grouping.
- [`calendar::Monthly`](../ratatui_widgets/calendar.md): displays a single month.
- [`Canvas`](#canvas): draws arbitrary shapes using drawing characters.
- [`Chart`](#chart): displays multiple datasets as a lines or scatter graph.
- [`Clear`](#clear): clears the area it occupies. Useful to render over previously drawn widgets.
- [`Fill`](#fill): paints every cell in its area with a single repeated symbol and style.
- [`Gauge`](#gauge): displays progress percentage using block characters.
- [`LineGauge`](#linegauge): display progress as a line.
- [`List`](#list): displays a list of items and allows selection.
- [`Paragraph`](#paragraph): displays a paragraph of optionally styled and wrapped text.
- [`Scrollbar`](#scrollbar): displays a scrollbar.
- [`Sparkline`](#sparkline): display a single data set as a sparkline.
- [`Table`](#table): displays multiple rows and columns in a grid and allows selection.
- [`Tabs`](#tabs): displays a tab bar and allows selection.
- [`RatatuiLogo`](#ratatuilogo): displays the Ratatui logo.
- [`RatatuiMascot`](#ratatuimascot): displays the Ratatui mascot.

Additionally, primitive text types implement [`Widget`](./prelude.md):
- `String`: renders the owned string content
- `&str`: renders the string slice content
- [`Line`](../ratatui_core/index.md): renders a single line of styled text spans
- [`Span`](../ratatui_core/index.md): renders a styled text segment
- [`Text`](../ratatui_core/index.md): renders multiple lines of styled text

For more information on these widgets, you can view the widget showcase and examples.

# Third-Party Widgets

Beyond the built-in widgets, there's a rich ecosystem of third-party widgets available that
extend Ratatui's functionality. These community-contributed widgets provide specialized UI
components for various use cases.

To discover third-party widgets:

- **Search crates.io**: Look for crates with "tui" or "ratatui" in their names or descriptions
- **Awesome Ratatui**: Check the [Awesome Ratatui](https://github.com/ratatui-org/awesome-ratatui)
  repository for a curated list of widgets, libraries, and applications
- **Widget Showcase**: Browse the [third-party widgets showcase](https://ratatui.rs/showcase/third-party-widgets/)
  on the Ratatui website to see widgets in action

These third-party widgets cover a wide range of functionality including specialized input
components, data visualization widgets, layout helpers, and domain-specific UI elements.

# Widget Traits

In Ratatui, widgets are implemented as Rust traits, which allow for easy implementation and
extension. The main traits for widgets are:

- [`Widget`](./prelude.md): Basic trait for stateless widgets that are consumed when rendered
- [`StatefulWidget`](./prelude.md): Trait for widgets that maintain state between renders
- [`WidgetRef`](./index.md): Trait for rendering widgets by reference (unstable)
- [`StatefulWidgetRef`](./index.md): Trait for rendering stateful widgets by reference (unstable)

## `Widget`

The [`Widget`](./prelude.md) trait is the most basic trait for widgets in Ratatui. It provides the basic
functionality for rendering a widget onto a buffer. Widgets implementing this trait are consumed
when rendered.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect};
pub trait Widget {
    fn render(self, area: Rect, buf: &mut Buffer);
}
```

Prior to Ratatui 0.26.0, widgets were generally created for each frame as they were consumed
during rendering. This meant that they were not meant to be stored but used as *commands* to
draw common figures in the UI. Starting with 0.26.0, implementing widgets on references became
the preferred pattern for reusability.

## `StatefulWidget`

The [`StatefulWidget`](./prelude.md) trait is similar to the [`Widget`](./prelude.md) trait, but also includes state that
can be managed and updated during rendering. This is useful for widgets that need to remember
things between draw calls, such as scroll position or selection state.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect};
pub trait StatefulWidget {
    type State;
    fn render(self, area: Rect, buf: &mut Buffer, state: &mut Self::State);
}
```

For example, the built-in [`List`](#list) widget can highlight the currently selected item. This
requires maintaining an offset to ensure the selected item is visible within the viewport.
Without state, the widget could only provide basic scrolling behavior, but with access to the
previous offset, it can implement natural scrolling where the offset is preserved until the
selected item moves out of view.

## `WidgetRef` and `StatefulWidgetRef`

The [`WidgetRef`](./index.md) and [`StatefulWidgetRef`](./index.md) traits were introduced in Ratatui 0.26.0 to enable
rendering widgets by reference instead of consuming them. These traits address several important
use cases that the original `Widget` and `StatefulWidget` traits couldn't handle elegantly.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect};
#[cfg(feature = "unstable-widget-ref")]
pub trait WidgetRef {
    fn render_ref(&self, area: Rect, buf: &mut Buffer);
}

#[cfg(feature = "unstable-widget-ref")]
pub trait StatefulWidgetRef {
    type State;
    fn render_ref(&self, area: Rect, buf: &mut Buffer, state: &mut Self::State);
}
```

The reference-based traits solve several key problems:

- **Reusability**: Widgets can be rendered multiple times without being consumed
- **Collections**: Store heterogeneous widgets in collections like `Vec<Box<dyn WidgetRef>>`
- **Borrowing**: Render widgets when you only have a reference, not ownership
- **Efficiency**: Avoid unnecessary cloning or reconstruction for repeated renders

These traits are currently **experimental** and gated behind the `unstable-widget-ref` feature
flag. This means:

- The API may change in future releases
- Method names, signatures, or behavior might be adjusted based on community feedback
- You must explicitly enable the feature flag to use them: `features = ["unstable-widget-ref"]`
- They are not covered by semantic versioning guarantees until stabilized

The traits are being evaluated for potential breaking changes and improvements. See the
[tracking issue](https://github.com/ratatui/ratatui/issues/1287) for ongoing discussions and
design considerations.

# Rendering Widgets

Widgets are typically rendered using the [`Frame`](../ratatui_core/index.md) type, which provides methods for rendering
both consuming and reference-based widgets. These methods are usually called from the closure
passed to `Terminal::draw`.

## Rendering Consuming Widgets

Most widgets in Ratatui are rendered using `Frame::render_widget()`, which consumes the widget
when rendering. This is the standard approach for stateless widgets that don't need to persist
data between frames.

```rust
use ratatui::{backend::TestBackend, Terminal};
use ratatui::widgets::Paragraph;
let backend = TestBackend::new(10, 3);
let mut terminal = Terminal::new(backend).unwrap();
terminal.draw(|frame| {
    let widget = Paragraph::new("Hello, world!");
    frame.render_widget(widget, frame.area());
});
```

## Rendering Widget References

When you implement widgets on references (`Widget for &MyWidget`), you can render them directly
using the same `Frame::render_widget()` method. This approach enables widget reuse without
reconstruction and is the recommended pattern for new widgets.

```rust
use ratatui::{backend::TestBackend, Terminal};
use ratatui::widgets::{Block, Paragraph};
let backend = TestBackend::new(10, 3);
let mut terminal = Terminal::new(backend).unwrap();
// Create the widget outside the draw closure
let paragraph = Paragraph::new("Hello, world!").block(Block::bordered());

terminal.draw(|frame| {
    // Widget can be rendered by reference without being consumed
    frame.render_widget(&paragraph, frame.area());
});

// The widget can be used again in subsequent frames
terminal.draw(|frame| {
    frame.render_widget(&paragraph, frame.area());
});
```

## Rendering Stateful Widgets

Widgets that need to maintain state between frames use `Frame::render_stateful_widget()`. This
method takes both the widget and a mutable reference to its state, allowing the widget to read
and modify state during rendering (such as updating scroll positions or handling selections).

```rust
use ratatui::{backend::TestBackend, Terminal};
use ratatui::widgets::{List, ListItem, ListState};
let backend = TestBackend::new(10, 3);
let mut terminal = Terminal::new(backend).unwrap();
let mut list_state = ListState::default();
terminal.draw(|frame| {
    let items = vec![ListItem::new("Item 1"), ListItem::new("Item 2")];
    let list = List::new(items);
    frame.render_stateful_widget(list, frame.area(), &mut list_state);
});
```

## Single Root Widget Pattern

A common compositional pattern in Ratatui applications is to have a single root widget (often an
`App` struct) that represents your entire application state. This widget is passed to
`Frame::render_widget()`, and within its render method, it calls render on child widgets
directly. This pattern provides a clean separation between your application logic and rendering
code, and allows for easy composition of complex UIs from simpler components.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect, widgets::Widget};
use ratatui::widgets::{Block, Paragraph};
#[derive(Default)]
struct App {
    should_quit: bool,
}

impl Widget for &App {
    fn render(self, area: Rect, buf: &mut Buffer) {
        // Render header
        let header = Paragraph::new("My App").block(Block::bordered());
        header.render(Rect::new(area.x, area.y, area.width, 3), buf);

        // Render main content
        let content = Paragraph::new("Main content area");
        content.render(
            Rect::new(area.x, area.y + 3, area.width, area.height - 3),
            buf,
        );
    }
}
```

# Authoring Custom Widgets

When implementing custom widgets in Ratatui, you'll make fundamental decisions about how your
widget manages state and how it's used by applications. Understanding these choices will help
you create widgets that fit well into your application's architecture. Widget implementation
involves several key architectural decisions that work together to determine how your widget
behaves - these decisions are independent but complementary, allowing you to mix and match
approaches based on your specific needs.

**State Management**: The first choice is where state lives. Some widgets need to track
information between renders - things like scroll positions, selections, or counters. You can
either build this state into the widget itself (widget-owned state) or keep it separate and pass
it in during rendering (external state).

**Ownership Model**: The second choice is how the widget is consumed. Widgets can either be
consumed when rendered (taking ownership) or work by reference (borrowing). Reference-based
widgets can be stored and reused across multiple frames, while consuming widgets are created
fresh each time.

**`StatefulWidget` vs Mutable References**: When your widget needs state, you have two main
approaches. The [`StatefulWidget`](./prelude.md) trait represents the established pattern - it separates the
widget from its state, allowing the application to own and manage the state independently. This
is what you'll see in most existing Ratatui code and built-in widgets like [`List`](#list) and
[`Table`](#table). The mutable reference approach (`Widget for &mut MyWidget`) is newer and less common,
but useful when the state is intrinsic to the widget's identity. With mutable references, the
widget owns its state directly.

The key question for state management is: "If I recreate this widget, should the state reset?"
If yes (like a counter that should start at zero), use mutable references with widget-owned
state. If no (like a list selection that should persist), use [`StatefulWidget`](./prelude.md) with external
state that the application manages.

**Evolution and Current Recommendations**: Ratatui's patterns have evolved significantly. Before
version 0.26.0, widgets were typically consuming (`Widget for MyWidget`) and created fresh each
frame. Starting with 0.26.0, reference-based widgets (`Widget for &MyWidget`) became possible,
allowing widgets to be stored and reused. You'll encounter both patterns in existing code, but
reference-based implementations are now recommended for new widgets because they enable
reusability and automatic [`WidgetRef`](./index.md) support through blanket implementations.

For new widgets, implement [`Widget`](./prelude.md) or [`StatefulWidget`](./prelude.md) on references to your widget types
(`&MyWidget` or `&mut MyWidget`). This provides reusability and automatic [`WidgetRef`](./index.md) support.
You can optionally implement the consuming version for backward compatibility.

## State Management Patterns

For a comprehensive exploration of different approaches to handling both mutable and immutable
state in widgets, see the [state examples] in the Ratatui repository. These examples demonstrate
various patterns including:

**Immutable State Patterns** (recommended for most use cases):
- Function-based immutable state (`fn render(frame: &mut Frame, area: Rect, state: &State)`)
- Shared reference widgets (`impl Widget for &MyWidget`)
- Consuming widgets (`impl Widget for MyWidget`)

**Mutable State Patterns** (for widgets that modify state during rendering):
- Function-based mutable state (`fn render(frame: &mut Frame, area: Rect, state: &mut State)`)
- Mutable widget references (`impl Widget for &mut MyWidget`)
- `StatefulWidget` pattern (`impl StatefulWidget for MyWidget`)
- Custom component traits (`trait MyComponent { fn render(&mut self, frame: &mut Frame, area:
  Rect) }`)
- Interior mutability with `RefCell` (`struct MyWidget { state: Rc<RefCell<State>> }`)
- Lifetime-based mutable references (`struct MyWidget<'a> { state: &'a mut State }`)
- Nested widget hierarchies (compositions with owned or external state)

Each pattern has different trade-offs in terms of complexity, performance, and architectural
fit, making them suitable for different use cases and application designs. For most
applications, start with immutable patterns as they are simpler to reason about and less prone
to borrowing issues.

## Shared References (`&Widget`)

The recommended pattern for most new widgets implements [`Widget`](./prelude.md) on a shared reference,
allowing the widget to be rendered multiple times without being consumed. This approach is ideal
for immutable widgets that don't need to modify their internal state during rendering, and it's
the most common pattern you should use for new widgets.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect, text::Line, widgets::Widget};
struct MyWidget {
    content: String,
}

impl Widget for &MyWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        Line::raw(&self.content).render(area, buf);
    }
}
```

This automatically provides [`WidgetRef`](./index.md) support through blanket implementations and enables
widgets to be stored and reused across frames without reconstruction. For most use cases where
the widget doesn't need to change its internal state during rendering, this is the best choice.

## Mutable References (`&mut Widget`)

For widgets that need to modify their internal state during rendering, implement [`Widget`](./prelude.md) on a
mutable reference. This is a newer pattern that's less common but useful when the state is
intrinsic to the widget's identity and behavior. Use this pattern when the widget should own and
manage its state directly, rather than having external state passed in.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect, text::Line, widgets::Widget};
struct CounterWidget {
    count: u32, // This state belongs to the widget
    label: String,
}

impl Widget for &mut CounterWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        self.count += 1; // State changes as part of rendering behavior
        let text = format!("{label}: {count}", label = self.label, count = self.count);
        Line::raw(text).render(area, buf);
    }
}
```

This pattern works well when the widget owns its state and the state is part of the widget's
identity. It's ideal for counters, animations, cursors, progress indicators, or other
widget-specific behavior where the state should reset when you create a new widget instance.

## Consuming Widget Implementation

The consuming widget pattern was the original approach in Ratatui and remains very common in
existing codebases. You'll encounter this pattern frequently when reading examples and community
code. Widgets implementing this pattern take ownership when rendered, which means they're
consumed on each use. While not the recommended approach for new widgets, it's still useful to
understand this pattern for compatibility and when working with existing code.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect, style::Modifier, text::{Line, Span}, widgets::Widget};
struct GreetingWidget {
    name: String,
}

impl Widget for GreetingWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let hello = Span::raw("Hello, ");
        let name = Span::styled(self.name, Modifier::BOLD);
        let line = Line::from(vec![hello, name]);
        line.render(area, buf);
    }
}
```

This approach is simpler and works well for widgets created fresh each frame, but it means the
widget cannot be reused. Before reference-based widgets were introduced in version 0.26.0, this
was the standard pattern, and it's still valid for simple use cases or when following existing
code patterns.

The easiest way to implement this pattern when you have a reference-based widget is to implement
the consuming version on the owned type, which can then call the reference-based implementation:

```rust
use ratatui_core::{buffer::Buffer, layout::Rect, widgets::Widget};
struct GreetingWidget;
impl Widget for &GreetingWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {}
}
impl Widget for GreetingWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        // Call the reference-based implementation
        (&self).render(area, buf);
    }
}
``````

## `StatefulWidget` Implementation

When your widget needs to work with external state - data that exists independently of the
widget and should persist between widget instances - implement [`StatefulWidget`](./prelude.md). This is the
established pattern used by built-in widgets like [`List`](#list) and [`Table`](#table), where the widget
configuration is separate from application state like selections or scroll positions.

Like [`Widget`](./prelude.md), you can implement [`StatefulWidget`](./prelude.md) on references to allow reuse, though it's
more common to see this trait implemented on owned types which are consumed during rendering.

```rust
use ratatui_core::{buffer::Buffer, layout::Rect, text::Line, widgets::{StatefulWidget, Widget}};
struct ListView {
    items: Vec<String>,
}

#[derive(Default)]
struct ListState {
    selected: Option<usize>, // This is application state
    scroll_offset: usize,
}

impl StatefulWidget for ListView {
    type State = ListState;

    fn render(self, area: Rect, buf: &mut Buffer, state: &mut ListState) {
        // Render based on external state, possibly modify for scrolling
        let display_text = state
            .selected
            .and_then(|i| self.items.get(i))
            .map_or("None selected", |s| s.as_str());
        Line::raw(display_text).render(area, buf);
    }
}
```

This pattern is ideal for selections, scroll positions, form data, or any state that should
persist between renders or be shared across your application. The state exists independently of
the widget, so recreating the widget doesn't reset the state.

### Automatic `WidgetRef` Support

When you implement `Widget for &MyWidget`, you automatically get [`WidgetRef`](./index.md) support without
any additional code. Ratatui provides blanket implementations that automatically implement these
traits for any type that implements [`Widget`](./prelude.md) or [`StatefulWidget`](./prelude.md) on a reference. This means
that implementing `Widget for &MyWidget` gives you both the standard widget functionality and
the unstable [`WidgetRef`](./index.md) capabilities for free.

## Manual `WidgetRef` Implementation (Advanced)

Manual implementation of [`WidgetRef`](./index.md) or [`StatefulWidgetRef`](./index.md) is only necessary when you need
to store widgets as trait objects (`Box<dyn WidgetRef>`) or when you want a different API than
the reference-based [`Widget`](./prelude.md) implementation provides. In most cases, the automatic
implementation via blanket implementations is sufficient.

These traits enable several benefits:
- Widgets can be stored and rendered multiple times without reconstruction
- Collections of widgets with different types can be stored using `Box<dyn WidgetRef>`
- Avoids the consumption model while maintaining backward compatibility

Manual implementation is only needed when you want to use trait objects or need a different API
than the reference-based [`Widget`](./prelude.md) implementation:

```rust
#[cfg(feature = "unstable-widget-ref")] {
use ratatui_core::{buffer::Buffer, layout::Rect, style::Modifier, text::{Line, Span}};
use ratatui::widgets::{Widget, WidgetRef};
struct GreetingWidget {
    name: String,
}

// Manual WidgetRef implementation (usually not needed)
impl WidgetRef for GreetingWidget {
    fn render_ref(&self, area: Rect, buf: &mut Buffer) {
        let hello = Span::raw("Hello, ");
        let name = Span::styled(&self.name, Modifier::BOLD);
        let line = Line::from(vec![hello, name]);
        line.render(area, buf);
    }
}

// For backward compatibility
impl Widget for GreetingWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        self.render_ref(area, buf);
    }
}
}
```

This pattern allows the widget to be stored and rendered multiple times:

```rust
#[cfg(feature = "unstable-widget-ref")] {
use ratatui_core::{buffer::Buffer, layout::Rect};
use ratatui::widgets::WidgetRef;
struct GreetingWidget { name: String }
impl WidgetRef for GreetingWidget {
    fn render_ref(&self, area: Rect, buf: &mut Buffer) {}
}
struct App {
    greeting: GreetingWidget,
}

// The widget can be rendered multiple times without reconstruction
fn render_app(app: &App, area: Rect, buf: &mut Buffer) {
    app.greeting.render_ref(area, buf);
}
}
```

### Using Trait Objects for Dynamic Collections

The main benefit of manual [`WidgetRef`](./index.md) implementation is the ability to create collections of
different widget types using trait objects. This is useful when you need to store widgets with
types that are not known at compile time:

```rust
#[cfg(feature = "unstable-widget-ref")] {
use ratatui_core::{buffer::Buffer, layout::Rect};
use ratatui::widgets::WidgetRef;
struct Greeting;
struct Farewell;
impl WidgetRef for Greeting { fn render_ref(&self, area: Rect, buf: &mut Buffer) {} }
impl WidgetRef for Farewell { fn render_ref(&self, area: Rect, buf: &mut Buffer) {} }
let area = Rect::new(0, 0, 10, 3);
let mut buf = &mut Buffer::empty(area);
let widgets: Vec<Box<dyn WidgetRef>> = vec![Box::new(Greeting), Box::new(Farewell)];

for widget in &widgets {
    widget.render_ref(area, buf);
}
}
```

However, if you implement `Widget for &MyWidget`, you can achieve similar functionality by
storing references or using the automatic [`WidgetRef`](./index.md) implementation without needing to
manually implement the trait.

## Authoring Custom Widget Libraries

When creating a library of custom widgets for distribution, there are specific considerations
that will make your library more compatible and accessible to a wider range of users. Following
these guidelines will help ensure your widget library works well in various environments and
can be easily integrated into different types of applications.

### Depend on `ratatui_core`

For widget libraries, depend on `ratatui-core` instead of the full `ratatui` crate. This
provides all the essential types and traits needed for widget development while avoiding
unnecessary dependencies on backends and other components that widget libraries don't need.

This approach offers several key advantages for both library authors and users:

- **Lighter dependencies**: Users don't pull in backend code they don't need, keeping their
  dependency tree smaller and more focused
- **Better compile times**: Fewer dependencies mean faster builds for both development and
  end-user projects
- **Future-proofing**: Your library remains compatible as Ratatui evolves its architecture,
  since core widget functionality is stable across versions

### Make Your Crate `no_std` Compatible

For maximum compatibility, especially in embedded environments, consider making your widget
library `no_std` compatible. This is often easier than you might expect and broadens the range
of projects that can use your widgets.

For more detail on advantages of this, maintenance tips and feature flags, see the
[no-std concept guide].

To implement `no_std` compatibility, add the `#![no_std]` attribute at the top of your `lib.rs`.
When working in a `no_std` environment, you'll need to make a few adjustments:

- Use `core::` instead of `std::` for basic functionality
- Add `extern crate alloc;` to access allocation types
- Use `alloc::` for heap-allocated types like `String`, `Vec`, and `Box`

Here's a complete example of a `no_std` compatible widget:

```ignore
#![no_std]

extern crate alloc;

use alloc::string::String;

use ratatui_core::buffer::Buffer;
use ratatui_core::layout::Rect;
use ratatui_core::text::Line;
use ratatui_core::widgets::Widget;

struct MyWidget {
    content: String,
}

impl Widget for &MyWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        Line::raw(&self.content).render(area, buf);
    }
}
```

The benefits of `no_std` compatibility include:

- **Broader compatibility**: Your widgets work seamlessly in embedded environments and other
  `no_std` contexts where standard library functionality isn't available
- **Easy to adopt**: Even if you haven't worked with `no_std` development before, the changes
  are typically minimal for widget libraries. Most widget logic involves basic data manipulation
  and rendering operations that work well within `no_std` constraints, making this compatibility
  straightforward to implement

## Contents

- [Enums](#enums)
  - [`canvas`](#canvas)
- [Traits](#traits)
  - [`StatefulWidgetRef`](#statefulwidgetref)
  - [`WidgetRef`](#widgetref)
  - [`FrameExt`](#frameext)
- [Functions](#functions)
  - [`StatefulWidget`](#statefulwidget)
  - [`Widget`](#widget)
  - [`BarChart`](#barchart)
  - [`Dimmed`](#dimmed)
  - [`Shadow`](#shadow)
  - [`BorderType`](#bordertype)
  - [`Borders`](#borders)
  - [`calendar`](#calendar)
  - [`Axis`](#axis)
  - [`Chart`](#chart)
  - [`Dataset`](#dataset)
  - [`GraphType`](#graphtype)
  - [`Wrap`](#wrap)
  - [`ScrollDirection`](#scrolldirection)
  - [`ScrollbarState`](#scrollbarstate)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`canvas`](#canvas) | enum |  |
| [`StatefulWidgetRef`](#statefulwidgetref) | trait |  |
| [`WidgetRef`](#widgetref) | trait |  |
| [`FrameExt`](#frameext) | trait | Extension trait for [`Frame`] that provides methods to render [`WidgetRef`] and [`StatefulWidgetRef`] to the current buffer. |
| [`StatefulWidget`](#statefulwidget) | fn |  |
| [`Widget`](#widget) | fn |  |
| [`BarChart`](#barchart) | fn |  |
| [`Dimmed`](#dimmed) | fn |  |
| [`Shadow`](#shadow) | fn |  |
| [`BorderType`](#bordertype) | fn |  |
| [`Borders`](#borders) | fn |  |
| [`calendar`](#calendar) | fn |  |
| [`Axis`](#axis) | fn |  |
| [`Chart`](#chart) | fn |  |
| [`Dataset`](#dataset) | fn |  |
| [`GraphType`](#graphtype) | fn |  |
| [`Wrap`](#wrap) | fn |  |
| [`ScrollDirection`](#scrolldirection) | fn |  |
| [`ScrollbarState`](#scrollbarstate) | fn |  |

## Enums

### `canvas`

```rust
enum canvas {
    All,
    AfterCursor,
    BeforeCursor,
    CurrentLine,
    UntilNewLine,
}
```

*Re-exported from `ratatui_core`*

Defines which region of the terminal's visible display area is cleared.

Clearing operates on character cells in the active display surface. It does not move, hide, or
reset the cursor position. If the cursor lies inside the cleared region, the character cell at
the cursor position is cleared as well.

Clearing applies to the terminal's visible display area, not just content previously drawn by
Ratatui. No guarantees are made about scrollback, history, or off-screen buffers.

#### Variants

- **`All`**

  Clears all character cells in the visible display area.

- **`AfterCursor`**

  Clears all character cells from the cursor position (inclusive) through the end of the
  display area.

- **`BeforeCursor`**

  Clears all character cells from the start of the display area through the cursor position
  (inclusive).

- **`CurrentLine`**

  Clears all character cells in the cursor's current line.

- **`UntilNewLine`**

  Clears all character cells from the cursor position (inclusive) to the end of the current
  line.

#### Trait Implementations

##### `impl Clone for ClearType`

- `fn clone(&self) -> ClearType` — [`canvas`](#canvas)

##### `impl Copy for ClearType`

##### `impl Debug for ClearType`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result` — [`Bar`](#bar), [`Bar`](#bar)

##### `impl Display for ClearType`

- `fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>` — [`Bar`](#bar), [`Widget`](./prelude.md#widget), [`Scrollbar`](#scrollbar)

##### `impl Eq for ClearType`

##### `impl<K> Equivalent for ClearType`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl FromStr for ClearType`

- `type Err = ParseError`

- `fn from_str(s: &str) -> ::core::result::Result<ClearType, <Self as ::core::str::FromStr>::Err>` — [`Widget`](./prelude.md#widget), [`canvas`](#canvas), [`ScrollbarState`](#scrollbarstate)

##### `impl Hash for ClearType`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for ClearType`

##### `impl PartialEq for ClearType`

- `fn eq(&self, other: &ClearType) -> bool` — [`canvas`](#canvas)

##### `impl StructuralPartialEq for ClearType`

##### `impl ToCompactString for ClearType`

- `fn try_to_compact_string(&self) -> Result<CompactString, ToCompactStringError>` — [`Widget`](./prelude.md#widget)

##### `impl ToLine for ClearType`

- `fn to_line(&self) -> Line<'_>` — [`FromCrossterm`](./backend.md#fromcrossterm)

##### `impl ToSpan for ClearType`

- `fn to_span(&self) -> Span<'_>` — [`VerticalAlignment`](./prelude.md#verticalalignment)

##### `impl ToString for ClearType`

- `fn to_string(&self) -> String`

##### `impl ToText for ClearType`

- `fn to_text(&self) -> Text<'_>` — [`Color`](./prelude.md#color)

## Traits

### `StatefulWidgetRef`

```rust
trait StatefulWidgetRef { ... }
```

 A `StatefulWidgetRef` is a trait that allows rendering a stateful widget by reference.

 This is the stateful equivalent of `WidgetRef`. It is useful when you need to store a reference
 to a stateful widget and render it later. It also allows you to render boxed stateful widgets.

 This trait was introduced in Ratatui 0.26.0. It is currently marked as unstable as we are still
 evaluating the API and may make changes in the future. See
 <https://github.com/ratatui/ratatui/issues/1287> for more information.

 A blanket implementation of `StatefulWidgetRef` for `&W` where `W` implements `StatefulWidget`
 is provided. Most of the time you will want to implement `StatefulWidget` against a reference to
 the widget instead of implementing `StatefulWidgetRef` directly.

 See the documentation for [`WidgetRef`](./index.md) for more information on boxed widgets. See the
 documentation for [`StatefulWidget`](./prelude.md) for more information on stateful widgets.

 For comprehensive information about widget implementation patterns, rendering, and usage,
 see the [`widgets`](#widgets) module documentation.

 # Examples

 ```rust
 #[cfg(feature = "unstable-widget-ref")] {
 use ratatui::widgets::StatefulWidgetRef;
 use ratatui_core::buffer::Buffer;
 use ratatui_core::layout::Rect;
 use ratatui_core::style::Stylize;
 use ratatui_core::text::Line;
 use ratatui_core::widgets::{StatefulWidget, Widget};

 struct PersonalGreeting;

 impl StatefulWidgetRef for PersonalGreeting {
     type State = String;
     fn render_ref(&self, area: Rect, buf: &mut Buffer, state: &mut Self::State) {
         Line::raw(format!("Hello {}", state)).render(area, buf);
     }
 }

 impl StatefulWidget for PersonalGreeting {
     type State = String;
     fn render(self, area: Rect, buf: &mut Buffer, state: &mut Self::State) {
         (&self).render_ref(area, buf, state);
     }
 }

 fn render(area: Rect, buf: &mut Buffer) {
     let widget = PersonalGreeting;
     let mut state = "world".to_string();
     widget.render(area, buf, &mut state);
 }
 }
 ```
# Stability

**This API is marked as unstable** and is only available when the `unstable-widget-ref`
crate feature is enabled. This comes with no stability guarantees, and could be changed
or removed at any time.

#### Associated Types

- `type State: 1`

#### Required Methods

- `fn render_ref(&self, area: Rect, buf: &mut Buffer, state: &mut <Self as >::State)`

  Draws the current state of the widget in the given buffer. That is the only method required

#### Implementors

- `&W`

### `WidgetRef`

```rust
trait WidgetRef { ... }
```

 A `WidgetRef` is a trait that allows rendering a widget by reference.

 This trait is useful when you want to store a reference to a widget and render it later. It also
 allows you to render boxed widgets.

 Boxed widgets allow you to store widgets with a type that is not known at compile time. This is
 useful when you want to store a collection of widgets with different types. You can then iterate
 over the collection and render each widget.

 This trait was introduced in Ratatui 0.26.0 and is implemented for all the internal widgets. It
 is currently marked as unstable as we are still evaluating the API and may make changes in the
 future. See <https://github.com/ratatui/ratatui/issues/1287> for more information.

 A blanket implementation of `Widget` for `&W` where `W` implements `WidgetRef` is provided.

 A blanket implementation of `WidgetRef` for `Option<W>` where `W` implements `WidgetRef` is
 provided. This is a convenience approach to make it easier to attach child widgets to parent
 widgets. It allows you to render an optional widget by reference.

 For comprehensive information about widget implementation patterns, rendering, and usage,
 see the [`widgets`](#widgets) module documentation.

 # Examples

 ```rust
 #[cfg(feature = "unstable-widget-ref")] {
 use ratatui::widgets::WidgetRef;
 use ratatui_core::buffer::Buffer;
 use ratatui_core::layout::Rect;
 use ratatui_core::text::Line;
 use ratatui_core::widgets::Widget;

 struct Greeting;

 struct Farewell;

 impl WidgetRef for Greeting {
     fn render_ref(&self, area: Rect, buf: &mut Buffer) {
         Line::raw("Hello").render(area, buf);
     }
 }

 /// Only needed for backwards compatibility
 impl Widget for Greeting {
     fn render(self, area: Rect, buf: &mut Buffer) {
         self.render_ref(area, buf);
     }
 }

 impl WidgetRef for Farewell {
     fn render_ref(&self, area: Rect, buf: &mut Buffer) {
         Line::raw("Goodbye").right_aligned().render(area, buf);
     }
 }

 /// Only needed for backwards compatibility
 impl Widget for Farewell {
     fn render(self, area: Rect, buf: &mut Buffer) {
         self.render_ref(area, buf);
     }
 }

 fn render(area: Rect, buf: &mut Buffer) {
 let greeting = Greeting;
 let farewell = Farewell;

 // these calls do not consume the widgets, so they can be used again later
 greeting.render_ref(area, buf);
 farewell.render_ref(area, buf);

 // a collection of widgets with different types
 let widgets: Vec<Box<dyn WidgetRef>> = vec![Box::new(greeting), Box::new(farewell)];
 for widget in widgets {
     widget.render_ref(area, buf);
 }
 }
 }
 ```
# Stability

**This API is marked as unstable** and is only available when the `unstable-widget-ref`
crate feature is enabled. This comes with no stability guarantees, and could be changed
or removed at any time.

#### Required Methods

- `fn render_ref(&self, area: Rect, buf: &mut Buffer)`

  Draws the current state of the widget in the given buffer. That is the only method required

#### Implementors

- `&W`
- `&str`
- `Option<W>`
- `alloc::string::String`

### `FrameExt`

```rust
trait FrameExt { ... }
```

 Extension trait for [`Frame`](../ratatui_core/index.md) that provides methods to render [`WidgetRef`](./index.md) and
 [`StatefulWidgetRef`](./index.md) to the current buffer.
# Stability

**This API is marked as unstable** and is only available when the `unstable-widget-ref`
crate feature is enabled. This comes with no stability guarantees, and could be changed
or removed at any time.

#### Required Methods

- `fn render_widget_ref<W: WidgetRef>(&mut self, widget: W, area: Rect)`

  Render a [`WidgetRef`](./index.md) to the current buffer using `WidgetRef::render_ref`.

- `fn render_stateful_widget_ref<W>(&mut self, widget: W, area: Rect, state: &mut <W as >::State)`

  Render a [`StatefulWidgetRef`](./index.md) to the current buffer using

#### Implementors

- [`Frame`](./prelude.md#frame)

## Functions

### `StatefulWidget`

```rust
fn StatefulWidget(&mut self, command: impl Command) -> Result<&mut T, Error>
```

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

### `Widget`

```rust
fn Widget(&mut self, clear_type: ClearType) -> io::Result<()>
```

### `BarChart`

```rust
fn BarChart<'a, I>(&mut self, content: I) -> io::Result<()>
where
    I: Iterator<Item = (u16, u16, &'a Cell)>
```

### `Dimmed`

```rust
fn Dimmed<__H: hash::Hasher>(&self, state: &mut __H)
```

### `Shadow`

```rust
fn Shadow(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result
```

Formats the `TestBackend` for display by calling the `buffer_view` function
on its internal buffer.

### `BorderType`

```rust
fn BorderType(&mut self) -> core::result::Result<(), core::convert::Infallible>
```

### `Borders`

```rust
fn Borders(&mut self) -> core::result::Result<Position, core::convert::Infallible>
```

### `calendar`

```rust
fn calendar(&mut self) -> core::result::Result<(), core::convert::Infallible>
```

### `Axis`

```rust
fn Axis(&self) -> core::result::Result<Size, core::convert::Infallible>
```

### `Chart`

```rust
fn Chart(&mut self) -> core::result::Result<WindowSize, core::convert::Infallible>
```

### `Dataset`

```rust
fn Dataset(&mut self) -> core::result::Result<(), core::convert::Infallible>
```

### `GraphType`

```rust
fn GraphType(value: CrosstermAttribute) -> Self
```

### `Wrap`

```rust
fn Wrap(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result
```

### `ScrollDirection`

```rust
fn ScrollDirection(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::result::Result<(), ::core::fmt::Error>
```

### `ScrollbarState`

```rust
fn ScrollbarState(bars: impl Into<Vec<Bar<'a>>>) -> Self
```

Creates a new `BarChart` widget with a vertical direction.

This function is equivalent to `BarChart::new()`.

