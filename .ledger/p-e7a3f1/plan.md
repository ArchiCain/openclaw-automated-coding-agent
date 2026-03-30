---
id: p-e7a3f1
created: 2026-03-28T00:00:00.000Z
updated: 2026-03-28T01:00:00.000Z
---

# Angular Frontend Rebuild

## Problem Statement

The current frontend is a React 19 + Vite application using Material UI v6. While functional, the UI is inconsistent and visually unpolished — it doesn't follow a cohesive Material Design language. The project needs to be rebuilt as an Angular application using Angular Material, taking the opportunity to both modernize the architecture and deliver a proper Material Design facelift.

The goal is to take advantage of Angular's opinionated architecture — standalone components, dependency injection, services, modules — to produce a frontend where every component is self-contained, portable, and makes its own API calls through injected services. The UI should be rebuilt with true Angular Material design principles: consistent typography, proper spacing, elevation hierarchy, coherent color palette, and polished component usage throughout.

The rebuild must preserve the existing feature-based architecture (`src/features/`) that the decomposition pipeline depends on, while restructuring internals to follow Angular best practices: standalone components, injectable services, Angular Router with guards, Angular Material theming, and reactive patterns with RxJS. All tooling should be stock Angular — Angular CLI, esbuild, Karma/Jasmine for tests. No Vite, no third-party build tools.

## Requirements

### Functional

- Replicate all existing routes: `/login`, `/` (chat), `/smoke-tests`, `/admin/users`, `/admin/users/new`, `/admin/users/:id`
- Cookie-based authentication flow with Keycloak (backend unchanged — same REST endpoints)
- Proactive token refresh (every 4 minutes) and inactivity timeout (30 minutes)
- Real-time chat via Socket.IO with message streaming (chunk-based)
- Chat history sidebar with conversation list
- Markdown rendering with syntax-highlighted code blocks in chat messages
- User management CRUD with search, pagination, sorting
- Role-based permission system (admin/user roles, permission derivation)
- Responsive layout: persistent sidebar on desktop, temporary drawer on mobile
- Dark/light theme toggle with backend persistence
- Confirmation modals for destructive actions

### Non-Functional

- Angular 19+ (latest stable) with standalone components throughout — no NgModules for feature code
- Angular CLI with esbuild (stock Angular tooling — no Vite, no third-party build tools)
- Angular Material for all UI components (replacing MUI)
- True Material Design visual language: consistent spacing, typography scale, elevation, color system
- RxJS for reactive state management and HTTP calls
- Angular HttpClient with interceptors (replacing Axios)
- Angular Router with functional guards (replacing React Router + ProtectedRoute)
- Strict TypeScript configuration
- Angular `environment.ts` for environment configuration, following the no-defaults policy
- Unit tests with Karma/Jasmine (Angular default, matching existing 80% coverage threshold)
- Docker-compatible build (existing Dockerfile pattern)
- Maintain feature-based directory structure for decomposition pipeline compatibility

## Architecture

### Projects Affected

**Frontend only** — the backend, database, keycloak, and infrastructure are unchanged. The Angular app consumes the exact same REST API and WebSocket endpoints.

### Angular Project Structure

The Angular app replaces `projects/application/frontend/app/` while preserving the outer project structure (dockerfiles/, chart/, Taskfile.yml).

```
projects/application/frontend/app/
├── src/
│   ├── main.ts                          # bootstrapApplication with providers
│   ├── app.component.ts                 # Root component
│   ├── app.routes.ts                    # Route definitions
│   ├── app.config.ts                    # Application config (providers, interceptors)
│   ├── features/
│   │   ├── api-client/                  # HttpClient wrapper service + WebSocket service
│   │   ├── keycloak-auth/               # Auth service, guards, interceptors, login components
│   │   ├── app-header/                  # Header component with avatar menu + nav menu
│   │   ├── layouts/                     # App layout component, responsive breakpoints
│   │   ├── mastra-agents/               # Chat UI components, services, message streaming
│   │   ├── angular-material-theme/      # Angular Material theme config + custom theme
│   │   ├── navigation/                  # Sidebar components (permanent + drawer)
│   │   ├── navigation-config/           # Menu structure, types, utilities
│   │   ├── shared/                      # Confirmation dialog, shared components
│   │   ├── testing-tools/               # Smoke tests, health check, DB client UI
│   │   ├── theme/                       # Dark/light toggle service + component
│   │   └── user-management/             # User CRUD pages + components + service
│   ├── environments/
│   │   └── environment.ts               # Environment config (no defaults)
│   └── styles.scss                      # Global styles + Angular Material theme
├── angular.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.spec.json
└── package.json
```

### Key Angular Patterns

**Standalone Components Throughout**
Every component, directive, and pipe is standalone. No NgModules for feature code. The app bootstraps with `bootstrapApplication()` and `provideRouter()`.

```typescript
@Component({
  selector: 'app-users-table',
  standalone: true,
  imports: [MatTableModule, MatPaginatorModule, MatSortModule, CommonModule],
  templateUrl: './users-table.component.html',
})
export class UsersTableComponent {
  private userService = inject(UserManagementService);
  // Component makes its own API calls
}
```

**Self-Contained Components with Services**
Each component that needs data injects the appropriate service directly. Components are portable — they can be dropped into any page and they handle their own data fetching.

```typescript
// Feature service — injectable, handles all API calls
@Injectable({ providedIn: 'root' })
export class UserManagementService {
  private http = inject(HttpClient);

  getUsers(query: UserListQuery): Observable<UserListResponse> {
    return this.http.get<UserListResponse>('/users', { params: query });
  }
}

// Component — self-contained, injects service
@Component({ standalone: true, ... })
export class UsersTableComponent implements OnInit {
  private userService = inject(UserManagementService);
  users$ = this.userService.getUsers({});
}
```

**Angular HttpClient Interceptors (replacing Axios interceptors)**
- Auth interceptor: attaches credentials (`withCredentials`), handles 401 with token refresh + request queue
- Activity interceptor: tracks user activity for inactivity timeout
- Token refresh interceptor: proactive refresh every 4 minutes

**Angular Router Guards (replacing ProtectedRoute)**
- `authGuard`: functional guard checking authentication state
- `permissionGuard`: checks role-based permissions
- Routes use `canActivate: [authGuard]` instead of wrapper components

**WebSocket Service (Socket.IO)**
- Injectable service wrapping Socket.IO client
- Returns RxJS Observables for event streams
- Chat components subscribe to message streams reactively

**Angular Material Theming (replacing MUI theme)**
- Custom Angular Material theme with dark/light palettes
- `ThemeService` manages toggle and persistence
- Uses Angular Material's theming system (`@use '@angular/material' as mat`)

### Feature Mapping (React → Angular)

| React Feature | Angular Feature | Key Changes |
|---------------|-----------------|-------------|
| `api-client` (Axios + Socket.IO) | `api-client` (HttpClient + Socket.IO service) | Axios → HttpClient, interceptors as Angular functional interceptors |
| `keycloak-auth` (Context + hooks) | `keycloak-auth` (Service + guards + interceptors) | AuthProvider → AuthService, ProtectedRoute → authGuard, useAuth → inject(AuthService) |
| `app-header` (React components) | `app-header` (standalone components) | Direct port, MUI → Angular Material toolbar/menu |
| `layouts` (Context + components) | `layouts` (Service + components) | LayoutContext → LayoutService, responsive via BreakpointObserver |
| `mastra-agents` (Context + WebSocket) | `mastra-agents` (Services + components) | ChatProvider → ChatService with RxJS, MessageListContext → MessageListService |
| `mui-theme` (MUI ThemeProvider) | `angular-material-theme` (SCSS theme) | JS theme config → SCSS theme files + ThemeService |
| `navigation` (React components) | `navigation` (standalone components) | Direct port with MatSidenav |
| `navigation-config` (config objects) | `navigation-config` (config + types) | Same structure, typed config |
| `shared` (ConfirmationModal) | `shared` (ConfirmationDialog) | MUI Dialog → MatDialog service |
| `testing-tools` (React pages) | `testing-tools` (standalone components) | Direct port |
| `theme` (hook + API) | `theme` (ThemeService + component) | useTheme → ThemeService |
| `user-management` (pages + components) | `user-management` (components + service) | Pages become routed standalone components |

### Integration Points

- **Backend API**: Unchanged. Same REST endpoints, same request/response shapes. Frontend defines its own TypeScript interfaces.
- **WebSocket**: Same Socket.IO namespaces (`/mastra-chat`, `/mastra-chat-history`), same events.
- **Keycloak**: Same cookie-based auth flow. Backend manages JWT cookies. Frontend just calls `/auth/login`, `/auth/logout`, `/auth/check`, `/auth/refresh`.
- **Docker**: Update Dockerfile to build Angular instead of Vite. Nginx config for SPA routing likely stays similar.
- **Environment**: `VITE_*` env vars become Angular environment config. Build-time injection via `environment.ts` or runtime injection via a config endpoint.

### Environment Variable Strategy

Use Angular's standard `environment.ts` pattern. The Docker build generates `environment.prod.ts` from env vars at build time using a simple shell script in the Dockerfile (matching how the current Vite build injects `VITE_*` vars). This is the stock Angular way — no runtime config endpoint needed.

### UI/UX Design Direction

The current React UI is functional but visually inconsistent. The Angular rebuild is an opportunity to apply proper Material Design principles:

- **Typography**: Use Angular Material's typography system consistently — `mat-headline-*`, `mat-body-*` classes
- **Spacing**: Consistent use of Material's 8px grid system via Angular Material density settings
- **Elevation**: Proper use of `mat-elevation-z*` — cards, dialogs, and menus at appropriate levels
- **Color system**: Coherent primary/accent/warn palette applied through Angular Material's theming, not ad-hoc hex values
- **Component usage**: Use Angular Material components idiomatically — `mat-table` with proper column defs, `mat-sidenav` with proper mode switching, `mat-form-field` with proper appearance variants
- **Layout**: Angular Flex Layout or CSS Grid for responsive structure, `BreakpointObserver` for responsive behavior
- **Polish**: Loading skeletons, smooth transitions, proper empty states, consistent icon usage from Material Icons

The goal is the exact same functionality with a unified, professional look that feels like a single cohesive application.

## Scope

### In Scope
- Complete Angular project scaffolding (angular.json, tsconfig, package.json) using Angular CLI defaults
- All 12 features rebuilt as Angular standalone components + services
- Visual facelift applying true Angular Material design principles (same functionality, polished UI)
- Angular Material theme with dark/light mode
- Angular Router with guards for auth and permissions
- HttpClient interceptors for auth, token refresh, and activity tracking
- Socket.IO integration via RxJS-wrapped service
- Responsive layout with Angular Material sidenav + BreakpointObserver
- Unit test setup with Karma/Jasmine (Angular default)
- Docker build configuration updates (Dockerfile for `ng build`)
- Taskfile.yml updates for Angular CLI commands
- E2E test updates to account for Angular Material DOM changes (selectors, class names)

### Out of Scope
- Backend changes (API stays the same)
- Keycloak configuration changes
- New features not in the current React app
- Server-side rendering (SSR) — current app is SPA, keep it SPA
- Database or infrastructure changes
- Helm chart changes (container exposes same port)

## Open Questions

None — all resolved.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Component style | Standalone components only | Angular best practice since v15+, no NgModules for feature code |
| Build tooling | Angular CLI with esbuild | Stock Angular, no Vite or third-party build tools |
| Testing framework | Karma/Jasmine | Angular default — no third-party test runners |
| Environment config | Angular `environment.ts` (build-time) | Standard Angular pattern, Docker build generates from env vars |
| State management | Services + RxJS (no NgRx) | Matches current app's simplicity (React Context → Angular Services), avoids over-engineering |
| HTTP client | Angular HttpClient | Framework-native, interceptor support, typed responses, RxJS integration |
| UI framework | Angular Material | Direct replacement for MUI, matches the user's requirement |
| WebSocket | Socket.IO client wrapped in service | Same library, RxJS Observable wrapper for Angular-native reactive patterns |
| CSS approach | SCSS + Angular Material theming | Angular Material's theming system is SCSS-based, consistent with Angular ecosystem |
| Feature structure | Preserve `src/features/` layout | Required for decomposition pipeline compatibility |
| Angular version | Latest (19+) | Use whatever is current latest stable |
| Markdown rendering | ngx-markdown | Established Angular library, supports syntax highlighting and GFM |
| UI direction | Material Design facelift | Same functionality, unified professional look with proper Material Design principles |
| E2E tests | Update selectors for Angular Material | Most tests use accessibility selectors (portable), update MUI-specific ones (`.MuiBackdrop-root` → `cdk-overlay-backdrop`) |

## E2E Test Migration Notes

The E2E tests (Playwright) are mostly compatible because they use accessibility-first selectors. Key changes needed:

| Current Selector | Change Required | Angular Material Equivalent |
|-----------------|----------------|---------------------------|
| `.MuiBackdrop-root` | Yes | `.cdk-overlay-backdrop` |
| `getByRole('heading', { name: /sign in/i })` | No | Same — keep heading text |
| `getByLabel(/username/i)` | No | Same — Angular Material `mat-form-field` with `mat-label` |
| `getByPlaceholder(/type.*message/i)` | No | Same — keep placeholder text |
| `getByRole('button', { name: /send/i })` | No | Same — keep button text |
| `getByRole('article', { name: /assistant message/i })` | No | Same — keep semantic HTML |
| `input[id="email"]` | No | Same — keep form control IDs |
| `button[aria-label*="logout" i]` | No | Same — keep aria-labels |

**Strategy**: Preserve all aria-labels, roles, form IDs, and placeholder text in the Angular rebuild so the E2E tests need minimal changes. Only MUI-specific CSS class selectors need updating.
