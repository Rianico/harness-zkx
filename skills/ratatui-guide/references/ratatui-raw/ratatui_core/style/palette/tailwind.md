*[ratatui_core](../../index.md) / [style](../../index.md) / [palette](../palette.md) / [tailwind](#)*

---

# Module `tailwind`

Represents the Tailwind CSS [default color palette][`palette`](../palette.md).

There are 22 palettes. Each palette has 11 colors, with variants from 50 to 950. Black and White
are also included for completeness and to avoid being affected by any terminal theme that might
be in use.

<style>
.color { display: flex; align-items: center; }
.color > div { width: 2rem; height: 2rem; }
.color > div.name { width: 150px; !important; }
</style>
<div style="overflow-x: auto">
<div style="display: flex; flex-direction:column; text-align: left">
<div class="color" style="font-size:0.8em">
    <div class="name"></div>
    <div>C50</div> <div>C100</div> <div>C200</div> <div>C300</div> <div>C400</div>
    <div>C500</div> <div>C600</div> <div>C700</div> <div>C800</div> <div>C900</div>
    <div>C950</div>
</div>
<div class="color">
    <div class="name">

[`SLATE`](#slate)</div>
    <div style="background-color: #f8fafc"></div> <div style="background-color: #f1f5f9"></div>
    <div style="background-color: #e2e8f0"></div> <div style="background-color: #cbd5e1"></div>
    <div style="background-color: #94a3b8"></div> <div style="background-color: #64748b"></div>
    <div style="background-color: #475569"></div> <div style="background-color: #334155"></div>
    <div style="background-color: #1e293b"></div> <div style="background-color: #0f172a"></div>
    <div style="background-color: #020617"></div>
</div>
<div class="color">
    <div class="name">

[`GRAY`](#gray)</div>
    <div style="background-color: #f9fafb"></div> <div style="background-color: #f3f4f6"></div>
    <div style="background-color: #e5e7eb"></div> <div style="background-color: #d1d5db"></div>
    <div style="background-color: #9ca3af"></div> <div style="background-color: #6b7280"></div>
    <div style="background-color: #4b5563"></div> <div style="background-color: #374151"></div>
    <div style="background-color: #1f2937"></div> <div style="background-color: #111827"></div>
    <div style="background-color: #0a0a0a"></div>
</div>
<div class="color">
    <div class="name">

[`ZINC`](#zinc)</div>
    <div style="background-color: #fafafa"></div> <div style="background-color: #f5f5f5"></div>
    <div style="background-color: #e5e5e5"></div> <div style="background-color: #d4d4d4"></div>
    <div style="background-color: #a1a1aa"></div> <div style="background-color: #71717a"></div>
    <div style="background-color: #52525b"></div> <div style="background-color: #404040"></div>
    <div style="background-color: #262626"></div> <div style="background-color: #171717"></div>
    <div style="background-color: #0a0a0a"></div>
</div>
<div class="color">
    <div class="name">

[`NEUTRAL`](#neutral)</div>
    <div style="background-color: #fafafa"></div> <div style="background-color: #f5f5f5"></div>
    <div style="background-color: #e5e5e5"></div> <div style="background-color: #d4d4d4"></div>
    <div style="background-color: #a3a3a3"></div> <div style="background-color: #737373"></div>
    <div style="background-color: #525252"></div> <div style="background-color: #404040"></div>
    <div style="background-color: #262626"></div> <div style="background-color: #171717"></div>
    <div style="background-color: #0a0a0a"></div>
</div>
<div class="color">
    <div class="name">

[`STONE`](#stone)</div>
    <div style="background-color: #fafaf9"></div> <div style="background-color: #f5f5f4"></div>
    <div style="background-color: #e7e5e4"></div> <div style="background-color: #d6d3d1"></div>
    <div style="background-color: #a8a29e"></div> <div style="background-color: #78716c"></div>
    <div style="background-color: #57534e"></div> <div style="background-color: #44403c"></div>
    <div style="background-color: #292524"></div> <div style="background-color: #1c1917"></div>
    <div style="background-color: #0c0a09"></div>
</div>
<div class="color">
    <div class="name">

[`RED`](#red)</div>
    <div style="background-color: #fef2f2"></div> <div style="background-color: #fee2e2"></div>
    <div style="background-color: #fecaca"></div> <div style="background-color: #fca5a5"></div>
    <div style="background-color: #f87171"></div> <div style="background-color: #ef4444"></div>
    <div style="background-color: #dc2626"></div> <div style="background-color: #b91c1c"></div>
    <div style="background-color: #991b1b"></div> <div style="background-color: #7f1d1d"></div>
    <div style="background-color: #450a0a"></div>
</div>
<div class="color">
    <div class="name">

[`ORANGE`](#orange)</div>
    <div style="background-color: #fff7ed"></div> <div style="background-color: #ffedd5"></div>
    <div style="background-color: #fed7aa"></div> <div style="background-color: #fdba74"></div>
    <div style="background-color: #fb923c"></div> <div style="background-color: #f97316"></div>
    <div style="background-color: #ea580c"></div> <div style="background-color: #c2410c"></div>
    <div style="background-color: #9a3412"></div> <div style="background-color: #7c2d12"></div>
    <div style="background-color: #431407"></div>
</div>
<div class="color">
    <div class="name">

[`AMBER`](#amber)</div>
    <div style="background-color: #fffbeb"></div> <div style="background-color: #fef3c7"></div>
    <div style="background-color: #fde68a"></div> <div style="background-color: #fcd34d"></div>
    <div style="background-color: #fbbf24"></div> <div style="background-color: #f59e0b"></div>
    <div style="background-color: #d97706"></div> <div style="background-color: #b45309"></div>
    <div style="background-color: #92400e"></div> <div style="background-color: #78350f"></div>
    <div style="background-color: #451a03"></div>
</div>
<div class="color">
    <div class="name">

[`YELLOW`](#yellow)</div>
    <div style="background-color: #fefce8"></div> <div style="background-color: #fef9c3"></div>
    <div style="background-color: #fef08a"></div> <div style="background-color: #fde047"></div>
    <div style="background-color: #facc15"></div> <div style="background-color: #eab308"></div>
    <div style="background-color: #ca8a04"></div> <div style="background-color: #a16207"></div>
    <div style="background-color: #854d0e"></div> <div style="background-color: #713f12"></div>
    <div style="background-color: #422006"></div>
</div>
<div class="color">
    <div class="name">

[`LIME`](#lime)</div>
    <div style="background-color: #f7fee7"></div> <div style="background-color: #ecfccb"></div>
    <div style="background-color: #d9f99d"></div> <div style="background-color: #bef264"></div>
    <div style="background-color: #a3e635"></div> <div style="background-color: #84cc16"></div>
    <div style="background-color: #65a30d"></div> <div style="background-color: #4d7c0f"></div>
    <div style="background-color: #3f6212"></div> <div style="background-color: #365314"></div>
    <div style="background-color: #1a2e05"></div>
</div>
<div class="color">
    <div class="name">

[`GREEN`](#green)</div>
    <div style="background-color: #f0fdf4"></div> <div style="background-color: #dcfce7"></div>
    <div style="background-color: #bbf7d0"></div> <div style="background-color: #86efac"></div>
    <div style="background-color: #4ade80"></div> <div style="background-color: #22c55e"></div>
    <div style="background-color: #16a34a"></div> <div style="background-color: #15803d"></div>
    <div style="background-color: #166534"></div> <div style="background-color: #14532d"></div>
    <div style="background-color: #052e16"></div>
</div>
<div class="color">
    <div class="name">

[`EMERALD`](#emerald)</div>
    <div style="background-color: #ecfdf5"></div> <div style="background-color: #d1fae5"></div>
    <div style="background-color: #a7f3d0"></div> <div style="background-color: #6ee7b7"></div>
    <div style="background-color: #34d399"></div> <div style="background-color: #10b981"></div>
    <div style="background-color: #059669"></div> <div style="background-color: #047857"></div>
    <div style="background-color: #065f46"></div> <div style="background-color: #064e3b"></div>
    <div style="background-color: #022c22"></div>
</div>
<div class="color">
    <div class="name">

[`TEAL`](#teal)</div>
    <div style="background-color: #f0fdfa"></div> <div style="background-color: #ccfbf1"></div>
    <div style="background-color: #99f6e4"></div> <div style="background-color: #5eead4"></div>
    <div style="background-color: #2dd4bf"></div> <div style="background-color: #14b8a6"></div>
    <div style="background-color: #0d9488"></div> <div style="background-color: #0f766e"></div>
    <div style="background-color: #115e59"></div> <div style="background-color: #134e4a"></div>
    <div style="background-color: #042f2e"></div>
</div>
<div class="color">
    <div class="name">

[`CYAN`](#cyan)</div>
    <div style="background-color: #ecfeff"></div> <div style="background-color: #cffafe"></div>
    <div style="background-color: #a5f3fc"></div> <div style="background-color: #67e8f9"></div>
    <div style="background-color: #22d3ee"></div> <div style="background-color: #06b6d4"></div>
    <div style="background-color: #0891b2"></div> <div style="background-color: #0e7490"></div>
    <div style="background-color: #155e75"></div> <div style="background-color: #164e63"></div>
    <div style="background-color: #083344"></div>
</div>
<div class="color">
    <div class="name">

[`SKY`](#sky)</div>
    <div style="background-color: #f0f9ff"></div> <div style="background-color: #e0f2fe"></div>
    <div style="background-color: #bae6fd"></div> <div style="background-color: #7dd3fc"></div>
    <div style="background-color: #38bdf8"></div> <div style="background-color: #0ea5e9"></div>
    <div style="background-color: #0284c7"></div> <div style="background-color: #0369a1"></div>
    <div style="background-color: #075985"></div> <div style="background-color: #0c4a6e"></div>
    <div style="background-color: #082f49"></div>
</div>
<div class="color">
    <div class="name">

[`BLUE`](#blue)</div>
    <div style="background-color: #eff6ff"></div> <div style="background-color: #dbeafe"></div>
    <div style="background-color: #bfdbfe"></div> <div style="background-color: #93c5fd"></div>
    <div style="background-color: #60a5fa"></div> <div style="background-color: #3b82f6"></div>
    <div style="background-color: #2563eb"></div> <div style="background-color: #1d4ed8"></div>
    <div style="background-color: #1e40af"></div> <div style="background-color: #1e3a8a"></div>
    <div style="background-color: #172554"></div>
</div>
<div class="color">
    <div class="name">

[`INDIGO`](#indigo)</div>
    <div style="background-color: #eef2ff"></div> <div style="background-color: #e0e7ff"></div>
    <div style="background-color: #c7d2fe"></div> <div style="background-color: #a5b4fc"></div>
    <div style="background-color: #818cf8"></div> <div style="background-color: #6366f1"></div>
    <div style="background-color: #4f46e5"></div> <div style="background-color: #4338ca"></div>
    <div style="background-color: #3730a3"></div> <div style="background-color: #312e81"></div>
    <div style="background-color: #1e1b4b"></div>
</div>
<div class="color">
    <div class="name">

[`VIOLET`](#violet)</div>
    <div style="background-color: #f5f3ff"></div> <div style="background-color: #ede9fe"></div>
    <div style="background-color: #ddd6fe"></div> <div style="background-color: #c4b5fd"></div>
    <div style="background-color: #a78bfa"></div> <div style="background-color: #8b5cf6"></div>
    <div style="background-color: #7c3aed"></div> <div style="background-color: #6d28d9"></div>
    <div style="background-color: #5b21b6"></div> <div style="background-color: #4c1d95"></div>
    <div style="background-color: #2e1065"></div>
</div>
<div class="color">
    <div class="name">

[`PURPLE`](#purple)</div>
    <div style="background-color: #faf5ff"></div> <div style="background-color: #f3e8ff"></div>
    <div style="background-color: #e9d5ff"></div> <div style="background-color: #d8b4fe"></div>
    <div style="background-color: #c084fc"></div> <div style="background-color: #a855f7"></div>
    <div style="background-color: #9333ea"></div> <div style="background-color: #7e22ce"></div>
    <div style="background-color: #6b21a8"></div> <div style="background-color: #581c87"></div>
    <div style="background-color: #4c136e"></div>
</div>
<div class="color">
    <div class="name">

[`FUCHSIA`](#fuchsia)</div>
    <div style="background-color: #fdf4ff"></div> <div style="background-color: #fae8ff"></div>
    <div style="background-color: #f5d0fe"></div> <div style="background-color: #f0abfc"></div>
    <div style="background-color: #e879f9"></div> <div style="background-color: #d946ef"></div>
    <div style="background-color: #c026d3"></div> <div style="background-color: #a21caf"></div>
    <div style="background-color: #86198f"></div> <div style="background-color: #701a75"></div>
    <div style="background-color: #4e145b"></div>
</div>
<div class="color">
    <div class="name">

[`PINK`](#pink)</div>
    <div style="background-color: #fdf2f8"></div> <div style="background-color: #fce7f3"></div>
    <div style="background-color: #fbcfe8"></div> <div style="background-color: #f9a8d4"></div>
    <div style="background-color: #f472b6"></div> <div style="background-color: #ec4899"></div>
    <div style="background-color: #db2777"></div> <div style="background-color: #be185d"></div>
    <div style="background-color: #9d174d"></div> <div style="background-color: #831843"></div>
    <div style="background-color: #5f0b37"></div>
</div>
<div class="color">
   <div class="name">

[`BLACK`](#black)</div>
    <div style="background-color: #000000; width:22rem"></div>
</div>
<div class="color">
    <div class="name">

[`WHITE`](#white)</div>
    <div style="background-color: #ffffff; width:22rem"></div>
</div>
</div>
</div>

# Example

```rust
use ratatui_core::style::Color;
use ratatui_core::style::palette::tailwind::{BLUE, RED};

assert_eq!(RED.c500, Color::Rgb(239, 68, 68));
assert_eq!(BLUE.c500, Color::Rgb(59, 130, 246));
```

## Contents

- [Structs](#structs)
  - [`Palette`](#palette)
- [Constants](#constants)
  - [`BLACK`](#black)
  - [`WHITE`](#white)
  - [`SLATE`](#slate)
  - [`GRAY`](#gray)
  - [`ZINC`](#zinc)
  - [`NEUTRAL`](#neutral)
  - [`STONE`](#stone)
  - [`RED`](#red)
  - [`ORANGE`](#orange)
  - [`AMBER`](#amber)
  - [`YELLOW`](#yellow)
  - [`LIME`](#lime)
  - [`GREEN`](#green)
  - [`EMERALD`](#emerald)
  - [`TEAL`](#teal)
  - [`CYAN`](#cyan)
  - [`SKY`](#sky)
  - [`BLUE`](#blue)
  - [`INDIGO`](#indigo)
  - [`VIOLET`](#violet)
  - [`PURPLE`](#purple)
  - [`FUCHSIA`](#fuchsia)
  - [`PINK`](#pink)
  - [`ROSE`](#rose)

## Quick Reference

| Item | Kind | Description |
|------|------|-------------|
| [`Palette`](#palette) | struct |  |
| [`BLACK`](#black) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #000000"></div></div> |
| [`WHITE`](#white) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #ffffff"></div></div> |
| [`SLATE`](#slate) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f8fafc"></div><div style="background-color: #f1f5f9"></div><div style="background-color: #e2e8f0"></div><div style="background-color: #cbd5e1"></div><div style="background-color: #94a3b8"></div><div style="background-color: #64748b"></div><div style="background-color: #475569"></div><div style="background-color: #334155"></div><div style="background-color: #1e293b"></div><div style="background-color: #0f172a"></div><div style="background-color: #020617"></div></div> |
| [`GRAY`](#gray) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f9fafb"></div><div style="background-color: #f3f4f6"></div><div style="background-color: #e5e7eb"></div><div style="background-color: #d1d5db"></div><div style="background-color: #9ca3af"></div><div style="background-color: #6b7280"></div><div style="background-color: #4b5563"></div><div style="background-color: #374151"></div><div style="background-color: #1f2937"></div><div style="background-color: #111827"></div><div style="background-color: #030712"></div></div> |
| [`ZINC`](#zinc) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fafafa"></div><div style="background-color: #f5f5f5"></div><div style="background-color: #e5e5e5"></div><div style="background-color: #d4d4d4"></div><div style="background-color: #a1a1aa"></div><div style="background-color: #71717a"></div><div style="background-color: #52525b"></div><div style="background-color: #404040"></div><div style="background-color: #262626"></div><div style="background-color: #171717"></div><div style="background-color: #09090b"></div></div> |
| [`NEUTRAL`](#neutral) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fafafa"></div><div style="background-color: #f5f5f5"></div><div style="background-color: #e5e5e5"></div><div style="background-color: #d4d4d4"></div><div style="background-color: #a3a3a3"></div><div style="background-color: #737373"></div><div style="background-color: #525252"></div><div style="background-color: #404040"></div><div style="background-color: #262626"></div><div style="background-color: #171717"></div><div style="background-color: #0a0a0a"></div></div> |
| [`STONE`](#stone) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fafaf9"></div><div style="background-color: #f5f5f4"></div><div style="background-color: #e7e5e4"></div><div style="background-color: #d6d3d1"></div><div style="background-color: #a8a29e"></div><div style="background-color: #78716c"></div><div style="background-color: #57534e"></div><div style="background-color: #44403c"></div><div style="background-color: #292524"></div><div style="background-color: #1c1917"></div><div style="background-color: #0c0a09"></div></div> |
| [`RED`](#red) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fef2f2"></div><div style="background-color: #fee2e2"></div><div style="background-color: #fecaca"></div><div style="background-color: #fca5a5"></div><div style="background-color: #f87171"></div><div style="background-color: #ef4444"></div><div style="background-color: #dc2626"></div><div style="background-color: #b91c1c"></div><div style="background-color: #991b1b"></div><div style="background-color: #7f1d1d"></div><div style="background-color: #450a0a"></div></div> |
| [`ORANGE`](#orange) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fff7ed"></div><div style="background-color: #ffedd5"></div><div style="background-color: #fed7aa"></div><div style="background-color: #fdba74"></div><div style="background-color: #fb923c"></div><div style="background-color: #f97316"></div><div style="background-color: #ea580c"></div><div style="background-color: #c2410c"></div><div style="background-color: #9a3412"></div><div style="background-color: #7c2d12"></div><div style="background-color: #431407"></div></div> |
| [`AMBER`](#amber) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fffbeb"></div><div style="background-color: #fef3c7"></div><div style="background-color: #fde68a"></div><div style="background-color: #fcd34d"></div><div style="background-color: #fbbf24"></div><div style="background-color: #f59e0b"></div><div style="background-color: #d97706"></div><div style="background-color: #b45309"></div><div style="background-color: #92400e"></div><div style="background-color: #78350f"></div><div style="background-color: #451a03"></div></div> |
| [`YELLOW`](#yellow) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fefce8"></div><div style="background-color: #fef9c3"></div><div style="background-color: #fef08a"></div><div style="background-color: #fde047"></div><div style="background-color: #facc15"></div><div style="background-color: #eab308"></div><div style="background-color: #ca8a04"></div><div style="background-color: #a16207"></div><div style="background-color: #854d0e"></div><div style="background-color: #713f12"></div><div style="background-color: #422006"></div></div> |
| [`LIME`](#lime) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f7fee7"></div><div style="background-color: #ecfccb"></div><div style="background-color: #d9f99d"></div><div style="background-color: #bef264"></div><div style="background-color: #a3e635"></div><div style="background-color: #84cc16"></div><div style="background-color: #65a30d"></div><div style="background-color: #4d7c0f"></div><div style="background-color: #3f6212"></div><div style="background-color: #365314"></div><div style="background-color: #1a2e05"></div></div> |
| [`GREEN`](#green) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f0fdf4"></div><div style="background-color: #dcfce7"></div><div style="background-color: #bbf7d0"></div><div style="background-color: #86efac"></div><div style="background-color: #4ade80"></div><div style="background-color: #22c55e"></div><div style="background-color: #16a34a"></div><div style="background-color: #15803d"></div><div style="background-color: #166534"></div><div style="background-color: #14532d"></div><div style="background-color: #052e16"></div></div> |
| [`EMERALD`](#emerald) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f0fdfa"></div><div style="background-color: #ccfbf1"></div><div style="background-color: #99f6e4"></div><div style="background-color: #5eead4"></div><div style="background-color: #2dd4bf"></div><div style="background-color: #14b8a6"></div><div style="background-color: #0d9488"></div><div style="background-color: #0f766e"></div><div style="background-color: #115e59"></div><div style="background-color: #134e4a"></div><div style="background-color: #042f2e"></div></div> |
| [`TEAL`](#teal) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f5fdf4"></div><div style="background-color: #e7f9e7"></div><div style="background-color: #c6f6d5"></div><div style="background-color: #9ae6b4"></div><div style="background-color: #68d391"></div><div style="background-color: #48bb78"></div><div style="background-color: #38a169"></div><div style="background-color: #2f855a"></div><div style="background-color: #276749"></div><div style="background-color: #22543d"></div><div style="background-color: #0d3321"></div></div> |
| [`CYAN`](#cyan) | const | <style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #ecfeff"></div><div style="background-color: #cffafe"></div><div style="background-color: #a5f3fc"></div><div style="background-color: #67e8f9"></div><div style="background-color: #22d3ee"></div><div style="background-color: #06b6d4"></div><div style="background-color: #0891b2"></div><div style="background-color: #0e7490"></div><div style="background-color: #155e75"></div><div style="background-color: #164e63"></div><div style="background-color: #083344"></div></div> |
| [`SKY`](#sky) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f0f9ff"></div><div style="background-color: #e0f2fe"></div><div style="background-color: #bae6fd"></div><div style="background-color: #7dd3fc"></div><div style="background-color: #38bdf8"></div><div style="background-color: #0ea5e9"></div><div style="background-color: #0284c7"></div><div style="background-color: #0369a1"></div><div style="background-color: #075985"></div><div style="background-color: #0c4a6e"></div><div style="background-color: #082f49"></div></div> |
| [`BLUE`](#blue) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #eff6ff"></div><div style="background-color: #dbeafe"></div><div style="background-color: #bfdbfe"></div><div style="background-color: #93c5fd"></div><div style="background-color: #60a5fa"></div><div style="background-color: #3b82f6"></div><div style="background-color: #2563eb"></div><div style="background-color: #1d4ed8"></div><div style="background-color: #1e40af"></div><div style="background-color: #1e3a8a"></div><div style="background-color: #172554"></div></div> |
| [`INDIGO`](#indigo) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #eef2ff"></div><div style="background-color: #e0e7ff"></div><div style="background-color: #c7d2fe"></div><div style="background-color: #a5b4fc"></div><div style="background-color: #818cf8"></div><div style="background-color: #6366f1"></div><div style="background-color: #4f46e5"></div><div style="background-color: #4338ca"></div><div style="background-color: #3730a3"></div><div style="background-color: #312e81"></div><div style="background-color: #1e1b4b"></div></div> |
| [`VIOLET`](#violet) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f5f3ff"></div><div style="background-color: #ede9fe"></div><div style="background-color: #ddd6fe"></div><div style="background-color: #c4b5fd"></div><div style="background-color: #a78bfa"></div><div style="background-color: #8b5cf6"></div><div style="background-color: #7c3aed"></div><div style="background-color: #6d28d9"></div><div style="background-color: #5b21b6"></div><div style="background-color: #4c1d95"></div><div style="background-color: #2e1065"></div></div> |
| [`PURPLE`](#purple) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #faf5ff"></div><div style="background-color: #f3e8ff"></div><div style="background-color: #e9d5ff"></div><div style="background-color: #d8b4fe"></div><div style="background-color: #c084fc"></div><div style="background-color: #a855f7"></div><div style="background-color: #9333ea"></div><div style="background-color: #7e22ce"></div><div style="background-color: #6b21a8"></div><div style="background-color: #581c87"></div><div style="background-color: #3b0764"></div></div> |
| [`FUCHSIA`](#fuchsia) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fdf4ff"></div><div style="background-color: #fae8ff"></div><div style="background-color: #f5d0fe"></div><div style="background-color: #f0abfc"></div><div style="background-color: #e879f9"></div><div style="background-color: #d946ef"></div><div style="background-color: #c026d3"></div><div style="background-color: #a21caf"></div><div style="background-color: #86198f"></div><div style="background-color: #701a75"></div><div style="background-color: #4a044e"></div></div> |
| [`PINK`](#pink) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fdf2f8"></div><div style="background-color: #fce7f3"></div><div style="background-color: #fbcfe8"></div><div style="background-color: #f9a8d4"></div><div style="background-color: #f472b6"></div><div style="background-color: #ec4899"></div><div style="background-color: #db2777"></div><div style="background-color: #be185d"></div><div style="background-color: #9d174d"></div><div style="background-color: #831843"></div><div style="background-color: #500724"></div></div> |
| [`ROSE`](#rose) | const | <style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fff1f2"></div><div style="background-color: #ffe4e6"></div><div style="background-color: #fecdd3"></div><div style="background-color: #fda4af"></div><div style="background-color: #fb7185"></div><div style="background-color: #f43f5e"></div><div style="background-color: #e11d48"></div><div style="background-color: #be123c"></div><div style="background-color: #9f1239"></div><div style="background-color: #881337"></div><div style="background-color: #4c0519"></div></div> |

## Structs

### `Palette`

```rust
struct Palette {
    pub c50: crate::style::Color,
    pub c100: crate::style::Color,
    pub c200: crate::style::Color,
    pub c300: crate::style::Color,
    pub c400: crate::style::Color,
    pub c500: crate::style::Color,
    pub c600: crate::style::Color,
    pub c700: crate::style::Color,
    pub c800: crate::style::Color,
    pub c900: crate::style::Color,
    pub c950: crate::style::Color,
}
```

#### Trait Implementations

##### `impl IntoEither for Palette`

## Constants

### `BLACK`
```rust
const BLACK: crate::style::Color;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #000000"></div></div>

### `WHITE`
```rust
const WHITE: crate::style::Color;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #ffffff"></div></div>

### `SLATE`
```rust
const SLATE: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f8fafc"></div><div style="background-color: #f1f5f9"></div><div style="background-color: #e2e8f0"></div><div style="background-color: #cbd5e1"></div><div style="background-color: #94a3b8"></div><div style="background-color: #64748b"></div><div style="background-color: #475569"></div><div style="background-color: #334155"></div><div style="background-color: #1e293b"></div><div style="background-color: #0f172a"></div><div style="background-color: #020617"></div></div>

### `GRAY`
```rust
const GRAY: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f9fafb"></div><div style="background-color: #f3f4f6"></div><div style="background-color: #e5e7eb"></div><div style="background-color: #d1d5db"></div><div style="background-color: #9ca3af"></div><div style="background-color: #6b7280"></div><div style="background-color: #4b5563"></div><div style="background-color: #374151"></div><div style="background-color: #1f2937"></div><div style="background-color: #111827"></div><div style="background-color: #030712"></div></div>

### `ZINC`
```rust
const ZINC: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fafafa"></div><div style="background-color: #f5f5f5"></div><div style="background-color: #e5e5e5"></div><div style="background-color: #d4d4d4"></div><div style="background-color: #a1a1aa"></div><div style="background-color: #71717a"></div><div style="background-color: #52525b"></div><div style="background-color: #404040"></div><div style="background-color: #262626"></div><div style="background-color: #171717"></div><div style="background-color: #09090b"></div></div>

### `NEUTRAL`
```rust
const NEUTRAL: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fafafa"></div><div style="background-color: #f5f5f5"></div><div style="background-color: #e5e5e5"></div><div style="background-color: #d4d4d4"></div><div style="background-color: #a3a3a3"></div><div style="background-color: #737373"></div><div style="background-color: #525252"></div><div style="background-color: #404040"></div><div style="background-color: #262626"></div><div style="background-color: #171717"></div><div style="background-color: #0a0a0a"></div></div>

### `STONE`
```rust
const STONE: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fafaf9"></div><div style="background-color: #f5f5f4"></div><div style="background-color: #e7e5e4"></div><div style="background-color: #d6d3d1"></div><div style="background-color: #a8a29e"></div><div style="background-color: #78716c"></div><div style="background-color: #57534e"></div><div style="background-color: #44403c"></div><div style="background-color: #292524"></div><div style="background-color: #1c1917"></div><div style="background-color: #0c0a09"></div></div>

### `RED`
```rust
const RED: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fef2f2"></div><div style="background-color: #fee2e2"></div><div style="background-color: #fecaca"></div><div style="background-color: #fca5a5"></div><div style="background-color: #f87171"></div><div style="background-color: #ef4444"></div><div style="background-color: #dc2626"></div><div style="background-color: #b91c1c"></div><div style="background-color: #991b1b"></div><div style="background-color: #7f1d1d"></div><div style="background-color: #450a0a"></div></div>

### `ORANGE`
```rust
const ORANGE: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fff7ed"></div><div style="background-color: #ffedd5"></div><div style="background-color: #fed7aa"></div><div style="background-color: #fdba74"></div><div style="background-color: #fb923c"></div><div style="background-color: #f97316"></div><div style="background-color: #ea580c"></div><div style="background-color: #c2410c"></div><div style="background-color: #9a3412"></div><div style="background-color: #7c2d12"></div><div style="background-color: #431407"></div></div>

### `AMBER`
```rust
const AMBER: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fffbeb"></div><div style="background-color: #fef3c7"></div><div style="background-color: #fde68a"></div><div style="background-color: #fcd34d"></div><div style="background-color: #fbbf24"></div><div style="background-color: #f59e0b"></div><div style="background-color: #d97706"></div><div style="background-color: #b45309"></div><div style="background-color: #92400e"></div><div style="background-color: #78350f"></div><div style="background-color: #451a03"></div></div>

### `YELLOW`
```rust
const YELLOW: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fefce8"></div><div style="background-color: #fef9c3"></div><div style="background-color: #fef08a"></div><div style="background-color: #fde047"></div><div style="background-color: #facc15"></div><div style="background-color: #eab308"></div><div style="background-color: #ca8a04"></div><div style="background-color: #a16207"></div><div style="background-color: #854d0e"></div><div style="background-color: #713f12"></div><div style="background-color: #422006"></div></div>

### `LIME`
```rust
const LIME: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f7fee7"></div><div style="background-color: #ecfccb"></div><div style="background-color: #d9f99d"></div><div style="background-color: #bef264"></div><div style="background-color: #a3e635"></div><div style="background-color: #84cc16"></div><div style="background-color: #65a30d"></div><div style="background-color: #4d7c0f"></div><div style="background-color: #3f6212"></div><div style="background-color: #365314"></div><div style="background-color: #1a2e05"></div></div>

### `GREEN`
```rust
const GREEN: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f0fdf4"></div><div style="background-color: #dcfce7"></div><div style="background-color: #bbf7d0"></div><div style="background-color: #86efac"></div><div style="background-color: #4ade80"></div><div style="background-color: #22c55e"></div><div style="background-color: #16a34a"></div><div style="background-color: #15803d"></div><div style="background-color: #166534"></div><div style="background-color: #14532d"></div><div style="background-color: #052e16"></div></div>

### `EMERALD`
```rust
const EMERALD: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f0fdfa"></div><div style="background-color: #ccfbf1"></div><div style="background-color: #99f6e4"></div><div style="background-color: #5eead4"></div><div style="background-color: #2dd4bf"></div><div style="background-color: #14b8a6"></div><div style="background-color: #0d9488"></div><div style="background-color: #0f766e"></div><div style="background-color: #115e59"></div><div style="background-color: #134e4a"></div><div style="background-color: #042f2e"></div></div>

### `TEAL`
```rust
const TEAL: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f5fdf4"></div><div style="background-color: #e7f9e7"></div><div style="background-color: #c6f6d5"></div><div style="background-color: #9ae6b4"></div><div style="background-color: #68d391"></div><div style="background-color: #48bb78"></div><div style="background-color: #38a169"></div><div style="background-color: #2f855a"></div><div style="background-color: #276749"></div><div style="background-color: #22543d"></div><div style="background-color: #0d3321"></div></div>

### `CYAN`
```rust
const CYAN: Palette;
```

<style>.palette div{width:2rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #ecfeff"></div><div style="background-color: #cffafe"></div><div style="background-color: #a5f3fc"></div><div style="background-color: #67e8f9"></div><div style="background-color: #22d3ee"></div><div style="background-color: #06b6d4"></div><div style="background-color: #0891b2"></div><div style="background-color: #0e7490"></div><div style="background-color: #155e75"></div><div style="background-color: #164e63"></div><div style="background-color: #083344"></div></div>

### `SKY`
```rust
const SKY: Palette;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f0f9ff"></div><div style="background-color: #e0f2fe"></div><div style="background-color: #bae6fd"></div><div style="background-color: #7dd3fc"></div><div style="background-color: #38bdf8"></div><div style="background-color: #0ea5e9"></div><div style="background-color: #0284c7"></div><div style="background-color: #0369a1"></div><div style="background-color: #075985"></div><div style="background-color: #0c4a6e"></div><div style="background-color: #082f49"></div></div>

### `BLUE`
```rust
const BLUE: Palette;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #eff6ff"></div><div style="background-color: #dbeafe"></div><div style="background-color: #bfdbfe"></div><div style="background-color: #93c5fd"></div><div style="background-color: #60a5fa"></div><div style="background-color: #3b82f6"></div><div style="background-color: #2563eb"></div><div style="background-color: #1d4ed8"></div><div style="background-color: #1e40af"></div><div style="background-color: #1e3a8a"></div><div style="background-color: #172554"></div></div>

### `INDIGO`
```rust
const INDIGO: Palette;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #eef2ff"></div><div style="background-color: #e0e7ff"></div><div style="background-color: #c7d2fe"></div><div style="background-color: #a5b4fc"></div><div style="background-color: #818cf8"></div><div style="background-color: #6366f1"></div><div style="background-color: #4f46e5"></div><div style="background-color: #4338ca"></div><div style="background-color: #3730a3"></div><div style="background-color: #312e81"></div><div style="background-color: #1e1b4b"></div></div>

### `VIOLET`
```rust
const VIOLET: Palette;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #f5f3ff"></div><div style="background-color: #ede9fe"></div><div style="background-color: #ddd6fe"></div><div style="background-color: #c4b5fd"></div><div style="background-color: #a78bfa"></div><div style="background-color: #8b5cf6"></div><div style="background-color: #7c3aed"></div><div style="background-color: #6d28d9"></div><div style="background-color: #5b21b6"></div><div style="background-color: #4c1d95"></div><div style="background-color: #2e1065"></div></div>

### `PURPLE`
```rust
const PURPLE: Palette;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #faf5ff"></div><div style="background-color: #f3e8ff"></div><div style="background-color: #e9d5ff"></div><div style="background-color: #d8b4fe"></div><div style="background-color: #c084fc"></div><div style="background-color: #a855f7"></div><div style="background-color: #9333ea"></div><div style="background-color: #7e22ce"></div><div style="background-color: #6b21a8"></div><div style="background-color: #581c87"></div><div style="background-color: #3b0764"></div></div>

### `FUCHSIA`
```rust
const FUCHSIA: Palette;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fdf4ff"></div><div style="background-color: #fae8ff"></div><div style="background-color: #f5d0fe"></div><div style="background-color: #f0abfc"></div><div style="background-color: #e879f9"></div><div style="background-color: #d946ef"></div><div style="background-color: #c026d3"></div><div style="background-color: #a21caf"></div><div style="background-color: #86198f"></div><div style="background-color: #701a75"></div><div style="background-color: #4a044e"></div></div>

### `PINK`
```rust
const PINK: Palette;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fdf2f8"></div><div style="background-color: #fce7f3"></div><div style="background-color: #fbcfe8"></div><div style="background-color: #f9a8d4"></div><div style="background-color: #f472b6"></div><div style="background-color: #ec4899"></div><div style="background-color: #db2777"></div><div style="background-color: #be185d"></div><div style="background-color: #9d174d"></div><div style="background-color: #831843"></div><div style="background-color: #500724"></div></div>

### `ROSE`
```rust
const ROSE: Palette;
```

<style>.palette div{width:22rem;height:2rem}</style><div class="palette" style="display:flex;flex-direction:row"><div style="background-color: #fff1f2"></div><div style="background-color: #ffe4e6"></div><div style="background-color: #fecdd3"></div><div style="background-color: #fda4af"></div><div style="background-color: #fb7185"></div><div style="background-color: #f43f5e"></div><div style="background-color: #e11d48"></div><div style="background-color: #be123c"></div><div style="background-color: #9f1239"></div><div style="background-color: #881337"></div><div style="background-color: #4c0519"></div></div>

