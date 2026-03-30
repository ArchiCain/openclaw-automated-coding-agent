import { Component } from '@angular/core';
import { HealthCheckComponent } from '../components/health-check/health-check.component';
import { DbClientComponent } from '../components/db-client/db-client.component';

@Component({
  selector: 'app-smoke-tests-page',
  standalone: true,
  imports: [HealthCheckComponent, DbClientComponent],
  template: `
    <div style="padding: 24px; max-width: 800px; margin: 0 auto;">
      <h1>Smoke Tests</h1>
      <div style="display: flex; flex-direction: column; gap: 24px;">
        <app-health-check />
        <app-db-client />
      </div>
    </div>
  `,
})
export class SmokeTestsPage {}
