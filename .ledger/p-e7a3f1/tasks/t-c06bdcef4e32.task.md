---
id: t-c06bdcef4e32
planId: p-e7a3f1
project: frontend
feature: shared-components
specialist: frontend-eng
dependsOn: ["t-6373994e32d2"]
status: ready
attempts: 0
commitHash: null
created: 2026-03-29T18:27:00.000Z
updated: 2026-03-29T18:27:00.000Z
---

# Task: Shared Confirmation Dialog Component

## Goal
Build the `shared` feature: a reusable `ConfirmationDialogComponent` using Angular Material's `MatDialog` service pattern. This replaces the React `ConfirmationModal` (MUI Dialog) used for destructive action confirmation (e.g., deleting a user).

## Context
The existing React implementation: `projects/application/frontend/app/src/features/shared/components/`. It renders a modal with a title, message, and confirm/cancel buttons. In Angular, dialogs are opened imperatively via `MatDialog.open()` rather than rendered declaratively, so the component is a dialog content component.

**Important for E2E compatibility**: The dialog overlay backdrop in Angular Material is `.cdk-overlay-backdrop` (vs MUI's `.MuiBackdrop-root`). Confirm/cancel buttons should have clear accessible labels.

## What to Build

Create `src/features/shared/` with:

- `confirmation-dialog/confirmation-dialog.component.ts` — standalone `@Component`:
  - Imports: `[MatDialogModule, MatButtonModule]`
  - `data = inject(MAT_DIALOG_DATA)` of type `ConfirmationDialogData`
  - `dialogRef = inject(MatDialogRef<ConfirmationDialogComponent>)`
  - `confirm()` — `dialogRef.close(true)`
  - `cancel()` — `dialogRef.close(false)`
- `confirmation-dialog/confirmation-dialog.component.html`:
  - `<mat-dialog-content>` with title and message
  - `<mat-dialog-actions>`: Cancel button and Confirm button (with `color="warn"`)
- `confirmation-dialog/types.ts`:
  - `ConfirmationDialogData { title: string; message: string; confirmLabel?: string; cancelLabel?: string; }`
- `index.ts` — barrel: `export { ConfirmationDialogComponent } from './confirmation-dialog/confirmation-dialog.component'; export * from './confirmation-dialog/types';`

**Usage pattern** (for consumer reference in task context):
```typescript
const ref = this.dialog.open(ConfirmationDialogComponent, {
  data: { title: 'Delete User', message: 'Are you sure?' }
});
ref.afterClosed().subscribe(confirmed => { if (confirmed) { ... } });
```

## Acceptance Criteria
- [ ] `ConfirmationDialogComponent` is standalone
- [ ] Dialog uses `MAT_DIALOG_DATA` injection token
- [ ] `confirm()` closes with `true`, `cancel()` closes with `false`
- [ ] Confirm button has `color="warn"` for destructive actions
- [ ] `ng build` succeeds
- [ ] Type-check passes

## References
- `projects/application/frontend/app/src/features/shared/components/` — existing React ConfirmationModal to port
