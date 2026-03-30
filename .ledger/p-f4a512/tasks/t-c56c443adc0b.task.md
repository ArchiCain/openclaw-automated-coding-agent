---
id: t-c56c443adc0b
planId: p-f4a512
project: backend
feature: python-backend-foundation
specialist: backend-eng
dependsOn: [t-3f8b41a454b7]
status: ready
attempts: 0
commitHash: null
created: 2026-03-30T04:13:00.000Z
updated: 2026-03-30T04:13:00.000Z
---

# Task: FastAPI Backend — pytest Tests (80% Coverage)

## Goal
Write a pytest test suite for the FastAPI backend achieving ≥80% code coverage. Covers health, auth, users, and theme endpoints using httpx AsyncClient and mocked Keycloak/AI dependencies.

## Context
This task builds on tasks `t-3f8b41a454b7` (scaffold) and depends on `t-24a806eb6b7a` (features) and `t-2ee15c48ba18` (agents). Tests live in `app/tests/`.

Use `pytest-asyncio` with httpx `AsyncClient` for async request testing. Mock Keycloak HTTP calls using `respx` or `unittest.mock`. Do not require a running database for unit tests — use in-memory SQLite or mock the database session.

## What to Build

### `app/tests/`
- `conftest.py` — pytest fixtures:
  - `app_client` — async httpx TestClient with overridden DB dependency (in-memory SQLite or mock)
  - `mock_keycloak` — respx/mock fixture for Keycloak token endpoint
  - `auth_headers` — fixture providing valid auth cookies for protected route tests
- `test_health.py` — tests for `GET /health`
- `test_auth.py` — tests for login, logout, check, refresh (mocked Keycloak)
- `test_users.py` — tests for user CRUD (mocked Keycloak admin API)
- `test_theme.py` — tests for theme preferences (mocked DB)

### `pytest.ini` or `pyproject.toml` `[tool.pytest.ini_options]`
```
asyncio_mode = "auto"
testpaths = ["app/tests"]
```

### Coverage configuration (`.coveragerc` or `pyproject.toml`)
Target ≥80% coverage. Exclude `alembic/`, `app/tests/`, `app/main.py` startup hooks.

## Acceptance Criteria
- [ ] `pytest` runs all tests without error
- [ ] Test coverage ≥80% as reported by `coverage run -m pytest && coverage report`
- [ ] Health endpoint test: `GET /health` returns 200 `{"status": "ok"}`
- [ ] Auth tests: login returns cookies, check returns user profile, 401 on missing auth
- [ ] User tests: list/create/get/update/delete users with mocked Keycloak admin
- [ ] Theme tests: get/set preferences with mocked DB session
- [ ] `conftest.py` provides reusable async fixtures
- [ ] No external dependencies required to run tests (all Keycloak/DB mocked)

## References
- `.ledger/p-f4a512/plan.md` — 80% coverage target, pytest + httpx requirement
- `projects/application/backend/app/test/` — NestJS integration test patterns (reference only)
- `projects/docs/app/docs/development/testing.md` — testing conventions
