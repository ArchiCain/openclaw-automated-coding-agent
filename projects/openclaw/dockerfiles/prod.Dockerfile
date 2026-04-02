FROM nixos/nix:latest

# Enable flakes and disable sandbox (required for cross-platform builds under emulation)
RUN mkdir -p /etc/nix && printf "experimental-features = nix-command flakes\nsandbox = false\n" >> /etc/nix/nix.conf

WORKDIR /build

# Copy the slim Docker-specific flake (not the full repo flake)
COPY dockerfiles/flake.nix ./flake.nix

# Generate flake.lock and build the dev shell (caches all tools in /nix/store)
RUN nix flake update && nix develop --command true

# Capture the Nix dev shell PATH and write it as an env file for runtime
RUN nix develop --command bash -c 'echo "NIX_PATHS=$PATH"' > /etc/nix-env

# Configure git to use HTTPS with credential store
RUN nix develop --command bash -c "\
    git config --global credential.helper 'store' \
    && git config --global url.\"https://github.com/\".insteadOf 'git@github.com:' \
    "

# Install OpenClaw and Claude Code globally, then install acpx plugin
# Also symlink CLIs to /usr/local/bin so they're on PATH at runtime
RUN mkdir -p /usr/local/bin && nix develop --command bash -c "\
    npm install -g openclaw@latest \
    && npm install -g @anthropic-ai/claude-code@latest \
    && NPM_BIN=\$(npm prefix -g)/bin \
    && ln -sf \$NPM_BIN/openclaw /usr/local/bin/openclaw \
    && ln -sf \$NPM_BIN/claude /usr/local/bin/claude \
    && export PATH=\$NPM_BIN:\$PATH \
    && openclaw plugins install @openclaw/acpx \
    "

# Resolve the Nix-provided Chromium path and write it to an env file for runtime.
# Playwright will use this instead of downloading its own Chromium.
RUN nix develop --command bash -c 'echo "CHROMIUM_PATH=$(which chromium)"' >> /etc/nix-env

# Pre-install acpx npm dependencies as root (while still in /build where flake.nix lives)
# This avoids permission issues at runtime since /nix/store is read-only for non-root
RUN nix develop --command bash -c "\
    ACPX_DIR=\$(dirname \$(readlink -f /usr/local/bin/openclaw))/../openclaw/dist/extensions/acpx \
    && if [ -d \$ACPX_DIR ]; then cd \$ACPX_DIR && npm install --omit=dev; fi \
    "

WORKDIR /app

# Copy OpenClaw config, skills, and soul
COPY app/ ./

# Copy entrypoint
COPY dockerfiles/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Create non-root user (Claude Code refuses --dangerously-skip-permissions as root)
RUN echo "agent:x:1000:1000:agent:/home/agent:/bin/bash" >> /etc/passwd \
    && echo "agent:x:1000:" >> /etc/group \
    && mkdir -p /home/agent/.claude /home/agent/.config /home/agent/.openclaw /workspace \
    && cp /root/.gitconfig /home/agent/.gitconfig \
    && chown -R 1000:1000 /app /home/agent /workspace

USER agent

# Copy config to OpenClaw's config directory and link workspace
RUN cp /app/openclaw.json /home/agent/.openclaw/openclaw.json \
    && ln -sf /app /home/agent/.openclaw/workspace

EXPOSE 18789

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["openclaw", "gateway"]
