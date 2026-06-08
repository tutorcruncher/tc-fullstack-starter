/**
 * Config-driven route classification. Downstream apps edit these arrays to mark
 * which routes are reachable without authentication. Pure functions only — no
 * domain-specific knowledge baked in.
 */

/** Exact public pathnames (no auth required). */
export const PUBLIC_ROUTES = ['/login'] as const;

/** Pathname prefixes treated as public (and anything nested beneath them). */
export const PUBLIC_ROUTE_PREFIXES: readonly string[] = [];

/** Whether `pathname` is reachable without authentication. */
export function isPublicRoute(pathname: string): boolean {
  if (PUBLIC_ROUTES.includes(pathname as (typeof PUBLIC_ROUTES)[number])) {
    return true;
  }
  return PUBLIC_ROUTE_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}
