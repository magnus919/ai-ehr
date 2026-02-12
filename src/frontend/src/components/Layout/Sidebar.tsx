import { NavLink } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  HomeIcon,
  UsersIcon,
  CalendarDaysIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  HeartIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  BeakerIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline';
import { useUIStore } from '@/store/uiStore';
import { APP_NAME } from '@/utils/constants';

// -----------------------------------------------------------------------------
// Navigation Items
// -----------------------------------------------------------------------------

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  badge?: number;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Patients', href: '/patients', icon: UsersIcon },
  { name: 'Scheduling', href: '/scheduling', icon: CalendarDaysIcon },
  { name: 'Vital Signs', href: '/vital-signs', icon: HeartIcon },
  { name: 'Clinical Notes', href: '/clinical-notes', icon: DocumentTextIcon },
  { name: 'Allergies', href: '/allergies', icon: ExclamationTriangleIcon },
  { name: 'Immunizations', href: '/immunizations', icon: BeakerIcon },
  { name: 'Orders', href: '/orders', icon: ClipboardDocumentListIcon },
  { name: 'Reports', href: '/reports', icon: ChartBarIcon },
];

const secondaryNavigation: NavItem[] = [
  { name: 'User Management', href: '/users', icon: UserGroupIcon },
  { name: 'Admin', href: '/admin', icon: Cog6ToothIcon },
];

// -----------------------------------------------------------------------------
// Sidebar Component
// -----------------------------------------------------------------------------

export function Sidebar() {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const sidebarMobileOpen = useUIStore((s) => s.sidebarMobileOpen);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const setSidebarMobileOpen = useUIStore((s) => s.setSidebarMobileOpen);

  return (
    <>
      {/* Mobile overlay */}
      {sidebarMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-gray-200 bg-white transition-all duration-300 dark:border-gray-700 dark:bg-gray-800',
          sidebarCollapsed ? 'w-sidebar-collapsed' : 'w-sidebar',
          // Mobile: slide in/out
          sidebarMobileOpen
            ? 'translate-x-0'
            : '-translate-x-full lg:translate-x-0',
        )}
        aria-label="Main navigation"
      >
        {/* Logo / Brand */}
        <div className="flex h-header items-center justify-between border-b border-gray-200 px-4 dark:border-gray-700">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 4.5v15m7.5-7.5h-15"
                  />
                </svg>
              </div>
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                {APP_NAME}
              </span>
            </div>
          )}
          {sidebarCollapsed && (
            <div className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 4.5v15m7.5-7.5h-15"
                />
              </svg>
            </div>
          )}
        </div>

        {/* Primary Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 scrollbar-thin" aria-label="Primary">
          <ul className="space-y-1" role="list">
            {navigation.map((item) => (
              <li key={item.name}>
                <SidebarNavLink item={item} collapsed={sidebarCollapsed} />
              </li>
            ))}
          </ul>

          {/* Divider */}
          <div className="my-4 border-t border-gray-200 dark:border-gray-700" />

          {/* Secondary Navigation */}
          <ul className="space-y-1" role="list">
            {secondaryNavigation.map((item) => (
              <li key={item.name}>
                <SidebarNavLink item={item} collapsed={sidebarCollapsed} />
              </li>
            ))}
          </ul>
        </nav>

        {/* Collapse Toggle */}
        <div className="hidden border-t border-gray-200 p-3 dark:border-gray-700 lg:block">
          <button
            onClick={toggleSidebar}
            className={clsx(
              'flex w-full items-center rounded-md px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700',
              sidebarCollapsed ? 'justify-center' : 'justify-between',
            )}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {!sidebarCollapsed && (
              <span className="text-xs font-medium">Collapse</span>
            )}
            {sidebarCollapsed ? (
              <ChevronDoubleRightIcon className="h-4 w-4" />
            ) : (
              <ChevronDoubleLeftIcon className="h-4 w-4" />
            )}
          </button>
        </div>
      </aside>
    </>
  );
}

// -----------------------------------------------------------------------------
// SidebarNavLink Sub-component
// -----------------------------------------------------------------------------

interface SidebarNavLinkProps {
  item: NavItem;
  collapsed: boolean;
}

function SidebarNavLink({ item, collapsed }: SidebarNavLinkProps) {
  return (
    <NavLink
      to={item.href}
      className={({ isActive }) =>
        clsx(
          'group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
          collapsed ? 'justify-center' : 'gap-3',
          isActive
            ? 'bg-primary-50 text-primary-700 dark:bg-primary-950/30 dark:text-primary-400'
            : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white',
        )
      }
      title={collapsed ? item.name : undefined}
      aria-label={collapsed ? item.name : undefined}
    >
      <item.icon
        className={clsx(
          'h-5 w-5 flex-shrink-0',
          'group-[.active]:text-primary-600 dark:group-[.active]:text-primary-400',
        )}
        aria-hidden="true"
      />
      {!collapsed && <span>{item.name}</span>}
      {!collapsed && item.badge != null && item.badge > 0 && (
        <span className="ml-auto inline-flex items-center rounded-full bg-primary-100 px-2 py-0.5 text-2xs font-medium text-primary-700 dark:bg-primary-900 dark:text-primary-300">
          {item.badge}
        </span>
      )}
    </NavLink>
  );
}
