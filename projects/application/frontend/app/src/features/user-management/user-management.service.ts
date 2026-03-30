import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CreateUserDto, UpdateUserDto, User, UserListQuery, UserListResponse } from './types';

@Injectable({ providedIn: 'root' })
export class UserManagementService {
  private http = inject(HttpClient);

  getUsers(query: UserListQuery): Observable<UserListResponse> {
    let params = new HttpParams();
    if (query.search !== undefined) params = params.set('search', query.search);
    if (query.page !== undefined) params = params.set('page', query.page);
    if (query.limit !== undefined) params = params.set('limit', query.limit);
    if (query.sortBy !== undefined) params = params.set('sortBy', query.sortBy);
    if (query.sortOrder !== undefined) params = params.set('sortOrder', query.sortOrder);
    return this.http.get<UserListResponse>('/users', { params });
  }

  getUser(id: string): Observable<User> {
    return this.http.get<User>(`/users/${id}`);
  }

  createUser(dto: CreateUserDto): Observable<User> {
    return this.http.post<User>('/users', dto);
  }

  updateUser(id: string, dto: UpdateUserDto): Observable<User> {
    return this.http.put<User>(`/users/${id}`, dto);
  }

  deleteUser(id: string): Observable<void> {
    return this.http.delete<void>(`/users/${id}`);
  }
}
