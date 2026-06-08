import { startTransition, StrictMode } from 'react';
import { hydrateRoot } from 'react-dom/client';
import { HydratedRouter } from 'react-router/dom';

// ---------------------------------------------------------------------------
// Optional error monitoring.
//
// Monitoring is NOT a default dependency. To enable Sentry, install
// `@sentry/react-router`, set `VITE_SENTRY_DSN`, and uncomment the block below
// (it self-disables when the DSN is unset). Initialise it BEFORE hydration so
// early errors are captured. See docs/CUSTOMIZATION.md for the full wiring and
// for Logfire (`VITE_LOGFIRE_TRACE_URL`).
//
//   import * as Sentry from '@sentry/react-router';
//   import { sentryDsn } from '~/helpers/env';
//
//   if (sentryDsn) {
//     Sentry.init({
//       dsn: sentryDsn,
//       // Avoid attaching PII (IPs, cookies, request bodies) by default.
//       sendDefaultPii: false,
//       integrations: [],
//     });
//   }
// ---------------------------------------------------------------------------

startTransition(() => {
  hydrateRoot(
    document,
    <StrictMode>
      <HydratedRouter />
    </StrictMode>,
  );
});
