#!/usr/bin/env bash
set -e

# Load Nix dev shell PATH (captured at build time, avoids needing `nix develop` at runtime)
if [ -f /etc/nix-env ]; then
  source /etc/nix-env
  export PATH="/usr/local/bin:$NIX_PATHS"
fi

# Configure Playwright to use Nix-provided Chromium (no download or --with-deps needed)
if [ -n "$CHROMIUM_PATH" ]; then
  export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH="$CHROMIUM_PATH"
  export PLAYWRIGHT_BROWSERS_PATH=0
fi

# Configure git credentials from GITHUB_TOKEN if provided
# Write to /tmp (tmpfs) instead of persistent PVC to avoid secrets on disk
if [ -n "$GITHUB_TOKEN" ]; then
  echo "https://x-access-token:${GITHUB_TOKEN}@github.com" > /tmp/.git-credentials
  chmod 600 /tmp/.git-credentials
  git config --global credential.helper "store --file=/tmp/.git-credentials"
fi

# Configure git identity (use env vars or defaults)
git config --global user.name "${GIT_USER_NAME:-openclaw-agent}"
git config --global user.email "${GIT_USER_EMAIL:-openclaw-agent@localhost}"

# Resolve the environment branch — all work happens on this branch
BRANCH="${DEPLOY_BRANCH:-${OPENCLAW_ENV_NAME:-mac-mini}}"

# Clone or update workspace repository
if [ -n "$OPENCLAW_REPO_URL" ]; then
  REPO_DIR="/workspace/automated-repo"
  if [ ! -d "$REPO_DIR/.git" ]; then
    echo "Cloning repository (branch: $BRANCH) into $REPO_DIR..."
    git clone --branch "$BRANCH" "$OPENCLAW_REPO_URL" "$REPO_DIR"
  else
    echo "Updating existing workspace (branch: $BRANCH)..."
    cd "$REPO_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
  fi
  cd "$REPO_DIR"
fi

# =============================================================================
# Persistent state via OPENCLAW_STATE_DIR
#
# Point OpenClaw's state directory at the PVC so sessions, agents, cron, logs,
# and all internal state survive pod restarts and redeployments.
# =============================================================================
export OPENCLAW_STATE_DIR="/workspace/.openclaw"
mkdir -p "$OPENCLAW_STATE_DIR"

# =============================================================================
# Per-environment workspace memory persistence
#
# Live memory lives on PVC at /workspace/openclaw-memory/{ENV_NAME}/ so that
# git branch switches in /workspace/automated-repo/ have zero effect on agent
# memory. On first boot, memory is seeded from the git snapshot or /app/
# defaults. Image-owned files are always overwritten from the image on every
# startup. Memory-only files are seeded once and then owned by the agent.
# =============================================================================
ENV_NAME="${OPENCLAW_ENV_NAME:-mac-mini}"
LIVE_WORKSPACE="/workspace/openclaw-memory/${ENV_NAME}"
GIT_WORKSPACE="${REPO_DIR}/.workspace/${ENV_NAME}"

# Seed live workspace from git snapshot if it doesn't exist yet.
#
# Priority order:
#  1. origin/$DEPLOY_BRANCH — the env-specific branch where memory-sync commits
#     accumulated memories. This is the authoritative backup for this environment.
#  2. local $GIT_WORKSPACE — the main-branch checkout, used as fallback if the
#     env-specific branch has no .workspace/ data (e.g., fresh setup).
#
# NOTE: We must fetch origin/$DEPLOY_BRANCH explicitly because the main checkout
# only has the main-branch version of .workspace/, which diverges from the
# memory-sync commits pushed to the env-specific branch.
if [ ! -d "$LIVE_WORKSPACE" ]; then
  echo "Seeding live workspace for ${ENV_NAME}..."
  mkdir -p "$LIVE_WORKSPACE/memory"

  SEED_BRANCH="${DEPLOY_BRANCH:-${ENV_NAME}}"
  SEEDED=false

  # Try to seed from origin/$SEED_BRANCH (has memory-sync snapshots)
  if [ -n "$REPO_DIR" ] && [ -d "$REPO_DIR/.git" ]; then
    git -C "$REPO_DIR" fetch origin "$SEED_BRANCH" 2>/dev/null || true
    if git -C "$REPO_DIR" cat-file -e "origin/${SEED_BRANCH}:.workspace/${ENV_NAME}/MEMORY.md" 2>/dev/null; then
      echo "  Seeding from origin/${SEED_BRANCH}:.workspace/${ENV_NAME}/"
      git -C "$REPO_DIR" archive "origin/${SEED_BRANCH}" ".workspace/${ENV_NAME}/" \
        | tar x --strip-components=2 -C "$LIVE_WORKSPACE/" 2>/dev/null && SEEDED=true || true
    fi
  fi

  # Fall back to main-branch local checkout
  if [ "$SEEDED" = false ] && [ -d "$GIT_WORKSPACE" ]; then
    echo "  Seeding from local git snapshot at ${GIT_WORKSPACE}"
    cp -a "$GIT_WORKSPACE/." "$LIVE_WORKSPACE/"
    SEEDED=true
  fi

  [ "$SEEDED" = true ] && echo "  Workspace seeded." || echo "  No git snapshot found — starting fresh."
fi

# Ensure memory dir exists
mkdir -p "$LIVE_WORKSPACE/memory"

# Re-point the workspace symlink to the PVC-backed live workspace
rm -f "$OPENCLAW_STATE_DIR/workspace"
ln -sfn "$LIVE_WORKSPACE" "$OPENCLAW_STATE_DIR/workspace"

# Image-owned files: always overwrite from /app/ on every boot (image is source of truth)
for file in SOUL.md AGENTS.md HEARTBEAT.md openclaw.json; do
  if [ -f "/app/$file" ]; then
    cp "/app/$file" "$LIVE_WORKSPACE/$file"
  fi
done

# Skills symlink: always point to image-baked skills (never drifts)
rm -f "$LIVE_WORKSPACE/skills"
ln -sfn /app/skills "$LIVE_WORKSPACE/skills"

# Memory-only files: seed once from /app/ or stub — then owned by the agent
# Helper: restore a single memory file from git, /app/, or stub (in that priority order)
restore_memory_file() {
  local dest="$1"         # full path to target file
  local filename="$2"     # basename, e.g. USER.md
  local stub="$3"         # fallback content if git and /app both lack the file
  local seed="${DEPLOY_BRANCH:-${ENV_NAME}}"
  if [ ! -f "$dest" ]; then
    if [ -n "$REPO_DIR" ] && git -C "$REPO_DIR" cat-file -e "origin/${seed}:.workspace/${ENV_NAME}/${filename}" 2>/dev/null; then
      git -C "$REPO_DIR" show "origin/${seed}:.workspace/${ENV_NAME}/${filename}" > "$dest" 2>/dev/null || true
    elif [ -f "/app/$filename" ]; then
      cp "/app/$filename" "$dest"
    else
      printf '%s' "$stub" > "$dest"
    fi
  fi
}

restore_memory_file "$LIVE_WORKSPACE/USER.md"     "USER.md"     "# USER.md - About Your Human\n\n_Update this as you learn about the person you're helping._\n"
restore_memory_file "$LIVE_WORKSPACE/IDENTITY.md" "IDENTITY.md" "# IDENTITY.md - Who Am I?\n\n_Fill this in during your first conversation._\n"
restore_memory_file "$LIVE_WORKSPACE/TOOLS.md"    "TOOLS.md"    "# TOOLS.md - Local Notes\n\nAdd environment-specific notes here (camera names, SSH hosts, voice preferences, etc.).\n"
restore_memory_file "$LIVE_WORKSPACE/MEMORY.md"   "MEMORY.md"   "# MEMORY.md - Long-Term Memory\n\n_Your curated long-term memory. Updated over time._\n"

# OPENCLAW_STATE_DIR=/workspace/.openclaw handles all state persistence.
# No symlinks needed — OpenClaw writes directly to the PVC.

# Set gateway auth token from env var if provided
if [ -n "$OPENCLAW_AUTH_TOKEN" ]; then
  openclaw config set gateway.auth.mode token
  openclaw config set gateway.auth.token "$OPENCLAW_AUTH_TOKEN"
fi

# Configure allowed origins for the control UI
# OPENCLAW_ALLOWED_ORIGINS is a comma-separated list (e.g., "http://localhost:18789,https://openclaw.mac-mini")
if [ -n "$OPENCLAW_ALLOWED_ORIGINS" ]; then
  ORIGINS_JSON=$(echo "$OPENCLAW_ALLOWED_ORIGINS" | awk -F',' '{for(i=1;i<=NF;i++) printf "\"%s\"%s", $i, (i<NF?",":""); print ""}')
  openclaw config set gateway.controlUi.allowedOrigins "[$ORIGINS_JSON]"
fi

# Configure Anthropic API key auth profile for the main agent
# Write to /tmp (tmpfs) and symlink to avoid secrets on persistent disk
if [ -n "$ANTHROPIC_API_KEY" ]; then
  AUTH_DIR="$OPENCLAW_STATE_DIR/agents/main/agent"
  mkdir -p "$AUTH_DIR" /tmp/openclaw-auth
  cat > /tmp/openclaw-auth/auth-profiles.json << EOF
{
  "version": 1,
  "profiles": {
    "anthropic:default": {
      "type": "api_key",
      "provider": "anthropic",
      "key": "$ANTHROPIC_API_KEY"
    }
  }
}
EOF
  chmod 600 /tmp/openclaw-auth/auth-profiles.json
  ln -sf /tmp/openclaw-auth/auth-profiles.json "$AUTH_DIR/auth-profiles.json"
fi

# Register cron jobs after gateway starts (needs websocket connection)
# Skip when OPENCLAW_CRON_ENABLED=false (e.g., local dev / manual-only mode)
CRON_ENABLED="${OPENCLAW_CRON_ENABLED:-true}"

if [ "$CRON_ENABLED" = "true" ]; then
  register_crons() {
    # Wait for gateway to be ready
    for i in $(seq 1 30); do
      if openclaw cron list >/dev/null 2>&1; then
        break
      fi
      sleep 2
    done

    # Ensure exactly one cron per name: remove all existing, then add fresh.
    # This prevents duplicates that accumulated from prior ephemeral-state restarts.
    ensure_single_cron() {
      local name="$1"
      local every="$2"
      local model="$3"
      # Remove all existing jobs with this name (cleans up duplicates)
      openclaw cron list --all --json 2>/dev/null | node -e "
        let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
          try{const j=JSON.parse(d);(j.jobs||j||[]).forEach(x=>{if(x.name==='$name')console.log(x.id)})}catch{}
        })
      " 2>/dev/null | while read -r jid; do
        openclaw cron remove "$jid" 2>/dev/null || true
      done
      openclaw cron add --name "$name" --every "$every" --model "$model" --session isolated --message "/skill $name" || true
    }

    ensure_single_cron "dispatcher" "5m" "anthropic/claude-haiku-4-5"
  }

  # Run cron registration in background after gateway starts
  register_crons &
else
  echo "Cron registration disabled (OPENCLAW_CRON_ENABLED=$CRON_ENABLED)"
fi

exec "$@"
