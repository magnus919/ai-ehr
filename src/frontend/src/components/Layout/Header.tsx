import { Fragment, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Menu,
  MenuButton,
  MenuItems,
  MenuItem,
  Transition,
} from '@headlessui/react';
import {
  MagnifyingGlassIcon,
  BellIcon,
  Bars3Icon,
  SunIcon,
  MoonIcon,
  ComputerDesktopIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { useAuthStore } from '@/store/authStore';
import { useUIStore, type Theme } from '@/store/uiStore';
import { ROLE_LABELS } from '@/utils/constants';

// -----------------------------------------------------------------------------
// Header Component
// -----------------------------------------------------------------------------

export function Header() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);
  const unreadCount = useUIStore((s) => s.unreadCount);
  const setSidebarMobileOpen = useUIStore((s) => s.setSidebarMobileOpen);
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (searchQuery.trim()) {
        navigate(`/patients?search=${encodeURIComponent(searchQuery.trim())}`);
        setSearchQuery('');
      }
    },
    [searchQuery, navigate],
  );

  const handleLogout = useCallback(() => {
    logout();
    navigate('/login');
  }, [logout, navigate]);

  const cycleTheme = useCallback(() => {
    const next: Record<Theme, Theme> = {
      light: 'dark',
      dark: 'system',
      system: 'light',
    };
    setTheme(next[theme]);
  }, [theme, setTheme]);

  const themeIcon =
    theme === 'dark' ? (
      <MoonIcon className="h-5 w-5" />
    ) : theme === 'light' ? (
      <SunIcon className="h-5 w-5" />
    ) : (
      <ComputerDesktopIcon className="h-5 w-5" />
    );

  return (
    <header className="sticky top-0 z-30 flex h-header items-center justify-between border-b border-gray-200 bg-white px-4 dark:border-gray-700 dark:bg-gray-800 sm:px-6">
      {/* Left: Mobile menu + Search */}
      <div className="flex flex-1 items-center gap-4">
        {/* Mobile menu button */}
        <button
          type="button"
          className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 lg:hidden"
          onClick={() => setSidebarMobileOpen(true)}
          aria-label="Open navigation menu"
        >
          <Bars3Icon className="h-6 w-6" />
        </button>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="hidden w-full max-w-md sm:block">
          <label htmlFor="global-search" className="sr-only">
            Search patients
          </label>
          <div className="relative">
            <MagnifyingGlassIcon
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
              aria-hidden="true"
            />
            <input
              id="global-search"
              type="search"
              placeholder="Search patients by name, MRN..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-base pl-9"
            />
          </div>
        </form>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          type="button"
          onClick={cycleTheme}
          className="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700"
          aria-label={`Current theme: ${theme}. Click to change.`}
          title={`Theme: ${theme}`}
        >
          {themeIcon}
        </button>

        {/* Notifications */}
        <button
          type="button"
          className="relative rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700"
          aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
        >
          <BellIcon className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-2xs font-bold text-white">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* User Menu */}
        <Menu as="div" className="relative">
          <MenuButton className="flex items-center gap-2 rounded-md p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm font-medium text-white">
              {user
                ? `${user.firstName.charAt(0).toUpperCase()}${user.lastName.charAt(0).toUpperCase()}`
                : '?'}
            </div>
            <div className="hidden text-left md:block">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {user ? `${user.firstName} ${user.lastName}` : 'User'}
              </p>
              <p className="text-2xs text-gray-500 dark:text-gray-400">
                {user?.role ? ROLE_LABELS[user.role] ?? user.role : ''}
              </p>
            </div>
          </MenuButton>

          <Transition
            as={Fragment}
            enter="transition ease-out duration-100"
            enterFrom="transform opacity-0 scale-95"
            enterTo="transform opacity-100 scale-100"
            leave="transition ease-in duration-75"
            leaveFrom="transform opacity-100 scale-100"
            leaveTo="transform opacity-0 scale-95"
          >
            <MenuItems className="absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black/5 focus:outline-none dark:bg-gray-800 dark:ring-gray-700">
              <div className="border-b border-gray-100 px-4 py-3 dark:border-gray-700">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {user ? `${user.firstName} ${user.lastName}` : 'User'}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {user?.email}
                </p>
              </div>
              <MenuItem>
                {({ focus }) => (
                  <button
                    onClick={() => navigate('/profile')}
                    className={clsx(
                      'flex w-full items-center gap-2 px-4 py-2 text-sm',
                      focus
                        ? 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
                        : 'text-gray-700 dark:text-gray-300',
                    )}
                  >
                    <UserCircleIcon className="h-4 w-4" />
                    My Profile
                  </button>
                )}
              </MenuItem>
              <MenuItem>
                {({ focus }) => (
                  <button
                    onClick={() => navigate('/settings')}
                    className={clsx(
                      'flex w-full items-center gap-2 px-4 py-2 text-sm',
                      focus
                        ? 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
                        : 'text-gray-700 dark:text-gray-300',
                    )}
                  >
                    <Cog6ToothIcon className="h-4 w-4" />
                    Settings
                  </button>
                )}
              </MenuItem>
              <div className="border-t border-gray-100 dark:border-gray-700" />
              <MenuItem>
                {({ focus }) => (
                  <button
                    onClick={handleLogout}
                    className={clsx(
                      'flex w-full items-center gap-2 px-4 py-2 text-sm',
                      focus
                        ? 'bg-gray-100 text-red-700 dark:bg-gray-700'
                        : 'text-red-600 dark:text-red-400',
                    )}
                  >
                    <ArrowRightOnRectangleIcon className="h-4 w-4" />
                    Sign Out
                  </button>
                )}
              </MenuItem>
            </MenuItems>
          </Transition>
        </Menu>
      </div>
    </header>
  );
}
