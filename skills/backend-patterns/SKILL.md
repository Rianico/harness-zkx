---
name: backend-patterns
description: >-
  Backend architecture and API design patterns — REST/GraphQL,
  database optimization (N+1, indexing), caching (Redis), auth
  (JWT/OAuth/sessions), background jobs, middleware, rate limiting,
  versioning. TRIGGER: API design, endpoint, database query, SQL,
  cache, Redis, rate limit, JWT.
---

# Backend Development Patterns

Backend architecture patterns and API design conventions for scalable server-side applications.

## When to Activate

- Designing REST or GraphQL API endpoints
- Implementing repository, service, or controller layers
- Optimizing database queries (N+1, indexing, connection pooling)
- Adding caching (Redis, in-memory, HTTP cache headers)
- Setting up background jobs or async processing
- Structuring error handling and validation
- Building middleware (auth, logging, rate limiting)
- Planning API versioning strategy
- Adding pagination, filtering, or sorting

## API Resource Design

### URL Structure

```
# Resources are nouns, plural, lowercase, kebab-case
GET    /api/v1/users
GET    /api/v1/users/:id
POST   /api/v1/users
PUT    /api/v1/users/:id
PATCH  /api/v1/users/:id
DELETE /api/v1/users/:id

# Sub-resources for relationships
GET    /api/v1/users/:id/orders
POST   /api/v1/users/:id/orders

# Actions that don't map to CRUD (use verbs sparingly)
POST   /api/v1/orders/:id/cancel
POST   /api/v1/auth/login
```

### Naming Rules

```
# GOOD
/api/v1/team-members          # kebab-case for multi-word resources
/api/v1/orders?status=active  # query params for filtering
/api/v1/users/123/orders      # nested resources for ownership

# BAD
/api/v1/getUsers              # verb in URL
/api/v1/user                  # singular (use plural)
/api/v1/team_members          # snake_case in URLs
```

## HTTP Methods and Status Codes

### Method Semantics

| Method | Idempotent | Safe | Use For |
|--------|-----------|------|---------|
| GET | Yes | Yes | Retrieve resources |
| POST | No | No | Create resources, trigger actions |
| PUT | Yes | No | Full replacement of a resource |
| PATCH | No* | No | Partial update of a resource |
| DELETE | Yes | No | Remove a resource |

### Status Code Reference

```
# Success
200 OK                    - GET, PUT, PATCH (with response body)
201 Created               - POST (include Location header)
204 No Content            - DELETE, PUT (no response body)

# Client Errors
400 Bad Request           - Validation failure, malformed JSON
401 Unauthorized          - Missing or invalid authentication
403 Forbidden             - Authenticated but not authorized
404 Not Found             - Resource doesn't exist
409 Conflict              - Duplicate entry, state conflict
422 Unprocessable Entity  - Semantically invalid (valid JSON, bad data)
429 Too Many Requests     - Rate limit exceeded

# Server Errors
500 Internal Server Error - Unexpected failure (never expose details)
502 Bad Gateway           - Upstream service failed
503 Service Unavailable   - Temporary overload, include Retry-After
```

### Common Mistakes

```
# BAD: 200 for everything
{ "status": 200, "success": false, "error": "Not found" }

# GOOD: Use HTTP status codes semantically
HTTP/1.1 404 Not Found
{ "error": { "code": "not_found", "message": "User not found" } }
```

## Response Format

### Success Response

```json
{
  "data": {
    "id": "abc-123",
    "email": "alice@example.com",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      { "field": "email", "message": "Invalid email", "code": "invalid_format" }
    ]
  }
}
```

For collection responses with pagination and envelope variants, see `$SKILL_DIR/references/pagination-filtering-patterns.md`.

## Pagination

### Offset vs Cursor

| Use Case | Pagination Type |
|----------|----------------|
| Admin dashboards, small datasets (<10K) | Offset |
| Infinite scroll, feeds, large datasets | Cursor |
| Public APIs | Cursor (default) with offset (optional) |
| Search results | Offset (users expect page numbers) |

**Offset:** Easy to implement, supports "jump to page N". Slow on large offsets.

**Cursor:** Consistent performance, stable with concurrent inserts. Cannot jump to arbitrary page.

For detailed implementation patterns, see `$SKILL_DIR/references/pagination-filtering-patterns.md`.

## Filtering, Sorting, Search

```
# Simple equality
GET /api/v1/orders?status=active&customer_id=abc-123

# Comparison operators
GET /api/v1/products?price[gte]=10&price[lte]=100

# Multiple values (comma-separated)
GET /api/v1/products?category=electronics,clothing

# Sorting (prefix - for descending)
GET /api/v1/products?sort=-created_at
GET /api/v1/products?sort=-featured,price

# Full-text search
GET /api/v1/products?q=wireless+headphones

# Sparse fieldsets
GET /api/v1/users?fields=id,name,email
```

## Authentication

### Token-Based Auth

```
# Bearer token
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# API key (server-to-server)
X-API-Key: sk_live_abc123
```

### Authorization Patterns

```typescript
// Resource-level: check ownership
if (order.userId !== req.user.id) {
  return res.status(403).json({ error: { code: "forbidden" } });
}

// Role-based: check permissions
app.delete("/api/v1/users/:id", requireRole("admin"), handler);
```

For JWT validation and RBAC implementation, see `$SKILL_DIR/references/backend-architecture-examples.md`.

## Rate Limiting

### Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000

# When exceeded
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

### Rate Limit Tiers

| Tier | Limit | Window | Use Case |
|------|-------|--------|----------|
| Anonymous | 30/min | Per IP | Public endpoints |
| Authenticated | 100/min | Per user | Standard API access |
| Premium | 1000/min | Per API key | Paid API plans |
| Internal | 10000/min | Per service | Service-to-service |

For in-memory rate limiter implementation, see `$SKILL_DIR/references/backend-architecture-examples.md`.

## API Versioning

### Strategy

```
1. Start with /api/v1/ - don't version until needed
2. Maintain at most 2 active versions (current + previous)
3. Deprecation timeline:
   - Announce deprecation (6 months notice for public APIs)
   - Add Sunset header: Sunset: Sat, 01 Jan 2026 00:00:00 GMT
   - Return 410 Gone after sunset date
4. Non-breaking changes don't need a new version:
   - Adding new fields to responses
   - Adding new optional query parameters
   - Adding new endpoints
5. Breaking changes require a new version:
   - Removing or renaming fields
   - Changing field types
   - Changing URL structure
   - Changing authentication method
```

### URL Path Versioning (Recommended)

```
/api/v1/users
/api/v2/users
```

Explicit, easy to route, cacheable.

## Repository Pattern

Abstract data access logic behind interfaces for testability and flexibility.

```typescript
interface MarketRepository {
  findAll(filters?: MarketFilters): Promise<Market[]>
  findById(id: string): Promise<Market | null>
  create(data: CreateMarketDto): Promise<Market>
  update(id: string, data: UpdateMarketDto): Promise<Market>
  delete(id: string): Promise<void>
}
```

For full implementation examples, see `$SKILL_DIR/references/api-implementation-examples.md`.

## Service Layer Pattern

Business logic separated from data access. Services coordinate between repositories, external APIs, and business rules.

```typescript
class MarketService {
  constructor(private marketRepo: MarketRepository) {}

  async searchMarkets(query: string, limit: number = 10): Promise<Market[]> {
    const embedding = await generateEmbedding(query)
    const results = await this.vectorSearch(embedding, limit)
    return this.marketRepo.findByIds(results.map(r => r.id))
  }
}
```

## Database Patterns

### Query Optimization

```typescript
// GOOD: Select only needed columns
.select('id, name, status, volume')

// BAD: Select everything
.select('*')
```

### N+1 Prevention

```typescript
// BAD: N queries in loop
for (const market of markets) {
  market.creator = await getUser(market.creator_id)
}

// GOOD: Batch fetch with single query
const creators = await getUsers(markets.map(m => m.creator_id))
const creatorMap = new Map(creators.map(c => [c.id, c]))
markets.forEach(m => m.creator = creatorMap.get(m.creator_id))
```

For transaction patterns, see `$SKILL_DIR/references/backend-architecture-examples.md`.

## Caching Strategies

### When to Cache

- Frequently read, rarely updated data
- Expensive computations or queries
- External API responses with stable results

### Cache Invalidation

- Write-through: Update cache on write
- Cache-aside: Lazy load on read miss
- TTL-based: Expire after time period

For Redis caching and cache-aside implementations, see `$SKILL_DIR/references/backend-architecture-examples.md`.

## Error Handling

### Principles

1. Use HTTP status codes semantically
2. Return structured error responses with codes
3. Never expose internal details (stack traces, SQL errors)
4. Log errors with context for debugging

For centralized error handler and retry patterns, see `$SKILL_DIR/references/backend-architecture-examples.md`.

## Background Jobs

Use queues for operations that don't need immediate response:

- Email sending
- Report generation
- Data processing
- Webhook delivery

For simple queue pattern implementation, see `$SKILL_DIR/references/backend-architecture-examples.md`.

## Logging

### Structured Logging

```typescript
logger.info('Fetching markets', {
  requestId,
  method: 'GET',
  path: '/api/markets'
})
```

Log in JSON format for parsing and aggregation. Include request IDs for tracing.

For full logging implementation, see `$SKILL_DIR/references/backend-architecture-examples.md`.

## API Design Checklist

Before shipping a new endpoint:

- [ ] Resource URL follows naming conventions (plural, kebab-case, no verbs)
- [ ] Correct HTTP method used (GET for reads, POST for creates, etc.)
- [ ] Appropriate status codes returned (not 200 for everything)
- [ ] Input validated with schema (Zod, Pydantic, Bean Validation)
- [ ] Error responses follow standard format with codes and messages
- [ ] Pagination implemented for list endpoints (cursor or offset)
- [ ] Authentication required (or explicitly marked as public)
- [ ] Authorization checked (user can only access their own resources)
- [ ] Rate limiting configured
- [ ] Response does not leak internal details
- [ ] Consistent naming with existing endpoints
- [ ] Documented (OpenAPI/Swagger spec updated)

## Reference Files

- `$SKILL_DIR/references/api-implementation-examples.md` - TypeScript, Python, Go implementations
- `$SKILL_DIR/references/pagination-filtering-patterns.md` - Detailed pagination and filtering patterns
- `$SKILL_DIR/references/backend-architecture-examples.md` - Caching, auth, logging, jobs, error handling
