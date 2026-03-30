import { Component, inject, OnInit, OnDestroy, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, MatPaginator } from '@angular/material/paginator';
import { MatSortModule, MatSort } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { UserManagementService } from '../../user-management.service';
import { ConfirmationDialogComponent } from '../../../shared/confirmation-dialog/confirmation-dialog.component';
import { ConfirmationDialogData } from '../../../shared/confirmation-dialog/types';
import { User } from '../../types';

@Component({
  selector: 'app-users-table',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDialogModule,
  ],
  templateUrl: './users-table.component.html',
})
export class UsersTableComponent implements OnInit, AfterViewInit, OnDestroy {
  private service = inject(UserManagementService);
  private dialog = inject(MatDialog);
  private destroy$ = new Subject<void>();
  private searchSubject = new Subject<string>();

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  dataSource = new MatTableDataSource<User>();
  displayedColumns = ['username', 'email', 'roles', 'actions'];
  loading = false;

  ngOnInit(): void {
    this.loadUsers();
    this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntil(this.destroy$))
      .subscribe((search) => {
        this.loadUsers({ search });
      });
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadUsers(query: { search?: string } = {}): void {
    this.loading = true;
    this.service.getUsers(query).subscribe({
      next: (res) => {
        this.dataSource.data = res.users;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  onSearchChange(value: string): void {
    this.searchSubject.next(value);
  }

  deleteUser(user: User): void {
    const data: ConfirmationDialogData = {
      title: 'Delete User',
      message: `Are you sure you want to delete user "${user.username}"?`,
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
    };
    const ref = this.dialog.open(ConfirmationDialogComponent, { data });
    ref.afterClosed().subscribe((confirmed) => {
      if (confirmed) {
        this.service.deleteUser(user.id).subscribe(() => {
          this.loadUsers();
        });
      }
    });
  }
}
