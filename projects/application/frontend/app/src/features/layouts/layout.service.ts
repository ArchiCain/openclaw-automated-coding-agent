import { Injectable, inject } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { BehaviorSubject, Observable, map } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LayoutService {
  private breakpoints = inject(BreakpointObserver);

  isMobile$: Observable<boolean> = this.breakpoints
    .observe(Breakpoints.Handset)
    .pipe(map((result) => result.matches));

  sidenavOpen$ = new BehaviorSubject<boolean>(false);

  toggleSidenav(): void {
    this.sidenavOpen$.next(!this.sidenavOpen$.value);
  }

  openSidenav(): void {
    this.sidenavOpen$.next(true);
  }

  closeSidenav(): void {
    this.sidenavOpen$.next(false);
  }
}
