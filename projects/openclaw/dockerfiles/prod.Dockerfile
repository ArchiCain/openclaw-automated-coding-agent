FROM ghcr.io/openclaw/openclaw:latest

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    curl \
    jq \
    ca-certificates \
    gnupg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -fsSL "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    -o /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl

# Install Helm
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install helmfile
RUN curl -fsSL https://github.com/helmfile/helmfile/releases/latest/download/helmfile_linux_amd64.tar.gz \
    | tar xz -C /usr/local/bin helmfile

# Install gh CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh && rm -rf /var/lib/apt/lists/*

# Install go-task
RUN sh -c "$(curl -fsSL https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code@latest

# Install acpx plugin
RUN openclaw plugins install @openclaw/acpx

# Install Playwright + headless Chromium for E2E testing
RUN npx playwright install --with-deps chromium

# Install helm-diff plugin (required by helmfile)
RUN helm plugin install https://github.com/databus23/helm-diff

WORKDIR /app

# Copy OpenClaw config, skills, and soul
COPY app/ ./

# Copy entrypoint
COPY dockerfiles/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Configure git to use HTTPS with credential store
RUN git config --global credential.helper store \
    && git config --global url."https://github.com/".insteadOf "git@github.com:"

# Create non-root user (Claude Code refuses --dangerously-skip-permissions as root)
RUN useradd -m -u 1000 -s /bin/bash agent \
    && mkdir -p /home/agent/.claude /home/agent/.config /home/agent/.openclaw /workspace \
    && cp /root/.gitconfig /home/agent/.gitconfig \
    && chown -R agent:agent /app /home/agent /workspace

USER agent

# Copy config to OpenClaw's config directory and link workspace
RUN cp /app/openclaw.json /home/agent/.openclaw/openclaw.json \
    && ln -sf /app /home/agent/.openclaw/workspace

EXPOSE 18789

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["openclaw", "gateway"]
