import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-db-client',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatCardModule,
  ],
  template: `
    <mat-card>
      <mat-card-header>
        <mat-card-title>DB Client</mat-card-title>
      </mat-card-header>
      <mat-card-content>
        <mat-form-field style="width: 100%;">
          <mat-label>Query</mat-label>
          <textarea matInput [(ngModel)]="query" rows="4" placeholder="Enter SQL query..."></textarea>
        </mat-form-field>
        <button mat-raised-button color="primary" (click)="runQuery()" [disabled]="loading || !query.trim()">
          Run Query
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
export class DbClientComponent {
  private http = inject(HttpClient);

  query = '';
  loading = false;
  result: string | null = null;
  error: string | null = null;

  runQuery(): void {
    this.loading = true;
    this.result = null;
    this.error = null;

    this.http.post('/db/query', { query: this.query }).subscribe({
      next: (res) => {
        this.result = JSON.stringify(res, null, 2);
        this.loading = false;
      },
      error: (err) => {
        this.error = err?.message ?? 'Query failed';
        this.loading = false;
      },
    });
  }
}
