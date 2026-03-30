---
id: t-b3fdb1c0f543
planId: p-e7a3f1
project: frontend
feature: layout-navigation
specialist: frontend-eng
dependsOn: ["t-6373994e32d2", "t-d54b526e09f5", "t-5a23bd61342d"]
status: ready
attempts: 0
commitHash: null
created: 2026-03-29T18:27:00.000Z
updated: 2026-03-29T18:27:00.000Z
---

# Task: Navigation Sidebar Components

## Goal
Build the `navigation` feature: the left sidebar navigation components using Angular Material `MatSidenav`. Includes both the permanent sidebar (desktop) and the temporary drawer (mobile), with hierarchical nav item rendering and permission-based filtering.

## Context
The existing React implementation: `projects/application/frontend/app/src/features/navigation/LeftNavigationSidebar.tsx` (permanent) and `LeftNavigationDrawer.tsx` (temporary/mobile). The Angular version uses `<mat-sidenav>` from `@angular/material/sidenav` and `<mat-nav-list>` from `@angular/material/list`.

The navigation renders items from `NAV_CONFIG` (from `navigation-config` feature, task t-d54b526e09f5). Items with `requiredPermission` are only shown if `AuthService.hasPermission()` returns true.

**Important for E2E compatibility**: Navigation links should use `routerLink` with `mat-list-item`. The hamburger menu button (`button[aria-label*="menu" i]` or similar) must be accessible.

## What to Build

Create `src/features/navigation/` with:

- `navigation-sidebar.component.ts` — standalone `@Component`:
  - Permanent sidebar for desktop; `mode="side"`, `opened` by default
  - Imports: `[MatSidenavModule, MatListModule, MatIconModule, RouterModule, CommonModule]`
  - `navItems` computed from `NAV_CONFIG` filtered by `AuthService.hasPermission()`
  - Renders `<mat-nav-list>` with `<a mat-list-item [routerLink]="item.route">` items
  - `<mat-icon>` before each label
  - Active route highlight via `routerLinkActive="active-link"`
- `navigation-sidebar.component.html` — template
- `navigation-drawer.component.ts` — standalone `@Component`:
  - Temporary drawer for mobile (`mode="over"`)
  - Accepts `@Input() opened: boolean` and `@Output() closedDrawer = new EventEmitter<void>()`
  - Same nav list rendering as sidebar
- `navigation-drawer.component.html` — template
- `index.ts` — barrel exporting both components

## Acceptance Criteria
- [ ] `NavigationSidebarComponent` renders `mat-nav-list` with all permitted nav items
- [ ] `NavigationDrawerComponent` closes on item click and emits `closedDrawer`
- [ ] Items with `requiredPermission` are hidden when user lacks permission
- [ ] `routerLinkActive` highlights the current route
- [ ] Both components are standalone
- [ ] `ng build` succeeds
- [ ] Type-check passes

## References
- `projects/application/frontend/app/src/features/navigation/LeftNavigationSidebar.tsx` — React component to port
- `projects/application/frontend/app/src/features/navigation/LeftNavigationDrawer.tsx` — React drawer to port
- `projects/application/frontend/app/src/features/navigation-config/` — nav config consumed by this feature
