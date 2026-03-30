import { Component, inject } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { BackendConfigService, BackendType } from './backend-config.service';

@Component({
  selector: 'app-backend-selector',
  standalone: true,
  imports: [MatButtonToggleModule, AsyncPipe],
  template: `
    <mat-button-toggle-group
      [value]="backendConfigService.selectedBackend$ | async"
      (change)="onBackendChange($event.value)"
      aria-label="Select backend">
      <mat-button-toggle value="nestjs">NestJS</mat-button-toggle>
      <mat-button-toggle value="fastapi">FastAPI</mat-button-toggle>
    </mat-button-toggle-group>
  `,
})
export class BackendSelectorComponent {
  backendConfigService = inject(BackendConfigService);

  onBackendChange(backend: BackendType): void {
    this.backendConfigService.setBackend(backend);
  }
}
