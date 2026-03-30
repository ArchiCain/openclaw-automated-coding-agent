import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-health-check',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatProgressSpinnerModule, MatCardModule],
  template: `
    <mat-card>
      <mat-card-header>
        <mat-card-title>Health Check</mat-card-title>
      </mat-card-header>
      <mat-card-content>
        <button mat-raised-button color="primary" (click)="checkHealth()" [disabled]="loading">
          Run Health Check
        </button>
        @if (loading) {
          <mat-spinner diameter="24" style="margin-top: 16px;"></mat-spinner>
        }
        @if (result !== null) {
          <pre style="margin-top: 16px; white-space: pre-wrap;">{{ result }}</pre>
        }
        @if (error) {
          <p style="color: red; margin-top: 16px;">{{ error }}</p>
        }
      </mat-card-content>
    </mat-card>
  `,
})
export class HealthCheckComponent {
  private http = inject(HttpClient);

  loading = false;
  result: string | null = null;
  error: string | null = null;

  checkHealth(): void {
    this.loading = true;
    this.result = null;
    this.error = null;

    this.http.get<object>('/health').subscribe({
      next: (res) => {
        this.result = JSON.stringify(res, null, 2);
        this.loading = false;
      },
      error: (err) => {
        this.error = err?.message ?? 'Health check failed';
        this.loading = false;
      },
    });
  }
}
