# OpenClaw Heartbeat Checklist

Fires every ~30 minutes. **Safety net only** — the orchestrator drives execution continuously. Heartbeat catches things that fell through the cracks.

## 1. Check for Stalled Plans

- [ ] Read all `.ledger/*/manifest.json` files
- [ ] For any with `status: "executing"` or `"decomposing"`: check the `updated` timestamp
- [ ] If `updated` is **more than 45 minutes ago**: the plan is stalled — orchestration dropped
  - Read manifest to find where it left off (last in-progress task, last completed step)
  - Resume immediately: re-spawn the right session for whatever was in-progress
  - If unrecoverable: write incident report, mark `stalled`, alert operator

## 2. Check for Decomposed Plans Not Yet Executing

- [ ] If any plan has `status: "decomposed"` (architect finished but execution never started)
  - This means the post-decomp execution trigger was missed
  - Immediately start executing: mark `executing`, spawn all wave-0 tasks

## 3. Check for Ready Plans (no active plan)

- [ ] If any plan has `status: "ready"` AND no plan is `executing` or `decomposing`
  - Start the orchestration immediately (spawn architect)

## 4. Check PR/CI Status

- [ ] For any plan with `status: "pr-submitted"`:
  - Run: `gh run list --repo sdcain-rts/automated-repo --branch openclaw/{planId} --limit 3 --json status,conclusion,name`
  - If CI failed: read logs (`gh run view --log-failed`), fix on plan branch, re-push

## 5. Memory Maintenance (weekly)

- [ ] Check if any `memory/YYYY-MM-DD.md` files are older than 14 days
- [ ] If yes:
  - Distill key insights into `MEMORY.md`
  - Delete old daily files
  - Commit: `git add memory/ MEMORY.md && git commit -m "chore(memory): prune old daily logs"`

## 6. Default Behavior

- If none of the above apply: reply `HEARTBEAT_OK` and stop.
- Keep token usage minimal — scan only, don't read full plan or task files unless acting.
