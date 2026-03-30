import { Component, inject } from '@angular/core';
import { AsyncPipe, CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { AppHeaderComponent } from '../app-header';
import { NavigationSidebarComponent, NavigationDrawerComponent } from '../navigation';
import { LayoutService } from './layout.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [
    MatSidenavModule,
    AppHeaderComponent,
    NavigationSidebarComponent,
    NavigationDrawerComponent,
    RouterModule,
    CommonModule,
    AsyncPipe,
  ],
  templateUrl: './app-layout.component.html',
})
export class AppLayoutComponent {
  layoutService = inject(LayoutService);
}
