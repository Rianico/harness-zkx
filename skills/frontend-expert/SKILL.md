---
name: frontend-expert
description: Cross-cutting frontend patterns for React, Next.js, Vue, and Nuxt. Covers component composition, state management, performance optimization, forms, accessibility, and SSR/hydration patterns. TRIGGER when: building React or Vue components; implementing custom hooks or composables; managing state with useState/useReducer/Zustand/Context or Pinia; optimizing render performance with memoization/virtualization/code splitting; handling forms with validation; debugging hydration mismatches; configuring Next.js Turbopack or Nuxt route rules; implementing lazy hydration or SSR data fetching.
argument-hint: "[react|vue|nextjs|nuxt|performance|state|forms|accessibility]"
---

# Frontend Development Patterns

Modern frontend patterns for React, Next.js, Vue, Nuxt, and performant user interfaces.

## When to Activate

- Building React or Vue components (composition, props, rendering)
- Managing state (useState, useReducer, Zustand, Context, Pinia)
- Implementing data fetching (SWR, React Query, useFetch, useAsyncData)
- Optimizing performance (memoization, virtualization, code splitting)
- Working with forms (validation, controlled inputs, Zod schemas)
- Debugging hydration mismatches (SSR vs client state)
- Configuring route rules and rendering strategies
- Building accessible, responsive UI patterns

## Quick Actions & Checklists

### React Component Checklist
- [ ] Prefer composition over inheritance
- [ ] Use compound components for related UI elements
- [ ] Keep components focused and small (<150 lines)
- [ ] Extract custom hooks for reusable logic
- [ ] Memoize expensive computations with `useMemo`
- [ ] Memoize callbacks passed to children with `useCallback`
- [ ] Wrap pure components with `React.memo` when needed

### Vue/Nuxt Component Checklist
- [ ] Use composables for reusable logic
- [ ] Keep SSR render deterministic (no Date.now(), Math.random() in templates)
- [ ] Use `useFetch`/`useAsyncData` for SSR-safe data fetching
- [ ] Apply route rules for caching and rendering strategies
- [ ] Lazy load non-critical components with `Lazy` prefix
- [ ] Handle `status === 'pending'` for lazy data

### Performance Checklist
- [ ] Code-split heavy components with `lazy()` (React) or `Lazy` prefix (Nuxt)
- [ ] Virtualize long lists with @tanstack/react-virtual
- [ ] Lazy hydrate below-the-fold content
- [ ] Use Suspense boundaries strategically
- [ ] Analyze bundle size regularly

### Accessibility Checklist
- [ ] Implement keyboard navigation (Arrow keys, Enter, Escape)
- [ ] Manage focus for modals and dynamic content
- [ ] Use semantic HTML and ARIA attributes
- [ ] Test with screen readers

---

## React & Next.js Patterns

### Component Patterns

**Composition Over Inheritance**: Build flexible UIs by composing small, focused components. Use children props and component composition instead of inheritance hierarchies.

**Compound Components**: Create cohesive UI elements (Tabs, Accordion, Select) that share implicit state through Context. Consumers compose the parts without managing internal state.

**Render Props**: Pass a function as children to customize rendering behavior. Useful for data loaders, list renderers, and flexible UI patterns.

**Need Deep Knowledge?** See `$SKILL_DIR/references/react-patterns.md` for full code examples of composition, compound components, and render props.

### Custom Hooks

Common hooks to extract:

| Hook | Purpose |
|------|---------|
| `useToggle` | Boolean state with toggle function |
| `useDebounce` | Debounced value with delay |
| `useQuery` | Async data fetching with loading/error states |
| `useLocalStorage` | Persist state to localStorage |
| `useClickOutside` | Detect clicks outside an element |

**Need Deep Knowledge?** See `$SKILL_DIR/references/react-patterns.md` for hook implementations.

### State Management

**Local State**: `useState` for component-local state.
**Complex State**: `useReducer` for state machines and multi-field forms.
**Global State**: Context + Reducer pattern or Zustand for cross-cutting state.
**Server State**: SWR or React Query for cached server data.

**Context + Reducer Pattern**: Combine `useReducer` with Context for complex state that multiple components need. Provides dispatch function for predictable updates.

**Need Deep Knowledge?** See `$SKILL_DIR/references/react-patterns.md` for Context + Reducer implementation.

### Next.js & Turbopack

Next.js 16+ uses Turbopack by default for development. Key decisions:

| Scenario | Recommendation |
|----------|----------------|
| Day-to-day dev | Turbopack (default) - faster cold start and HMR |
| Webpack-only plugin | Use `--webpack` flag |
| Bundle optimization | Use Bundle Analyzer (Next.js 16.1+) |
| Production build | Check docs for your Next.js version |

**Cache Management**: Turbopack uses file-system caching under `.next`. Restarts reuse previous work (5-14x faster on large projects).

**Need Deep Knowledge?** See `$SKILL_DIR/references/nextjs-turbopack.md` for Turbopack defaults, cache management, and bundle analyzer usage.

---

## Vue & Nuxt Patterns

### Composables

Nuxt 4 composables for SSR-safe data fetching:

| Composable | Use Case |
|------------|----------|
| `useFetch` | Simple API reads - forwards SSR data to client payload |
| `useAsyncData` | Custom fetchers, multiple async sources, custom keys |
| `$fetch` | User-triggered writes, client-only actions |
| `useLazyFetch` | Non-blocking data with pending state |

**Key Rules**:
- Give `useAsyncData` a stable key for cache reuse
- Keep handlers side-effect free (run during SSR and hydration)
- Use `lazy: true` for non-critical data that shouldn't block navigation

### Route Rules

Configure rendering strategies in `nuxt.config.ts`:

| Rule | Effect |
|------|--------|
| `prerender: true` | Static HTML at build time |
| `swr: 3600` | Cached content, background revalidation |
| `isr: true` | Incremental static regeneration |
| `ssr: false` | Client-rendered route |
| `cache: { maxAge }` | Nitro-level response caching |

Pick rules per route group: marketing pages, catalogs, dashboards, and APIs need different strategies.

### Hydration Safety

**Common Mismatch Causes**:
- `Date.now()`, `Math.random()` in SSR templates
- Browser-only APIs during SSR
- Storage reads in template state
- `route.fullPath` for SSR markup (fragments are client-only)

**Solutions**:
- Move browser logic to `onMounted()`, `import.meta.client`, `ClientOnly`
- Use `ssr: false` as escape hatch, not default fix
- Use Nuxt's `useRoute()`, not vue-router's

### Lazy Loading

```vue
<template>
  <LazyRecommendations v-if="showRecommendations" />
  <LazyProductGallery hydrate-on-visible />
</template>
```

- Use `Lazy` prefix for dynamic imports
- Add `v-if` to prevent chunk load until needed
- Use `hydrate-on-visible` for below-the-fold content
- Use `defineLazyHydrationComponent()` for custom strategies

**Need Deep Knowledge?** See `$SKILL_DIR/references/nuxt4-patterns.md` for full composables, route rules, and lazy hydration examples.

---

## Performance Optimization

### Memoization Decision Guide

| Pattern | When to Use |
|---------|-------------|
| `useMemo` | Expensive computations dependent on deps |
| `useCallback` | Functions passed to memoized children |
| `React.memo` | Pure components receiving same props often |

### Code Splitting

**React**: Use `lazy()` + `Suspense` for heavy components (charts, 3D, editors).
**Nuxt**: Routes auto-split. Use `Lazy` prefix for non-route components.

### Virtualization

For lists >100 items, use virtualization to render only visible items:

**React**: `@tanstack/react-virtual` - `useVirtualizer` hook
**Vue**: `@tanstack/vue-virtual` or `vue-virtual-scroller`

---

## Form Handling

### Controlled Inputs Pattern

1. Store form data in state object
2. Validate on submit (or on change for real-time feedback)
3. Display errors adjacent to fields
4. Disable submit during submission

### Validation Libraries

| Library | Best For |
|---------|----------|
| Zod | Type-safe schemas, works with React Hook Form |
| Yup | Mature, wide ecosystem |
| Valibot | Tree-shakeable, smaller bundles |

---

## Error Boundary Pattern

React error boundaries catch JavaScript errors in component trees. Log errors and show fallback UI instead of crashing the whole app.

Key methods:
- `getDerivedStateFromError`: Update state to show fallback
- `componentDidCatch`: Log error details

Wrap critical sections with boundaries to isolate failures.

---

## Animation Patterns

### Framer Motion Quick Reference

| Animation Type | Key Props |
|----------------|-----------|
| Entry/Exit | `initial`, `animate`, `exit` |
| List items | `AnimatePresence` wrapper |
| Modal | Overlay fade + content scale/translate |
| Hover/Tap | `whileHover`, `whileTap` |

Keep animations subtle (200-300ms) for UI feedback.

---

## Accessibility Patterns

### Keyboard Navigation

| Key | Action |
|-----|--------|
| ArrowDown/Up | Navigate list items |
| Enter | Select item |
| Escape | Close dropdown/modal |
| Tab | Move focus |

Use `role` attributes (`combobox`, `listbox`, `dialog`) and `aria-expanded`, `aria-haspopup`.

### Focus Management

- Save `document.activeElement` before opening modals
- Focus modal on open, restore focus on close
- Trap focus within modals and dialogs
- Use `tabIndex={-1}` for programmatic focus

---

## Need Deep Knowledge?

| Topic | Reference |
|-------|-----------|
| React components, hooks, state | `$SKILL_DIR/references/react-patterns.md` |
| Next.js Turbopack configuration | `$SKILL_DIR/references/nextjs-turbopack.md` |
| Nuxt 4 composables, route rules | `$SKILL_DIR/references/nuxt4-patterns.md` |

---

**Remember**: Modern frontend patterns enable maintainable, performant user interfaces. Choose patterns that fit your project complexity.
