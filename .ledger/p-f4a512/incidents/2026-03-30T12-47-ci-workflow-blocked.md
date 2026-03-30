# Incident: CI workflow missing build-backend-python job

## Date: 2026-03-30T12:47:00Z
## Status: needs-operator

## What happened
After merging `openclaw/p-f4a512` to `mac-mini`, the `backend-python` deployment entered `ImagePullBackOff` because the image was never built. The CI workflow `.github/workflows/deploy-mac-mini.yml` does not have a `build-backend-python` job — it builds backend, frontend, keycloak, openclaw but not the new Python backend.

## Root cause
New projects need a corresponding build job added to the CI workflow. This was not included in plan p-f4a512's scope (no `docs` project task for the workflow).

## Fix required
Add to `.github/workflows/deploy-mac-mini.yml`:

1. A new `build-backend-python` job (after `build-openclaw`, before `deploy`):
```yaml
  build-backend-python:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: tailscale/github-action@v3
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
          oauth-secret: ${{ secrets.TS_OAUTH_SECRET }}
          tags: tag:ci
      - uses: docker/setup-buildx-action@v3
        with:
          driver-opts: network=host
          buildkitd-config-inline: |
            [registry."mac-mini:30500"]
              http = true
              insecure = true
      - uses: docker/build-push-action@v6
        with:
          context: projects/application/backend-python
          file: projects/application/backend-python/dockerfiles/prod.Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/backend-python:${{ env.IMAGE_TAG }}
            ${{ env.REGISTRY }}/backend-python:latest
          cache-from: type=gha,scope=backend-python
          cache-to: type=gha,mode=max,scope=backend-python
```

2. Add `build-backend-python` to the `deploy` job's needs:
```yaml
  deploy:
    needs: [build-backend, build-frontend, build-keycloak, build-openclaw, build-backend-python]
```

3. Add rollout check in verify step:
```yaml
kubectl rollout status deployment/backend-python -n app --timeout=180s
```

## Why operator action is needed
The GitHub PAT does not have `workflow` scope — cannot push changes to `.github/workflows/` files. The operator needs to either:
- Add `workflow` scope to the PAT, OR
- Make this change manually and push to `mac-mini`

## Current state
- `backend-python` pod: `ImagePullBackOff` (image not in registry)
- All other deployments: healthy
- The change is ready — just needs to be committed and pushed with a PAT that has workflow scope
