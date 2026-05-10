# Pattern Extraction Methodology

How to extract practical code patterns from documentation.

## Pattern Categories

### 1. Initialization Patterns

First code users need to run:

```rust
// Example: Hello world / basic setup
fn main() -> std::io::Result<()> {
    ratatui::run(|terminal| {
        // minimal app
    })
}
```

**Sources:**
- "Getting Started" sections
- "Quick Start" guides
- README examples
- Supplementary tutorial first examples

### 2. Common Usage Patterns

Operations users do frequently:

```rust
// Example: Basic layout split
let [header, body, footer] = Layout::vertical([
    Constraint::Length(3),
    Constraint::Fill(1),
    Constraint::Length(1),
]).areas(frame.area());
```

**Sources:**
- Documentation examples
- Tutorial code blocks
- Common recipes

### 3. Stateful Patterns

Components with external state:

```rust
// Example: List with selection
let mut state = ListState::default();
state.select(Some(0));
frame.render_stateful_widget(list, area, &mut state);
```

**Indicators:**
- `State` suffix types
- `render_stateful_widget` calls
- `&mut state` parameters

### 4. Error Handling Patterns

Common pitfalls and solutions:

```rust
// Example: Proper terminal cleanup
fn main() -> std::io::Result<()> {
    let terminal = ratatui::init();
    // ... app logic ...
    ratatui::restore();  // Always restore!
    Ok(())
}
```

**Sources:**
- "Troubleshooting" sections
- FAQ error scenarios
- Common mistakes documentation

### 5. Integration Patterns

Combining multiple features:

```rust
// Example: Nested layout with widgets
let [header, body, footer] = Layout::vertical([...]).areas(area);
let [sidebar, main] = Layout::horizontal([...]).areas(body);
// Render widgets in each area
```

**Sources:**
- Advanced tutorials
- Example applications
- Integration guides

## Extraction Priority

1. **Supplementary docs** (tutorials, guides) - best for beginner-friendly patterns
2. **Primary docs** code blocks - authoritative examples
3. **FAQ sections** - problem-solution pairs

## Pattern Selection Criteria

| Criterion | Include | Skip |
|-----------|---------|------|
| Complexity | Simple to medium | Complex edge cases |
| Generality | Reusable template | Example-specific |
| Frequency | Common operation | Rare use case |
| Clarity | Self-contained | Requires external context |

## Pattern Complexity Levels

| Level | Lines | Description |
|-------|-------|-------------|
| Simple | 5-15 | Single concept, minimal setup |
| Medium | 15-40 | Multiple concepts, some setup |
| Complex | 40+ | Full example, significant setup |

**Rule:** Include 1-2 simple, 2-3 medium per module. Complex patterns go to references/.

## Pattern Template

```yaml
- name: "<Descriptive Name>"
  code: |
    <code block>
  complexity: simple | medium | complex
  category: initialization | common_usage | stateful | error_handling | integration
```

## Anti-Patterns to Avoid

- Patterns with placeholder values that need explanation
- Code that imports from example-specific modules
- Patterns that depend on external state not shown
- Incomplete snippets missing key context

## Pattern Count Guidelines

| Module Size | Patterns in SKILL.md | Patterns in References |
|-------------|---------------------|------------------------|
| Small (< 5k tokens) | 3-5 | 0 |
| Medium (5-15k tokens) | 5-8 | 5-10 |
| Large (> 15k tokens) | 5-8 | 10-20 |
