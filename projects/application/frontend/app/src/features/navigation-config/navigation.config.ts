import { NavSection } from './types';

export const NAV_CONFIG: NavSection[] = [
  {
    items: [
      {
        label: 'Chat',
        icon: 'chat',
        route: '/',
      },
      {
        label: 'Smoke Tests',
        icon: 'science',
        route: '/smoke-tests',
      },
    ],
  },
  {
    title: 'Admin',
    items: [
      {
        label: 'Users',
        icon: 'people',
        route: '/admin/users',
        requiredPermission: 'admin',
      },
    ],
  },
];
