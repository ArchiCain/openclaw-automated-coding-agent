import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpErrorResponse, HttpEvent } from '@angular/common/http';
import { BehaviorSubject, throwError, Observable } from 'rxjs';
import { catchError, filter, switchMap, take } from 'rxjs/operators';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';

const refreshing$ = new BehaviorSubject<boolean>(false);

// Auth endpoints that must NOT trigger a refresh attempt on 401 —
// they are the auth system itself and would cause an infinite loop.
const AUTH_URLS = ['/auth/check', '/auth/refresh', '/auth/login', '/auth/logout'];

function isAuthUrl(url: string): boolean {
  return AUTH_URLS.some(path => url.includes(path));
}

function retryAfterRefresh(
  req: HttpRequest<unknown>,
  next: HttpHandlerFn,
  auth: AuthService,
  router: Router
): Observable<HttpEvent<unknown>> {
  if (refreshing$.getValue()) {
    return refreshing$.pipe(
      filter(r => !r),
      take(1),
      switchMap(() => next(req))
    );
  }

  refreshing$.next(true);
  return auth.refresh().pipe(
    switchMap(success => {
      refreshing$.next(false);
      if (success) {
        return next(req);
      }
      router.navigate(['/login']);
      return throwError(() => new Error('Session expired'));
    }),
    catchError(err => {
      refreshing$.next(false);
      router.navigate(['/login']);
      return throwError(() => err);
    })
  );
}

export const tokenRefreshInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError(err => {
      if (
        err instanceof HttpErrorResponse &&
        err.status === 401 &&
        !isAuthUrl(req.url)
      ) {
        return retryAfterRefresh(req, next, auth, router);
      }
      return throwError(() => err);
    })
  );
};
