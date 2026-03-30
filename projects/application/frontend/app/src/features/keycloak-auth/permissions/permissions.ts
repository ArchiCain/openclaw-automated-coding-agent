import { AuthUser, Permission } from '../types';

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  admin: [
    'users:read',
    'users:create',
    'users:update',
    'users:delete',
    'conversations:read',
    'conversations:create',
    'conversations:delete',
  ],
  user: ['conversations:read', 'conversations:create'],
};

function getPermissionsForRoles(roles: string[]): Permission[] {
  const permissionSet = new Set<Permission>();
  for (const role of roles) {
    const permissions = ROLE_PERMISSIONS[role] ?? [];
    for (const permission of permissions) {
      permissionSet.add(permission);
    }
  }
  return Array.from(permissionSet);
}

export function hasPermission(user: AuthUser | null, permission: string): boolean {
  if (!user) {
    return false;
  }
  const userPermissions = getPermissionsForRoles(user.roles);
  return userPermissions.includes(permission as Permission);
}
