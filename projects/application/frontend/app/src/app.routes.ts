import { Routes } from '@angular/router';
import { authGuard, permissionGuard } from './features/keycloak-auth';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/keycloak-auth').then((m) => m.LoginComponent),
  },
  {
    path: '',
    loadComponent: () =>
      import('./features/layouts').then((m) => m.AppLayoutComponent),
    canActivate: [authGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () =>
          import('./features/mastra-agents').then((m) => m.ChatPage),
      },
      {
        path: 'smoke-tests',
        loadComponent: () =>
          import('./features/testing-tools').then((m) => m.SmokeTestsPage),
      },
      {
        path: 'admin/users',
        canActivate: [permissionGuard('admin')],
        children: [
          {
            path: '',
            loadComponent: () =>
              import('./features/user-management').then((m) => m.UsersListPage),
          },
          {
            path: 'new',
            loadComponent: () =>
              import('./features/user-management').then((m) => m.CreateUserPage),
          },
          {
            path: ':id',
            loadComponent: () =>
              import('./features/user-management').then((m) => m.EditUserPage),
          },
        ],
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
