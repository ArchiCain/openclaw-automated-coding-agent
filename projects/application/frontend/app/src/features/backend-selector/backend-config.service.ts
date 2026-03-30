import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';

export type BackendType = 'nestjs' | 'fastapi';

@Injectable({ providedIn: 'root' })
export class BackendConfigService {
  private readonly STORAGE_KEY = 'preferred-backend';
  readonly selectedBackend$ = new BehaviorSubject<BackendType>(this.loadFromStorage());

  getBaseUrl(): string {
    return this.selectedBackend$.getValue() === 'fastapi'
      ? (environment.fastapiUrl ?? 'http://api-python.mac-mini')
      : '';
  }

  setBackend(backend: BackendType): void {
    this.selectedBackend$.next(backend);
    localStorage.setItem(this.STORAGE_KEY, backend);
  }

  getSelectedBackend(): BackendType {
    return this.selectedBackend$.getValue();
  }

  private loadFromStorage(): BackendType {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored === 'fastapi' ? 'fastapi' : 'nestjs';
  }
}
