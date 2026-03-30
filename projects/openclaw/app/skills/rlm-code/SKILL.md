---
name: rlm-code
description: Use Claude Code to make code changes in the repo via git worktrees
---

# rlm-code

Make code changes in the automated-repo monorepo using a git worktree and feature branch.

## Git Workflow

Every code change follows this workflow:

1. **Create a git worktree** with a descriptive branch name:
   ```bash
   git worktree add /workspace/.worktrees/{branch-name} -b {branch-name}
   ```
2. **Work in the worktree** — all file reads, edits, and commands happen in the worktree directory, not in the main checkout.
3. **Commit frequently** — small, focused commits with clear messages describing what changed and why.
4. **Push the branch** to remote:
   ```bash
   cd /workspace/.worktrees/{branch-name}
   git push -u origin {branch-name}
   ```
5. **Report back** — summarize the branch name and what was done.

### Branch Naming
Format: `openclaw/{short-description}` (e.g., `openclaw/test-file-change`)

### Commit Messages
Keep them simple and descriptive:
- `add: new utility function for date formatting`
- `update: user service to handle pagination`
- `fix: missing import in auth module`

## Safety Rules

- Never work directly on `main`. Always use a worktree with a feature branch.
- Do not create pull requests unless explicitly asked.
- Do not merge anything.
- Do not modify infrastructure, CI/CD, Helm charts, or GitHub Actions.
- Read existing code before modifying it. Follow existing patterns.
- Never guess at file paths — look them up.

## Repository Structure

```
projects/
├── application/
│   ├── backend/         # NestJS 11 API
│   ├── frontend/        # React 19 SPA
│   ├── database/        # PostgreSQL 16 + pgvector
│   ├── keycloak/        # Auth provider
│   └── e2e/             # Playwright E2E tests
├── openclaw/            # OpenClaw (do not modify)
└── docs/                # MkDocs documentation
```
