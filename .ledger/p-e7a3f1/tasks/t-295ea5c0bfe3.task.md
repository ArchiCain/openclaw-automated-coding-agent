---
id: t-295ea5c0bfe3
planId: p-e7a3f1
project: frontend
feature: material-theme
specialist: frontend-eng
dependsOn: ["t-6373994e32d2"]
status: ready
attempts: 0
commitHash: null
created: 2026-03-29T18:27:00.000Z
updated: 2026-03-29T18:27:00.000Z
---

# Task: Angular Material Theme Configuration

## Goal
Create the Angular Material custom theme in `src/features/angular-material-theme/` and wire it into `src/styles.scss`. This defines the visual foundation — color palette, typography, and density — for the entire application using Angular Material's SCSS theming system.

## Context
The current React app uses Material UI with a custom theme in `projects/application/frontend/app/src/features/mui-theme/`. The Angular rebuild replaces this with Angular Material's `@use '@angular/material' as mat` SCSS theming. The theme must support both dark and light mode palettes; the ThemeService (a separate task) toggles between them at runtime by setting a CSS class on `<body>`.

## What to Build

Create `src/features/angular-material-theme/` with:

- `_theme.scss` — define custom palettes using `mat.define-palette()` for primary, accent, and warn colors; define light theme with `mat.define-light-theme()` and dark theme with `mat.define-dark-theme()`; export both as SCSS variables for use in `styles.scss`
- `index.ts` — barrel export (minimal; theme is CSS-only but export the feature path for documentation)

Update `src/styles.scss` to:
- `@use '@angular/material' as mat;` — include Angular Material's core styles
- `@include mat.core()` — include base Material styles (typography, ripple, etc.)
- Apply the light theme globally: `@include mat.all-component-themes($light-theme);`
- Apply dark theme under `.dark-theme` body class: `@include mat.all-component-themes($dark-theme);`
- Add global typography using Material's type scale
- Set base CSS variables for consistent spacing (8px grid)

**Color direction**: Use a professional blue-based primary palette (e.g., Angular Material's `$mat-indigo` or `$mat-blue`), a complementary accent, and standard red for warn. Match the polished Material Design aesthetic described in the plan.

## Acceptance Criteria
- [ ] `ng build` succeeds with the theme imported
- [ ] Light theme styles applied by default (no `.dark-theme` class)
- [ ] Dark theme styles applied when `<body class="dark-theme">` is set
- [ ] No ad-hoc hex color values in theme — all colors from Angular Material palette system
- [ ] `src/styles.scss` includes `@use '@angular/material' as mat` and Material core
- [ ] Type-check passes

## References
- `projects/docs/app/docs/projects/application/frontend.md` — existing `mui-theme` feature to understand scope (being replaced)
- Angular Material theming guide: use `@use '@angular/material' as mat` pattern, `mat.define-palette()`, `mat.define-light-theme()`, `mat.all-component-themes()`
