import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { NAV_CONFIG, NavSection } from '../navigation-config';
import { AuthService } from '../keycloak-auth';

@Component({
  selector: 'app-navigation-drawer',
  standalone: true,
  imports: [MatListModule, MatIconModule, RouterModule, CommonModule],
  templateUrl: './navigation-drawer.component.html',
})
export class NavigationDrawerComponent {
  @Input() opened = false;
  @Output() closedDrawer = new EventEmitter<void>();

  private authService = inject(AuthService);

  navSections: NavSection[] = NAV_CONFIG.map((section) => ({
    ...section,
    items: section.items.filter(
      (item) => !item.requiredPermission || this.authService.hasPermission(item.requiredPermission)
    ),
  })).filter((section) => section.items.length > 0);

  onItemClick(): void {
    this.closedDrawer.emit();
  }
}
