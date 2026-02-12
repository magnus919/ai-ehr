import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Notification } from '@/types';
import { STORAGE_KEYS } from '@/utils/constants';

// -----------------------------------------------------------------------------
// UI Store Types
// -----------------------------------------------------------------------------

export type Theme = 'light' | 'dark' | 'system';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface UIState {
  // Sidebar
  sidebarCollapsed: boolean;
  sidebarMobileOpen: boolean;

  // Theme
  theme: Theme;

  // Notifications
  notifications: Notification[];
  unreadCount: number;

  // Breadcrumbs
  breadcrumbs: BreadcrumbItem[];

  // Global loading
  globalLoading: boolean;

  // Command palette
  commandPaletteOpen: boolean;
}

interface UIActions {
  // Sidebar
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setSidebarMobileOpen: (open: boolean) => void;

  // Theme
  setTheme: (theme: Theme) => void;

  // Notifications
  addNotification: (notification: Omit<Notification, 'id' | 'read' | 'createdAt'>) => void;
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // Breadcrumbs
  setBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void;

  // Global loading
  setGlobalLoading: (loading: boolean) => void;

  // Command palette
  setCommandPaletteOpen: (open: boolean) => void;
}

type UIStore = UIState & UIActions;

// -----------------------------------------------------------------------------
// Helper to generate unique IDs
// -----------------------------------------------------------------------------

let notificationCounter = 0;
function generateId(): string {
  notificationCounter += 1;
  return `notif-${Date.now()}-${notificationCounter}`;
}

// -----------------------------------------------------------------------------
// UI Store
// -----------------------------------------------------------------------------

export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      (set) => ({
        // State
        sidebarCollapsed: false,
        sidebarMobileOpen: false,
        theme: 'system' as Theme,
        notifications: [],
        unreadCount: 0,
        breadcrumbs: [],
        globalLoading: false,
        commandPaletteOpen: false,

        // Sidebar Actions
        toggleSidebar: () =>
          set(
            (state) => ({ sidebarCollapsed: !state.sidebarCollapsed }),
            false,
            'toggleSidebar',
          ),

        setSidebarCollapsed: (collapsed) =>
          set({ sidebarCollapsed: collapsed }, false, 'setSidebarCollapsed'),

        setSidebarMobileOpen: (open) =>
          set({ sidebarMobileOpen: open }, false, 'setSidebarMobileOpen'),

        // Theme Actions
        setTheme: (theme) => {
          // Apply theme to document
          const root = document.documentElement;
          if (theme === 'dark') {
            root.classList.add('dark');
          } else if (theme === 'light') {
            root.classList.remove('dark');
          } else {
            // System preference
            const prefersDark = window.matchMedia(
              '(prefers-color-scheme: dark)',
            ).matches;
            if (prefersDark) {
              root.classList.add('dark');
            } else {
              root.classList.remove('dark');
            }
          }
          localStorage.setItem(STORAGE_KEYS.THEME, theme);
          set({ theme }, false, 'setTheme');
        },

        // Notification Actions
        addNotification: (notification) => {
          const newNotification: Notification = {
            ...notification,
            id: generateId(),
            read: false,
            createdAt: new Date().toISOString(),
          };
          set(
            (state) => ({
              notifications: [newNotification, ...state.notifications].slice(0, 50),
              unreadCount: state.unreadCount + 1,
            }),
            false,
            'addNotification',
          );
        },

        markNotificationRead: (id) =>
          set(
            (state) => ({
              notifications: state.notifications.map((n) =>
                n.id === id ? { ...n, read: true } : n,
              ),
              unreadCount: Math.max(0, state.unreadCount - 1),
            }),
            false,
            'markNotificationRead',
          ),

        markAllNotificationsRead: () =>
          set(
            (state) => ({
              notifications: state.notifications.map((n) => ({ ...n, read: true })),
              unreadCount: 0,
            }),
            false,
            'markAllNotificationsRead',
          ),

        removeNotification: (id) =>
          set(
            (state) => {
              const notification = state.notifications.find((n) => n.id === id);
              return {
                notifications: state.notifications.filter((n) => n.id !== id),
                unreadCount:
                  notification && !notification.read
                    ? Math.max(0, state.unreadCount - 1)
                    : state.unreadCount,
              };
            },
            false,
            'removeNotification',
          ),

        clearNotifications: () =>
          set(
            { notifications: [], unreadCount: 0 },
            false,
            'clearNotifications',
          ),

        // Breadcrumbs
        setBreadcrumbs: (breadcrumbs) =>
          set({ breadcrumbs }, false, 'setBreadcrumbs'),

        // Global loading
        setGlobalLoading: (loading) =>
          set({ globalLoading: loading }, false, 'setGlobalLoading'),

        // Command palette
        setCommandPaletteOpen: (open) =>
          set({ commandPaletteOpen: open }, false, 'setCommandPaletteOpen'),
      }),
      {
        name: 'omr-ui-storage',
        partialize: (state) => ({
          sidebarCollapsed: state.sidebarCollapsed,
          theme: state.theme,
        }),
      },
    ),
    { name: 'UIStore' },
  ),
);

// -----------------------------------------------------------------------------
// Theme initialization (call once on app load)
// -----------------------------------------------------------------------------

export function initializeTheme(): void {
  const stored = localStorage.getItem(STORAGE_KEYS.THEME) as Theme | null;
  const theme = stored ?? 'system';
  useUIStore.getState().setTheme(theme);

  // Listen for system theme changes
  if (theme === 'system') {
    window
      .matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', (e) => {
        if (useUIStore.getState().theme === 'system') {
          const root = document.documentElement;
          if (e.matches) {
            root.classList.add('dark');
          } else {
            root.classList.remove('dark');
          }
        }
      });
  }
}
