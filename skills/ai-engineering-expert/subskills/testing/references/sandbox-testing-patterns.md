# Testing Patterns for AI-Assisted Development

Testing specifically designed for AI-generated code, where the same model writes and reviews — creating systematic blind spots.

## The Core Problem

```
AI writes fix  →  AI reviews fix  →  AI says "looks correct"  →  Bug still exists
```

When an AI writes code and then reviews its own work, it carries the same assumptions into both steps. This creates predictable failure patterns that only automated tests can catch.

### Real-World Example

```
Fix 1: Added notification_settings to API response
  → Forgot to add it to SELECT query
  → AI reviewed and missed (same blind spot)

Fix 2: Added it to SELECT query
  → TypeScript build error (column not in generated types)
  → AI reviewed Fix 1 but didn't catch SELECT issue

Fix 3: Changed to SELECT *
  → Fixed production path, forgot sandbox path
  → AI reviewed and missed it AGAIN (4th occurrence)

Fix 4: Test caught it instantly on first run
```

The #1 AI-introduced regression: **sandbox/production path inconsistency**.

## Sandbox-Mode API Testing

Most AI-friendly projects have a sandbox/mock mode. This enables fast, DB-free API testing.

### Setup (Vitest + Next.js App Router)

**vitest.config.ts**
```typescript
import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    include: ["__tests__/**/*.test.ts"],
    setupFiles: ["__tests__/setup.ts"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
```

**__tests__/setup.ts**
```typescript
// Force sandbox mode — no database needed
process.env.SANDBOX_MODE = "true";
process.env.NEXT_PUBLIC_SUPABASE_URL = "";
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "";
```

### Test Helper

```typescript
// __tests__/helpers.ts
import { NextRequest } from "next/server";

export function createTestRequest(
  url: string,
  options?: {
    method?: string;
    body?: Record<string, unknown>;
    headers?: Record<string, string>;
    sandboxUserId?: string;
  },
): NextRequest {
  const { method = "GET", body, headers = {}, sandboxUserId } = options || {};
  const fullUrl = url.startsWith("http") ? url : `http://localhost:3000${url}`;
  const reqHeaders: Record<string, string> = { ...headers };

  if (sandboxUserId) {
    reqHeaders["x-sandbox-user-id"] = sandboxUserId;
  }

  const init: { method: string; headers: Record<string, string>; body?: string } = {
    method,
    headers: reqHeaders,
  };

  if (body) {
    init.body = JSON.stringify(body);
    reqHeaders["content-type"] = "application/json";
  }

  return new NextRequest(fullUrl, init);
}

export async function parseResponse(response: Response) {
  const json = await response.json();
  return { status: response.status, json };
}
```

### Writing Regression Tests

**Principle:** Write tests for bugs that were found, not for code that works.

```typescript
// __tests__/api/user/profile.test.ts
import { describe, it, expect } from "vitest";
import { createTestRequest, parseResponse } from "../../helpers";
import { GET, PATCH } from "@/app/api/user/profile/route";

// Define the contract — what fields MUST be in response
const REQUIRED_FIELDS = [
  "id", "email", "full_name", "phone", "role",
  "created_at", "avatar_url", "notification_settings",
];

describe("GET /api/user/profile", () => {
  it("returns all required fields", async () => {
    const req = createTestRequest("/api/user/profile");
    const res = await GET(req);
    const { status, json } = await parseResponse(res);

    expect(status).toBe(200);
    for (const field of REQUIRED_FIELDS) {
      expect(json.data).toHaveProperty(field);
    }
  });

  // Regression test — this exact bug was introduced 4 times
  it("notification_settings is not undefined (BUG-R1 regression)", async () => {
    const req = createTestRequest("/api/user/profile");
    const res = await GET(req);
    const { json } = await parseResponse(res);

    expect("notification_settings" in json.data).toBe(true);
    const ns = json.data.notification_settings;
    expect(ns === null || typeof ns === "object").toBe(true);
  });
});
```

## Common AI Regression Patterns

### Pattern 1: Sandbox/Production Path Mismatch

**Frequency:** Most common (observed in 3 of 4 regressions)

```typescript
// BAD: AI adds field to production path only
if (isSandboxMode()) {
  return { data: { id, email, name } };  // Missing new field
}
// Production path
return { data: { id, email, name, notification_settings } };

// GOOD: Both paths return same shape
if (isSandboxMode()) {
  return { data: { id, email, name, notification_settings: null } };
}
return { data: { id, email, name, notification_settings } };
```

**Test to catch:**
```typescript
it("sandbox and production return same fields", async () => {
  const res = await GET(createTestRequest("/api/user/profile"));
  const { json } = await parseResponse(res);

  for (const field of REQUIRED_FIELDS) {
    expect(json.data).toHaveProperty(field);
  }
});
```

### Pattern 2: SELECT Clause Omission

**Frequency:** Common with Supabase/Prisma when adding columns

```typescript
// BAD: New column added to response but not SELECT
const { data } = await supabase
  .from("users")
  .select("id, email, name")  // notification_settings missing
  .single();

return { data: { ...data, notification_settings: data.notification_settings } };
// → notification_settings always undefined

// GOOD: Use SELECT * or explicitly include
const { data } = await supabase.from("users").select("*").single();
```

### Pattern 3: Error State Leakage

```typescript
// BAD: Error state set but old data not cleared
catch (err) {
  setError("Failed to load");
  // reservations still shows data from previous tab!
}

// GOOD: Clear related state on error
catch (err) {
  setReservations([]);  // Clear stale data
  setError("Failed to load");
}
```

### Pattern 4: Optimistic Update Without Rollback

```typescript
// BAD: No rollback on failure
const handleRemove = async (id: string) => {
  setItems(prev => prev.filter(i => i.id !== id));
  await fetch(`/api/items/${id}`, { method: "DELETE" });
  // If API fails, item is gone from UI but still in DB
};

// GOOD: Capture previous state and rollback
const handleRemove = async (id: string) => {
  const prevItems = [...items];
  setItems(prev => prev.filter(i => i.id !== id));
  try {
    const res = await fetch(`/api/items/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("API error");
  } catch {
    setItems(prevItems);  // Rollback
    alert("Failed to remove");
  }
};
```

## Strategy: Test Where Bugs Were Found

Don't aim for 100% coverage. Instead:

```
Bug found in /api/user/profile   → Write test for profile API
Bug found in /api/user/messages  → Write test for messages API
Bug found in /api/user/favorites → Write test for favorites API
No bug in /api/notifications     → Don't write test (yet)
```

**Why this works with AI:**

1. AI makes the **same category of mistake** repeatedly
2. Bugs cluster in complex areas (auth, multi-path logic, state)
3. Once tested, that regression **cannot happen again**
4. Tests grow organically with bug fixes

## Quick Reference Table

| AI Regression Pattern | Test Strategy | Priority |
|-----------------------|---------------|----------|
| Sandbox/production mismatch | Assert same response shape in sandbox | High |
| SELECT clause omission | Assert all required fields in response | High |
| Error state leakage | Assert state cleanup on error | Medium |
| Missing rollback | Assert state restored on failure | Medium |
| Type cast masking null | Assert field is not undefined | Medium |

## DO / DON'T

**DO:**
- Write tests immediately after finding a bug
- Test the API response shape, not implementation
- Run tests as the first step of every bug-check
- Keep tests fast (< 1 second total with sandbox)
- Name tests after the bug: "BUG-R1 regression"

**DON'T:**
- Write tests for code that has never had a bug
- Trust AI self-review as substitute for automated tests
- Skip sandbox path testing because "it's just mock data"
- Write integration tests when unit tests suffice
- Aim for coverage percentage — aim for regression prevention

## Integrating into Bug-Check Workflow

```markdown
<!-- .claude/commands/bug-check.md -->
## Step 1: Automated Tests (mandatory, cannot skip)

Run FIRST before any code review:
    npm run test       # Vitest suite
    npm run build      # TypeScript check

- If tests fail → highest priority bug
- If build fails → highest priority error
- Only proceed to Step 2 if both pass

## Step 2: Code Review (AI review)

1. Sandbox/production path consistency
2. API response shape matches frontend
3. SELECT clause completeness
4. Error handling with rollback
5. Optimistic update race conditions

## Step 3: For each bug fixed, propose a regression test
```

---

## Summary Checklist

After fixing a bug:
- [ ] Test written before or alongside fix
- [ ] Test named after the bug ("BUG-X regression")
- [ ] Test runs fast (sandbox mode, no DB)
- [ ] Test would have caught the original bug
- [ ] Test added to bug-check workflow
