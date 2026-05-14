# Next.js Turbopack Reference

Next.js 16+ Turbopack configuration, caching, and bundle optimization.

## Overview

Next.js 16+ uses Turbopack by default for local development: an incremental bundler written in Rust that significantly speeds up dev startup and hot updates.

## When to Use Turbopack vs Webpack

| Scenario | Recommendation |
|----------|----------------|
| Day-to-day development | Turbopack (default) - faster cold start and HMR |
| Webpack-only plugin needed | Use `--webpack` flag (or `--no-turbopack` depending on version) |
| Hitting a Turbopack bug | Switch to webpack temporarily, report issue |
| Production build | Check official Next.js docs for your version |

## How It Works

- **Turbopack**: Incremental bundler for Next.js dev. Uses file-system caching so restarts are much faster (5-14x on large projects).
- **Default in dev**: From Next.js 16, `next dev` runs with Turbopack unless disabled.
- **File-system caching**: Restarts reuse previous work; cache is typically under `.next`; no extra config needed for basic use.
- **Bundle Analyzer (Next.js 16.1+)**: Experimental Bundle Analyzer to inspect output and find heavy dependencies; enable via config or experimental flag.

## Commands

```bash
# Development with Turbopack (default in Next.js 16+)
next dev

# Development with webpack (if needed)
next dev --webpack

# Production build
next build

# Start production server
next start
```

## Cache Management

### Cache Location

Turbopack stores its cache in the `.next` directory by default. This cache enables:

- **Fast restarts**: Reuse compiled modules from previous sessions
- **Incremental compilation**: Only recompile changed files
- **HMR speed**: Faster hot module replacement

### Cache Clearing

If you encounter issues that might be cache-related:

```bash
# Clear Next.js cache
rm -rf .next

# Or more targeted
rm -rf .next/cache
```

### When to Clear Cache

- Build errors after dependency updates
- Stale module issues
- HMR not picking up changes
- After major refactors

## Bundle Analyzer

### Enabling Bundle Analyzer (Next.js 16.1+)

Bundle Analyzer helps identify large dependencies and optimize code splitting.

```javascript
// next.config.js
module.exports = {
  experimental: {
    bundleAnalyzer: {
      enabled: true,
    },
  },
}
```

### Analyzing Bundle Size

1. Run build with analyzer enabled
2. Open the generated report in browser
3. Identify large chunks and dependencies
4. Optimize by:
   - Code splitting large components
   - Replacing heavy libraries with lighter alternatives
   - Lazy loading non-critical features

## Best Practices

### Development Performance

1. **Stay on recent Next.js 16.x** for stable Turbopack and caching behavior
2. **Verify Turbopack is active** - check dev output for "Using Turbopack"
3. **Avoid clearing cache unnecessarily** - let Turbopack manage it
4. **Report Turbopack bugs** - helps improve the tooling

### Production Optimization

1. **Use bundle analysis tooling** for your Next.js version
2. **Prefer App Router** and server components where possible
3. **Implement strategic code splitting** for heavy client components
4. **Monitor bundle size changes** in CI/CD

### Troubleshooting Slow Dev

1. Confirm Turbopack is active (check console output)
2. Verify cache isn't being cleared by:
   - Git hooks
   - Docker volume issues
   - CI/CD cache invalidation
3. Check for webpack-only plugins forcing fallback
4. Report persistent issues to Next.js team

## Migration Notes

### From Webpack to Turbopack

- Most projects work without changes
- Custom webpack configs may need adjustment
- Some webpack plugins don't have Turbopack equivalents
- Test thoroughly before relying on Turbopack in production

### Backward Compatibility

- `--webpack` flag available for projects that need webpack
- Check Next.js docs for version-specific behavior
- Monitor deprecation notices in release notes
