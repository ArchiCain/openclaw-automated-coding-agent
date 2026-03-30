import { ApplicationConfig, APP_INITIALIZER, inject } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { tap } from 'rxjs';
import { routes } from './app.routes';
import {
  AuthService,
  authInterceptor,
  tokenRefreshInterceptor,
  activityInterceptor,
} from './features/keycloak-auth';
import { ThemeService } from './features/theme';
import { backendUrlInterceptor } from './features/backend-selector';

function initializeApp(): () => Promise<void> {
  const authService = inject(AuthService);
  const themeService = inject(ThemeService);
  return () =>
    new Promise<void>((resolve) => {
      authService
        .checkAuth()
        .pipe(
          tap((authState) => {
            if (authState.theme) {
              themeService.initialize(authState.theme);
            }
          })
        )
        .subscribe({ next: () => resolve(), error: () => resolve() });
    });
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(
      withInterceptors([backendUrlInterceptor, authInterceptor, tokenRefreshInterceptor, activityInterceptor])
    ),
    provideAnimationsAsync(),
    {
      provide: APP_INITIALIZER,
      useFactory: initializeApp,
      multi: true,
    },
  ],
};
