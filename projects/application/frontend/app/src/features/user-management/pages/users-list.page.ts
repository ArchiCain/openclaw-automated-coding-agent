import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { UsersTableComponent } from '../components/users-table/users-table.component';

@Component({
  selector: 'app-users-list-page',
  standalone: true,
  imports: [RouterModule, MatButtonModule, UsersTableComponent],
  template: `
    <div style="padding: 24px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h1 style="margin: 0;">Users</h1>
        <a mat-raised-button color="primary" routerLink="/admin/users/new">Add User</a>
      </div>
      <app-users-table />
    </div>
  `,
})
export class UsersListPage {}
