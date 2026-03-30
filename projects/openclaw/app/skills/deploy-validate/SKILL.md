---
name: deploy-validate
description: Pre-merge and post-deploy validation for the automated-repo monorepo. Use when a plan branch is ready to merge to mac-mini (pre-ship validation) OR after a deploy has completed (post-deploy smoke test). Runs Helm template dry-run, Docker build validation, and Playwright E2E tests against the live deployed app. Triggers when orchestrator says "pre-ship validation", "deploy validation", "post-deploy check", or when QA passes and before merge to mac-mini.
---

# Deploy Validator

Two-phase validation that catches what code review and unit tests miss:
1. **Pre-merge** — validates the build will succeed before touching mac-mini
2. **Post-deploy** — runs Playwright E2E against the live app to confirm runtime correctness

---

## Phase 1: Pre-Merge Validation

Run this on the plan branch **before** merging to mac-mini.

### 1a. Helm Template Dry-Run

```bash
cd /workspace/automated-repo
helm template frontend projects/application/frontend/chart/ --debug 2>&1 | head -50
helm template backend projects/application/backend/chart/ --debug 2>&1 | head -50
```

Fail if: any `Error:` lines appear. Warn if values reference undefined keys.

Also validate Helmfile resolves:
```bash
helmfile -f infrastructure/k8s/helmfile.yaml template 2>&1 | grep -E "^Error|^error" | head -20
```

### 1b. Docker Build Validation

If `docker` is available:
```bash
cd /workspace/automated-repo

# Frontend
docker build \
  --file projects/application/frontend/dockerfiles/prod.Dockerfile \
  --build-arg BACKEND_URL=http://placeholder \
  --no-cache \
  --progress=plain \
  projects/application/frontend/ 2>&1 | tail -30

# Backend
docker build \
  --file projects/application/backend/dockerfiles/prod.Dockerfile \
  --no-cache \
  --progress=plain \
  projects/application/backend/ 2>&1 | tail -30
```

If `docker` is NOT available (common in this sandbox): flag it in the report and note it as a known gap. Do not fail the validation — instead recommend the operator verify docker build manually or via CI.

### 1c. Pre-flight Checklist

Before passing pre-merge, verify:
- [ ] `app/nginx.conf` exists in any frontend project being rebuilt
- [ ] `package-lock.json` is committed and in sync (`npm install --package-lock-only` produces no diff)
- [ ] All files referenced by Dockerfile `COPY` statements exist in the repo
- [ ] `helm template` produces no errors

Run the lockfile sync check:
```bash
cd /workspace/automated-repo/projects/application/frontend/app
cp package-lock.json /tmp/lockfile-before.json
npm install --package-lock-only --silent 2>/dev/null
diff /tmp/lockfile-before.json package-lock.json | head -20
# If diff is non-empty: lockfile is stale — commit the updated one
```

---

## Phase 2: Post-Deploy E2E

Run this after CI has deployed to the `app` namespace and pods are `Running`.

### 2a. Wait for Rollout

```bash
kubectl rollout status deployment/frontend -n app --timeout=120s
kubectl rollout status deployment/backend -n app --timeout=120s
kubectl get pods -n app
```

### 2b. Run Playwright Tests

```bash
cd /workspace/automated-repo/projects/application/e2e/app

# Install browsers if needed
npx playwright install chromium --with-deps 2>/dev/null || true

# Run against deployed app
FRONTEND_URL=https://app.mac-mini \
BACKEND_URL=https://api.mac-mini \
KEYCLOAK_URL=https://auth.mac-mini \
npx playwright test \
  --reporter=list \
  --timeout=60000 \
  2>&1
```

If the app uses self-signed certs, add `--ignore-https-errors` to the playwright command.

Check `playwright.config.ts` for the env var names it expects — they may be `FRONTEND_PORT`/`BACKEND_PORT` vs full URLs.

### 2c. Interpret Results

- **All pass** → post-deploy validation complete, report success
- **Some fail** → read the failure output carefully:
  - Auth failures (login page not loading, 502) → proxy/nginx config issue
  - CORS errors in console → nginx proxy routes missing
  - Component not found → Angular selector changed from what tests expect
  - Timeout → app is slow to start, retry once

For each failure, identify the responsible task from the plan's manifest and write feedback to `.ledger/{plan-id}/tasks/{task-id}.feedback.md`.

---

## Reporting

### Pre-merge report format:
```
PRE-MERGE VALIDATION: PASS | FAIL

Helm template: PASS | FAIL — {error if any}
Docker build (frontend): PASS | FAIL | SKIPPED (no docker) — {error if any}
Docker build (backend): PASS | FAIL | SKIPPED (no docker) — {error if any}
Lockfile sync: PASS | STALE (committed fix) — {diff summary if stale}
Pre-flight checklist: PASS | FAIL — {missing files if any}
```

### Post-deploy report format:
```
POST-DEPLOY E2E: PASS | FAIL

{N} tests passed, {N} failed
Failed tests:
  - {test name}: {error summary}
    → Responsible task: t-{id} ({feature})
```

---

## Rules

- **Never merge to mac-mini without passing pre-merge validation**
- **If docker is unavailable, flag it but don't block** — note the gap in the report
- **On lockfile stale**, commit the fix to the plan branch and re-run merge
- **On post-deploy E2E fail**, route feedback to responsible task(s) and trigger rework
- **Max 2 E2E retries** for timeout failures before marking as a real failure
