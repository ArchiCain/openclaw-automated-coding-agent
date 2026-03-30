# Projects Overview

All deployable services live under `projects/`, organized into three groups with a shared docs project.

```
projects/
├── application/         # Main product (K8s namespace: app)
│   ├── backend/
│   ├── frontend/
│   ├── database/
│   ├── keycloak/
│   └── e2e/
├── openclaw/            # Autonomous coding agent (K8s namespace: openclaw)
└── docs/                # This documentation site
```

Each project follows a consistent structure:

```
project-name/
├── app/              # Source code
├── dockerfiles/      # Container definitions (local + prod)
├── chart/            # Helm chart for K8s deployment
├── Taskfile.yml      # Project-level automation
└── README.md
```

## Application

The main product — a full-stack web application with AI features. Deployed to the `app` K8s namespace.

| Project | Stack | Purpose |
|---------|-------|---------|
| [Backend](application/backend.md) | NestJS 11 | REST API, WebSocket chat, database, AI agents, Keycloak auth |
| [Frontend](application/frontend.md) | React 19 + Vite 6 | Conversational AI UI, user management |
| [Database](application/database.md) | PostgreSQL 16 + pgvector | Shared database infrastructure |
| [Keycloak](application/keycloak.md) | Keycloak 23 | Authentication and authorization |
| [E2E Tests](application/e2e.md) | Playwright 1.48 | Browser-based end-to-end tests |

## OpenClaw

The autonomous coding agent. Deployed to the `openclaw` K8s namespace.

| Project | Stack | Purpose |
|---------|-------|---------|
| [OpenClaw Gateway](openclaw/overview.md) | OpenClaw + Claude Code ACP + Playwright | Autonomous agent with built-in Web UI, webhook receiver, cron jobs, and E2E testing |

Runtime data (agent configs, plans) lives in `.coding-agent-data/` at the repo root.

## Conventions

### Feature-based architecture

All application code lives inside `src/features/`. There are no separate `pages/` or `endpoints/` directories at the project root.

```
src/
└── features/
    ├── auth/            # Full feature: controllers + services + guards
    ├── user-dashboard/  # Full feature: pages + components + hooks
    └── api-client/      # Shared feature: reusable utilities
```

Features are either **full-stack** (with pages/endpoints, representing a complete user-facing capability) or **shared** (reusable utilities consumed by other features).

### NestJS module pattern

Every backend feature must have its own NestJS module. `app.module.ts` should only import feature modules:

```typescript
// Good
@Module({ imports: [HealthModule, AuthModule, UsersModule] })
export class AppModule {}

// Bad - never import controllers/services directly in app.module
@Module({ controllers: [HealthController] })
export class AppModule {}
```

### Naming conventions

- Directories: `kebab-case` (e.g., `user-dashboard`, `api-client`)
- Frontend pages: `*.page.tsx` (React) or standalone components (Angular)
- Backend controllers: `*.controller.ts`
- Tests: `*.spec.ts` (backend), `*.test.tsx` (frontend)
- Integration tests: `*.integration.spec.ts`
