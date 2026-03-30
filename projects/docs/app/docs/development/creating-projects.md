# Creating New Projects

Guide for scaffolding a new project in the monorepo. Used by the decomposition pipeline when a plan requires a project that doesn't exist yet.

## When to Create a New Project

Only create a new project when:
- The work requires a completely different tech stack not present in any existing project
- The work is a genuinely separate deployable (new microservice, new app)
- Putting it in an existing project would violate clear architectural boundaries

Most work should fit into existing projects. Review `projects/overview.md` before deciding.

## Project Structure

Every project follows the same directory layout:

```
projects/{project-name}/
├── app/                       # Application source code
│   ├── src/
│   │   ├── features/          # All code lives here
│   │   └── main.ts            # Entry point (or equivalent)
│   ├── package.json
│   └── tsconfig.json
├── dockerfiles/
│   ├── Dockerfile.dev         # Development container (hot reload)
│   └── Dockerfile.prod        # Production container (multi-stage)
├── chart/                     # Helm chart for K8s deployment
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
├── docker-compose.yml         # Project-level compose overrides (if needed)
├── Taskfile.yml               # Project automation tasks
└── README.md                  # Lightweight pointer to docs
```

## Step-by-Step Process

### 1. Create the Project Directory

```bash
mkdir -p projects/{project-name}/app/src/features
mkdir -p projects/{project-name}/dockerfiles
mkdir -p projects/{project-name}/chart/templates
```

### 2. Initialize the Application

For a NestJS backend:
```bash
cd projects/{project-name}/app
npm init -y
npm install @nestjs/core @nestjs/common @nestjs/platform-express
```

For a React frontend:
```bash
cd projects/{project-name}/app
npm create vite@latest . -- --template react-ts
```

### 3. Set Up Feature Architecture

Create the initial feature structure. All code must live in `src/features/`:

```
src/features/
├── health/                    # Required: health check feature
│   ├── health.controller.ts
│   ├── health.module.ts
│   └── index.ts
└── {first-feature}/           # The initial feature for this project
```

### 4. Create Dockerfiles

**Development Dockerfile** (`dockerfiles/Dockerfile.dev`):
- Base image appropriate for tech stack
- Install dependencies
- Volume mount support for hot reload
- Health check endpoint

**Production Dockerfile** (`dockerfiles/Dockerfile.prod`):
- Multi-stage build
- Non-root user
- Minimal final image
- Health check endpoint

### 5. Add to Docker Compose

Add the service to `infrastructure/docker/compose.yml`:

```yaml
{project-name}:
  build:
    context: ../../projects/{project-name}
    dockerfile: dockerfiles/Dockerfile.dev
  ports:
    - "${PROJECT_NAME_PORT}:8080"
  volumes:
    - ../../projects/{project-name}/app:/app
    - /app/node_modules
  env_file:
    - ../../.env
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - app_network
```

### 6. Create Helm Chart

Add a Helm chart in `projects/{project-name}/chart/` following the patterns in existing project charts.

### 7. Add to Helmfile

Add a release to `infrastructure/k8s/helmfile.yaml.gotmpl`:

```yaml
- name: {project-name}
  namespace: app
  chart: ../../projects/{project-name}/chart
  values:
    - environments/{{ .Environment.Name }}.yaml
```

### 8. Add Build Task

Add build tasks to the root Taskfile for building and pushing the Docker image.

### 9. Create Taskfile

Create `projects/{project-name}/Taskfile.yml` with standard tasks:
- `local:start`, `local:stop`, `local:restart`
- `local:logs`, `local:shell`
- `local:health`

### 10. Add Documentation

Create `projects/docs/app/docs/projects/{project-name}.md` with:
- Purpose and tech stack
- Feature inventory
- Public interfaces (API endpoints, etc.)
- Conventions

Update `projects/docs/app/docs/projects/overview.md` to include the new project.

### 11. Update Environment

Add any required environment variables to `.env.template` and document them.

## Conventions

- **Project names**: kebab-case (`notification-service`, `analytics-dashboard`)
- **Ports**: Each project gets a unique port. Check existing services in `infrastructure/docker/compose.yml`
- **Networks**: All app services join `app_network`
- **Health checks**: Every service must expose `GET /health`
- **Feature architecture**: All code in `src/features/`, no separate `pages/` or `endpoints/`
