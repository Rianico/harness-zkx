*[ratatui_core](../index.md) / [symbols](../index.md) / [merge](#)*

---

# Module `merge`

This module provides strategies for merging symbols in a layout.

It defines the [`MergeStrategy`](#mergestrategy) enum, which allows for different behaviors when combining
symbols, such as replacing the previous symbol, merging them if an exact match exists, or using
a fuzzy match to find the closest representation.

The merging strategies are useful for [collapsing borders] in layouts, where multiple symbols
may need to be combined to create a single, coherent border representation.

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`MergeStrategy`](#mergestrategy) | enum | A strategy for merging two symbols into one. |

## Enums

### `MergeStrategy`

```rust
enum MergeStrategy {
    Replace,
    Exact,
    Fuzzy,
}
```

A strategy for merging two symbols into one.

This enum defines how two symbols should be merged together, allowing for different behaviors
when combining symbols, such as replacing the previous symbol, merging them if an exact match
exists, or using a fuzzy match to find the closest representation.

This is useful for [collapsing borders] in layouts, where multiple symbols may need to be
combined to create a single, coherent border representation.

Not all combinations of box drawing symbols can be represented as a single unicode character, as
many of them are not defined in the [Box Drawing Unicode block]. This means that some merging
strategies will not yield a valid unicode character. The [`MergeStrategy::Replace`](../index.md) strategy
will be used as a fallback in such cases, replacing the previous symbol with the next one.

Specifically, the following combinations of box drawing symbols are not defined in the [Box
Drawing Unicode block]:

- Combining any dashed segments with any non dashed segments (e.g. `╎` with `─` or `━`).
- Combining any rounded segments with any other segments (e.g. `╯` with `─` or `━`).
- Combining any double segments with any thick segments (e.g. `═` with `┃` or `━`).
- Combining some double segments with some plain segments (e.g. `┐` with `╔`).

The merging strategies include:

- [`Self::Replace`](../index.md): Replaces the previous symbol with the next one.
- [`Self::Exact`](../index.md): Merges symbols only if an exact composite unicode character exists, falling
  back to [`Self::Replace`](../index.md) if not.
- [`Self::Fuzzy`](../index.md): Merges symbols even if an exact composite unicode character doesn't exist,
  using the closest match, and falling back to [`Self::Exact`](../index.md) if necessary.

See `Cell::merge_symbol` for how to use this strategy in practice, and
`Block::merge_borders` for a more concrete example of merging borders in a layout.

# Examples

```rust
use ratatui_core::symbols::merge::MergeStrategy;

assert_eq!(MergeStrategy::Replace.merge("│", "━"), "━");
assert_eq!(MergeStrategy::Exact.merge("│", "─"), "┼");
assert_eq!(MergeStrategy::Fuzzy.merge("┘", "╔"), "╬");
```

#### Variants

- **`Replace`**

  Replaces the previous symbol with the next one.
  
  This strategy simply replaces the previous symbol with the next one, without attempting to
  merge them. This is useful when you want to ensure that the last rendered symbol takes
  precedence over the previous one, regardless of their compatibility.
  
  The following diagram illustrates how this would apply to several overlapping blocks where
  the thick bordered blocks are rendered last, replacing the previous symbols:
  
  ```text
  ┌───┐    ┌───┐  ┌───┏━━━┓┌───┐
  │   │    │   │  │   ┃   ┃│   │
  │   │    │ ┏━━━┓│   ┃   ┃│   │
  │   │    │ ┃ │ ┃│   ┃   ┃│   │
  └───┏━━━┓└─┃─┘ ┃└───┗━━━┛┏━━━┓
      ┃   ┃  ┃   ┃         ┃   ┃
      ┃   ┃  ┗━━━┛         ┃   ┃
      ┃   ┃                ┃   ┃
      ┗━━━┛                ┗━━━┛
  ```
  
  # Example
  
  ```rust
  use ratatui_core::symbols::merge::MergeStrategy;
  let strategy = MergeStrategy::Replace;
  assert_eq!(strategy.merge("│", "━"), "━");
  ```

- **`Exact`**

  Merges symbols only if an exact composite unicode character exists.
  
  This strategy attempts to merge two symbols into a single composite unicode character if the
  exact representation exists. If the required unicode symbol does not exist, it falls back to
  [`MergeStrategy::Replace`](../index.md), replacing the previous symbol with the next one.
  
  The following diagram illustrates how this would apply to several overlapping blocks where
  the thick bordered blocks are rendered last, merging the previous symbols into a single
  composite character. All combinations of the plain and thick segments exist, so these
  symbols can be merged into a single character:
  
  ```text
  ┌───┐    ┌───┐  ┌───┲━━━┓┌───┐
  │   │    │   │  │   ┃   ┃│   │
  │   │    │ ┏━┿━┓│   ┃   ┃│   │
  │   │    │ ┃ │ ┃│   ┃   ┃│   │
  └───╆━━━┓└─╂─┘ ┃└───┺━━━┛┢━━━┪
      ┃   ┃  ┃   ┃         ┃   ┃
      ┃   ┃  ┗━━━┛         ┃   ┃
      ┃   ┃                ┃   ┃
      ┗━━━┛                ┗━━━┛
  ```
  
  The following diagram illustrates how this would apply to several overlapping blocks where
  the characters don't have a composite unicode character, so the previous symbols are
  replaced by the next one:
  
  ```text
  ┌───┐    ┌───┐  ┌───╔═══╗┌───┐
  │   │    │   │  │   ║   ║│   │
  │   │    │ ╔═╪═╗│   ║   ║│   │
  │   │    │ ║ │ ║│   ║   ║│   │
  └───╔═══╗└─╫─┘ ║└───╚═══╝╔═══╗
      ║   ║  ║   ║         ║   ║
      ║   ║  ╚═══╝         ║   ║
      ║   ║                ║   ║
      ╚═══╝                ╚═══╝
  ┌───┐    ┌───┐  ┌───╭───╮┌───┐
  │   │    │   │  │   │   ││   │
  │   │    │ ╭─┼─╮│   │   ││   │
  │   │    │ │ │ ││   │   ││   │
  └───╭───╮└─┼─┘ │└───╰───╯╭───╮
      │   │  │   │         │   │
      │   │  ╰───╯         │   │
      │   │                │   │
      ╰───╯                ╰───╯
  ```
  
  # Example
  
  ```rust
  use ratatui_core::symbols::merge::MergeStrategy;
  let strategy = MergeStrategy::Exact;
  assert_eq!(strategy.merge("│", "━"), "┿"); // exact match exists
  assert_eq!(strategy.merge("┘", "╔"), "╔"); // no exact match, falls back to Replace
  ```

- **`Fuzzy`**

  Merges symbols even if an exact composite unicode character doesn't exist, using the closest
  match.
  
  If required unicode symbol exists, acts exactly like [`MergeStrategy::Exact`](../index.md), if not, the
  following rules are applied:
  
  1. There are no characters that combine dashed with plain / thick segments, so we replace
     dashed segments with plain and thick dashed segments with thick. The following diagram
     shows how this would apply to merging a block with thick dashed borders over a block with
     plain dashed borders:
  
  ```text
  ┌╌╌╌┐    ┌╌╌╌┐  ┌╌╌╌┲╍╍╍┓┌╌╌╌┐
  ╎   ╎    ╎   ╎  ╎   ╏   ╏╎   ╎
  ╎   ╎    ╎ ┏╍┿╍┓╎   ╏   ╏╎   ╎
  ╎   ╎    ╎ ╏ ╎ ╏╎   ╏   ╏╎   ╎
  └╌╌╌╆╍╍╍┓└╌╂╌┘ ╏└╌╌╌┺╍╍╍┛┢╍╍╍┪
      ╏   ╏  ╏   ╏         ╏   ╏
      ╏   ╏  ┗╍╍╍┛         ╏   ╏
      ╏   ╏                ╏   ╏
      ┗╍╍╍┛                ┗╍╍╍┛
  ```
  
  2. There are no characters that combine rounded segments with other segments, so we replace
     rounded segments with plain. The following diagram shows how this would apply to merging
     a block with rounded corners over a block with plain corners:
  
  ```text
  ┌───┐    ┌───┐  ┌───┬───╮┌───┐
  │   │    │   │  │   │   ││   │
  │   │    │ ╭─┼─╮│   │   ││   │
  │   │    │ │ │ ││   │   ││   │
  └───┼───╮└─┼─┘ │└───┴───╯├───┤
      │   │  │   │         │   │
      │   │  ╰───╯         │   │
      │   │                │   │
      ╰───╯                ╰───╯
  ```
  
  3. There are no symbols that combine thick and double borders, so we replace all double
     segments with thick or all thick with double. The second symbol parameter takes
     precedence in choosing whether to use double or thick. The following diagram shows how
     this would apply to merging a block with double borders over a block with thick borders
     and then the reverse (merging a block with thick borders over a block with double
     borders):
  
  ```text
  ┏━━━┓    ┏━━━┓  ┏━━━╦═══╗┏━━━┓
  ┃   ┃    ┃   ┃  ┃   ║   ║┃   ┃
  ┃   ┃    ┃ ╔═╬═╗┃   ║   ║┃   ┃
  ┃   ┃    ┃ ║ ┃ ║┃   ║   ║┃   ┃
  ┗━━━╬═══╗┗━╬━┛ ║┗━━━╩═══╝╠═══╣
      ║   ║  ║   ║         ║   ║
      ║   ║  ╚═══╝         ║   ║
      ║   ║                ║   ║
      ╚═══╝                ╚═══╝
  
  ╔═══╗    ╔═══╗  ╔═══┳━━━┓╔═══╗
  ║   ║    ║   ║  ║   ┃   ┃║   ║
  ║   ║    ║ ┏━╋━┓║   ┃   ┃║   ║
  ║   ║    ║ ┃ ║ ┃║   ┃   ┃║   ║
  ╚═══╋━━━┓╚═╋═╝ ┃╚═══┻━━━┛┣━━━┫
      ┃   ┃  ┃   ┃         ┃   ┃
      ┃   ┃  ┗━━━┛         ┃   ┃
      ┃   ┃                ┃   ┃
      ┗━━━┛                ┗━━━┛
  ```
  
  4. Some combinations of double and plain don't exist, so if the symbol is still
     unrepresentable, change all plain segments with double or all double with plain. The
     second symbol parameter takes precedence in choosing whether to use double or plain. The
     following diagram shows how this would apply to merging a block with double borders over
     a block with plain borders and then the reverse (merging a block with plain borders over
     a block with double borders):
  
  ```text
  ┌───┐    ┌───┐  ┌───╦═══╗┌───┐
  │   │    │   │  │   ║   ║│   │
  │   │    │ ╔═╪═╗│   ║   ║│   │
  │   │    │ ║ │ ║│   ║   ║│   │
  └───╬═══╗└─╫─┘ ║└───╩═══╝╠═══╣
      ║   ║  ║   ║         ║   ║
      ║   ║  ╚═══╝         ║   ║
      ║   ║                ║   ║
      ╚═══╝                ╚═══╝
  ╔═══╗    ╔═══╗  ╔═══┬───┐╔═══╗
  ║   ║    ║   ║  ║   │   │║   ║
  ║   ║    ║ ┌─╫─┐║   │   │║   ║
  ║   ║    ║ │ ║ │║   │   │║   ║
  ╚═══┼───┐╚═╪═╝ │╚═══┴───┘├───┤
      │   │  │   │         │   │
      │   │  └───┘         │   │
      │   │                │   │
      └───┘                └───┘
  ```
  
  # Examples
  
  ```rust
  use ratatui_core::symbols::merge::MergeStrategy;
  let strategy = MergeStrategy::Fuzzy;
  
  // exact matches are merged normally
  assert_eq!(strategy.merge("┌", "┐"), "┬");
  
  // dashed segments are replaced with plain
  assert_eq!(strategy.merge("╎", "╍"), "┿");
  
  // rounded segments are replaced with plain
  assert_eq!(strategy.merge("┘", "╭"), "┼");
  
  // double and thick segments are merged based on the second symbol
  assert_eq!(strategy.merge("┃", "═"), "╬");
  assert_eq!(strategy.merge("═", "┃"), "╋");
  
  // combinations of double with plain that don't exist are merged based on the second symbol
  assert_eq!(strategy.merge("┐", "╔"), "╦");
  assert_eq!(strategy.merge("╔", "┐"), "┬");
  ```

#### Implementations

- `fn merge<'a>(self, prev: &'a str, next: &'a str) -> &'a str`

  Merges two symbols using this merge strategy.

  

  This method takes two string slices representing the previous and next symbols, and

  returns a string slice representing the merged symbol based on the merge strategy.

  

  If either of the symbols are not in the [Box Drawing Unicode block], the `next` symbol is

  returned as is. If both symbols are valid, they are merged according to the rules defined

  in the [`MergeStrategy`](#mergestrategy).

  

  Most code using this method will use the `Cell::merge_symbol` method, which uses this

  method internally to merge the symbols of a cell.

  

  # Example

  

  ```rust

  use ratatui_core::symbols::merge::MergeStrategy;

  

  let strategy = MergeStrategy::Fuzzy;

  assert_eq!(strategy.merge("┌", "┐"), "┬"); // merges to a single character

  assert_eq!(strategy.merge("┘", "╭"), "┼"); // replaces rounded with plain

  assert_eq!(strategy.merge("╎", "╍"), "┿"); // replaces dashed with plain

  assert_eq!(strategy.merge("┐", "╔"), "╦"); // merges double with plain

  assert_eq!(strategy.merge("╔", "┐"), "┬"); // merges plain with double

  ```

  

#### Trait Implementations

##### `impl Clone for MergeStrategy`

- `fn clone(&self) -> MergeStrategy` — [`MergeStrategy`](#mergestrategy)

##### `impl Copy for MergeStrategy`

##### `impl Debug for MergeStrategy`

- `fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result`

##### `impl Default for MergeStrategy`

- `fn default() -> MergeStrategy` — [`MergeStrategy`](#mergestrategy)

##### `impl Eq for MergeStrategy`

##### `impl<K> Equivalent for MergeStrategy`

- `fn equivalent(&self, key: &K) -> bool`

##### `impl Hash for MergeStrategy`

- `fn hash<__H: hash::Hasher>(&self, state: &mut __H)`

##### `impl IntoEither for MergeStrategy`

##### `impl PartialEq for MergeStrategy`

- `fn eq(&self, other: &MergeStrategy) -> bool` — [`MergeStrategy`](#mergestrategy)

##### `impl StructuralPartialEq for MergeStrategy`

