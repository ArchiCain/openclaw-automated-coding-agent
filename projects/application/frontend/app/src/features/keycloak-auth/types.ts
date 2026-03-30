export interface AuthUser {
  id: string;
  username: string;
  email: string;
  roles: string[];
}

export interface AuthState {
  authenticated: boolean;
  user: AuthUser | null;
  loading: boolean;
  theme?: 'dark' | 'light';
}

export type Permission =
  | 'users:read'
  | 'users:create'
  | 'users:update'
  | 'users:delete'
  | 'conversations:read'
  | 'conversations:create'
  | 'conversations:delete';
