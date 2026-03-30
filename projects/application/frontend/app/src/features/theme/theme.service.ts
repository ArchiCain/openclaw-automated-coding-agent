import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private http = inject(HttpClient);

  isDarkMode$ = new BehaviorSubject<boolean>(false);

  initialize(theme: 'dark' | 'light'): void {
    const isDark = theme === 'dark';
    this.isDarkMode$.next(isDark);
    this.applyThemeClass(isDark);
  }

  toggle(): void {
    const isDark = !this.isDarkMode$.getValue();
    this.isDarkMode$.next(isDark);
    this.applyThemeClass(isDark);
    this.http
      .patch('/users/me/preferences', { theme: isDark ? 'dark' : 'light' })
      .subscribe();
  }

  private applyThemeClass(isDark: boolean): void {
    if (isDark) {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
  }
}
