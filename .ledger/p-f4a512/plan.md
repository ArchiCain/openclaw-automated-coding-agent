---
id: p-f4a512
created: 2026-03-30T03:37:00.000Z
updated: 2026-03-30T03:37:00.000Z
---

# FastAPI Python Backend

## Problem Statement

The application currently has a single backend written in NestJS (TypeScript). We want to add a second backend that is functionally identical, written in Python using FastAPI. This will allow comparing backend implementations and exploring Python-based AI tooling. The existing NestJS backend must not be modified. The Angular frontend needs a toggle in the header to switch between backends at runtime.

## Requirements

### Functional

- All existing REST endpoints replicated exactly:
  - `GET /health`
  - `POST /auth/login`, `POST /auth/logout`, `POST /auth/check`, `POST /auth/refresh`
  - `GET /users`, `POST /users`, `GET /users/:id`, `PATCH /users/:id`, `DELETE /users/:id`
  - `GET /users/me/preferences` (theme preferences)
  - `PATCH /users/me/preferences`
- Cookie-based authentication via Keycloak (same flow as NestJS backend)
- WebSocket support for chat via Socket.IO or WebSocket (same `/mastra-chat` and `/mastra-chat-history` namespaces)
- Mastra agent integration (Anthropic/OpenAI AI agents, same as NestJS)
- Same CORS configuration (environment-based allowed origins)
- Same health check response format
- Same JWT/cookie auth flow with Keycloak

### Frontend Toggle

- A "Backend Selector" toggle/menu added to the Angular app header (AppHeaderComponent)
- Options: "NestJS" (default) and "FastAPI"
- Selection is persisted in localStorage
- Angular's `api-client` / HTTP calls use the selected backend URL
- Toggle is visible only in development/debug mode or always (operator decision — default: always visible)

### Non-Functional

- Python 3.12+
- FastAPI with uvicorn
- SQLAlchemy 2.0 + asyncpg for async PostgreSQL (same database schema, same tables)
- python-keycloak or httpx for Keycloak admin calls
- python-socketio for WebSocket/Socket.IO
- Pydantic v2 for request/response models
- Alembic for migrations (shares migration history with NestJS backend via same DB)
- pytest + httpx for tests (80% coverage target matching NestJS)
- Docker multi-stage build (same pattern as NestJS)
- Helm chart for K8s deployment (same structure as backend chart)
- Environment variable parity with NestJS backend
- Runs on port 8080 (same as NestJS, different K8s service)

## Architecture

### Projects Affected

- `projects/application/backend-python/` — new project (FastAPI)
- `projects/application/frontend/` — add backend toggle to header
- `infrastructure/k8s/` — add Helmfile release for backend-python
- `infrastructure/docker/` — add backend-python service to compose

### Project Structure

```
projects/application/backend-python/
├── app/
│   ├── main.py                    # FastAPI app factory, middleware, lifespan
│   ├── config.py                  # Settings from env vars (pydantic-settings)
│   ├── features/
│   │   ├── health/                # GET /health
│   │   ├── auth/                  # Cookie-based Keycloak auth endpoints
│   │   ├── user_management/       # User CRUD via Keycloak admin
│   │   ├── theme/                 # User theme preferences
│   │   ├── mastra_agents/         # AI agents + Socket.IO chat
│   │   └── database/              # SQLAlchemy async engine, base model, migrations
│   └── tests/
│       ├── test_health.py
│       ├── test_auth.py
│       ├── test_users.py
│       └── conftest.py
├── alembic/                       # DB migrations (reuse existing schema)
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile                     # Multi-stage build (builder + runtime)
├── dockerfiles/
│   ├── local.Dockerfile
│   └── prod.Dockerfile
└── chart/                         # Helm chart
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        ├── ingress.yaml
        └── configmap.yaml
```

### Frontend Toggle

Add to `AppHeaderComponent`:
- `BackendSelectorComponent` — a `mat-button-toggle-group` in the toolbar
  - Options: `nestjs` | `fastapi`
  - Reads/writes to `localStorage` key `preferred-backend`
- `BackendConfigService` — injectable service that returns the base URL for the selected backend
  - `nestjs`: empty string (relative, same as today)
  - `fastapi`: `http://api-python.mac-mini` (or configured env var)
- Update Angular `HttpClient` base URL: add an interceptor that prepends the backend URL from `BackendConfigService` for non-auth URLs (or make it a global base URL pattern)

### Integration Points

- **Database**: Same PostgreSQL instance, same schema. FastAPI reads/writes the same tables as NestJS.
- **Keycloak**: Same realm, same client credentials. FastAPI uses same cookie-based auth flow.
- **Docker Compose**: New `backend-python` service alongside existing `backend`.
- **K8s**: New Helmfile release `backend-python` with ingress at `api-python.mac-mini`.
- **Frontend**: Toggle in header switches which backend URL is used for API calls.

### Environment Variable Parity

| NestJS Var | FastAPI Equivalent | Description |
|-----------|-------------------|-------------|
| `PORT` | `PORT` | Listen port (8080) |
| `DATABASE_URL` | `DATABASE_URL` | PostgreSQL connection string |
| `KEYCLOAK_URL` | `KEYCLOAK_URL` | Keycloak base URL |
| `KEYCLOAK_REALM` | `KEYCLOAK_REALM` | Realm name |
| `KEYCLOAK_CLIENT_ID` | `KEYCLOAK_CLIENT_ID` | Client ID |
| `KEYCLOAK_CLIENT_SECRET` | `KEYCLOAK_CLIENT_SECRET` | Client secret |
| `ALLOWED_ORIGINS` | `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY` | For AI agents |
| `OPENAI_API_KEY` | `OPENAI_API_KEY` | For AI agents |

## Scope

### In Scope
- Complete FastAPI application replicating all NestJS endpoints
- Docker build configuration (prod + local)
- Helm chart for K8s
- Helmfile release entry
- Docker Compose service entry
- Frontend backend selector toggle (header component + service + interceptor)
- Unit + integration tests (pytest, 80% coverage target)
- AI agent integration (same models as NestJS: Anthropic claude-sonnet, OpenAI gpt-4o)

### Out of Scope
- Database schema changes (use existing schema as-is)
- Keycloak realm changes
- Replacing NestJS backend
- Migrating existing data

## Open Questions

None — all resolved.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python version | 3.12 | Latest stable with best async support |
| ASGI server | uvicorn | Standard FastAPI production server |
| ORM | SQLAlchemy 2.0 async | Matches existing DB schema, async-first |
| Keycloak | python-keycloak + httpx | Best maintained Python Keycloak library |
| WebSocket | python-socketio with ASGI | Socket.IO parity with NestJS |
| Test framework | pytest + httpx AsyncClient | Standard Python, async-capable |
| Frontend toggle position | AppHeader toolbar | Visible always, quick switch for testing |
| Backend URL config | localStorage + interceptor | No page reload needed, persists across sessions |
| Ingress hostname | api-python.mac-mini | Mirrors api.mac-mini pattern |
