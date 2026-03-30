# OpenClaw Heartbeat Checklist

Fires every ~30 minutes. Scan status files only — do not read full plans unless acting.

## 1. Check for Stalled Plans

- [ ] Read all `.backlog/*/status.json` files
- [ ] For any with `status: "executing"` or `"decomposing"`: check the `updated` timestamp
- [ ] If `updated` is **more than 45 minutes ago**: the plan is likely stalled
  - Investigate: check the plan branch, look at the last task state
  - If session appears dead: resume the orchestration loop from where it left off
  - If unrecoverable: write incident report, mark status `stalled`, alert operator

## 2. Check for Ready Plans

- [ ] If any plan has `status: "ready"` AND no plan is currently `executing` or `decomposing`
  - Start the orchestration loop for that plan immediately
  - (Watchdog cron normally catches this — heartbeat is a fallback)

## 3. Check PR/CI Status

- [ ] For any plan with `status: "pr-submitted"`:
  - Run: `gh run list --repo sdcain-rts/automated-repo --branch openclaw/{planId} --limit 3 --json status,conclusion,name`
  - If CI failed: read logs (`gh run view --log-failed`), fix on plan branch, re-push

## 4. Memory Maintenance (weekly)

- [ ] Check if any `memory/YYYY-MM-DD.md` files are older than 14 days
- [ ] If yes:
  - Distill key insights and lessons into `MEMORY.md`
  - Delete the old daily files (git history preserves them)
  - Commit the changes: `git add memory/ MEMORY.md && git commit -m "chore(memory): prune old daily logs"`

## 5. Default Behavior

- If none of the above conditions apply: reply `HEARTBEAT_OK` and stop.
- Keep token usage minimal — scan only, don't read full plan files unless acting.
