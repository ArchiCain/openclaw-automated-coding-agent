# Decomposition Pipeline

How the automated plan-to-code pipeline works, including the decomposition philosophy, principles, and rules.

## Overview

The decomposition pipeline breaks a brainstormed plan into executable tasks through a single architect pass:

```
Plan (brainstorm output)
  → Architect reads plan + docs + codebase
    → Tasks (flat list, routed to specialist engineers by project)
```

The architect skill handles all decomposition in one pass, creating tasks with the right granularity for specialist engineers (frontend-eng, backend-eng, infra-eng) to implement. Tasks are tracked in `.ledger/` — a durable, structured record that survives restarts.

## Core Principles

### Decomposition
Breaking a unit of work into tasks that collectively fulfill the plan's purpose.

**Good decomposition:**
- Tasks are cohesive (single responsibility per unit)
- Tasks are loosely coupled (minimal cross-dependencies)
- No gaps — tasks fully cover the plan's scope
- No overlaps — clear boundaries between tasks

### Distillation
Extracting only the context a task needs to be implemented independently.

**Good distillation:**
- Task can be worked on with ONLY its task.md (no reading other task files)
- No redundant context (don't pass what isn't used)
- Interfaces over implementations (pass contracts, not details)
- Conventions come from docs (reference doc paths, don't embed stale snapshots)

### Research is Mandatory
Before creating any tasks:
1. **Read the input plan completely** — understand what's being built and why
2. **Explore the codebase** — verify what exists before deciding what to create
3. **Read the relevant docs** — understand architecture, conventions, and interfaces
4. **Identify integration points** — what already exists that this touches?
5. **Surface implicit requirements** — what isn't stated but is necessary?

## Ledger Structure

All work is tracked in `.ledger/`:

```
.ledger/{plan-id}/
├── plan.md              # Brainstorm output (input to architect)
├── manifest.json        # Plan lifecycle state + task registry
├── tasks/               # Flat directory of all tasks
│   ├── t-a1b2c3d4e5f6.task.md
│   ├── t-a1b2c3d4e5f6.feedback.md  (on rejection)
│   ├── t-b2c3d4e5f6a1.task.md
│   └── ...
├── qa-reports/
│   └── {feature}-{timestamp}.md
└── incidents/
    └── {timestamp}.md
```

Tasks are flat (not nested by project/feature). Project and feature routing are metadata in the task frontmatter.

### Plan ID Format

Plans use `p-{6-char-hex}` (e.g., `p-a1b2c3`). Tasks use `t-{12-char-hex}` (e.g., `t-a1b2c3d4e5f6`).

### Manifest File

The plan root has a `manifest.json` tracking plan lifecycle and all task states:

```json
{
  "planId": "p-{id}",
  "status": "ready|decomposing|decomposed|executing|pr-submitted|completed|stalled",
  "branch": "openclaw/p-{id}",
  "updated": "ISO-8601",
  "tasks": {
    "t-{12hex}": {
      "status": "ready|in-progress|implemented|reviewed|needs-rework|qa-passed|blocked",
      "project": "frontend|backend|infra-docker|...",
      "feature": "feature-slug",
      "specialist": "frontend-eng|backend-eng|infra-eng",
      "dependsOn": ["t-other-id"],
      "attempts": 0,
      "commitHash": null
    }
  },
  "features": {
    "feature-slug": { "status": "in-progress|review-complete|qa-passed|blocked" }
  },
  "history": [{ "status": "...", "at": "ISO-8601" }]
}
```

## Task Schema

```markdown
---
id: t-{12-char-hex}
planId: {plan-id}
project: {project-slug}
feature: {feature-slug}
specialist: {specialist-skill-name}
dependsOn: []
status: ready
attempts: 0
commitHash: null
created: {ISO-8601}
updated: {ISO-8601}
---

# Task: {Descriptive Title}

## Goal
{What to build and why — 2-3 sentences}

## Context
{Integration points, API contracts, existing code to reference}

## What to Build
{Concrete deliverables — but HOW is up to the specialist}

## Acceptance Criteria
- [ ] {Verifiable criterion}

## References
- `projects/docs/app/docs/...` — {why}
- `projects/application/.../src/features/...` — {existing code}
```

### Task Routing

Each task is assigned to a specialist based on its project:

| Project | Specialist | What It Covers |
|---------|-----------|----------------|
| `frontend` | `frontend-eng` | Angular components, services, guards, routes |
| `backend` | `backend-eng` | NestJS controllers, services, entities, modules |
| `infra-docker` | `infra-eng` | Docker Compose, Dockerfiles |
| `infra-k8s` | `infra-eng` | Helm charts, Helmfile |
| `infra-terraform` | `infra-eng` | Terraform resources |
| `database` | `infra-eng` | Database config, migrations |
| `keycloak` | `infra-eng` | Keycloak realm config |
| `e2e` | `qa-eng` | Playwright E2E tests |

### Dependencies

`dependsOn` references task IDs directly (e.g., `["t-a1b2c3d4e5f6"]`). A task won't start until all its dependencies reach `reviewed` or `qa-passed` status.

**General dependency patterns:**
- Types, DTOs, entities, constants → `[]` (no dependencies, implement first)
- Services, repositories → depend on types/DTOs/entities they consume
- Guards, middleware, interceptors → depend on services they inject
- Controllers, gateways → depend on services and DTOs
- Components, pages → depend on services and types
- Config (routing, barrels) → depends on all concerns it wires together

**Cross-project dependencies** (e.g., frontend needs a backend API) use task IDs directly. The architect includes the interface contract in both tasks.

### Feature Tagging

Every task gets a `feature` tag — a slug identifying the user-facing functionality it belongs to.

**The golden rule**: Split by user-facing functionality, NOT technical concern.
- Good: `auth-login`, `user-dashboard`, `chat-messaging`
- Bad: `controllers`, `services`, `types`

Features are used for:
- Serialization (tasks in the same feature don't run in parallel to avoid conflicts)
- QA grouping (qa-eng runs when all tasks for a feature are reviewed)

## Task Granularity

The architect decides granularity using judgment:

- **Completable in one session** — under 30 minutes
- **Coherent** — files that must be created together belong in one task
- **Clear acceptance criteria** — specialist and reviewer know when it's done
- **Related files can be grouped** — a service + its types can be one task
- **App wiring is separate** — route registration, barrel exports, provider setup are their own tasks

Specialists are domain experts, not constrained junior devs — tasks describe **what** to build, not **how**.

## Naming Rules

Names must be self-contained and scoped to their own level:

| Good Name | Bad Name |
|-----------|----------|
| `Backend API` | `Backend API — User Dashboard Plan` |
| `Calculator Feature` | `Calculator Feature — Math Quest` |
| `Authentication Service` | `Auth Service — Keycloak Feature` |

The hierarchy provides context through the plan and feature tags.

## No Shared Code Between Projects

Projects do not share code. Each project owns its own types and interfaces. The contract between projects is the HTTP API (or other transport protocol), not shared TypeScript files.

Frontend discovers backend endpoints by reading the backend documentation at `docs/projects/application/backend.md`. The frontend defines its own TypeScript interfaces for these contracts.

## Documentation as Source of Truth

The architect reads from `projects/docs/app/docs/` for all repo context:

| Context Needed | Doc File |
|----------------|----------|
| What projects exist | `projects/overview.md` |
| Feature organization | `architecture/feature-architecture.md` |
| Backend details | `projects/application/backend.md` |
| Frontend details | `projects/application/frontend.md` |
| Infrastructure layout | `infrastructure/overview.md` |
| Creating new projects | `development/creating-projects.md` |
| Testing conventions | `development/testing.md` |

Specialists also read these docs at runtime — conventions are not embedded in task files.
