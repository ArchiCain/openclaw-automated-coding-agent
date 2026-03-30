# OpenClaw Gateway

Autonomous coding agent powered by OpenClaw + Claude Code ACP. Deployed to the `openclaw` K8s namespace.

## Architecture

```
Mac Mini K3s Cluster
│
├── app namespace (existing, unchanged)
│   ├── database, backend, frontend, keycloak, docs
│
└── openclaw namespace
    └── openclaw-gateway (Deployment)
        ├── OpenClaw Gateway daemon (orchestration)
        ├── Built-in Web UI (chat, monitoring)
        ├── Claude Code CLI (ACP sessions)
        ├── Playwright + headless Chromium (E2E testing)
        ├── git, go-task, gh CLI
        ├── Skills (SKILL.md files)
        ├── Secrets from K8s Secret
        ├── Workspace PVC (50Gi)
        └── Ingress: openclaw.mac-mini
```

## What It Does

OpenClaw operates as a **team of specialist agents** that pick up work from a queue. Work is tracked in `.ledger/` — a structured, durable record that survives restarts and crashes.

Work arrives through three channels:

1. **Dispatcher cron** — scans `.ledger/*/manifest.json` every 5 minutes, routes tasks to specialists
2. **Heartbeat** — fallback status check every 30 minutes
3. **Web UI / direct message** — operator sends messages directly

The Gateway orchestrates Claude Code ACP sessions, with each specialist running in an isolated session for context separation.

## Project Structure

```
projects/openclaw/
├── app/
│   ├── openclaw.json           # Gateway configuration
│   ├── SOUL.md                 # Agent identity and orchestration rules
│   ├── HEARTBEAT.md            # Periodic health check checklist
│   └── skills/
│       ├── architect/          # Decomposes plans into tasks
│       ├── dispatcher/         # Routes work to specialists (cron)
│       ├── frontend-eng/       # Angular 19 specialist
│       ├── backend-eng/        # NestJS 11 specialist
│       ├── infra-eng/          # Docker/Helm/Terraform specialist
│       ├── reviewer/           # Code review against acceptance criteria
│       ├── qa-eng/             # Feature-level integration/E2E testing
│       ├── pr-manager/         # Creates PRs for human review
│       └── rlm-code/           # Ad-hoc coding utility
├── dockerfiles/
│   ├── prod.Dockerfile         # Nix-based image
│   ├── flake.nix               # Nix dev shell
│   └── entrypoint.sh           # Git credentials + startup
├── chart/                      # Helm chart for K8s deployment
├── Taskfile.yml
└── README.md
```

## The Team

OpenClaw manages a team of specialist skills, each running as an isolated Claude Code ACP session:

| Skill | Role | What It Does |
|-------|------|-------------|
| `architect` | Senior Architect | Reads plans, researches codebase + docs, creates tasks with specialist routing |
| `frontend-eng` | Angular Expert | Implements frontend tasks — standalone components, Material, RxJS |
| `backend-eng` | NestJS Expert | Implements backend tasks — modules, controllers, services, TypeORM |
| `infra-eng` | Infrastructure Specialist | Handles Docker, Helm, Helmfile, Terraform, Taskfile changes |
| `reviewer` | Code Reviewer | Reviews implementations against acceptance criteria and conventions |
| `qa-eng` | QA Engineer | Validates features holistically with integration and E2E tests |
| `dispatcher` | Work Router | Scans ledger every 5 min, routes tasks to the right specialist |
| `pr-manager` | DevOps | Creates PRs from completed plan branches to main |

Specialists read project documentation from `projects/docs/app/docs/` at runtime for conventions — skills don't embed project knowledge.

## The Ledger

All work is tracked in `.ledger/`:

```
.ledger/{plan-id}/
├── plan.md              # Original plan (immutable after creation)
├── manifest.json        # Plan lifecycle state + task registry
├── tasks/
│   ├── t-{12hex}.task.md
│   ├── t-{12hex}.feedback.md  (on rejection)
│   └── ...
├── qa-reports/
│   └── {feature}-{timestamp}.md
└── incidents/
    └── {timestamp}.md
```

## Work Flow

```
Plan ready → Dispatcher detects → Architect decomposes into tasks
  → Tasks routed to specialists by project type
    → Specialist implements → Reviewer checks
      → All tasks reviewed → QA validates feature
        → All features QA-passed → PR Manager creates PR
          → Human reviews and merges
```

## Configuration

| Variable | Purpose | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | LLM provider for Gateway orchestration | Yes |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code ACP sessions | Yes |
| `GITHUB_TOKEN` | Git operations and GitHub API | Yes |
| `OPENCLAW_WEBHOOK_SECRET` | GitHub webhook authentication | Yes |
| `OPENCLAW_AUTH_TOKEN` | Web UI authentication | Yes |
| `OPENCLAW_REPO_URL` | Repository URL to clone into workspace | Yes |
| `OPENCLAW_PORT` | Gateway port (default: 18789) | No |
| `OPENCLAW_HOST` | Ingress hostname (default: openclaw.mac-mini) | No |
| `OPENCLAW_NAMESPACE` | K8s namespace (default: openclaw) | No |
| `OPENCLAW_WORKSPACE_SIZE` | PVC size (default: 50Gi) | No |

## Access

- **Deployed**: `https://openclaw.mac-mini` (via Tailscale)
- **Local dev**: `http://localhost:18789`

## Cron Jobs

| Job | Schedule | Model | Purpose |
|-----|----------|-------|---------|
| `dispatcher` | Every 5 min | Haiku | Scan ledger, route work to specialists |
| `heartbeat` | Every 30 min | Sonnet | Fallback status check, stall detection |

## Common Tasks

```bash
task openclaw:local:start       # Start via Docker Compose
task openclaw:local:stop        # Stop the service
task openclaw:local:logs        # Follow logs
task openclaw:local:health      # Check health endpoint
task openclaw:remote:build      # Build image on K8s node
task openclaw:remote:deploy     # Full build + deploy
task openclaw:k8s:status        # Show pod status
task openclaw:k8s:logs          # Follow pod logs
task openclaw:k8s:shell         # Shell into the pod
```

## E2E Testing

The OpenClaw pod includes Playwright + headless Chromium. It can run E2E tests against the live deployed application because it shares the K8s cluster:

```bash
# Via K8s DNS (recommended)
E2E_BASE_URL=http://frontend.app.svc.cluster.local:8080 npx playwright test

# Via Traefik ingress (full path)
E2E_BASE_URL=http://app.mac-mini npx playwright test
```
