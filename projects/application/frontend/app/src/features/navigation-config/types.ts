export interface NavItem {
  label: string;
  icon: string;
  route?: string;
  children?: NavItem[];
  requiredPermission?: string;
}

export interface NavSection {
  title?: string;
  items: NavItem[];
}
