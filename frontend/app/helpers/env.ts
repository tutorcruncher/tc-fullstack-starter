/**
 * The sole place that reads `import.meta.env`. Never access `import.meta.env`
 * anywhere else — import these constants instead, so configuration has a single
 * surface and optional integrations self-disable when their var is unset.
 */

export const apiBaseUrl: string = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

/** Optional error monitoring. `undefined` when unset, which disables Sentry. */
export const sentryDsn: string | undefined = import.meta.env.VITE_SENTRY_DSN;

/** Optional distributed tracing. `undefined` when unset, which disables Logfire. */
export const logfireTraceUrl: string | undefined = import.meta.env.VITE_LOGFIRE_TRACE_URL;

/** True in `vite dev`, false in production builds. */
export const isDev: boolean = import.meta.env.DEV;
