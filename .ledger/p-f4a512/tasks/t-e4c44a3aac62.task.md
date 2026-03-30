---
id: t-e4c44a3aac62
planId: p-f4a512
project: infra-docker
feature: python-backend-infra
specialist: infra-eng
dependsOn: [t-b1b9102dc06b]
status: ready
attempts: 0
commitHash: null
created: 2026-03-30T04:13:00.000Z
updated: 2026-03-30T04:13:00.000Z
---

# Task: Docker Compose — Add backend-python Service

## Goal
Add the `backend-python` FastAPI service to `infrastructure/docker/compose.yml` so the local development stack includes the Python backend alongside the existing NestJS backend.

## Context
The existing compose file is at `infrastructure/docker/compose.yml`. It currently has `database`, `pgweb`, `backend` (NestJS), `keycloak`, `frontend`, and other services. Add a new `backend-python` service following the same pattern as the existing `backend` service.

The `backend-python` service:
- Builds from `projects/application/backend-python/`
- Uses `dockerfiles/local.Dockerfile`
- Mounts source for hot reload
- Runs on a distinct port (e.g., `BACKEND_PYTHON_PORT:8080`)
- Shares the same `.env` file
- Depends on `database` (healthy) and `keycloak` (healthy)

The `.env` file at the repo root already has all required env vars (same vars, same values as NestJS backend).

## What to Build

### Update `infrastructure/docker/compose.yml`
Add after the `backend` service block:

```yaml
backend-python:
  init: true
  platform: linux/amd64
  build:
    context: ../../projects/application/backend-python
    dockerfile: dockerfiles/local.Dockerfile
  ports:
    - "${BACKEND_PYTHON_PORT:-8086}:8080"
  env_file:
    - ../../.env
  environment:
    - PORT=8080
    - SERVICE_NAME=backend-python
  volumes:
    - ../../projects/application/backend-python/app:/app
  healthcheck:
    test: ["CMD-SHELL", "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/health')\""]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  restart: unless-stopped
  depends_on:
    database:
      condition: service_healthy
    keycloak:
      condition: service_healthy
```

No other services need modification.

## Acceptance Criteria
- [ ] `backend-python` service added to `infrastructure/docker/compose.yml`
- [ ] Service uses `build.context: ../../projects/application/backend-python`
- [ ] Source volume mounted for hot reload: `../../projects/application/backend-python/app:/app`
- [ ] Port exposed as `${BACKEND_PYTHON_PORT:-8086}:8080`
- [ ] Health check configured using Python's built-in `urllib` (no extra deps)
- [ ] Depends on `database` and `keycloak` healthy conditions
- [ ] Existing services in compose.yml are not modified

## References
- `infrastructure/docker/compose.yml` — existing compose file; mirror the `backend` service pattern
- `.ledger/p-f4a512/plan.md` — Docker Compose service requirement
