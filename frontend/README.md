# React Router Starter

A reusable, production-shaped starter for building web apps with **React Router v7**
(framework mode, SSR on) + **React 19** + **TypeScript** (strict) + **Tailwind CSS v4** +
**Vite**. It ships a single neutral example feature ("Items") that exercises every layer —
loaders, actions, a typed API client, the UI primitives, forms, tables, pagination, toasts,
and tests — so you can delete it and build your own resource by analogy.

This template is deliberately backend-agnostic and free of any domain vocabulary. Point it at
an HTTP API, rename the example resource, edit the design tokens, and ship.

## Stack

| Concern | Choice |
| --- | --- |
| Framework | React Router v7 (framework/SSR mode) |
| UI runtime | React 19 |
| Language | TypeScript 5.8 (strict) |
| Styling | Tailwind CSS v4 (`@theme` tokens, no `tailwind.config.js`) |
| Build / dev | Vite 6 |
| Data | RR7 route loaders + actions through one typed `app/data/api.ts` |
| Unit / component tests | Jest 30 + ts-jest + Testing Library |
| E2E tests | Playwright |
| Lint / format | ESLint 9 (flat config) + Prettier + Husky + lint-staged |
| Package manager | npm (only) |
| Node | 20 LTS (pinned in `.nvmrc`) |

## Quick start

```bash
npm ci                       # install from the committed package-lock.json
cp .env.example .env         # set VITE_API_BASE_URL (defaults to the backend on http://localhost:8000)
npm run dev                  # dev server on http://localhost:5173
```

Then verify the toolchain end to end:

```bash
npm run typecheck            # react-router typegen && tsc (strict, no errors)
npm run lint                 # eslint, --max-warnings 0
npm test                     # jest + coverage gates (80/75/70/75)
npm run build                # production build into build/
npm run start                # serve the production build
```

All of the above must pass clean on a fresh clone.

## Hand it to a coding agent: "build me X"

The point of this template is that the structure is predictable enough for a coding agent (or
a new teammate) to extend by analogy. To add a resource — say `Widgets` — tell the agent:

> "Add a `Widgets` resource following the existing `Items` feature: types in `app/types/`,
> a `widgetsApi` in `app/data/api.ts`, routes under `app/routes/widgets/`, and tests mirroring
> the `Items` tests."

The agent has everything it needs in [`CLAUDE.md`](./CLAUDE.md) (conventions + project map),
[`STYLE_GUIDE.md`](./STYLE_GUIDE.md) (code style), and [`TESTING_GUIDE.md`](./TESTING_GUIDE.md)
(test discipline). The end-to-end recipe is in [`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md):

1. Define types (`app/types/<resource>.ts`, re-export from `app/types/index.ts`).
2. Add the API resource object to `app/data/api.ts` (`list`/`get`/`create`/`update`/`remove`).
3. Register the route tree in `app/routes.ts` (list, nested layout, detail, new, edit).
4. Write the list loader (URL search params → `api.list`) + the table/pagination/search.
5. Build the shared form and the create/edit actions; fire `useToast` on success/error.
6. Add typed mocks + a component test, route/loader test, route/action test, and an e2e spec.

## Project structure

```
app/
├── components/
│   ├── ui/          # Generic primitives (Button, Input, Table, Modal, Heading, …)
│   ├── icons/       # lucide makeIcon factory + curated aliases
│   └── items/       # Example-feature components (delete when you remove Items)
├── data/            # api.ts — the single typed HTTP client
├── helpers/         # cn, env, storage, dateFormatting, meta, routes, pagination, monitoring
├── hooks/           # useClickOutside, useAsyncAction, useOrderParams
├── providers/       # AppProviders, ToastProvider, AuthProvider.example
├── routes/          # Route modules (home, not-found, items/*)
├── app.css          # Tailwind v4 entry + @theme design tokens
├── prose.css        # Optional generic markdown styling
├── root.tsx         # RR7 root: Layout, App, ErrorBoundary, links
├── entry.client.tsx # Client hydration entry
└── routes.ts        # Programmatic route manifest
tests/               # Jest tests mirroring app/ + shared render helpers + typed mocks
e2e/                 # Playwright specs + auth storage-state fixture
docs/                # ARCHITECTURE.md, CUSTOMIZATION.md
```

## Data flow

Data is loaded the idiomatic RR7 way: route **loaders** read the request (URL search params,
params) and call the typed `app/data/api.ts` client; route **actions** handle mutations.
Components never call `fetch()` directly. Failed requests throw `ApiError`, which either
bubbles to the route `ErrorBoundary` or is caught by an action and returned to the form as
field errors. See [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

> For live/polling screens where loaders are a poor fit, a component-level
> `useEffect` + `useState` fetch alternative is documented in
> [`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md).

## Deployment

The primary deployment artifact is the **Dockerfile** (multi-stage `node:20-alpine`, builds
with `npm ci` + `npm run build`, runs `npm run start`):

```bash
docker build -t my-app .
docker run -p 3000:3000 --env-file .env my-app
```

A `Procfile` (`web: npm run start`) is included as an optional convenience for PaaS hosts
that read one; the Dockerfile is the source of truth.

## Optional monitoring

Monitoring is **not** a default dependency. `app/helpers/monitoring.ts` exposes a
`reportError(error)` that no-ops (logs to the console in dev) until you wire a vendor.
`app/helpers/env.ts` already surfaces `sentryDsn` and `logfireTraceUrl` (both `undefined`
when their env vars are unset, so integrations self-disable). To enable Sentry or Logfire —
or to wire a provider-agnostic analytics interface — follow
[`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md).

## Docs index

- [`CLAUDE.md`](./CLAUDE.md) — agent entry point: stack, structure, commands, conventions.
- [`STYLE_GUIDE.md`](./STYLE_GUIDE.md) — code conventions (TS, Tailwind tokens, primitives).
- [`TESTING_GUIDE.md`](./TESTING_GUIDE.md) — testing discipline + coverage gates.
- [`NOT_CARRIED_FORWARD.md`](./NOT_CARRIED_FORWARD.md) — what was deliberately dropped and why.
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — how SSR boots and data flows.
- [`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md) — make it yours.
