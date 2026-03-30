# OpenClaw Full Design — Execution, Environment & Orchestration

This is the complete design for OpenClaw's autonomous development pipeline: everything from receiving a plan through delivering a PR to the human. It covers execution, validation, deployment, environment ownership, and the trigger mechanism.

---

# Part 1: Current State & Context

## What Works Today

**Decomposition pipeline (3 skills, each runs in its own Claude Code ACP session):**
- `rlm-decompose-1` — plan.md → project-level plans
- `rlm-decompose-2` — project plan → feature-level plans
- `rlm-decompose-3` — feature plan → atomic concern task.md files

**Infrastructure:**
- OpenClaw Gateway runs in Docker, clones its own workspace (no host bind mount)
- ACP sessions with Claude Code working (`defaultAgent: "claude"`, `permissionMode: approve-all`)
- Concurrency limits set to 20 across the board
- Skills live in `projects/openclaw/app/skills/`
- Agent identity defined in `projects/openclaw/app/SOUL.md`
- Gateway config in `projects/openclaw/app/openclaw.json`

**First plan decomposed:** `p-e7a3f1` (Angular frontend rebuild) — produced 60 files, 7,500+ lines across 2 projects, 14 features, 44 atomic tasks.

## What Exists But Is Generic
- `rlm-code` — a basic "make changes via git worktree" skill. Doesn't know about task.md files, acceptance criteria, or validation loops.

## What Doesn't Exist Yet
- Execution skill (implement a task.md)
- Validation/review skill (verify implementation against acceptance criteria)
- E2E testing integration (run Playwright against the live app)
- PR creation for human review
- Task status tracking during execution
- Retry/feedback loops
- Team orchestration
- Plan watcher / trigger mechanism
- Environment ownership and deployment rules

## Key Files

| File | Path | What It Covers |
|------|------|----------------|
| SOUL.md | `projects/openclaw/app/SOUL.md` | Current agent identity and routing rules |
| openclaw.json | `projects/openclaw/app/openclaw.json` | Gateway config (agents, ACP, plugins) |
| Decomposition docs | `projects/docs/app/docs/architecture/decomposition.md` | Full pipeline, task schema, dependency patterns |
| Feature architecture | `projects/docs/app/docs/architecture/feature-architecture.md` | How code is organized |
| Existing skills | `projects/openclaw/app/skills/rlm-decompose-*/SKILL.md` | Skill format and patterns |
| rlm-code skill | `projects/openclaw/app/skills/rlm-code/SKILL.md` | Existing generic coding skill |
| E2E tests | `projects/docs/app/docs/projects/application/e2e.md` | Current E2E test setup |

## Task.md Structure (What Executors Will Consume)

```markdown
---
id: t-{12-char-hex}
parent: {feature-task-id}
dependsOn: [sibling-concern-prefixes]
created: {ISO-8601}
updated: {ISO-8601}
---

# Task: {Concern Name}

## Purpose
## Context (Conventions, Interfaces, Boundaries, References)
## Specification (Requirements, Files, Acceptance Criteria)
```

Each task specifies exact file paths to create, code patterns to follow, and verifiable acceptance criteria checkboxes.

## Backlog Structure

```
.backlog/{plan-id}/
├── plan.md
├── status.json
├── {project}/
│   ├── plan.md
│   └── {feature}/
│       ├── plan.md
│       ├── types.task.md
│       ├── service.task.md
│       ├── component.task.md
│       └── config.task.md
```

`dependsOn` arrays define execution order within a feature. Cross-feature ordering is handled by the orchestrator based on feature-level analysis.

## OpenClaw Capabilities

- **ACP sessions** — spawn Claude Code sessions with `sessions_spawn(runtime: "acp", agentId: "claude")`
- **Subagents** — OpenClaw-native delegated runs (lighter weight, no external CLI)
- **Skills** — SKILL.md files that provide context/instructions for specific tasks
- **Exec tool** — can run shell commands (build, test, lint)
- **Max spawn depth: 3**, max children per agent: 20, max concurrent: 20
- **Session timeout:** 30 minutes (`runTimeoutSeconds: 1800`)

---

# Part 2: The Big Picture

## The Vision

OpenClaw is a full development team. You talk to it like a team lead — it has developers, reviewers, and knows how to ship. It owns a branch and an environment. Its job is to take plans, turn them into working code, deploy it, verify it works, and submit a PR for the human to review.

| Role | Responsibility | How It Maps |
|------|---------------|-------------|
| **Team Lead** | Orchestrates all work, assigns tasks, tracks progress | OpenClaw main agent (SOUL.md) |
| **Architects** | Plan and decompose features | decompose-1/2/3 skills (done) |
| **Junior Devs** | Implement atomic tasks from task.md files | `rlm-execute` skill (to build) |
| **Senior Devs** | Review implementations against acceptance criteria | `rlm-validate` skill (to build) |
| **DevOps** | Create the final PR for human review | `rlm-pr` skill (to build) |

## The End-to-End Flow

```
Human pushes plan.md to mac-mini branch with status: ready
  ↓ (cron detects within 5 minutes)
OpenClaw creates plan branch openclaw/p-{id} from mac-mini
  ↓
Decompose: plan → projects → features → atomic tasks
  ↓
Execute: for each feature, for each task:
  ├── Spawn executor (rlm-execute) → implements code, commits
  ├── Spawn validator (rlm-validate) → reviews against acceptance criteria
  ├── If rejected: retry with feedback (max 3 attempts)
  └── If validated: move to next task
  ↓
Build sweep: full build + tests across all plan changes
  ↓
Deploy: merge plan branch into mac-mini → GitHub Actions CI/CD
  ↓
Verify: monitor CI run, run E2E tests post-deploy
  ↓
Deliver: create PR from plan branch → main for human review
  ↓
Done. Human reviews, tests, approves.
```

---

# Part 3: Agent Topology & Skills

## Decision: Single agent, multiple skills

All roles use the same Claude Code ACP agent (`claude`) with different skills providing role-specific context. No new agents in `openclaw.json`.

**Rationale:**
- Every role ultimately needs Claude Code's tools (file read/write, bash, git). There's no capability difference between agents — only instruction differences. That's exactly what skills are for.
- Multi-agent routing adds complexity (separate system prompts, model configs, routing rules in SOUL.md) without capability gain. The decompose pipeline already proves the single-agent-multiple-skills pattern works.
- If we later want different models per role (e.g., Haiku for validation to save tokens), we can split then. Premature optimization now.
- OpenClaw's spawn depth limit (3) is precious. Using separate agents for roles would consume depth levels that are better reserved for the orchestrator → skill → sub-task hierarchy.

## Skill Roster

| Skill | Role | Input | Output |
|-------|------|-------|--------|
| `rlm-execute` | Junior Dev | task.md on the plan branch | Committed implementation |
| `rlm-validate` | Senior Dev | task.md + diff from executor | Pass/reject with feedback |
| `rlm-pr` | DevOps | Plan branch + plan.md | Single PR to main for human review |
| `rlm-decompose-1/2/3` | Architect | Plans at each level | Child plans/tasks (existing) |

**What about deployment, E2E testing, and PR review?**

- **Deployment** is not a skill — it's a consequence of merging the plan branch into the environment's deploy branch (`mac-mini`). GitHub Actions CI/CD handles build, push, and deploy. OpenClaw monitors the run via `gh run watch` and reacts to failures.
- **E2E testing** is an orchestrator action post-deploy. OpenClaw runs `task e2e:test` via exec tool and reads results. No Claude Code session needed.
- **PR review** is human. OpenClaw submits a PR from the plan branch to `main` and stops. The human reviews, comments, or approves.
- **Team Lead** is OpenClaw itself (SOUL.md). Not a skill — it's the main agent loop.

---

# Part 4: Git Workflow

## Decision: One branch per plan, sequential everything, no worktrees

```
main (human-controlled — production)
  └── mac-mini (deploy branch — CI/CD deploys from here)
        └── openclaw/p-e7a3f1 (plan branch — ALL work for this plan)
              ├── commit: feat(shared-types): implement types [t-aaa111]
              ├── commit: feat(shared-types): implement barrel [t-aaa222]
              ├── commit: feat(auth-login): implement types [t-bbb111]
              ├── commit: feat(auth-login): implement service [t-bbb222]
              ├── commit: feat(auth-login): implement component [t-bbb333]
              ├── commit: feat(auth-login): implement config [t-bbb444]
              ├── commit: feat(chat-room): implement types [t-ccc111]
              ├── ...
              └── commit: feat(user-mgmt): implement config [t-nnn444]
```

**Branch naming:** `openclaw/{plan-id}`
Example: `openclaw/p-e7a3f1`

**Execution model:**
- **One plan at a time.** OpenClaw works a single plan from start to finish.
- **Features execute sequentially** in dependency order. Cross-feature dependencies (documented in feature plan Boundaries) determine the order.
- **Tasks within a feature execute sequentially** in `dependsOn` order (topological sort).
- **All work happens on one branch.** No worktrees, no parallel branches, no merge conflicts.
- Each task is a commit (or small group of commits) on the plan branch.

**Testing the work in the environment:**
- OpenClaw merges the plan branch into `mac-mini` to trigger CI/CD and deploy
- This lets OpenClaw (and the human) see the work running in the actual environment
- The plan branch stays intact — it's the clean record of all the work

**Submitting for human review:**
- When the plan is complete, OpenClaw creates a PR: `openclaw/p-e7a3f1` → `main`
- The PR contains the entire plan's work — all features, all tasks
- The human reviews, tests in the mac-mini environment, and approves or comments
- OpenClaw's job for this plan ends at PR submission

**Why one plan at a time?**
- Simpler mental model — one body of work, one branch, linear history
- No merge conflicts between parallel plans
- No worktree management overhead
- Easier to reason about state (what's done, what's next)
- Parallel plan execution is a future optimization when the pipeline is proven

**Why not one branch per feature?**
- Features within a plan often depend on each other (shared types → services → components)
- Separate branches would require constant rebasing as upstream features complete
- One branch keeps everything linear and simple
- The human gets one PR to review, not 14

---

# Part 5: Execution Flow

## Task Lifecycle

```
ready → executing → implemented → validating → validated
                                             → rejected → executing (retry)
                                                        → blocked (max retries)
```

## Feature Lifecycle

```
ready → executing → validated
                  → blocked (has blocked tasks or dependencies blocked)
```

## Plan Lifecycle

```
decomposed → executing → validated → deployed → pr-submitted
                       → blocked (has blocked features)
```

## The Pipeline (Single Task)

```
┌─────────────────────────────────────────────────┐
│ ORCHESTRATOR (OpenClaw main agent)              │
│                                                 │
│  1. Pick next ready task (dependency-resolved)  │
│  2. Spawn ACP session with rlm-execute skill    │
│  3. Wait for completion                         │
│  4. Spawn ACP session with rlm-validate skill   │
│  5. If rejected and retries < 3: goto 2         │
│  6. If rejected and retries = 3: mark blocked   │
│  7. If validated: update status, pick next task  │
└─────────────────────────────────────────────────┘
```

## Step Details

**Step 2 — Execution (rlm-execute):**

The executor receives:
- The task.md file path
- The plan branch (already checked out)
- The feature plan.md path (for broader context)

The executor:
1. Reads the task.md and feature plan
2. Reads referenced files and conventions docs
3. Implements the specification — creates/modifies files listed in the task
4. Runs local validation:
   - `ng build` (or relevant build command) — must pass
   - `npx tsc --noEmit` — must pass
   - Lint check — must pass
   - Unit tests for the concern if applicable
5. Commits with message: `feat({feature}): implement {concern} [t-{id}]`
6. Reports success/failure back to orchestrator

If local validation fails, the executor fixes issues within its session (up to the 30-min timeout). It does not push — the branch stays local until deploy time.

**Step 4 — Validation (rlm-validate):**

The validator receives:
- The task.md file path (acceptance criteria are the rubric)
- The diff for this task's commit(s)
- The repo path (to inspect full file context)

The validator:
1. Reads the task.md acceptance criteria
2. Reviews the diff against each criterion
3. Checks for:
   - All acceptance criteria met
   - Files match the specification
   - Code follows conventions listed in task context
   - No obvious bugs, security issues, or missing error handling
4. Returns a structured verdict:
   - `PASS` — all criteria met
   - `REJECT` — with specific feedback per failed criterion

The validator does NOT re-run builds or tests (executor already did). It's a code review, not a CI check.

**Step 5 — Retry on rejection:**
- Feedback is written to a `{concern}.feedback.md` file alongside the task
- Executor on retry reads both the original task.md and the feedback
- Each retry is a fresh ACP session (clean context, no accumulated confusion)
- Feedback file includes the attempt number and all prior feedback (accumulated)

## The Pipeline (Feature Level)

Once all tasks in a feature are `validated`:
1. Orchestrator runs a final build + unit test sweep on the branch
2. Update feature status to `validated`
3. Move to the next feature in dependency order

## The Pipeline (Plan Level)

Once all features in the plan are `validated`:
1. Orchestrator runs a full build + test sweep across the entire plan's changes
2. Push the plan branch to origin
3. Merge plan branch into `mac-mini` → triggers GitHub Actions CI/CD
4. Monitor CI run via `gh run watch`
5. CI passes → run E2E tests against the deployed environment
6. CI fails → read failure logs (`gh run view --log-failed`), fix on the plan branch, re-merge
7. If deploy broke the live app → break-glass rollback (`helm rollback -n app {service}`), incident report
8. Once deployed and healthy → spawn ACP session with `rlm-pr` skill to create PR: plan branch → `main`
9. **Done.** Human takes it from here.

---

# Part 6: Status Tracking

## Decision: Status in task.md frontmatter + plan-level status.json

**Task frontmatter gains a `status` field:**
```yaml
---
id: t-a1b2c3d4e5f6
parent: t-aabbcc
dependsOn: [types, dto]
status: validated        # ready | executing | implemented | validating | validated | rejected | blocked
attempts: 1              # number of execution attempts
created: 2026-03-28T10:00:00Z
updated: 2026-03-28T12:34:56Z
---
```

**Plan-level status.json (already exists, extend it):**
```json
{
  "planId": "p-e7a3f1",
  "status": "executing",
  "branch": "openclaw/p-e7a3f1",
  "currentFeature": "frontend/auth-login",
  "currentTask": "t-b2c3d4e5f6a1",
  "features": {
    "frontend/shared-types": {
      "status": "validated",
      "tasks": {
        "types": { "status": "validated", "taskId": "t-a1b2c3d4e5f6", "attempts": 1 },
        "barrel": { "status": "validated", "taskId": "t-a2b3c4d5e6f7", "attempts": 1 }
      }
    },
    "frontend/auth-login": {
      "status": "executing",
      "tasks": {
        "types": { "status": "validated", "taskId": "t-b1c2d3e4f5a6", "attempts": 1 },
        "service": { "status": "executing", "taskId": "t-b2c3d4e5f6a1", "attempts": 1 },
        "component": { "status": "ready", "taskId": "t-b3c4d5e6f7a2", "attempts": 0 },
        "config": { "status": "ready", "taskId": "t-b4c5d6e7f8a3", "attempts": 0 }
      }
    },
    "frontend/chat-room": {
      "status": "ready",
      "tasks": {}
    }
  },
  "updated": "2026-03-28T12:34:56Z"
}
```

**Why both frontmatter and status.json?**
- Frontmatter is the source of truth for individual task state (self-contained, read by executors/validators)
- Status.json is a denormalized index for the orchestrator (fast scan without reading every task.md file, shows the full picture at a glance)
- The orchestrator updates both atomically after each state transition

---

# Part 7: Feedback Loops

## Decision: Feedback files alongside task files, accumulated across attempts

**Feedback file:** `.backlog/{plan}/{project}/{feature}/{concern}.feedback.md`

```markdown
# Feedback: {Concern Name}

## Attempt 1 — REJECTED
**Validator session:** {session-id}
**Date:** 2026-03-28T12:00:00Z

### Failed Criteria
- [ ] Service method should return `Observable<User[]>` — returns `Promise<User[]>` instead
- [ ] Error handling should use `HttpException` — uses raw throw

### Notes
The service follows the NestJS pattern but uses async/await instead of RxJS observables
as specified in the conventions. The auth-login feature plan explicitly requires Observable-based
services for consistency with the Angular frontend's subscription model.

---

## Attempt 2 — PASS
**Validator session:** {session-id}
**Date:** 2026-03-28T12:30:00Z
All criteria met.
```

**Flow:**
1. Validator writes/appends to the feedback file
2. On retry, executor reads both `{concern}.task.md` and `{concern}.feedback.md`
3. Executor sees exactly what was wrong and the validator's notes
4. Fresh session avoids the executor getting stuck in the same wrong approach

**Max retries: 3 attempts total (1 initial + 2 retries)**

After 3 failed attempts:
- Task marked `blocked`
- Orchestrator continues with other tasks in the feature (if they don't depend on the blocked task)
- Dependent tasks are also marked `blocked` (cascade)
- Orchestrator logs the blocked task chain for operator review

---

# Part 8: Build/Test Strategy

## Decision: Local validation per task, build sweep per feature, E2E post-deploy

| Stage | What Runs | When | Who |
|-------|-----------|------|-----|
| **Task execution** | Type-check, lint, unit tests for the concern | During rlm-execute | Executor |
| **Task validation** | Code review against acceptance criteria | After execution | Validator |
| **Feature sweep** | Full build + all unit tests | After all tasks in feature validated | Orchestrator (exec) |
| **Plan sweep** | Full build + all unit tests | After all features validated | Orchestrator (exec) |
| **CI/CD** | Build images, deploy to environment | After merge to `mac-mini` | GitHub Actions |
| **E2E** | Playwright test suite | After successful deploy | Orchestrator (exec) |

**Why validate per-task, not per-feature?**
- Catching issues early is cheaper than debugging a broken build after 8 tasks
- Each task is small enough that type-check + lint is fast (seconds, not minutes)
- The executor can fix its own issues within its session before the validator even sees it

**What if a feature sweep fails?**
- The orchestrator identifies which commit introduced the failure (git bisect or diff analysis)
- That task gets re-opened with feedback from the build error
- Goes through the execute → validate cycle again

---

# Part 9: PR Strategy

## Decision: One PR per plan, submitted to human for review

**The PR is the final deliverable.** OpenClaw's job for a plan ends when the PR is submitted.

**PR creation (rlm-pr skill):**
- Triggered when plan is fully validated, deployed to the environment, and healthy
- Creates PR from plan branch (`openclaw/p-e7a3f1`) to `main`
- PR title: `feat: {plan title}` (e.g., `feat: Angular frontend rebuild`)
- PR body generated from:
  - Plan purpose and scope
  - List of features implemented (with brief descriptions)
  - Summary of tasks per feature (counts, any blocked items)
  - Link to the deployed environment for manual testing
  - Any incidents or notable decisions made during execution

**What the human does:**
- Reviews the PR (the full plan diff against main)
- Tests in the mac-mini environment (already deployed)
- Comments with feedback or approves
- Merges to main when satisfied

**What OpenClaw does NOT do:**
- Does not merge to main — that's the human's call
- Does not respond to PR comments — future enhancement
- Does not iterate on human feedback — future enhancement (for now, human can open a new plan)

---

# Part 10: Environment Ownership

## Namespace Architecture (Mac Mini)

```
Shared Infrastructure (cluster-scoped)
├── traefik/          — Ingress controller
├── registry/         — In-cluster Docker registry
└── dns/              — CoreDNS for split DNS

OpenClaw's Domain
├── openclaw/         — OpenClaw Gateway pod + workspace PVC
└── app/              — Backend, Frontend, Database, Keycloak, Docs
```

This is what exists today. No renaming, no multi-team prefixing. The current `openclaw/` and `app/` namespaces are OpenClaw's world.

> **Future note:** Multi-team is possible via namespace pairs (`team-n-openclaw/` + `team-n-app/`) with per-team RBAC scoping, helmfile `team` variable, and separate ingress subdomains. Not needed now — the architecture doesn't preclude it later.

## RBAC: Scoped Access to Its Own Environment

### Current State

OpenClaw has a **ClusterRole** with full cluster access. This is more than it needs.

### Proposed: Namespaced Roles

Replace the ClusterRole with two namespaced Roles. OpenClaw keeps the *capability* to manage its environment directly, but the instructions (SOUL.md) establish that the normal path is CI/CD.

**Role in `openclaw` namespace (read-only — observe itself):**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: openclaw-self
  namespace: openclaw
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec", "services", "configmaps", "secrets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets"]
    verbs: ["get", "list", "watch"]
```

**Role in `app` namespace (full control — break-glass access):**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: openclaw-app-manager
  namespace: app
rules:
  - apiGroups: ["", "apps", "batch", "networking.k8s.io"]
    resources: ["*"]
    verbs: ["*"]
```

**RoleBindings:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: openclaw-self
  namespace: openclaw
subjects:
  - kind: ServiceAccount
    name: openclaw-gateway
    namespace: openclaw
roleRef:
  kind: Role
  name: openclaw-self
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: openclaw-app-manager
  namespace: app
subjects:
  - kind: ServiceAccount
    name: openclaw-gateway
    namespace: openclaw
roleRef:
  kind: Role
  name: openclaw-app-manager
```

**What this gives OpenClaw:**
- **Read-only** on its own namespace (observe itself, read logs)
- **Full control** of the `app` namespace (deploy, scale, restart, debug)
- **Zero access** to infrastructure namespaces (traefik, registry, dns)

The full `app` namespace access is the escape hatch. OpenClaw *can* kubectl into the app namespace to debug a crashed pod, inspect logs, restart a deployment, or even do an emergency helm rollback. But the standing instruction is: don't. Use the process.

---

# Part 11: Deployment Model

## The Rule (enforced in SOUL.md, not RBAC)

> **To deploy changes to the application, merge to the deployment branch and let GitHub Actions handle it.** Direct kubectl/helm commands against the app namespace are reserved for debugging and emergency recovery only — never for routine deployment.

This is how a real dev team works. They have prod access. They don't use it to deploy. They use it when something's on fire.

## Normal Flow: Merge to Deploy Branch → GitHub Actions

```
OpenClaw merges plan branch into mac-mini
  ↓
GitHub Actions triggers automatically
  ↓
CI pipeline: build images → push to registry → helmfile apply → wait for rollout
  ↓
OpenClaw monitors via `gh run watch`
  ↓
pass: run E2E tests, update plan status
fail: OpenClaw reads the CI failure logs, fixes on plan branch, re-merges
```

**What OpenClaw does:**
- Merges plan branch into `mac-mini` (`git merge`, then `git push`)
- Monitors CI runs (`gh run watch`, `gh run view`)
- Reads CI failure logs (`gh run view --log-failed`)
- Fixes issues on the plan branch and re-merges

**What OpenClaw does NOT do (normally):**
- `docker build` / `docker push`
- `helm upgrade` / `helmfile apply`
- `kubectl apply` / `kubectl rollout restart`
- `kubectl scale`

## Break-Glass: Direct K8s Access

When something is broken and CI/CD can't fix it (or is too slow), OpenClaw can:

| Action | When |
|--------|------|
| `kubectl logs -n app deployment/backend` | Debugging a crash or error |
| `kubectl describe pod -n app ...` | Investigating OOMKills, scheduling issues |
| `kubectl rollout restart -n app deployment/backend` | Pod stuck in bad state |
| `helm rollback -n app backend` | Deployment broke the app, need immediate rollback |
| `kubectl exec -n app ...` | Deep debugging (DB queries, network checks) |
| `kubectl port-forward -n app ...` | Testing internal services |

**The key distinction:** These are *reactive debugging* actions, not *proactive deployment* actions. OpenClaw should document in the incident report why it went direct.

## What CI/CD-First Saves

1. **No Docker/buildkit in the OpenClaw container** — CI runners handle image builds
2. **No DinD sidecar or Docker socket** — the whole image build problem goes away
3. **Audit trail** — every deployment is a GitHub Actions run, visible in the repo
4. **Tested pipeline** — if CI/CD works for OpenClaw, it works for humans too
5. **No drift** — same deploy path regardless of who triggers it
6. **Natural gate** — CI can run build verification, unit tests, linting before deploy
7. **Simpler OpenClaw image** — just needs `gh` CLI and `kubectl` (already has both)

## What It Costs

- **~2-5 minutes per deploy** — GitHub Actions cold start + build + rollout
- **GitHub dependency** — if Actions is down, OpenClaw can't deploy (but can break-glass)
- **Can't iterate as fast** — no rapid build-deploy-test loop inside the pod

The cost is acceptable. OpenClaw doesn't need rapid deploy iteration — it works on the next feature while waiting. And if GitHub Actions is down, that's what the break-glass access is for.

## Environment Configuration

OpenClaw needs to know its environment context. Injected via environment variables in the Helm chart:

```yaml
env:
  OPENCLAW_APP_NAMESPACE: "app"
  OPENCLAW_SELF_NAMESPACE: "openclaw"
  DEPLOY_ENV: "mac-mini"
  DEPLOY_BRANCH: "mac-mini"       # branch that triggers CI/CD for this environment
  GITHUB_REPO: "owner/automated-repo"
```

These get referenced in SOUL.md so OpenClaw knows:
- Which namespace is "mine" for observability
- Which branch to merge into to trigger deployment
- Which repo to create PRs against

## E2E Testing Post-Deploy

E2E tests run after successful deployment, not before. They validate the live running application.

**Trigger:** CI/CD deploy succeeds → OpenClaw runs E2E
**How:** `task e2e:test` from within the OpenClaw pod (Playwright against the live app endpoints)
**On failure:** Create a GitHub issue with failure details
**On pass:** Plan is fully verified — submit PR to main

> **Note:** Playwright/Chromium needs to be available in the OpenClaw container. Currently disabled in the Dockerfile due to NixOS base image issues. This needs to be resolved — either install Chromium in the container or run E2E as a separate CI step.

---

# Part 12: Plan Watcher (Trigger Mechanism)

## How OpenClaw Gets Work

The human pushes a `plan.md` with `status: ready` to the `mac-mini` branch. A real cron job (not OpenClaw's built-in cron) inside the OpenClaw container detects it and tells the gateway to start working.

```
Human creates plan.md → pushes to mac-mini branch
  ↓ (within 5 minutes)
Cron: git fetch → detect ready plan → message OpenClaw gateway
  ↓
OpenClaw: create plan branch → decompose → execute → validate → deploy → PR
```

## The Script

**`/workspace/scripts/plan-watcher.sh`** (runs inside the OpenClaw container)

```bash
#!/bin/bash
set -euo pipefail

DEPLOY_BRANCH="${DEPLOY_BRANCH:-mac-mini}"
GATEWAY_URL="${GATEWAY_URL:-http://localhost:18789}"
WORKSPACE="/workspace/repo"
LOCK_FILE="/tmp/plan-watcher.lock"
LOG_FILE="/workspace/logs/plan-watcher.log"

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >> "$LOG_FILE"
}

# Prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
  pid=$(cat "$LOCK_FILE")
  if kill -0 "$pid" 2>/dev/null; then
    exit 0  # Previous run still active
  fi
  rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

cd "$WORKSPACE"

# 1. Fetch latest from remote
git fetch origin "$DEPLOY_BRANCH" --quiet 2>/dev/null || {
  log "ERROR: git fetch failed"
  exit 1
}

# 2. Check if OpenClaw is already working on a plan
# Look for any plan with status "executing" or "decomposing" in local backlog
BUSY=$(find .backlog -maxdepth 2 -name "status.json" -exec grep -l '"status":\s*"executing"\|"status":\s*"decomposing"' {} \; 2>/dev/null || true)
if [ -n "$BUSY" ]; then
  log "INFO: Already working on a plan, skipping"
  exit 0
fi

# 3. Check the remote branch for plans with status "ready"
PLANS=$(git ls-tree --name-only "origin/$DEPLOY_BRANCH" .backlog/ 2>/dev/null || true)

for plan_dir in $PLANS; do
  plan_id=$(basename "$plan_dir")
  status_file="$plan_dir/status.json"

  # Read status.json from the remote branch (not local)
  status=$(git show "origin/$DEPLOY_BRANCH:$status_file" 2>/dev/null || echo "")
  if [ -z "$status" ]; then
    continue
  fi

  # Check if status is "ready"
  plan_status=$(echo "$status" | grep -o '"status":\s*"[^"]*"' | head -1 | grep -o '"[^"]*"$' | tr -d '"')
  if [ "$plan_status" = "ready" ]; then
    log "INFO: Found ready plan: $plan_id"

    # 4. Notify the OpenClaw Gateway
    MESSAGE="New plan ready for execution: $plan_id. The plan is on the $DEPLOY_BRANCH branch at .backlog/$plan_id/plan.md with status 'ready'. Create a plan branch openclaw/$plan_id from $DEPLOY_BRANCH, then decompose and execute it following the orchestration loop."

    response=$(curl -sf -X POST "$GATEWAY_URL/api/message" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${OPENCLAW_AUTH_TOKEN:-}" \
      -d "{\"message\": \"$MESSAGE\"}" 2>&1) || {
      log "ERROR: Failed to notify gateway for plan $plan_id: $response"
      continue
    }

    log "INFO: Notified gateway to start plan $plan_id"
    # Only trigger one plan at a time
    break
  fi
done

log "INFO: Plan watcher check complete"
```

## Cron Setup

**In the entrypoint.sh:**

```bash
#!/bin/bash
# ... existing entrypoint setup ...

# Start plan watcher cron
mkdir -p /workspace/logs /workspace/scripts
echo "*/5 * * * * /workspace/scripts/plan-watcher.sh >> /workspace/logs/plan-watcher.log 2>&1" | crontab -
crond -b  # Run cron daemon in background

# Start OpenClaw Gateway (foreground)
exec openclaw gateway
```

## What the Script Does

1. **Lock check** — prevents overlapping runs if a previous check takes > 5 minutes
2. **Git fetch** — pulls latest refs from origin (specifically the deploy branch)
3. **Busy check** — looks at local backlog for any plan already in `executing` or `decomposing` state. If OpenClaw is already working, skip.
4. **Scan remote branch** — reads `status.json` files from `origin/mac-mini` (not local) to find plans with `status: ready`
5. **Notify gateway** — sends a message to the OpenClaw Gateway API telling it to pick up the plan
6. **One at a time** — only triggers the first ready plan found, since we're doing one plan at a time

## What the Script Does NOT Do

- Does not modify any files or git state
- Does not start decomposition itself
- Does not check out the branch or merge anything
- It's purely a detector and notifier

## The Gateway API Endpoint

> **TODO:** Verify the correct API endpoint for the OpenClaw Gateway. The Web UI exists at port 18789, so there's definitely a message API behind it. Candidates: `POST /api/message`, `POST /api/chat`. Check the OpenClaw Gateway documentation or source for the exact format.

## The Human's Workflow

```
1. Write a plan.md (or have Claude Code help write it)
2. Place it at .backlog/{plan-id}/plan.md
3. Create status.json with status: "ready"
4. Commit and push to mac-mini branch
5. Within 5 minutes, OpenClaw picks it up and starts working
6. Check progress anytime via OpenClaw Web UI at openclaw.mac-mini
7. When done, review the PR from openclaw/{plan-id} → main
```

## Monitoring

The script logs to `/workspace/logs/plan-watcher.log`:

```
[2026-03-28T15:00:00Z] INFO: Plan watcher check complete
[2026-03-28T15:05:00Z] INFO: Already working on a plan, skipping
[2026-03-28T15:10:00Z] INFO: Found ready plan: p-a1b2c3
[2026-03-28T15:10:01Z] INFO: Notified gateway to start plan p-a1b2c3
```

---

# Part 13: SOUL.md Evolution

## Decision: SOUL.md becomes the team lead playbook

The current SOUL.md handles decomposition routing. It needs to grow to cover the full orchestration loop, deployment rules, and environment ownership. High-level structure:

```
SOUL.md
├── Identity (exists, rethink)
│   └── "You are a team lead with a full development team at your disposal"
├── Trigger (new)
│   ├── A cron job (real cron, not OpenClaw cron) runs every 5 minutes
│   ├── Script: git fetch → check mac-mini branch for ready plans → notify gateway
│   ├── Gateway receives message: "plan p-{id} is ready"
│   └── See plan-watcher script for details
├── Orchestration Loop (new)
│   ├── Pick up the current plan (one at a time)
│   ├── Determine feature execution order (dependency graph)
│   ├── For each feature: execute tasks sequentially in dependsOn order
│   ├── After each feature: run build sweep
│   ├── After all features: run plan sweep
│   ├── Merge to deploy branch → monitor CI/CD
│   ├── Run E2E tests post-deploy
│   ├── Submit PR to main for human review
│   └── Done — wait for next plan
├── Skill Routing (exists, extend)
│   ├── decompose-1/2/3 (existing)
│   ├── rlm-execute (new)
│   ├── rlm-validate (new)
│   └── rlm-pr (new)
├── Delegation Rules (exists, extend)
│   ├── Never modify code directly (existing)
│   ├── Always delegate to Claude Code ACP sessions (existing)
│   ├── One plan at a time, sequential features, sequential tasks
│   └── Status updates: update frontmatter + status.json after every state change
├── Deployment Rules (new — critical)
│   ├── To deploy: merge plan branch to `mac-mini` → GitHub Actions handles the rest
│   ├── Monitor CI runs via `gh run watch` / `gh run view`
│   ├── React to CI failures by reading logs and fixing on the plan branch
│   ├── NEVER use kubectl/helm to deploy — that's what CI/CD is for
│   ├── Direct K8s access (kubectl, helm) is for debugging and emergency recovery ONLY
│   └── If you use break-glass access: document why in an incident report
├── Environment Awareness (new)
│   ├── You own the `app` namespace — it's your environment to keep healthy
│   ├── You can observe it (logs, pod status, resource usage) anytime
│   ├── You are responsible for knowing when it's healthy and when it's not
│   └── Post-deploy: verify health, run E2E, report issues
└── Decision Framework (new)
    ├── When to retry vs block a task
    ├── When to escalate to operator
    ├── When to break-glass vs wait for CI/CD
    └── How to handle blocked tasks within a plan
```

**Key principle:** SOUL.md stays high-level. It defines *what* the orchestrator does and *when*, not *how* (the how lives in skills). Think of it as a team lead's playbook, not an implementation manual. The deployment rules are *instructions*, not physical restrictions — OpenClaw has the K8s access but is told to follow the process unless there's a genuine emergency.

---

# Part 14: Error Recovery

## Failure Taxonomy

| Failure | Detection | Response | Escalation |
|---------|-----------|----------|------------|
| **Task execution fails** (build/lint/type errors) | Executor reports failure | Executor retries within session (30-min timeout) | If session times out: mark `rejected`, retry as new session |
| **Task validation rejects** | Validator returns REJECT | Re-execute with feedback (max 3 attempts) | After 3 attempts: mark `blocked` |
| **Feature sweep fails** | Build/test command fails | Identify broken commit, re-open that task | If can't identify: mark feature `blocked` |
| **ACP session timeout** | 30-min timeout hit | Retry task as new session (counts as attempt) | After 3 timeouts: mark `blocked` |
| **Session spawn fails** | ACP error response | Retry spawn after backoff (3 retries) | After 3 spawn failures: pause execution, alert operator |
| **CI/CD build fails** | `gh run view --log-failed` | Read logs, fix on plan branch, re-merge to deploy branch | After 3 fix attempts: pause, alert operator |
| **CI/CD deploy fails** | `gh run view --log-failed` | Read logs, diagnose (bad manifest? resource limit?) | If app degraded: break-glass `helm rollback`, incident report |
| **App unhealthy post-deploy** | Health check / pod status | Check logs (`kubectl logs -n app`), assess severity | If critical: break-glass rollback + incident report |
| **E2E tests fail** | Playwright exit code | Diagnose failure, fix on plan branch if code issue | If environment issue: incident report |
| **Blocked task cascade** | Dependent tasks can't proceed | Mark all downstream tasks `blocked` | Log full blocked chain |

## Operator Escalation

When the orchestrator encounters something it can't resolve:
1. Create a structured report in `.backlog/{plan-id}/incidents/{timestamp}.md`
2. Include: what failed, what was tried, current state, suggested next steps
3. Mark the affected feature as `needs-attention` in status.json
4. **Stop.** With one plan at a time, there's no "other work" to continue. Alert the operator and wait.

**No automatic rollbacks on main.** The plan branch is the working space — main is never affected until the human merges the PR. If the deploy branch (`mac-mini`) gets broken, break-glass rollback is available.

---

# Part 15: Concurrency Model

**V1 is deliberately simple: one thing at a time.**

```
1 plan → features sequentially → tasks sequentially
       → 1 ACP session at a time (execute or validate, never both)
```

At any moment, there is exactly:
- 1 plan being worked
- 1 feature being worked within that plan
- 1 task being executed or validated

This uses 1-2 ACP sessions total (executor + orchestrator, or validator + orchestrator). Well within the 20-session limit. The remaining capacity is headroom for retries and future parallelization.

**Future optimization:** Parallelize independent features within a plan (those with no cross-feature dependencies). This is a pure scheduling change in the orchestrator — the skills don't need to change.

---

# Part 16: OpenClaw's Full Lifecycle Summary

```
Code Lifecycle
├── Decompose plans → tasks
├── Execute tasks (implement code)
├── Validate implementations
├── Create final PR for human review

Deployment Monitoring
├── Merge plan branch to mac-mini → triggers GitHub Actions
├── Watch CI runs after merge
├── Read CI failure logs and fix issues
├── Monitor app health post-deploy (kubectl read-only)

Environment Observability (break-glass access available)
├── Check pod health (restarts, OOMKills)
├── Read application logs
├── Inspect resource usage
├── Debug crashes or errors
└── Emergency rollback if needed

E2E Validation
├── Run Playwright tests post-deploy
├── Report results
└── Create issues for failures
```

---

# Part 17: Implementation Order

1. **rlm-execute** skill — the core. Can test immediately against real tasks from p-e7a3f1
2. **Status tracking** — add status/attempts to task frontmatter, extend plan status.json
3. **rlm-validate** skill — enables the feedback loop
4. **Feedback mechanism** — feedback.md files and retry flow
5. **SOUL.md update** — full orchestration loop, deployment rules, environment awareness
6. **rlm-pr** skill — plan branch → `main` PR for human review
7. **Plan watcher** — cron script + entrypoint changes for automatic plan detection
8. **RBAC update** — replace ClusterRole with namespaced Roles (openclaw read-only, app full)

Steps 1-4 give us a working execution + validation loop we can test against real tasks.
Step 5 gives OpenClaw the playbook to run the full pipeline autonomously.
Steps 6-8 connect the trigger, output, and environment access.

---

# Part 18: Implementation Checklist (Environment)

1. **Replace ClusterRole with namespaced Roles** — scope to `openclaw` (read) + `app` (full)
2. **Add environment variables** to OpenClaw Helm chart (`OPENCLAW_APP_NAMESPACE`, `DEPLOY_BRANCH`, etc.)
3. **Verify `gh` CLI** works from inside the OpenClaw pod (auth, PR creation, run monitoring)
4. **Verify `kubectl`** works against `app` namespace from inside the pod (ServiceAccount token)
5. **Add deployment rules** to SOUL.md (CI/CD first, break-glass for emergencies)
6. **Resolve Playwright/Chromium** in OpenClaw container for E2E testing
7. **Verify Gateway API endpoint** for plan watcher notifications
8. **Install cron** in OpenClaw container and add plan-watcher.sh to entrypoint

---

# Part 19: Security

## Audit Summary

OpenClaw legitimately needs: `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, `OPENCLAW_AUTH_TOKEN`, `OPENCLAW_WEBHOOK_SECRET`. These are its own credentials for doing its job. No issue there.

The problems are about what OpenClaw can access that it shouldn't, and how secrets are stored.

## Critical: ClusterRole Exposes All Cluster Secrets

**Current state:** OpenClaw's RBAC (`projects/openclaw/chart/templates/rbac.yaml`) grants a ClusterRole with `resources: ["*"], verbs: ["*"]` across `core`, `apps`, `batch`, and `networking.k8s.io` API groups. This is cluster-wide.

**What this means:** OpenClaw (or any Claude Code session it spawns) can:
```bash
# Read database password
kubectl get secret database-secret -n app -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d

# Read Keycloak admin password
kubectl get secret keycloak-secret -n app -o jsonpath='{.data.KEYCLOAK_ADMIN_PASSWORD}' | base64 -d

# Read backend API keys
kubectl get secret backend-secret -n app -o jsonpath='{.data.ANTHROPIC_API_KEY}' | base64 -d

# Read secrets in ANY namespace (traefik TLS certs, registry config, etc.)
kubectl get secrets --all-namespaces
```

OpenClaw has zero business reading database passwords or Keycloak admin creds. It doesn't connect to the DB. It doesn't administer Keycloak. These are application-internal secrets.

**Fix:** Replace ClusterRole with namespaced Roles (already in the design — Part 10). The `app` namespace Role should explicitly exclude Secrets:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: openclaw-app-manager
  namespace: app
rules:
  # Observe pods, deployments, services (for health checks and debugging)
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec", "services", "endpoints"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "replicasets"]
    verbs: ["get", "list", "watch", "patch", "update"]
  # Rollback capability (helm rollback needs deployment update)
  - apiGroups: ["apps"]
    resources: ["deployments/rollback"]
    verbs: ["create"]
  # View ingress for debugging routing
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["get", "list", "watch"]
  # NO access to: secrets, configmaps, namespaces, jobs, batch resources
```

This gives OpenClaw what it needs for debugging and break-glass rollbacks, without exposing application secrets. If OpenClaw needs to read a configmap for debugging, it can `kubectl logs` the pod instead — the app's behavior reveals its config.

> **Note:** This is a tighter scope than the original proposal in Part 10 which gave `resources: ["*"], verbs: ["*"]` to the app namespace. That was too broad. OpenClaw doesn't need to create/delete pods, manage jobs, or read secrets in the app namespace.

## High: Secrets on Persistent Disk

**Current state:** The entrypoint writes secrets to the 50Gi workspace PVC:
- `~/.git-credentials` — contains `GITHUB_TOKEN` in plaintext
- `~/.openclaw/agents/main/agent/auth-profiles.json` — contains `ANTHROPIC_API_KEY`

These files persist across pod restarts because they're on the PVC.

**Risk:** If the PVC is backed up, migrated, or the volume is accessed by another pod (misconfiguration, debugging), these secrets are exposed.

**Fix: Use tmpfs for secrets, not the workspace PVC.**

```yaml
# In the OpenClaw deployment template, add an emptyDir tmpfs volume:
volumes:
  - name: secrets-tmp
    emptyDir:
      medium: Memory  # RAM-backed, never written to disk
      sizeLimit: 10Mi

volumeMounts:
  - name: secrets-tmp
    mountPath: /home/agent/.git-credentials
    subPath: git-credentials
  - name: secrets-tmp
    mountPath: /home/agent/.openclaw/agents/main/agent/auth-profiles.json
    subPath: auth-profiles.json
```

Or simpler: update `entrypoint.sh` to write these files to `/tmp` (which is typically tmpfs in containers) and symlink:

```bash
# Write to tmpfs, not PVC
echo "https://x-access-token:${GITHUB_TOKEN}@github.com" > /tmp/.git-credentials
chmod 600 /tmp/.git-credentials
git config --global credential.helper "store --file=/tmp/.git-credentials"
```

## Medium: Tighten the App Namespace Role for Break-Glass

The original Part 10 proposal gave `resources: ["*"], verbs: ["*"]` in the `app` namespace. This was designed as "full control for break-glass." But even break-glass doesn't need:
- Secret read/write (OpenClaw doesn't manage app secrets)
- ConfigMap write (CI/CD handles config changes)
- Namespace create/delete (OpenClaw doesn't manage namespaces)
- Job create (OpenClaw doesn't run batch jobs in the app namespace)

The tightened Role above covers the actual break-glass scenarios:
- Read pod logs and status → `pods`, `pods/log` get/list/watch
- Restart stuck pods → `deployments` patch/update
- Rollback broken deploys → `deployments/rollback` create
- Inspect routing → `ingresses` get/list/watch

## Medium: Network Policies

OpenClaw can currently reach any service in the cluster via DNS. This is mostly fine (it needs to health check the app), but it could be tightened:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: openclaw-egress
  namespace: openclaw
spec:
  podSelector:
    matchLabels:
      app: openclaw-gateway
  policyTypes:
    - Egress
  egress:
    # Allow DNS resolution
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
    # Allow HTTPS to GitHub and Anthropic APIs
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443
    # Allow HTTP to app namespace services (health checks, E2E)
    - to:
        - namespaceSelector:
            matchLabels:
              name: app
      ports:
        - protocol: TCP
          port: 8080
```

This is a nice-to-have, not urgent. The RBAC fix is what matters most.

## Low: SOUL.md Security Rules

Add to SOUL.md's Deployment Rules section:

```
├── Security Rules (new)
│   ├── NEVER read Kubernetes Secrets — you don't need application passwords
│   ├── NEVER store secrets in the workspace repo or backlog files
│   ├── NEVER log or commit API keys, tokens, or passwords
│   ├── If you encounter a secret accidentally, do not persist it anywhere
│   └── Report any security concerns in incident reports
```

Like the deployment rules, these are instructions — the RBAC changes make them physically enforced too, but the instructions prevent the LLM from even attempting.

## What's Already Fine

| Item | Why It's OK |
|------|-------------|
| `ANTHROPIC_API_KEY` in OpenClaw env | OpenClaw needs it to call the API. Can't function without it. |
| `GITHUB_TOKEN` in OpenClaw env | OpenClaw needs it to push, create PRs. Core functionality. |
| `CLAUDE_CODE_OAUTH_TOKEN` in env | ACP sessions need it. Core functionality. |
| `approve-all` permission mode | Intentional for autonomous operation. OpenClaw's job is to modify files without per-change human approval. |
| `.env` file on host | Gitignored, not tracked. Only exists on the deployment machine and in GitHub Actions secrets. |
| Service DNS URLs in env | OpenClaw needs to know where services are for health checks and E2E. Not sensitive. |
| ACP sessions inheriting env | They need ANTHROPIC_API_KEY and GITHUB_TOKEN to do their work. Same security boundary as the parent. |

## Implementation Priority

1. **Replace ClusterRole with namespaced Roles** (critical — do when we do step 8 of implementation order)
   - `openclaw` namespace: read-only (pods, logs, deployments)
   - `app` namespace: observe + rollback (no secrets, no configmaps, no create/delete)
2. **Move secrets to tmpfs** (high — update entrypoint.sh and deployment template)
3. **Add security rules to SOUL.md** (low — do when we update SOUL.md in step 5)
4. **Network policies** (nice-to-have — add when hardening the environment)

---

# Part 20: Implementation Handoff

This section is the cold-start guide. A new Claude Code session should be able to read this and execute the full implementation without needing to explore the codebase for patterns.

## Pattern Reference

Before creating any skill, read this existing skill as the pattern reference:
- **`projects/openclaw/app/skills/rlm-code/SKILL.md`** — simplest skill, shows the format

Skills are markdown files with YAML frontmatter:
```markdown
---
name: skill-name
description: One-line description of what this skill does
---

# skill-name

{What this skill does — one paragraph}

## Input
{What the skill receives}

## {Skill-specific sections}
{Instructions for Claude Code when this skill is invoked}
```

Skills live at `projects/openclaw/app/skills/{skill-name}/SKILL.md`. The directory name must match the `name` field in frontmatter. OpenClaw loads them from the `./skills` directory via `openclaw.json`.

## Step 1: Create `rlm-execute` Skill

**Create:** `projects/openclaw/app/skills/rlm-execute/SKILL.md`

This is the core skill — it implements a single atomic task from a task.md file.

```markdown
---
name: rlm-execute
description: Implement an atomic task from a task.md file on the plan branch
---

# rlm-execute

Implement a single atomic task from the backlog. You receive a task.md file that specifies exactly what to build — files to create, patterns to follow, and acceptance criteria to meet.

## Input

You will be told:
- The **task.md file path** (e.g., `.backlog/p-e7a3f1/frontend/auth-login/service.task.md`)
- The **feature plan.md path** (e.g., `.backlog/p-e7a3f1/frontend/auth-login/plan.md`)
- The **working directory** — you are already on the plan branch

## Before You Start

1. Read the task.md completely — understand the Purpose, Context, and Specification
2. Read the feature plan.md — understand the broader feature context
3. Read every file listed in the task's References section
4. If a `{concern}.feedback.md` file exists alongside the task, read it — it contains feedback from a previous failed attempt. Address every point.

## Implementation

1. **Read existing code** before creating new files. Understand the patterns already in use.
2. **Create/modify only the files listed** in the task's Specification → Files section.
3. **Follow the conventions** listed in the task's Context → Conventions section exactly.
4. **Implement all requirements** in the task's Specification → Requirements section.
5. **Meet every acceptance criterion** — these are your definition of done.

## Local Validation

After implementation, run these checks. Fix any failures before committing.

**For frontend (Angular/React) changes:**
```bash
cd projects/application/frontend
npx tsc --noEmit          # Type check
npm run lint              # Lint check
npm run build             # Build check
npm test -- --watchAll=false  # Unit tests (if applicable)
```

**For backend (NestJS) changes:**
```bash
cd projects/application/backend
npx tsc --noEmit          # Type check
npm run lint              # Lint check
npm run build             # Build check
npm test                  # Unit tests (if applicable)
```

Adapt commands based on the project specified in the task. If the build or type-check fails, fix the issue. You have up to 30 minutes.

## Commit

When all checks pass, commit your changes:

```bash
git add {specific files you created/modified}
git commit -m "feat({feature-slug}): implement {concern-type} [t-{task-id}]"
```

- Only add files you created or modified. Do not `git add .`
- The commit message must include the task ID in brackets
- Do not push — the orchestrator handles pushing when ready

## Safety Rules

- Never modify files outside the task's specified file list
- Never modify infrastructure, CI/CD, Helm charts, or GitHub Actions
- Never work on main — you should already be on a plan branch
- If you encounter a dependency that doesn't exist yet (e.g., a service the task imports from), check if a prior task's commit already created it. If not, report the missing dependency — do not create it yourself.
- Do not write tests unless the task explicitly asks for them

## Done

Report back with:
- List of files created/modified
- Commit hash
- Whether all local validation checks passed
- Any issues encountered
```

**Done when:** The skill file exists, follows the frontmatter format, and contains instructions that a Claude Code session can follow to implement any task.md from the backlog.

---

## Step 2: Add Status Tracking to Task Schema

**Modify:** `.backlog/p-e7a3f1/status.json` (extend the existing file)

The existing `status.json` has a simple structure. Extend it to include feature and task tracking:

```json
{
  "planId": "p-e7a3f1",
  "status": "decomposed",
  "branch": null,
  "currentFeature": null,
  "currentTask": null,
  "features": {},
  "updated": "2026-03-28T12:00:00Z",
  "history": [
    { "status": "draft", "at": "2026-03-27T00:00:00Z" },
    { "status": "ready", "at": "2026-03-27T10:00:00Z" },
    { "status": "decomposed", "at": "2026-03-28T12:00:00Z" }
  ]
}
```

**Modify:** Every `*.task.md` file in `.backlog/p-e7a3f1/` — add `status: ready` and `attempts: 0` to their frontmatter.

The frontmatter currently has:
```yaml
---
id: t-{hex}
parent: {parent-id}
dependsOn: [...]
created: {ISO-8601}
updated: {ISO-8601}
---
```

Add to each:
```yaml
---
id: t-{hex}
parent: {parent-id}
dependsOn: [...]
status: ready
attempts: 0
created: {ISO-8601}
updated: {ISO-8601}
---
```

**Done when:** `status.json` has the extended schema with `branch`, `currentFeature`, `currentTask`, `features` fields. All task.md files have `status: ready` and `attempts: 0` in their frontmatter.

---

## Step 3: Create `rlm-validate` Skill

**Create:** `projects/openclaw/app/skills/rlm-validate/SKILL.md`

```markdown
---
name: rlm-validate
description: Validate a task implementation against its acceptance criteria
---

# rlm-validate

Review a task implementation by comparing the code diff against the task.md acceptance criteria. You are a code reviewer, not a builder.

## Input

You will be told:
- The **task.md file path** (contains the acceptance criteria)
- The **commit hash(es)** to review
- The **working directory** — you are on the plan branch

## Process

1. Read the task.md completely — focus on:
   - Specification → Acceptance Criteria (your rubric)
   - Specification → Files (expected file list)
   - Context → Conventions (coding standards to verify)

2. View the diff for the commit(s):
   ```bash
   git show {commit-hash} --stat    # See which files changed
   git show {commit-hash}           # See the full diff
   ```

3. For each acceptance criterion, verify it is met by the diff. Check:
   - Does the code do what the criterion says?
   - Are all specified files present?
   - Does the code follow the conventions listed in the task?
   - Are there obvious bugs, missing error handling, or security issues?
   - Does the code import/reference dependencies correctly?

4. **Do NOT** re-run builds, type-checks, lint, or tests. The executor already did this. You are reviewing the code, not the build.

## Verdict

Return a structured verdict in exactly this format:

### If all criteria pass:

```
VERDICT: PASS

All acceptance criteria met.
```

### If any criteria fail:

```
VERDICT: REJECT

### Failed Criteria
- [ ] {criterion text} — {what's wrong and what should change}
- [ ] {criterion text} — {what's wrong and what should change}

### Notes
{Additional context about why this doesn't meet the spec. Be specific — the executor will read this in a fresh session with no prior context.}
```

## Rules

- Be specific in feedback. "Doesn't follow conventions" is useless. "Uses `async/await` but the convention in Context says to use RxJS `Observable`" is actionable.
- Only reject for real issues — acceptance criteria not met, wrong files, convention violations, bugs. Do not reject for style preferences.
- Do not modify any files. You are a reviewer.
- Do not suggest improvements beyond what the acceptance criteria require.
```

**Done when:** The skill file exists and contains clear instructions for reviewing a task implementation against its acceptance criteria, with a structured PASS/REJECT verdict format.

---

## Step 4: Create Feedback Mechanism

No new files to create — this is a convention enforced by the orchestrator (SOUL.md).

When `rlm-validate` returns `REJECT`, the orchestrator:
1. Creates/appends to `.backlog/{plan}/{project}/{feature}/{concern}.feedback.md`
2. Increments the task's `attempts` count in frontmatter
3. Sets task status to `rejected`
4. Re-invokes `rlm-execute` with the same task (executor reads the feedback file)

**Done when:** The SOUL.md update (Step 5) includes the feedback loop logic.

---

## Step 5: Update SOUL.md

**Modify:** `projects/openclaw/app/SOUL.md`

Replace the entire file. The new SOUL.md should contain:

### Section 1: Identity
- You are a team lead with a full development team (Claude Code sessions) at your disposal
- You are an orchestrator — delegate ALL work to Claude Code via ACP sessions
- You own the `app` namespace — it's your environment

### Section 2: How You Get Work
- A cron job runs every 5 minutes checking for ready plans on the `mac-mini` branch
- When triggered, you receive a message with the plan ID
- Create a plan branch `openclaw/{plan-id}` from the `mac-mini` branch
- Work one plan at a time, sequentially

### Section 3: Orchestration Loop
The main algorithm — this is the core of what OpenClaw does:

```
1. Receive notification: plan p-{id} is ready
2. git checkout mac-mini && git pull
3. git checkout -b openclaw/p-{id}
4. Update status.json: status → "decomposing"
5. Delegate decompose-1 → decompose-2 → decompose-3 (existing pipeline)
6. Update status.json: status → "executing"
7. Determine feature execution order:
   a. Read all feature plan.md files
   b. Parse cross-feature dependencies from Boundaries sections
   c. Topological sort: features with no upstream deps go first
8. For each feature (in dependency order):
   a. Update status.json: currentFeature → this feature
   b. Read all task.md files in the feature directory
   c. Topological sort tasks by dependsOn
   d. For each task (in dependency order):
      i.   Update task frontmatter: status → "executing", attempts += 1
      ii.  Spawn ACP session with rlm-execute skill
           - Pass: task.md path, feature plan.md path
      iii. Read executor result
      iv.  Update task frontmatter: status → "implemented"
      v.   Spawn ACP session with rlm-validate skill
           - Pass: task.md path, commit hash from executor
      vi.  Read validator verdict
      vii. If PASS: update task status → "validated"
      viii.If REJECT and attempts < 3:
           - Write/append feedback to {concern}.feedback.md
           - Update task status → "rejected"
           - Go to (i) — retry with fresh session
      ix.  If REJECT and attempts = 3:
           - Update task status → "blocked"
           - Mark dependent tasks as "blocked" (cascade)
           - Log blocked chain
           - Continue to next non-blocked task
   e. After all tasks: run feature build sweep
      - cd to project directory, run build + type-check
      - If fails: identify broken commit, re-open that task
   f. Update feature status → "validated"
9. After all features: run plan build sweep
   - Full build + all tests
10. Push plan branch to origin
11. Merge plan branch into mac-mini:
    git checkout mac-mini && git merge openclaw/p-{id} && git push
12. Monitor GitHub Actions: gh run watch
13. If CI passes: run E2E tests (task e2e:test)
14. If CI fails: read logs (gh run view --log-failed), fix on plan branch, re-merge
15. Update status.json: status → "deployed"
16. Spawn ACP session with rlm-pr skill
    - Creates PR: openclaw/p-{id} → main
17. Update status.json: status → "pr-submitted"
18. Done. Wait for next plan.
```

### Section 4: Skill Routing
- `rlm-decompose-1/2/3` — decomposition pipeline (existing)
- `rlm-execute` — implement a task.md
- `rlm-validate` — review implementation against acceptance criteria
- `rlm-pr` — create the final PR to main

### Section 5: Delegation Rules
- Never modify code directly — always delegate to Claude Code ACP sessions
- One plan at a time, features sequential, tasks sequential
- Each skill invocation is a fresh ACP session (context isolation)
- Update task frontmatter AND status.json after every state transition

### Section 6: Deployment Rules
- To deploy: merge plan branch to `mac-mini` → GitHub Actions handles the rest
- Monitor CI runs via `gh run watch` / `gh run view`
- React to CI failures by reading logs and fixing on the plan branch
- NEVER use kubectl/helm to deploy — that's what CI/CD is for
- Direct K8s access (kubectl, helm) is for debugging and emergency recovery ONLY
- If you use break-glass access: document why in an incident report

### Section 7: Environment Awareness
- You own the `app` namespace — it's your environment
- You can observe it (kubectl logs, pod status) anytime
- Post-deploy: verify health, run E2E, report issues

### Section 8: Security Rules
- NEVER read Kubernetes Secrets — you don't need application passwords
- NEVER store secrets in the workspace repo or backlog files
- NEVER log or commit API keys, tokens, or passwords

### Section 9: Constraints
- Max 20 concurrent ACP sessions (but V1 uses 1-2 at a time)
- 30-minute timeout per ACP session
- 3 attempts max per task before marking blocked
- Always delegate to Claude Code — never modify files directly

**Done when:** SOUL.md contains all 9 sections, the orchestration loop is a concrete algorithm (not vague guidance), and a new OpenClaw session could follow it step-by-step.

---

## Step 6: Create `rlm-pr` Skill

**Create:** `projects/openclaw/app/skills/rlm-pr/SKILL.md`

```markdown
---
name: rlm-pr
description: Create a PR from the plan branch to main for human review
---

# rlm-pr

Create a pull request from the plan branch to main. This is the final deliverable — the human reviews, tests, and merges.

## Input

You will be told:
- The **plan branch name** (e.g., `openclaw/p-e7a3f1`)
- The **plan.md file path** (e.g., `.backlog/p-e7a3f1/plan.md`)
- The **status.json file path** (for execution summary)

## Process

1. Read the plan.md — extract the plan title, purpose, and scope
2. Read the status.json — get feature list, task counts, any blocked items
3. Generate the PR:

```bash
gh pr create \
  --base main \
  --head {plan-branch} \
  --title "feat: {plan title}" \
  --body "$(cat <<'EOF'
## Summary

{Plan purpose — 1-3 sentences from plan.md}

## Features Implemented

{For each feature in status.json:}
- [x] **{feature-name}** — {brief description from feature plan.md}
  - {N} tasks completed, {M} blocked (if any)

## Blocked Items

{If any tasks are blocked, list them with the reason from feedback.md}

## Environment

This plan is deployed and running on the mac-mini environment.
Test at: https://app.mac-mini

## Plan Reference

Plan ID: {plan-id}
Backlog: `.backlog/{plan-id}/`

---
🤖 Generated by OpenClaw
EOF
)"
```

## Rules

- Target branch is always `main`
- Do not merge the PR — the human does that
- Do not modify any files — just create the PR
- If `gh pr create` fails, report the error
```

**Done when:** The skill file exists and a Claude Code session could use it to create a well-formatted PR.

---

## Step 7: Create Plan Watcher Script

**Create:** `projects/openclaw/app/scripts/plan-watcher.sh`

Use the script from Part 12 of this document. Copy it verbatim.

**Modify:** `projects/openclaw/dockerfiles/entrypoint.sh`

Add before the final `exec` line:
```bash
# Start plan watcher cron
mkdir -p /workspace/logs
cp /opt/openclaw/scripts/plan-watcher.sh /workspace/scripts/plan-watcher.sh 2>/dev/null || true
chmod +x /workspace/scripts/plan-watcher.sh 2>/dev/null || true
echo "*/5 * * * * /workspace/scripts/plan-watcher.sh >> /workspace/logs/plan-watcher.log 2>&1" | crontab -
crond -b 2>/dev/null || true
```

**Modify:** `projects/openclaw/dockerfiles/prod.Dockerfile`

Add a `COPY` for the scripts directory:
```dockerfile
COPY app/scripts/ /opt/openclaw/scripts/
```

> **Note:** The gateway API endpoint (`POST /api/message` or similar) needs to be verified. The script may need adjustment once the correct endpoint is confirmed.

**Done when:** The script exists, the Dockerfile copies it, and the entrypoint starts cron. The gateway API endpoint TODO is documented.

---

## Step 8: Update RBAC

**Modify:** `projects/openclaw/chart/templates/rbac.yaml`

Replace the entire file with the tightened namespaced Roles from Part 19 (Security):

```yaml
{{- if .Values.rbac.create }}
# Read-only access to OpenClaw's own namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ .Release.Name }}-self
  namespace: {{ .Release.Namespace }}
  labels:
    app: {{ .Release.Name }}
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec", "services", "configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ .Release.Name }}-self
  namespace: {{ .Release.Namespace }}
  labels:
    app: {{ .Release.Name }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ .Release.Name }}-self
subjects:
  - kind: ServiceAccount
    name: {{ .Values.serviceAccount.name | default .Release.Name }}
    namespace: {{ .Release.Namespace }}
---
# Observe + rollback access to app namespace (no secrets)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ .Release.Name }}-app-manager
  namespace: {{ .Values.appNamespace | default "app" }}
  labels:
    app: {{ .Release.Name }}
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec", "services", "endpoints"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "replicasets"]
    verbs: ["get", "list", "watch", "patch", "update"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ .Release.Name }}-app-manager
  namespace: {{ .Values.appNamespace | default "app" }}
  labels:
    app: {{ .Release.Name }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ .Release.Name }}-app-manager
subjects:
  - kind: ServiceAccount
    name: {{ .Values.serviceAccount.name | default .Release.Name }}
    namespace: {{ .Release.Namespace }}
{{- end }}
```

**Modify:** `projects/openclaw/chart/values.yaml`

Add:
```yaml
appNamespace: "app"
```

**Modify:** `infrastructure/k8s/helmfile.yaml.gotmpl` (OpenClaw release section)

Add `appNamespace` to the OpenClaw release values:
```yaml
appNamespace: "app"
```

**Also modify:** `projects/openclaw/dockerfiles/entrypoint.sh`

Change git-credentials to use tmpfs:
```bash
# Write to /tmp (tmpfs), not persistent PVC
echo "https://x-access-token:${GITHUB_TOKEN}@github.com" > /tmp/.git-credentials
chmod 600 /tmp/.git-credentials
git config --global credential.helper "store --file=/tmp/.git-credentials"
```

Do the same for `auth-profiles.json` — write to `/tmp` instead of the workspace PVC.

**Done when:** ClusterRole is replaced with two namespaced Roles. No Secret access in either namespace. `appNamespace` value wired through from helmfile to chart. Secrets written to tmpfs.

---

## Verification Checklist

After all 8 steps, verify:

- [ ] `projects/openclaw/app/skills/rlm-execute/SKILL.md` exists with correct frontmatter
- [ ] `projects/openclaw/app/skills/rlm-validate/SKILL.md` exists with correct frontmatter
- [ ] `projects/openclaw/app/skills/rlm-pr/SKILL.md` exists with correct frontmatter
- [ ] All task.md files in `.backlog/p-e7a3f1/` have `status: ready` and `attempts: 0` in frontmatter
- [ ] `.backlog/p-e7a3f1/status.json` has extended schema (branch, currentFeature, features, etc.)
- [ ] `projects/openclaw/app/SOUL.md` contains the full orchestration loop with all 9 sections
- [ ] `projects/openclaw/app/scripts/plan-watcher.sh` exists and is executable
- [ ] `projects/openclaw/dockerfiles/entrypoint.sh` starts cron and writes secrets to tmpfs
- [ ] `projects/openclaw/dockerfiles/prod.Dockerfile` copies the scripts directory
- [ ] `projects/openclaw/chart/templates/rbac.yaml` uses namespaced Roles (no ClusterRole)
- [ ] `projects/openclaw/chart/values.yaml` has `appNamespace: "app"`
- [ ] `infrastructure/k8s/helmfile.yaml.gotmpl` passes `appNamespace` to OpenClaw release

---

# Open TODOs

1. **Gateway API endpoint** — confirm the exact endpoint for sending messages to the OpenClaw Gateway from the plan watcher script
2. **Playwright/Chromium** — resolve installation in the NixOS-based OpenClaw container for E2E testing
3. **Plan watcher script** — the script reads from the remote branch via `git show`, needs testing to confirm this works with the workspace repo's git config
4. **Break-glass incident reports** — define the exact format for `.backlog/{plan-id}/incidents/{timestamp}.md`
5. **Feature execution ordering** — the orchestrator needs a concrete algorithm for reading cross-feature dependencies from feature plan Boundaries and producing an execution order
6. **Security: Network policies** — restrict OpenClaw egress to GitHub/Anthropic APIs + app namespace services only (nice-to-have)
