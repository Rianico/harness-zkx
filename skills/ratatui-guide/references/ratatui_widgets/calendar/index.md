*[ratatui_widgets](../index.md) / [calendar](index.md)*

---

# Module `calendar`

A simple calendar widget. `(feature: widget-calendar)`

The [`Monthly`](#monthly) widget will display a calendar for the month provided in `display_date`. Days
are styled using the default style unless:
* `show_surrounding` is set, then days not in the `display_date` month will use that style.
* a style is returned by the [`DateStyler`](#datestyler) for the day

[`Monthly`](#monthly) has several controls for what should be displayed

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Monthly`](#monthly) | struct | Display a month calendar for the month containing `display_date` |
| [`CalendarEventStore`](#calendareventstore) | struct | A simple `DateStyler` based on a [`HashMap`] |
| [`DateStyler`](#datestyler) | trait | Provides a method for styling a given date. |

## Structs

### `Monthly<'a, DS: DateStyler>`

```rust
struct Monthly<'a, DS: DateStyler> {
    // [REDACTED: Private Fields]
}
```

Display a month calendar for the month containing `display_date`

#### Implementations

- `const fn new(display_date: Date, events: DS) -> Self`

  Construct a calendar for the `display_date` and highlight the `events`

- `fn show_surrounding<S: Into<Style>>(self, style: S) -> Self`

  Fill the calendar slots for days not in the current month also, this causes each line to be

  completely filled. If there is an event style for a date, this style will be patched with

  the event's style

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

- `fn show_weekdays_header<S: Into<Style>>(self, style: S) -> Self`

  Display a header containing weekday abbreviations

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

- `fn show_month_header<S: Into<Style>>(self, style: S) -> Self`

  Display a header containing the month and year

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

- `fn default_style<S: Into<Style>>(self, style: S) -> Self`

  How to render otherwise unstyled dates

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

- `fn block(self, block: Block<'a>) -> Self` — [`Block`](../block/index.md#block)

  Render the calendar within a [Block]

- `fn width(&self) -> u16`

  Return the width required to render the calendar.

- `fn height(&self) -> u16`

  Return the height required to render the calendar.

#### Trait Implementations

##### `impl<DS> AsRef for crate::calendar::Monthly<'a, DS>`

- `fn as_ref(&self) -> &crate::calendar::Monthly<'a, DS>` — [`Monthly`](#monthly)

##### `impl<DS: clone::Clone + DateStyler> Clone for Monthly<'a, DS>`

- `fn clone(&self) -> Monthly<'a, DS>` — [`Monthly`](#monthly)

##### `impl<DS: fmt::Debug + DateStyler> Debug for Monthly<'a, DS>`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl<DS: cmp::Eq + DateStyler> Eq for Monthly<'a, DS>`

##### `impl<K> Equivalent for Monthly<'a, DS>`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl<DS: hash::Hash + DateStyler> Hash for Monthly<'a, DS>`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for Monthly<'a, DS>`

##### `impl<DS: cmp::PartialEq + DateStyler> PartialEq for Monthly<'a, DS>`

- `fn eq(&self, other: &Monthly<'a, DS>) -> bool` — [`Monthly`](#monthly)

##### `impl<DS: DateStyler> StructuralPartialEq for Monthly<'a, DS>`

##### `impl<DS: DateStyler> Widget for Monthly<'_, DS>`

- `fn render(self, area: Rect, buf: &mut Buffer)`

### `CalendarEventStore`

```rust
struct CalendarEventStore(hashbrown::HashMap<time::Date, ratatui_core::style::Style>);
```

A simple `DateStyler` based on a `HashMap`

#### Implementations

- `fn today<S: Into<Style>>(style: S) -> Self`

  Construct a store that has the current date styled.

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

- `fn add<S: Into<Style>>(&mut self, date: Date, style: S)`

  Add a date and style to the store

  

  `style` accepts any type that is convertible to [`Style`](../../ratatui_core/style/index.md) (e.g. [`Style`](../../ratatui_core/style/index.md), [`Color`](#color), or

  your own type that implements `Into<Style>`).

#### Trait Implementations

##### `impl Clone for CalendarEventStore`

- `fn clone(&self) -> CalendarEventStore` — [`CalendarEventStore`](#calendareventstore)

##### `impl DateStyler for CalendarEventStore`

- `fn get_style(&self, date: Date) -> Style`

##### `impl Debug for CalendarEventStore`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for CalendarEventStore`

- `fn default() -> Self`

##### `impl Eq for CalendarEventStore`

##### `impl<K> Equivalent for CalendarEventStore`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl IntoEither for CalendarEventStore`

##### `impl PartialEq for CalendarEventStore`

- `fn eq(&self, other: &CalendarEventStore) -> bool` — [`CalendarEventStore`](#calendareventstore)

##### `impl StructuralPartialEq for CalendarEventStore`

## Traits

### `DateStyler`

```rust
trait DateStyler { ... }
```

Provides a method for styling a given date. [Monthly] is generic on this trait, so any type
that implements this trait can be used.

#### Required Methods

- `fn get_style(&self, date: Date) -> Style`

  Given a date, return a style for that date

#### Implementors

- [`CalendarEventStore`](#calendareventstore)
- `&CalendarEventStore`

