import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { UserFormComponent } from '../components/user-form/user-form.component';
import { User } from '../types';

@Component({
  selector: 'app-create-user-page',
  standalone: true,
  imports: [UserFormComponent],
  template: `
    <div style="padding: 24px;">
      <h1>Create User</h1>
      <app-user-form (saved)="onSaved($event)" />
    </div>
  `,
})
export class CreateUserPage {
  private router = inject(Router);

  onSaved(_user: User): void {
    this.router.navigate(['/admin/users']);
  }
}
