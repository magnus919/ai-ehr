import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import App from './App';
import { initializeTheme } from './store/uiStore';
import './index.css';

// -----------------------------------------------------------------------------
// React Query Configuration
// -----------------------------------------------------------------------------

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (
          typeof error === 'object' &&
          error !== null &&
          'status' in error &&
          typeof (error as Record<string, unknown>).status === 'number'
        ) {
          const status = (error as Record<string, number>).status;
          if (status >= 400 && status < 500) return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});

// -----------------------------------------------------------------------------
// Initialize Theme
// -----------------------------------------------------------------------------

initializeTheme();

// -----------------------------------------------------------------------------
// Mount Application
// -----------------------------------------------------------------------------

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error(
    'Root element not found. Ensure there is a <div id="root"></div> in index.html.',
  );
}

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'var(--toast-bg, #fff)',
            color: 'var(--toast-color, #1f2937)',
            border: '1px solid var(--toast-border, #e5e7eb)',
            fontSize: '0.875rem',
          },
          success: {
            iconTheme: {
              primary: '#16a34a',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#dc2626',
              secondary: '#fff',
            },
            duration: 6000,
          },
        }}
      />

      {/* React Query DevTools (only in development) */}
      <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
    </QueryClientProvider>
  </StrictMode>,
);
