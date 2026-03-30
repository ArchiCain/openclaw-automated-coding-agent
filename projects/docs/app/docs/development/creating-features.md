# Creating Features

Guide for adding new features to existing projects. Used by the decomposition pipeline when breaking project plans into feature-level work.

## Feature Architecture

All application code lives inside `src/features/`. There are no separate `pages/` or `endpoints/` directories. See the [Feature Architecture](../architecture/feature-architecture.md) guide for the full pattern.

## Feature Types

### Full-Stack Features
Complete features with user-facing interfaces:
- **Frontend**: Pages, components, hooks, services, types
- **Backend**: Controllers, services, entities, DTOs, guards, module
- Represents a complete user-facing capability
- Examples: `auth`, `user-dashboard`, `document-upload`

### Shared Features
Reusable utilities used by multiple features:
- Provides common functionality across the application
- No direct user interface
- Must be used by 2+ features to justify existence
- Examples: `api-client`, `ui-components`, `database-client`

## Backend Feature (NestJS)

### Required Structure

```
src/features/{feature-name}/
├── controllers/
│   └── {feature}.controller.ts
├── services/
│   └── {feature}.service.ts
├── entities/                      # If database models needed
│   └── {feature}.entity.ts
├── dto/                           # If request/response types needed
│   ├── create-{feature}.dto.ts
│   └── update-{feature}.dto.ts
├── guards/                        # If auth guards needed
├── decorators/                    # If custom decorators needed
├── {feature}.module.ts            # REQUIRED: NestJS module
└── index.ts                       # Public exports
```

### Critical Rule: Module Per Feature

Every backend feature MUST have its own NestJS module. The `app.module.ts` should ONLY import feature modules:

```typescript
// CORRECT
@Module({
  imports: [HealthModule, UserManagementModule, NewFeatureModule],
})
export class AppModule {}
```

Never import controllers or providers directly into `app.module.ts`.

### Adding a Backend Feature

1. Create the feature directory under `src/features/`
2. Create the module file with `@Module()` decorator
3. Register controllers, providers, and exports
4. Create `index.ts` that exports the module
5. Import the module in `app.module.ts`

## Frontend Feature (React)

### Required Structure

```
src/features/{feature-name}/
├── pages/                         # Route-level components
│   └── {feature}.page.tsx
├── components/                    # Feature-specific components
│   ├── ComponentA.tsx
│   └── ComponentB.tsx
├── hooks/                         # Custom hooks
│   └── use{Feature}.ts
├── services/                      # API clients
│   └── {feature}.api.ts
├── types/                         # TypeScript interfaces
│   └── types.ts
└── index.ts                       # Public exports
```

### Adding a Frontend Feature

1. Create the feature directory under `src/features/`
2. Create page components (suffix with `.page.tsx`)
3. Add routes in the app router
4. Create feature-specific components, hooks, and services
5. Create `index.ts` that exports public API

## Naming Conventions

- **Directories**: kebab-case (`user-dashboard`, `api-client`)
- **Frontend pages**: `{name}.page.tsx` (`dashboard.page.tsx`)
- **Backend controllers**: `{name}.controller.ts` (`users.controller.ts`)
- **Backend modules**: `{name}.module.ts` (`users.module.ts`)
- **Tests**: `*.spec.ts` (backend), `*.test.tsx` (frontend)
- **Types**: `types.ts` or `{name}.types.ts`

## Feature Independence

- Features should be largely self-contained
- Minimize dependencies between features
- Shared features should not depend on full-stack features
- Use dependency injection for loose coupling
- Co-locate tests with feature code
