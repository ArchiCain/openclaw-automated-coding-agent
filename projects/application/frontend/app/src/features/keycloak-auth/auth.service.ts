import { Injectable, inject, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, map, switchMap, tap, catchError, of } from 'rxjs';
import { AuthState, AuthUser } from './types';
import { hasPermission } from './permissions/permissions';

@Injectable({ providedIn: 'root' })
export class AuthService implements OnDestroy {
  private http = inject(HttpClient);

  authState$ = new BehaviorSubject<AuthState>({
    authenticated: false,
    user: null,
    loading: false,
  });

  isAuthenticated$: Observable<boolean> = this.authState$.pipe(
    map((state) => state.authenticated)
  );

  currentUser$: Observable<AuthUser | null> = this.authState$.pipe(
    map((state) => state.user)
  );

  private refreshIntervalId: ReturnType<typeof setInterval> | null = null;

  login(username: string, password: string): Observable<void> {
    return this.http.post<void>('/auth/login', { username, password }).pipe(
      switchMap(() => this.checkAuth()),
      map(() => undefined)
    );
  }

  logout(): Observable<void> {
    return this.http.post<void>('/auth/logout', {}).pipe(
      tap(() => {
        this.stopProactiveRefresh();
        this.authState$.next({
          authenticated: false,
          user: null,
          loading: false,
        });
      }),
      map(() => undefined),
      // If logout call fails (e.g. already expired), still clear local state
      catchError(() => {
        this.stopProactiveRefresh();
        this.authState$.next({ authenticated: false, user: null, loading: false });
        return of(undefined);
      })
    );
  }

  checkAuth(): Observable<AuthState> {
    this.authState$.next({ ...this.authState$.getValue(), loading: true });
    return this.http
      .get<{ authenticated: boolean; user?: AuthUser; theme?: 'dark' | 'light' }>('/auth/check')
      .pipe(
        tap((response) => {
          this.authState$.next({
            authenticated: response.authenticated,
            user: response.user ?? null,
            loading: false,
            theme: response.theme,
          });
        }),
        map(() => this.authState$.getValue()),
        // On any error (401, 5xx, network) — treat as unauthenticated, don't throw
        catchError(() => {
          this.authState$.next({ authenticated: false, user: null, loading: false });
          return of(this.authState$.getValue());
        })
      );
  }

  refresh(): Observable<boolean> {
    return this.http
      .post<{ success: boolean }>('/auth/refresh', {})
      .pipe(
        map((response) => response.success),
        catchError(() => of(false))
      );
  }

  startProactiveRefresh(): void {
    this.stopProactiveRefresh();
    this.refreshIntervalId = setInterval(() => {
      this.refresh().subscribe();
    }, 4 * 60 * 1000);
  }

  stopProactiveRefresh(): void {
    if (this.refreshIntervalId !== null) {
      clearInterval(this.refreshIntervalId);
      this.refreshIntervalId = null;
    }
  }

  recordActivity(): void {
    // Resets inactivity timer — called by activityInterceptor on each outbound request
  }

  hasPermission(permission: string): boolean {
    const { user } = this.authState$.getValue();
    return hasPermission(user, permission);
  }

  ngOnDestroy(): void {
    this.stopProactiveRefresh();
  }
}
