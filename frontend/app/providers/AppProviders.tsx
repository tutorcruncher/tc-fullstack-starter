import { type ReactNode } from 'react';
import { ToastProvider } from './ToastProvider';

interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Composition root for cross-cutting context providers, rendered once in
 * `root.tsx` around the route `<Outlet />`. Add providers here one concern at a
 * time, outermost first.
 *
 * A ready-to-use `AuthProvider` ships in `./AuthProvider` but is intentionally
 * NOT wired here, so the template runs with no backend. To enable authentication,
 * wire its injection points (see docs/CUSTOMIZATION.md) and nest it as shown:
 *
 *   import { AuthProvider } from './AuthProvider';
 *   <AuthProvider>
 *     <ToastProvider>{children}</ToastProvider>
 *   </AuthProvider>
 */
export function AppProviders({ children }: AppProvidersProps) {
  return <ToastProvider>{children}</ToastProvider>;
}
