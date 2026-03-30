import { Component, Input, Output, EventEmitter, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { UserManagementService } from '../../user-management.service';
import { User } from '../../types';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCheckboxModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './user-form.component.html',
})
export class UserFormComponent implements OnInit {
  @Input() userId?: string;
  @Output() saved = new EventEmitter<User>();

  private service = inject(UserManagementService);
  private fb = inject(FormBuilder);

  form = this.fb.group({
    username: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    firstName: ['', Validators.required],
    lastName: ['', Validators.required],
    password: [''],
    roles: this.fb.group({
      admin: [false],
      user: [false],
    }),
  });

  loading = false;
  submitting = false;

  get isEditMode(): boolean {
    return !!this.userId;
  }

  ngOnInit(): void {
    if (!this.isEditMode) {
      this.form.get('password')!.setValidators([Validators.required, Validators.minLength(8)]);
      this.form.get('password')!.updateValueAndValidity();
    }

    if (this.isEditMode) {
      this.loadUser();
    }
  }

  loadUser(): void {
    this.loading = true;
    this.service.getUser(this.userId!).subscribe({
      next: (user) => {
        this.form.patchValue({
          username: user.username,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          roles: {
            admin: user.roles?.includes('admin') ?? false,
            user: user.roles?.includes('user') ?? false,
          },
        });
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    const { username, email, firstName, lastName, password, roles } = this.form.value;
    const selectedRoles: string[] = [];
    if (roles?.admin) selectedRoles.push('admin');
    if (roles?.user) selectedRoles.push('user');

    this.submitting = true;

    if (this.isEditMode) {
      this.service
        .updateUser(this.userId!, {
          username: username ?? '',
          email: email ?? '',
          firstName: firstName ?? '',
          lastName: lastName ?? '',
          roles: selectedRoles,
        })
        .subscribe({
          next: (user) => {
            this.submitting = false;
            this.saved.emit(user);
          },
          error: () => {
            this.submitting = false;
          },
        });
    } else {
      this.service
        .createUser({
          username: username ?? '',
          email: email ?? '',
          password: password ?? '',
          firstName: firstName ?? '',
          lastName: lastName ?? '',
          roles: selectedRoles,
        })
        .subscribe({
          next: (user) => {
            this.submitting = false;
            this.saved.emit(user);
          },
          error: () => {
            this.submitting = false;
          },
        });
    }
  }
}
