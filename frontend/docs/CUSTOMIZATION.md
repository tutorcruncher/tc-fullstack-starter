# Customization

Recipes for turning this starter into your app, and for the patterns that were deliberately left as
opt-in rather than baked in. The end-to-end "add a resource" flow is summarized in
[`../README.md`](../README.md) and [`../CLAUDE.md`](../CLAUDE.md); this doc covers the individual
knobs.

## Change the `~` path alias

The alias `~/*` → `app/*` is declared in **three places that must stay in sync**:

1. `tsconfig.json` — `compilerOptions.paths`: `{ "~/*": ["./app/*"] }` (and `baseUrl: "."`).
2. `vite.config.ts` — via the `vite-tsconfig-paths` plugin (reads the tsconfig, so no separate
   config — but it must be in the plugin list).
3. `jest.config.cjs` — `moduleNameMapper`: `{ "^~/(.*)$": "<rootDir>/app/$1" }`.

To rename the alias (e.g. to `@/`), edit all three. To point it at a different root, change the
target path in all three. If imports resolve in the editor but break in tests (or vice versa), one
of these three is out of sync.

## Add a provider

Cross-cutting state is composed in `app/providers/AppProviders.tsx`. Add a provider with **one
concern**, expose a `use<Name>()` hook that **throws when used outside the provider**, and nest it:

```tsx
// app/providers/AppProviders.tsx
export function AppProviders({ children }: { children: ReactNode }): JSX.Element {
  return (
    <ToastProvider>
      <ThemeProvider>{children}</ThemeProvider>
    </ToastProvider>
  );
}
```

Inside the provider, memoize the context value (`useMemo`) and any exposed handlers (`useCallback`)
so consumers don't re-render needlessly. Put the provider file in `app/providers/`.

### Wiring the AuthProvider

`app/providers/AuthProvider.tsx` ships ready to use but is intentionally **not wired** into
`AppProviders`, and the example "Items" API is called **without** auth, so the template runs against
any backend with no login. To enable auth:

1. Point `authApi.checkUser()` in `app/data/api.ts` at your real "current user" endpoint (it defaults
   to `GET /users/me`).
2. Nest `<AuthProvider>` inside `AppProviders` (outermost), as shown in `AppProviders.tsx`.
3. Add real login (a `/login` route + an action that stores the token) and confirm `/login` is in
   `PUBLIC_ROUTES` in `app/helpers/routes.ts`.

### The SSR token-auth caveat

The example reads a bearer token from `localStorage` (via `safeGetItem`). **`localStorage` does not
exist on the server**, so an SSR loader can't read it — a token-in-localStorage scheme only
authenticates client-side navigations, not the initial server render.

For **authenticated SSR loaders** you have two options:

- **Cookie-based sessions (recommended for SSR).** Store the session in an HTTP-only cookie. The
  loader receives the `request`, so it can read `request.headers.get('Cookie')` and forward it to
  your backend — the server render is authenticated. This is the cleanest path when you control the
  backend and it's same-site.
- **Forward the Authorization header.** If you keep a token-based scheme across domains, have the
  loader read the inbound `Authorization`/`Cookie` header off `request` and pass it through to
  `apiRequest` (extend `apiRequest` to accept request headers). Client-only token reads via
  `safeGetItem` still work for client navigations; the server path must use the forwarded header.

Either way: **never assume `localStorage` in a loader.** If you can't move to cookies, gate the
authenticated screens behind client-side fetch (see below) or accept that their first paint is
client-rendered.

## Edit the `@theme` design tokens

All design tokens live in the `@theme` block of `app/app.css` — there is **no `tailwind.config.js`**.
To reskin, edit that one block:

```css
@theme {
  --color-primary-500: oklch(0.62 0.19 250);
  --color-neutral-100: oklch(0.97 0 0);
  --text-h1: 2rem;
  --text-body: 1rem;
  --spacing-gutter: 1.5rem;
}
```

Tokens become utilities automatically (`bg-primary-500`, `text-h1`, `p-gutter`) and CSS variables
(`var(--color-primary-500)`). Add the **z-layer scale** here too (e.g. `--z-modal`, `--z-toast`)
rather than scattering magic `z-index` numbers through components. Change `APP_NAME` in
`app/helpers/meta.ts` (currently `'RR Starter'`) so page titles read correctly. Tweak `prose.css`
if you render markdown.

## Disable SSR (SPA mode)

Flip the one switch in `react-router.config.ts`:

```ts
export default { ssr: false } satisfies Config; // was: ssr: true
```

In SPA mode there is no server render: loaders/actions still work but run on the client, and the
token-in-localStorage auth scheme works without the SSR caveat above. Build output becomes a static
client bundle. Adjust your deploy (the Dockerfile's `npm run start` SSR server is no longer needed —
serve the static `build/client` instead).

## Add environment variables

`app/helpers/env.ts` is the **sole** place that reads `import.meta.env`. To add a variable:

1. Add it to `.env.example` with a sensible default/placeholder, prefixed `VITE_` (Vite only exposes
   `VITE_`-prefixed vars to client code).
2. Read it in `env.ts` and export a typed constant:
   ```ts
   export const featureFlagX = import.meta.env.VITE_FEATURE_X === 'true';
   ```
3. Import the constant everywhere else — never touch `import.meta.env` outside `env.ts`.

Optional integrations should resolve to `undefined`/`false` when unset so they self-disable with no
config (the existing `sentryDsn` / `logfireTraceUrl` follow this).

## Wire optional monitoring (Sentry / Logfire)

Monitoring is **not** a default dependency. The template ships `app/helpers/monitoring.ts` exposing
`reportError(error)` that no-ops (logs to the console in dev). To enable a vendor:

### Sentry

1. `npm install @sentry/react-router`.
2. Set `VITE_SENTRY_DSN` in your env (already surfaced as `sentryDsn` in `env.ts`).
3. Uncomment the gated init block in `app/entry.client.tsx`:
   ```ts
   if (sentryDsn) {
     Sentry.init({ dsn: sentryDsn, sendDefaultPii: false /* avoid attaching PII */ });
   }
   ```
4. Route `reportError` through `Sentry.captureException` inside `app/helpers/monitoring.ts`. The
   root `ErrorBoundary` already calls `reportError`, so caught route errors flow to Sentry once wired.

### Logfire (OpenTelemetry browser tracing)

1. `npm install @pydantic/logfire-browser @opentelemetry/auto-instrumentations-web`.
2. Set `VITE_LOGFIRE_TRACE_URL` (surfaced as `logfireTraceUrl` in `env.ts`).
3. Initialize it in the same gated block in `entry.client.tsx`, only when `logfireTraceUrl` is set.

Keep both **env-gated** so a clone with no monitoring env vars runs untouched.

## Add a provider-agnostic analytics interface

Rather than coupling to a specific analytics vendor, define a thin interface and inject an
implementation. This keeps swaps cheap and makes a "no-op in dev / no-consent" mode trivial:

```ts
// app/helpers/analytics.ts
export interface Analytics {
  track(event: string, props?: Record<string, unknown>): void;
  pageView(path: string): void;
}

const noop: Analytics = { track: () => {}, pageView: () => {} };

export const analytics: Analytics = noop; // swap for a real impl (Amplitude, Segment, GA, …) here
```

### Privacy / consent gating

If you render sensitive screens (or handle data that shouldn't be captured by session replay /
analytics), gate analytics behind a route/consent check rather than firing it globally: classify
sensitive routes (extend `app/helpers/routes.ts` with a predicate), and have the analytics impl
pause replay / skip `track` on those routes. This replaces the source app's hardcoded
route-privacy gating with a small, explicit, app-owned rule.

## Component-level fetch (the live/polling alternative)

Loaders/actions are the **default** because they give SSR data, revalidation, and progressive
enhancement. But for **live or polling screens** (dashboards that re-fetch on an interval, screens
driven by websockets/SSE) a loader is a poor fit — you don't want a full route revalidation on every
tick. For those, use a component-level `useEffect` + `useState` fetch **through the same `api.ts`
client** (still never a bare `fetch()`):

```tsx
export default function LiveDashboard(): JSX.Element {
  const [data, setData] = useState<Item[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function poll(): Promise<void> {
      try {
        const r = await itemsApi.list();
        if (!cancelled) setData(r.items);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Failed to load');
      }
    }
    void poll();
    const id = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (error) return <ErrorState message={error} />;
  return <ItemsTable items={data} />;
}
```

Use this **only** for genuinely live data; everything else loads via a route loader.

## Optional UI add-ons

These were intentionally left out of `package.json` (see
[`../NOT_CARRIED_FORWARD.md`](../NOT_CARRIED_FORWARD.md)). Add them only when a feature needs them:

- **`framer-motion`** — richer enter/exit transitions. The `Modal` already animates via CSS
  keyframes (in `app.css` `@layer utilities`); install framer-motion only if you want shared,
  spring-style motion presets, and define them once rather than inline-per-component.
- **`react-datepicker`** — a full date-picker UI. The starter uses the native `Date` API / native
  inputs; reach for this when you need range selection / locale-heavy pickers.
- **`markdown-to-jsx`** — render markdown to React. Pair it with `prose.css` (which already styles
  the output) when you display user-authored rich text.
