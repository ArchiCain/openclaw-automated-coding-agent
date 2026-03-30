import { Component, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { UserFormComponent } from '../components/user-form/user-form.component';
import { User } from '../types';

@Component({
  selector: 'app-edit-user-page',
  standalone: true,
  imports: [UserFormComponent],
  template: `
    <div style="padding: 24px;">
      <h1>Edit User</h1>
      <app-user-form [userId]="id" (saved)="onSaved($event)" />
    </div>
  `,
})
export class EditUserPage {
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  id = this.route.snapshot.paramMap.get('id')!;

  onSaved(_user: User): void {
    this.router.navigate(['/admin/users']);
  }
}
