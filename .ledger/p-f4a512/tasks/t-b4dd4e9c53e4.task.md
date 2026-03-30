---
id: t-b4dd4e9c53e4
planId: p-f4a512
project: infra-k8s
feature: python-backend-infra
specialist: infra-eng
dependsOn: [t-b1b9102dc06b]
status: ready
attempts: 0
commitHash: null
created: 2026-03-30T04:13:00.000Z
updated: 2026-03-30T04:13:00.000Z
---

# Task: Helm Chart and Helmfile Release for backend-python

## Goal
Create a Helm chart for the `backend-python` FastAPI service and add its Helmfile release to the K8s deployment configuration. The Python backend should be deployable to K8s at `api-python.mac-mini`.

## Context
Each application service has its chart at `projects/<service>/chart/`. The Helmfile at `infrastructure/k8s/helmfile.yaml.gotmpl` references these charts. Mirror the existing `backend` chart and Helmfile release pattern.

The `backend-python` service:
- Runs on port 8080 (same as NestJS backend, different K8s service)
- Ingress hostname: `api-python.mac-mini` (mirrors `api.mac-mini` for NestJS)
- Same env vars as NestJS backend (`DATABASE_URL`, `KEYCLOAK_URL`, etc.)
- Image from the in-cluster registry: `${REGISTRY}/backend-python:${IMAGE_TAG}`

## What to Build

### `projects/application/backend-python/chart/`
Mirror `projects/application/backend/chart/` exactly:

**`Chart.yaml`:**
```yaml
apiVersion: v2
name: backend-python
description: FastAPI Python backend service
type: application
version: 0.1.0
appVersion: "1.0.0"
```

**`values.yaml`:** Same structure as backend's values.yaml — `replicaCount`, `image`, `service.port: 8080`, `ingress`, `env`, `secretEnv`, `resources`, `healthCheck.path: /health`.

**`templates/`:** Copy the full template set from `projects/application/backend/chart/templates/` (deployment.yaml, service.yaml, ingress.yaml, configmap.yaml, secret.yaml). These are generic — they work for any service with the same values shape.

### Update `infrastructure/k8s/helmfile.yaml.gotmpl`
Add a new release after the `backend` release:

```yaml
- name: backend-python
  namespace: {{ env "NAMESPACE" | default "app" }}
  chart: ../../projects/application/backend-python/chart
  needs:
    - {{ env "NAMESPACE" | default "app" }}/database
    - {{ env "NAMESPACE" | default "app" }}/keycloak
  values:
    - image:
        repository: {{ env "BACKEND_PYTHON_IMAGE" | default (print (env "REGISTRY" | default "localhost:30500") "/backend-python") }}
        tag: {{ env "IMAGE_TAG" | default "latest" }}
      replicas: {{ env "BACKEND_PYTHON_REPLICAS" | default "1" }}
      ingress:
        enabled: true
        host: {{ env "BACKEND_PYTHON_HOST" | default "api-python.mac-mini" }}
        tls: {{ .Values | get "ingressTLS" false }}
      env:
        PORT: "8080"
        DATABASE_URL: {{ env "BACKEND_PYTHON_DATABASE_URL" | default (env "DATABASE_URL" | default "") }}
        KEYCLOAK_URL: {{ env "KEYCLOAK_URL" | default "http://keycloak:8080" }}
        KEYCLOAK_REALM: {{ env "KEYCLOAK_REALM" | default "application" }}
        KEYCLOAK_CLIENT_ID: {{ env "KEYCLOAK_CLIENT_ID" | default "backend-service" }}
        ALLOWED_ORIGINS: {{ env "ALLOWED_ORIGINS" | default "" }}
      secretEnv:
        KEYCLOAK_CLIENT_SECRET: {{ env "KEYCLOAK_CLIENT_SECRET" | default "backend-service-secret" }}
        ANTHROPIC_API_KEY: {{ env "ANTHROPIC_API_KEY" | default "" }}
        OPENAI_API_KEY: {{ env "OPENAI_API_KEY" | default "" }}
      resources:
        requests:
          memory: {{ env "BACKEND_PYTHON_MEMORY_REQUEST" | default "256Mi" }}
          cpu: {{ env "BACKEND_PYTHON_CPU_REQUEST" | default "100m" }}
        limits:
          memory: {{ env "BACKEND_PYTHON_MEMORY_LIMIT" | default "512Mi" }}
          cpu: {{ env "BACKEND_PYTHON_CPU_LIMIT" | default "500m" }}
```

### Also update DNS CoreDNS chart (if it lists known hostnames)
Check if `infrastructure/k8s/charts/dns/` has a static hostname list that needs `api-python.mac-mini` added. If so, add it.

## Acceptance Criteria
- [ ] `projects/application/backend-python/chart/Chart.yaml` created with correct metadata
- [ ] `projects/application/backend-python/chart/values.yaml` with all required value keys
- [ ] `projects/application/backend-python/chart/templates/` contains deployment, service, ingress, configmap, secret templates
- [ ] Helmfile release `backend-python` added to `infrastructure/k8s/helmfile.yaml.gotmpl`
- [ ] Release depends on `database` and `keycloak`
- [ ] Ingress defaults to `api-python.mac-mini`
- [ ] All env vars from plan's parity table are configurable via helm values
- [ ] `helm template` on the chart produces valid K8s YAML (no syntax errors)

## References
- `projects/application/backend/chart/` — Helm chart to mirror
- `infrastructure/k8s/helmfile.yaml.gotmpl` — existing Helmfile; add release following `backend` pattern
- `.ledger/p-f4a512/plan.md` — ingress hostname, K8s deployment requirements
- `projects/docs/app/docs/infrastructure/overview.md` — adding new services
