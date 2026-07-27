---
name: sysops-expert
description: >-
  Systems operations for deployment/Docker/CI-CD/health checks/rollback/production readiness. TRIGGER: deploy, Docker/k8s/container, CI/CD/GitHub Actions/Jenkins, health/readiness/liveness probe, rollback, staging/production, DevOps/SRE, monitoring/observability, security hardening, resource limits
argument-hint: |-
  [deploy|docker|cicd|containers]
---

# SysOps Expert

Deployment, containerization, and infrastructure patterns for production-ready systems.

## When to Activate

- Setting up CI/CD pipelines
- Dockerizing applications or designing multi-container architectures
- Planning deployment strategy (rolling, blue-green, canary)
- Implementing health checks and readiness probes
- Preparing for production release
- Troubleshooting container networking or volume issues
- Reviewing Dockerfiles for security and size
- Configuring environment-specific settings

## Quick Actions & Checklists

### Production Deployment Checklist

- [ ] All tests pass (unit, integration, E2E)
- [ ] No hardcoded secrets in code or config files
- [ ] Docker image builds reproducibly (pinned versions)
- [ ] Environment variables validated at startup
- [ ] Health check endpoint returns meaningful status
- [ ] Resource limits set (CPU, memory)
- [ ] Rollback plan documented and tested
- [ ] Monitoring and alerts configured

### Docker Security Hardening

- [ ] Use specific version tags (never `:latest`)
- [ ] Run as non-root user
- [ ] Apply `no-new-privileges:true`
- [ ] Set `read_only: true` with tmpfs for writable paths
- [ ] Drop all capabilities, add only what's needed
- [ ] No secrets in image layers

### Container Debugging Quick Reference

```bash
docker compose logs -f app           # Follow app logs
docker compose exec app sh           # Shell into container
docker compose ps                    # Running services
docker compose up --build            # Rebuild and restart
docker compose down -v               # Stop and remove volumes
```

**Need Deep Knowledge?**
- Dockerfiles: `$SKILL_DIR/references/dockerfile-patterns.md`
- Docker Compose: `$SKILL_DIR/references/docker-compose-patterns.md`
- CI/CD Pipelines: `$SKILL_DIR/references/cicd-pipeline.md`
- Production Readiness: `$SKILL_DIR/references/production-checklist.md`

## Deployment Strategies

### Rolling Deployment (Default)

Replace instances gradually -- old and new versions run simultaneously during rollout.

```
Instance 1: v1 -> v2  (update first)
Instance 2: v1        (still running v1)
Instance 3: v1        (still running v1)
...
```

| | |
|---|---|
| **Pros** | Zero downtime, gradual rollout |
| **Cons** | Two versions run simultaneously -- requires backward-compatible changes |
| **Use when** | Standard deployments, backward-compatible changes |

### Blue-Green Deployment

Run two identical environments. Switch traffic atomically.

```
Blue  (v1) <- traffic
Green (v2)   idle, running new version

# After verification:
Blue  (v1)   idle (becomes standby)
Green (v2) <- traffic
```

| | |
|---|---|
| **Pros** | Instant rollback (switch back to blue), clean cutover |
| **Cons** | Requires 2x infrastructure during deployment |
| **Use when** | Critical services, zero-tolerance for issues |

### Canary Deployment

Route a small percentage of traffic to the new version first.

```
v1: 95% of traffic
v2:  5% of traffic  (canary)

# If metrics look good, gradually shift:
v1: 50% -> v2: 50% -> v2: 100%
```

| | |
|---|---|
| **Pros** | Catches issues with real traffic before full rollout |
| **Cons** | Requires traffic splitting infrastructure, monitoring |
| **Use when** | High-traffic services, risky changes, feature flags |

## Docker & Containers

### Multi-Stage Dockerfiles

Use multi-stage builds to minimize production image size. The dev stage enables hot reload; the production stage contains only runtime dependencies.

**Key Pattern:**

```dockerfile
# Stage: dependencies
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage: dev (hot reload, debug tools)
FROM node:22-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Stage: production (minimal image)
FROM node:22-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001
USER appuser
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
# ...
```

See `$SKILL_DIR/references/dockerfile-patterns.md` for complete Node.js, Go, and Python examples.

### Docker Compose for Local Development

Standard pattern for a web app with database and cache:

```yaml
services:
  app:
    build:
      context: .
      target: dev                     # Use dev stage
    volumes:
      - .:/app                        # Bind mount for hot reload
      - /app/node_modules             # Preserve container deps
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5

volumes:
  pgdata:
```

**Override Files:** Use `docker-compose.override.yml` (auto-loaded) for dev-only settings like debug ports. Use `docker-compose.prod.yml` for production resource limits.

See `$SKILL_DIR/references/docker-compose-patterns.md` for full stack examples, networking, and security hardening.

### Networking

Services in the same Compose network resolve by service name:

```
# From "app" container:
postgres://postgres:postgres@db:5432/app_dev    # "db" resolves to db container
```

**Custom Networks:** Isolate services that shouldn't communicate directly (e.g., frontend can't reach db).

**Exposing Ports:**
- `"3000:3000"` -- accessible from anywhere
- `"127.0.0.1:5432:5432"` -- only from host
- Omit `ports` entirely -- only accessible within Docker network

### Volume Strategies

| Type | Use Case |
|------|----------|
| **Named volume** | Persistent data (database files) -- managed by Docker |
| **Bind mount** | Source code for hot reload -- maps host directory |
| **Anonymous volume** | Preserve container content from bind mount override (e.g., `/app/node_modules`) |

### Security Hardening

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /app/.cache
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE          # Only if binding to ports < 1024
```

## CI/CD

### Pipeline Stages

```
PR opened:
  lint -> typecheck -> unit tests -> integration tests -> preview deploy

Merged to main:
  lint -> typecheck -> unit tests -> integration tests -> build image -> deploy staging -> smoke tests -> deploy production
```

See `$SKILL_DIR/references/cicd-pipeline.md` for complete GitHub Actions workflow and common patterns.

## Health Checks & Probes

### Application Health Endpoint

```typescript
// Simple check
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

// Detailed check (for internal monitoring)
app.get("/health/detailed", async (req, res) => {
  const checks = {
    database: await checkDatabase(),
    redis: await checkRedis(),
  };
  const allHealthy = Object.values(checks).every(c => c.status === "ok");
  res.status(allHealthy ? 200 : 503).json({ status: allHealthy ? "ok" : "degraded", checks });
});
```

### Kubernetes Probes

| Probe | Purpose |
|-------|---------|
| **liveness** | Restart container if unhealthy |
| **readiness** | Remove from service if not ready |
| **startup** | Allow slow startup before liveness checks |

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 30
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 10

startupProbe:
  httpGet:
    path: /health
    port: 3000
  periodSeconds: 5
  failureThreshold: 30    # 150s max startup time
```

## Production Readiness

### Environment Configuration

**Twelve-Factor Pattern:** All config via environment variables, never in code.

```bash
DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
API_KEY=${API_KEY}           # injected by secrets manager
```

**Validation:** Fail fast at startup if config is missing or invalid.

### Rollback Strategy

```bash
# Kubernetes
kubectl rollout undo deployment/app

# Vercel
vercel rollback

# Railway
railway up --commit <previous-sha>
```

**Rollback Checklist:**
- Previous image/artifact is available and tagged
- Database migrations are backward-compatible (no destructive changes)
- Feature flags can disable new features without deploy
- Rollback tested in staging before production release

See `$SKILL_DIR/references/production-checklist.md` for the complete checklist.
