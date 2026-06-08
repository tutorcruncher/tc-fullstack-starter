import { isDev, sentryDsn } from '~/helpers/env';

/**
 * Report an unexpected error to your monitoring backend. By default this is a
 * no-op in production and logs to the console in development.
 *
 * To wire up a real monitoring vendor, add it as a dependency and forward the
 * error here. For example, with Sentry (gated on `VITE_SENTRY_DSN` via
 * `sentryDsn`), once `@sentry/react-router` is installed and initialised:
 *
 *   import * as Sentry from '@sentry/react-router';
 *   if (sentryDsn) {
 *     Sentry.captureException(error);
 *   }
 *
 * `sentryDsn` is read here so the env wiring stays connected; the import is
 * intentionally not added so the starter ships with no monitoring dependency.
 */
export function reportError(error: unknown): void {
  if (isDev) {
    console.error('[monitoring] reportError:', error);
  }
  void sentryDsn;
}
