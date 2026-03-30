import { Component, EventEmitter, Output, inject } from '@angular/core';
import { AsyncPipe, CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { AuthService } from '../keycloak-auth';
import { ThemeToggleComponent } from '../theme';
import { BackendSelectorComponent } from '../backend-selector';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    CommonModule,
    ThemeToggleComponent,
    BackendSelectorComponent,
    AsyncPipe,
  ],
  templateUrl: './app-header.component.html',
})
export class AppHeaderComponent {
  @Output() menuToggled = new EventEmitter<void>();

  authService = inject(AuthService);
  private router = inject(Router);

  onLogout(): void {
    this.authService.logout().subscribe(() => {
      this.router.navigate(['/login']);
    });
  }
}
