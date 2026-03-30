import { TestBed } from '@angular/core/testing';
import { BackendConfigService } from './backend-config.service';

describe('BackendConfigService', () => {
  let service: BackendConfigService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({});
    service = TestBed.inject(BackendConfigService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should default to nestjs when localStorage is empty', () => {
    expect(service.getSelectedBackend()).toBe('nestjs');
  });

  it('should load fastapi from localStorage', () => {
    localStorage.setItem('preferred-backend', 'fastapi');
    // Re-create service to re-read localStorage
    const newService = new BackendConfigService();
    expect(newService.getSelectedBackend()).toBe('fastapi');
  });

  it('should default to nestjs for unknown localStorage value', () => {
    localStorage.setItem('preferred-backend', 'unknown-value');
    const newService = new BackendConfigService();
    expect(newService.getSelectedBackend()).toBe('nestjs');
  });

  it('should return empty string for nestjs base URL', () => {
    service.setBackend('nestjs');
    expect(service.getBaseUrl()).toBe('');
  });

  it('should return fastapi URL for fastapi base URL', () => {
    service.setBackend('fastapi');
    expect(service.getBaseUrl()).toContain('api-python');
  });

  it('should persist backend selection to localStorage', () => {
    service.setBackend('fastapi');
    expect(localStorage.getItem('preferred-backend')).toBe('fastapi');
  });

  it('should update selectedBackend$ when setBackend is called', () => {
    const values: string[] = [];
    service.selectedBackend$.subscribe((v) => values.push(v));

    service.setBackend('fastapi');
    service.setBackend('nestjs');

    expect(values).toEqual(['nestjs', 'fastapi', 'nestjs']);
  });
});
