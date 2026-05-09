*[ratatui_core](./index.md) / [widgets](#)*

---

# Module `widgets`

The `widgets` module contains the `Widget` and `StatefulWidget` traits, which are used to
render UI elements on the screen.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`StatefulWidget`](#statefulwidget) | trait |  |
| [`Widget`](#widget) | trait |  |

## Traits

### `StatefulWidget`

```rust
trait StatefulWidget { ... }
```

A `StatefulWidget` is a widget that can take advantage of some local state to remember things
between two draw calls.

For a comprehensive guide to widgets, including trait explanations, implementation patterns,
and available widgets, see the [`widgets`](#widgets) module documentation.

Most widgets can be drawn directly based on the input parameters. However, some features may
require some kind of associated state to be implemented.

For example, the `List` widget can highlight the item currently selected. This can be translated
in an offset, which is the number of elements to skip in order to have the selected item within
the viewport currently allocated to this widget. The widget can therefore only provide the
following behavior: whenever the selected item is out of the viewport scroll to a predefined
position (making the selected item the last viewable item or the one in the middle for example).
Nonetheless, if the widget has access to the last computed offset then it can implement a
natural scrolling experience where the last offset is reused until the selected item is out of
the viewport.

## Examples

```rust,ignore
use std::io;

use ratatui::{
    backend::TestBackend,
    widgets::{List, ListItem, ListState, StatefulWidget, Widget},
    Terminal,
};

// Let's say we have some events to display.
struct Events {
    // `items` is the state managed by your application.
    items: Vec<String>,
    // `state` is the state that can be modified by the UI. It stores the index of the selected
    // item as well as the offset computed during the previous draw call (used to implement
    // natural scrolling).
    state: ListState,
}

impl Events {
    fn new(items: Vec<String>) -> Events {
        Events {
            items,
            state: ListState::default(),
        }
    }

    pub fn set_items(&mut self, items: Vec<String>) {
        self.items = items;
        // We reset the state as the associated items have changed. This effectively reset
        // the selection as well as the stored offset.
        self.state = ListState::default();
    }

    // Select the next item. This will not be reflected until the widget is drawn in the
    // `Terminal::draw` callback using `Frame::render_stateful_widget`.
    pub fn next(&mut self) {
        let i = match self.state.selected() {
            Some(i) => {
                if i >= self.items.len() - 1 {
                    0
                } else {
                    i + 1
                }
            }
            None => 0,
        };
        self.state.select(Some(i));
    }

    // Select the previous item. This will not be reflected until the widget is drawn in the
    // `Terminal::draw` callback using `Frame::render_stateful_widget`.
    pub fn previous(&mut self) {
        let i = match self.state.selected() {
            Some(i) => {
                if i == 0 {
                    self.items.len() - 1
                } else {
                    i - 1
                }
            }
            None => 0,
        };
        self.state.select(Some(i));
    }

    // Unselect the currently selected item if any. The implementation of `ListState` makes
    // sure that the stored offset is also reset.
    pub fn unselect(&mut self) {
        self.state.select(None);
    }
}

let backend = TestBackend::new(5, 5);
let mut terminal = Terminal::new(backend).unwrap();

let mut events = Events::new(vec![String::from("Item 1"), String::from("Item 2")]);

loop {
    terminal.draw(|f| {
        // The items managed by the application are transformed to something
        // that is understood by ratatui.
        let items: Vec<ListItem> = events
            .items
            .iter()
            .map(|i| ListItem::new(i.as_str()))
            .collect();
        // The `List` widget is then built with those items.
        let list = List::new(items);
        // Finally the widget is rendered using the associated state. `events.state` is
        // effectively the only thing that we will "remember" from this draw call.
        f.render_stateful_widget(list, f.size(), &mut events.state);
    });

    // In response to some input events or an external http request or whatever:
    events.next();
}
```

#### Associated Types

- `type State: 1`

#### Required Methods

- `fn render(self, area: Rect, buf: &mut Buffer, state: &mut <Self as >::State)`

  Draws the current state of the widget in the given buffer. That is the only method required

### `Widget`

```rust
trait Widget { ... }
```

A `Widget` is a type that can be drawn on a [`Buffer`](./index.md) in a given [`Rect`](./index.md).

For a comprehensive guide to widgets, including trait explanations, implementation patterns,
and available widgets, see the [`widgets`](#widgets) module documentation.

Prior to Ratatui 0.26.0, widgets generally were created for each frame as they were consumed
during rendering. This meant that they were not meant to be stored but used as *commands* to
draw common figures in the UI.

Starting with Ratatui 0.26.0, all the internal widgets implement Widget for a reference to
themselves. This allows you to store a reference to a widget and render it later. Widget crates
should consider also doing this to allow for more flexibility in how widgets are used.

In Ratatui 0.26.0, we also added an unstable `WidgetRef` trait and implemented this on all the
internal widgets. In addition to the above benefit of rendering references to widgets, this also
allows you to render boxed widgets. This is useful when you want to store a collection of
widgets with different types. You can then iterate over the collection and render each widget.
See <https://github.com/ratatui/ratatui/issues/1287> for more information.

In general where you expect a widget to immutably work on its data, we recommended to implement
`Widget` for a reference to the widget (`impl Widget for &MyWidget`). If you need to store state
between draw calls, implement `StatefulWidget` if you want the Widget to be immutable, or
implement `Widget` for a mutable reference to the widget (`impl Widget for &mut MyWidget`) if
you want the widget to be mutable. The mutable widget pattern is used infrequently in apps, but
can be quite useful.

A blanket implementation of `Widget` for `&W` where `W` implements `WidgetRef` is provided.
Widget is also implemented for `&str` and `String` types.

# Examples

```rust,ignore
use ratatui::{
    backend::TestBackend,
    widgets::{Clear, Widget},
    Terminal,
};
let backend = TestBackend::new(5, 5);
let mut terminal = Terminal::new(backend).unwrap();

terminal.draw(|frame| {
    frame.render_widget(Clear, frame.area());
});
```

It's common to render widgets inside other widgets:

```rust
use ratatui_core::buffer::Buffer;
use ratatui_core::layout::Rect;
use ratatui_core::text::Line;
use ratatui_core::widgets::Widget;

struct MyWidget;

impl Widget for MyWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        Line::raw("Hello").render(area, buf);
    }
}
```

#### Required Methods

- `fn render(self, area: Rect, buf: &mut Buffer)`

  Draws the current state of the widget in the given buffer. That is the only method required

#### Implementors

- [`Line`](./index.md#line)
- [`Span`](./index.md#span)
- [`Text`](./index.md#text)
- `&Line<'_>`
- `&Span<'_>`
- `&Text<'_>`
- `&str`
- `Option<W>`
- `alloc::string::String`

