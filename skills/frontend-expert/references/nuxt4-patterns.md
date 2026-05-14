# Nuxt 4 Patterns Reference

Detailed patterns for Nuxt 4 composables, route rules, lazy hydration, and SSR data fetching.

## When to Activate

- Hydration mismatches between server HTML and client state
- Route-level rendering decisions (prerender, SWR, ISR, client-only)
- Performance work around lazy loading, lazy hydration, payload size
- Page or component data fetching with `useFetch`, `useAsyncData`, `$fetch`
- Nuxt routing issues tied to route params, middleware, SSR/client differences

---

## Hydration Safety

### Common Mismatch Causes

| Cause | Solution |
|-------|----------|
| `Date.now()` in SSR template | Move to `onMounted()` or `import.meta.client` |
| `Math.random()` in SSR | Use deterministic seed or client-only |
| Browser-only APIs during SSR | Wrap in `ClientOnly` or `.client.vue` |
| Storage reads in template state | Use `useState` with client-only initialization |
| `route.fullPath` for SSR markup | Fragments are client-only; use `route.path` |

### Solutions

**Move browser logic to client-only context:**

```vue
<script setup>
// ✅ Correct: client-only logic
onMounted(() => {
  const stored = localStorage.getItem('preference')
  if (stored) preference.value = stored
})

// ✅ Correct: conditional rendering
const isClient = ref(false)
onMounted(() => isClient.value = true)
</script>

<template>
  <ClientOnly>
    <BrowserOnlyComponent />
  </ClientOnly>
</template>
```

**Use Nuxt's composables correctly:**

```typescript
// ✅ Correct: Nuxt's useRoute
const route = useRoute()

// ❌ Wrong: vue-router's useRoute
import { useRoute } from 'vue-router'  // Don't do this
```

**Escape hatch for truly browser-only areas:**

```vue
<!-- .client.vue suffix makes component client-only -->
<!-- components/Chart.client.vue -->
```

---

## Data Fetching

### useFetch vs useAsyncData

| Composable | Use Case |
|------------|----------|
| `useFetch` | Simple API reads - forwards SSR data to client payload |
| `useAsyncData` | Custom fetchers, multiple async sources, custom keys |
| `$fetch` | User-triggered writes, client-only actions |
| `useLazyFetch` | Non-blocking data with pending state |

### useFetch Example

```typescript
const route = useRoute()

const { data: article, status, error, refresh } = await useFetch(
  `/api/articles/${route.params.slug}`
)

// With options
const { data: comments } = await useFetch(
  `/api/articles/${route.params.slug}/comments`,
  {
    lazy: true,      // Non-blocking navigation
    server: false,   // Client-only fetch
    pick: ['id', 'author', 'content'],  // Trim payload
  }
)
```

### useAsyncData Example

```typescript
const route = useRoute()

// Custom key for cache reuse
const { data: article } = await useAsyncData(
  () => `article:${route.params.slug}`,
  () => $fetch(`/api/articles/${route.params.slug}`),
  {
    // Options
  }
)

// Multiple async sources
const { data: combined } = await useAsyncData(
  'combined-data',
  async () => {
    const [user, settings] = await Promise.all([
      $fetch('/api/user'),
      $fetch('/api/settings')
    ])
    return { user, settings }
  }
)
```

### Key Rules

1. **Give useAsyncData a stable key** for cache reuse and predictable refresh
2. **Keep handlers side-effect free** - they run during SSR and hydration
3. **Use `lazy: true`** for non-critical data that shouldn't block navigation
4. **Handle `status === 'pending'`** in the UI for lazy data
5. **Use `server: false`** only for data not needed for SEO or first paint

### When to Use $fetch

```typescript
// ✅ Correct: user-triggered actions
const handleSubmit = async () => {
  await $fetch('/api/submit', {
    method: 'POST',
    body: formData
  })
}

// ❌ Wrong: top-level page data
// This won't be SSR-friendly
const data = await $fetch('/api/data')  // Don't do this at page level
```

---

## Route Rules

### Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Static HTML at build time
    '/': { prerender: true },
    
    // Cached content with background revalidation
    '/products/**': { swr: 3600 },  // 1 hour
    
    // Incremental static regeneration
    '/blog/**': { isr: true },
    
    // Client-rendered route
    '/admin/**': { ssr: false },
    
    // API caching
    '/api/**': { cache: { maxAge: 60 * 60 } },
    
    // Redirects
    '/old-page': { redirect: '/new-page' },
  },
})
```

### Rule Types

| Rule | Effect | Use Case |
|------|--------|----------|
| `prerender: true` | Static HTML at build time | Marketing pages, docs |
| `swr: seconds` | Cached + background revalidation | Product catalogs, listings |
| `isr: true` | Incremental static regeneration | Blogs, news sites |
| `ssr: false` | Client-rendered route | Dashboards, admin panels |
| `cache: { maxAge }` | Nitro-level response caching | API endpoints |
| `redirect: '/path'` | HTTP redirect | Legacy URL migration |

### Strategy Selection

| Page Type | Recommended Rule |
|-----------|------------------|
| Marketing home | `prerender: true` |
| Product catalog | `swr: 3600` (1 hour) |
| Blog posts | `isr: true` |
| User dashboard | `ssr: false` |
| Public API | `cache: { maxAge: 3600 }` |

---

## Lazy Loading and Performance

### Lazy Components

```vue
<template>
  <!-- Lazy prefix for dynamic import -->
  <LazyRecommendations v-if="showRecommendations" />
  
  <!-- Conditional loading -->
  <LazyHeavyChart 
    v-if="showChart" 
    hydrate-on-visible 
  />
</template>

<script setup>
// Lazy components are loaded only when rendered
const showRecommendations = ref(false)
const showChart = ref(false)
</script>
```

### Lazy Hydration Strategies

```vue
<template>
  <!-- Hydrate when visible -->
  <LazyProductGallery hydrate-on-visible />
  
  <!-- Hydrate on interaction -->
  <LazyComments hydrate-on-interaction />
  
  <!-- Hydrate when idle -->
  <LazyNewsletter hydrate-on-idle />
</template>
```

### Custom Lazy Hydration

```typescript
// Define custom hydration trigger
const LazyChat = defineLazyHydrationComponent({
  name: 'ChatWidget',
  trigger: 'visible',  // or 'interaction', 'idle', or custom function
})
```

### Performance Best Practices

1. **Nuxt auto-splits pages by route** - keep route boundaries meaningful
2. **Use `Lazy` prefix** for non-critical components
3. **Add `v-if`** to prevent chunk load until needed
4. **Use `hydrate-on-visible`** for below-the-fold content
5. **Passing new props triggers immediate hydration** - be aware of reactivity
6. **Use `NuxtLink`** for internal navigation (enables prefetching)

---

## Review Checklist

- [ ] First SSR render and hydrated client render produce the same markup
- [ ] Page data uses `useFetch` or `useAsyncData`, not top-level `$fetch`
- [ ] Non-critical data is lazy and has explicit loading UI
- [ ] Route rules match the page's SEO and freshness requirements
- [ ] Heavy interactive islands are lazy-loaded or lazily hydrated
- [ ] Browser-only logic is in `onMounted`, `ClientOnly`, or `.client.vue`
- [ ] `useAsyncData` has stable keys for cache reuse
- [ ] Payload size is trimmed with `pick` when appropriate
