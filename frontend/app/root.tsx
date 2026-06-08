import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from 'react-router';

import type { Route } from './+types/root';
import stylesheet from './app.css?url';
import { ErrorState } from '~/components/ui/ErrorState';
import { isDev } from '~/helpers/env';
import { reportError } from '~/helpers/monitoring';
import { AppProviders } from '~/providers/AppProviders';

/**
 * Document-level <link>s. The compiled Tailwind stylesheet is referenced here so
 * it is injected by <Links /> in <Layout>. Add fonts, favicons, or preconnects
 * by returning more descriptors.
 */
export const links: Route.LinksFunction = () => [{ rel: 'stylesheet', href: stylesheet }];

/**
 * The root HTML shell. React Router renders the matched route tree as
 * `children`; this component supplies the surrounding document. <Meta /> and
 * <Links /> emit per-route meta/link tags; <ScrollRestoration /> and <Scripts />
 * are required for SSR + hydration. Keep this free of domain UI.
 */
export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

/**
 * Application root. Wraps the route <Outlet /> in the cross-cutting providers.
 *
 * If you need a public-vs-authenticated split (e.g. a marketing/login shell with
 * no chrome, and an app shell with a sidebar/header), branch here on the current
 * route. A ready-to-wire auth provider lives at
 * `app/providers/AuthProvider.tsx` (not wired by default); see docs/CUSTOMIZATION.md.
 *
 *   import { useLocation } from 'react-router';
 *   import { isPublicRoute } from '~/helpers/routes';
 *
 *   const { pathname } = useLocation();
 *   if (isPublicRoute(pathname)) {
 *     return (
 *       <AppProviders>
 *         <Outlet />
 *       </AppProviders>
 *     );
 *   }
 *   return (
 *     <AppProviders>
 *       <AppShell>
 *         <Outlet />
 *       </AppShell>
 *     </AppProviders>
 *   );
 */
export default function App() {
  return (
    <AppProviders>
      <Outlet />
    </AppProviders>
  );
}

/**
 * Catch-all error UI for the route tree. Distinguishes route errors (thrown
 * `Response`s — 404s, loader/action `throw new Response(...)`) from unexpected
 * thrown `Error`s. Only the latter are reported to monitoring; route errors are
 * expected control flow. The error stack is shown in development only.
 */
export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = 'Something went wrong';
  let details = 'An unexpected error occurred.';
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? 'Page not found' : `Error ${error.status}`;
    details =
      error.status === 404
        ? 'The page you were looking for could not be found.'
        : error.statusText || details;
  } else if (error instanceof Error) {
    reportError(error);
    if (isDev) {
      details = error.message;
      stack = error.stack;
    }
  }

  return (
    <main className="container-narrow py-16">
      <ErrorState message={`${message}. ${details}`} />
      {stack && (
        <pre className="mt-6 w-full overflow-x-auto rounded-md bg-neutral-100 p-4 text-small text-neutral-700">
          <code>{stack}</code>
        </pre>
      )}
    </main>
  );
}
