# Architecture

How this starter boots, renders, and moves data. It is a standard **React Router v7
framework-mode** app with SSR on — this doc explains the pieces so you can reason about (and
extend) the data flow without surprises.

## The big picture

```
request ──> server (SSR)              hydration ──> client
   │           │                          │
   │   matches routes.ts                  │   entry.client.tsx
   │   runs matched loaders               │   hydrateRoot(<HydratedRouter/>)
   │   renders root Layout + Outlet        │   loaders/actions now run via fetch
   │   streams HTML                        │   to the server route handlers
```

Both the server and the client run the **same route modules**. Loaders run on the server for the
initial request (real SSR), then on the client for subsequent client-side navigations.

## SSR boot & hydration

- **`react-router.config.ts`** — `export default { ssr: true } satisfies Config`. This is the
  single switch that puts the app in SSR mode. (Flipping it to `ssr: false` turns the app into a
  client-rendered SPA — see [`CUSTOMIZATION.md`](./CUSTOMIZATION.md).)
- **`app/root.tsx`** — the required RR7 root module. It exports:
  - **`Layout({ children })`** — wraps the *entire HTML document*:
    `<html><head><Meta/><Links/></head><body>{children}<ScrollRestoration/><Scripts/></body></html>`.
    This is essential for SSR: `<Meta/>`/`<Links/>` inject per-route metadata and stylesheets,
    `<Scripts/>` ships the client bundle, `<ScrollRestoration/>` restores scroll on navigation.
  - **`App()`** (default export) — renders `<Outlet/>` wrapped in `<AppProviders>`, so every route
    sits inside the app's cross-cutting context (Toast, and whatever else you compose in).
  - **`ErrorBoundary({ error })`** — catches errors from any route. It distinguishes
    `isRouteErrorResponse(error)` (404s and thrown route responses) from generic thrown `Error`s and
    renders the `ErrorState` primitive accordingly. It reports to monitoring only if monitoring is
    configured (via `reportError` — a no-op until you wire a vendor).
  - **`links`** — the `Route.LinksFunction` that includes `app.css`.
- **`app/entry.client.tsx`** — the client hydration entry. It calls
  `startTransition(() => hydrateRoot(document, <StrictMode><HydratedRouter /></StrictMode>))`. Note
  it uses **`HydratedRouter`**, not `BrowserRouter` — it re-attaches React to the server-rendered
  DOM rather than re-rendering from scratch. A commented block shows where optional monitoring
  (e.g. `Sentry.init`, gated on `import.meta.env.VITE_SENTRY_DSN`) hooks in *before* hydration.
- **`app/entry.server.tsx`** is **not customized** in this template — RR7 provides the default
  server entry, and the `isbot` dependency lets it decide between streaming and buffered rendering
  for bots vs browsers. Add an `app/entry.server.tsx` only if you need to customize that.

## Route matching — `app/routes.ts`

Routes are declared programmatically using the `@react-router/dev/routes` DSL (`index`, `route`,
`layout`, `prefix`), not by file-system convention. This makes the route tree explicit and easy for
an agent to extend:

```ts
import { type RouteConfig, index, route, layout, prefix } from '@react-router/dev/routes';

export default [
  index('routes/home.tsx'),
  ...prefix('items', [
    index('routes/items/items.tsx'),                  // /items (list)
    route('new', 'routes/items/item-new.tsx'),        // /items/new
    layout('routes/items/item-layout.tsx', [          // loads the shared item
      route(':itemId', 'routes/items/item-detail.tsx'),       // /items/:itemId
      route(':itemId/edit', 'routes/items/item-edit.tsx'),    // /items/:itemId/edit
    ]),
  ]),
  route('*', 'routes/not-found.tsx'),                 // catch-all 404
] satisfies RouteConfig;
```

The nested `layout(...)` is the key idiom: the layout route runs a loader that fetches the shared
record once and exposes it to its children (detail, edit) via **`Outlet` context** — so the detail
and edit routes don't each re-fetch the same item.

## Generated `+types` — type-safe routes

`react-router typegen` reads `routes.ts` and generates a `+types/<route>.d.ts` file next to each
route module (under `.react-router/types`, surfaced via the `rootDirs` setting in `tsconfig.json`).
Each route imports its own generated types:

```tsx
import type { Route } from './+types/item-detail';

export async function loader({ params }: Route.LoaderArgs) { /* params.itemId is typed */ }
export function meta(_: Route.MetaArgs) { return buildMetaData('Item'); }
export default function ItemDetail({ loaderData }: Route.ComponentProps) { /* loaderData is typed */ }
```

This keeps `params`, `loaderData`, and `meta` type-safe and **breaks the build when the route tree
changes**. `npm run typecheck` runs typegen first, so always run it after editing `routes.ts`.

## Data flow — loaders, actions, and `app/data/api.ts`

All data movement goes through **one typed HTTP client**, `app/data/api.ts`. Components and routes
never call `fetch()` directly.

```
loader/action ──> itemsApi.list()/create()/… ──> apiRequest<T>(path, opts)
                                                      │
                                          base URL + JSON headers (+ optional token)
                                                      │
                                              fetch ──> response
                                                      │
                              ok? parse JSON : throw ApiError(status, message)
```

- **`apiRequest<T>(path, options?)`** — prepends `apiBaseUrl` (from `helpers/env.ts`), sets JSON
  headers (and an optional bearer token from `safeGetItem`), parses the JSON response, and on
  `!response.ok` throws **`ApiError`** with `status` and a message extracted from
  `json.detail || json.error`.
- **Resource objects** (e.g. `itemsApi`) group a resource's endpoints:
  `list(params?) / get(id) / create(payload) / update(id, payload) / remove(id)`. Returns are typed
  (`PaginatedResponse<Item>`, `Item`, `void`).
- **`PaginatedResponse<T> = { items: T[]; total: number; page: number; page_size: number }`** is the
  standard list shape (`page_size` snake_case mirrors a typical backend).

### List route (loader + URL-driven state)

The list loader reads **URL search params** (page, search, sort) — not component state — and calls
`api.list`. List state lives in the URL via `useSearchParams` + `useOrderParams`, so back/forward,
sharing, and reload all work, and the loader is the single source of truth:

```tsx
export async function loader({ request }: Route.LoaderArgs) {
  const url = new URL(request.url);
  return itemsApi.list({
    page: Number(url.searchParams.get('page') ?? 1),
    search: url.searchParams.get('search') ?? undefined,
    order_by: url.searchParams.get('order_by') ?? undefined,
  });
}
```

### Mutations (actions)

Create/edit/delete go through route **actions**. An action calls `api.create`/`api.update`/
`api.remove`, then either `redirect`s on success or **catches `ApiError` and returns field errors**
to be rendered in the form:

```tsx
export async function action({ request, params }: Route.ActionArgs) {
  const form = await request.formData();
  try {
    const item = await itemsApi.create({ name: String(form.get('name')) /* … */ });
    return redirect(`/items/${item.id}`);
  } catch (error) {
    if (error instanceof ApiError) return { error: error.message };
    throw error; // unexpected → ErrorBoundary
  }
}
```

### Error propagation

- In a **loader**, let `ApiError` bubble — RR7 routes it to the nearest `ErrorBoundary` (the root
  one renders `ErrorState`).
- In an **action**, catch `ApiError` and return it as data so the form can show an `Alert`; re-throw
  anything unexpected so it still reaches the `ErrorBoundary`.
- Success/failure user feedback (toasts) is fired client-side via `useToast` from the route
  component after the action resolves.

## Styling pipeline

`app/app.css` is the Tailwind v4 entry (`@import 'tailwindcss'`). Design tokens are declared in its
`@theme` block (there is no `tailwind.config.js`); `@layer base` styles native form controls,
`@layer components` defines reusable utility classes, `@layer utilities` holds keyframes (e.g. the
`Modal` entry animation). Tailwind compiles via the `@tailwindcss/vite` plugin (first in the Vite
plugin order). `prose.css` is an optional generic markdown stylesheet imported from `app.css`.

## Vite plugin order

`vite.config.ts` registers three plugins **in this order**:
`tailwindcss()` → `reactRouter()` → `tsconfigPaths()`. Tailwind first so styles compile; the RR7
plugin provides SSR + typegen + the route build; `vite-tsconfig-paths` makes the `~/*` alias resolve
in dev and build (mirrored by `tsconfig` paths and the jest `moduleNameMapper`).
