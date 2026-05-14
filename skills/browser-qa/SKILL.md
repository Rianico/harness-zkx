---
name: browser-qa
description: Automates browser-based QA and post-deploy monitoring. Use for pre-deploy verification, ad-hoc testing, and sustained monitoring after deploys, merges, or dependency upgrades.
---

# Browser QA — Automated Testing & Monitoring

## When to Use

- After deploying to staging/preview/production
- Pre-deploy verification before shipping
- Post-deploy monitoring during launch windows
- After merging risky PRs or dependency upgrades
- Accessibility audits and responsive testing
- Comparing staging vs production for regressions

## Modes

### --once (default)

Single-pass ad-hoc verification. Runs all phases and reports.

```
/browser-qa https://myapp.com
/browser-qa https://myapp.com --once
```

### --watch

Sustained monitoring with interval and duration.

```
/browser-qa https://myapp.com --watch --interval 5m --duration 2h
```

### --compare

Diff mode: compare staging vs production for regressions.

```
/browser-qa --compare https://staging.myapp.com https://myapp.com
```

## What It Checks

**Ad-hoc (--once) phases:**
1. Smoke Test — console errors, network failures, Core Web Vitals
2. Interaction Test — nav links, forms, auth flows, critical journeys
3. Visual Regression — screenshots at 3 breakpoints, layout shift detection
4. Accessibility — axe-core scan, WCAG AA violations, keyboard nav

**Watch (--watch) monitors:**
- HTTP Status — is the page returning 200?
- Console Errors — new errors that weren't there before?
- Network Failures — failed API calls, 5xx responses?
- Performance — LCP/CLS/INP regression vs baseline?
- Content — did key elements disappear? (h1, nav, footer, CTA)
- API Health — are critical endpoints responding within SLA?

## Alert Thresholds

```yaml
critical:  # immediate alert
  - HTTP status != 200
  - Console error count > 5 (new errors only)
  - LCP > 4s
  - API endpoint returns 5xx

warning:   # flag in report
  - LCP increased > 500ms from baseline
  - CLS > 0.1
  - New console warnings
  - Response time > 2x baseline

info:      # log only
  - Minor performance variance
  - New network requests (third-party scripts added?)
```

## Notifications

When a critical threshold is crossed in watch mode:
- Desktop notification (macOS/Linux)
- Optional: Slack/Discord webhook
- Log to `~/.claude/browser-qa.log`

## Output Format

```markdown
## QA Report — myapp.com — 2026-05-14 10:30 PST

### Mode: --once

#### Smoke Test
- Console errors: 0 critical, 2 warnings (analytics noise)
- Network: all 200/304, no failures
- Core Web Vitals: LCP 1.2s, CLS 0.02, INP 89ms

#### Interactions
- [✓] Nav links: 12/12 working
- [✗] Contact form: missing error state for invalid email
- [✓] Auth flow: login/logout working

#### Accessibility
- 2 AA violations: missing alt text, low contrast footer links

### Verdict: SHIP WITH FIXES (2 issues, 0 blockers)
```

## Integration

**Browser MCP support:**
- `mChild__claude-in-chrome__*` tools (preferred)
- Playwright via `mcp__browserbase__*`
- Direct Puppeteer scripts

**Workflow pairing:**
- `/e2e-workflow` — structured E2E test generation
- `/click-path-audit` — user journey analysis

**Hooks:**
- Add as PostToolUse hook on `git push` to auto-check after deploys
- Run in CI after deploy step for automated monitoring
