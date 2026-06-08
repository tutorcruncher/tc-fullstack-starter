# Integration — how the backend and frontend talk

This is the contract between [`backend/`](backend/) (FastAPI + SQLModel) and
[`frontend/`](frontend/) (React Router v7). Read it before doing anything that spans both halves.
Most of it lines up by design (both were distilled from the same product), but a few things are
**not obvious** — they're called out below.

## Topology

```
browser ──▶ frontend (vite dev :5173, or the SSR node server in prod)
                  │
                  ├─ browser fetch ─┐
                  └─ SSR loader/action fetch ─┐
                                              ▼
                              backend  (uvicorn :8000)
                                ├─ internal API   (JWT bearer)            ← the SPA uses this
                                └─ public API /api/v1 (per-org API keys)  ← machine/external consumers
```

The frontend's API client (`frontend/app/data/api.ts`) targets `VITE_API_BASE_URL`, which defaults to
`http://localhost:8000` (the backend dev server). The backend's `allowed_origins` (in
`backend/app/core/config.py`) already includes the frontend dev origin `http://localhost:5173`.

## Two backend API surfaces — the SPA uses the **internal** one

This is the single most important non-obvious point. The backend exposes **two** authenticated APIs:

1. **Internal API** — authenticated with a **JWT bearer token** (`backend/app/auth/jwt.py::auth_user`),
   issued by `POST /auth/login`. This is role-scoped and per-user. **The frontend SPA uses this.**
2. **Public API** — mounted at **`/api/v1`**, authenticated with **per-organization API keys**
   (`app_live_…`, SHA-256-hashed), **read-only**, org-scoped. This is for *external/machine* consumers
   (partner integrations, server-to-server jobs) — **not** the browser SPA. See
   `backend/.claude/rules/api/public-api.md`.

Don't point the SPA at `/api/v1`. Use the internal endpoints with a JWT.

## Auth flow (internal API)

1. User submits credentials → frontend calls `POST /auth/login` (backend returns
   `{ "access_token": "...", "token_type": "bearer" }`).
2. Frontend stores the token (the reference `AuthProvider` uses `localStorage` via the `safe*` storage
   helpers) and `api.ts` attaches `Authorization: Bearer <token>` to every request.
3. Backend `auth_user` decodes/validates the JWT and sets `request.state.user`; protected routes use
   `Permission.*` dependencies.
4. The frontend's `authApi.checkUser()` (→ `GET /users/me`) validates the token on load; wire it by
   nesting `AuthProvider` into `AppProviders` (see `frontend/docs/CUSTOMIZATION.md`).

> The frontend ships auth **unwired** so it runs against any backend with no login. The backend's
> `/auth/login` is real. To connect them you wire the `AuthProvider` and confirm the endpoints.

### SSR caveat (important)

React Router **loaders/actions run on the server**, where `localStorage` does not exist — so a
client-only bearer token is invisible to SSR data fetching. Pick one:

- **Cookie session (recommended for SSR):** store the token in an HTTP-only cookie; the browser sends
  it automatically and the loader's `fetch` forwards it. Cleanest when you control the backend and it's
  same-site.
- **Forward the header:** read the incoming request's `Authorization`/`Cookie` in the loader and pass it
  to the backend `fetch`.
- **Client-only data:** use `clientLoader` so the authed fetch only runs in the browser (loses SSR for
  that route).

Details: `frontend/docs/CUSTOMIZATION.md` → "The SSR token-auth caveat".

## CORS

The browser enforces CORS on cross-origin requests (frontend `:5173` → backend `:8000`). Keep the
frontend's origin in the backend's `allowed_origins`:

- **Dev:** `http://localhost:5173` is already in the default `allowed_origins`.
- **Prod:** add your deployed frontend origin to `allowed_origins` (env var). If you use cookie auth,
  also send credentials (the frontend fetch needs `credentials: 'include'` and the backend CORS needs
  `allow_credentials=True` with an explicit origin, not `*`).

## The wire contract (keep both sides in sync)

| Concern | Backend | Frontend | Notes |
|---|---|---|---|
| List shape | `PaginatedResponse[T]` `{items,total,page,page_size}` | `PaginatedResponse<T>` `{items,total,page,page_size}` | **snake_case** `page_size` on the wire |
| Errors | HTTP error → `{ "detail": "…" }` | `ApiError(status, message)` reads `detail \|\| error` | one shape, typed on the client |
| Field casing | snake_case (SQLModel/Pydantic) | TS types mirror backend field names | don't camelCase across the wire |
| Base URL | `base_url` = `:8000` | `VITE_API_BASE_URL` = `:8000` | must match |

Nothing **enforces** this contract across repos — if you rename `page_size` or change the error key on
one side, update the other (and its tests). Consider generating the frontend types from the backend's
OpenAPI schema (`/openapi.json`) if you want it enforced.

## Connect-them checklist

The two halves ship with **different placeholder resources** — they don't talk out of the box until you
align them:

- [ ] **Pick one resource name.** Backend ships `ExampleResource` (`/example-resources`); frontend ships
      `Item` (`itemsApi` → `/items`). Rename both to your real entity and use the **same path**.
- [ ] **Base URL / CORS.** Set `VITE_API_BASE_URL` to the backend origin and ensure that origin is in the
      backend's `allowed_origins`.
- [ ] **Auth.** Wire the frontend `AuthProvider` (+ `authApi.checkUser` → your real "current user"
      endpoint) to the backend's `/auth/login` + JWT, and decide cookie-vs-header for SSR.
- [ ] **Match endpoints.** The frontend calls `/items`, `/users/me`; the backend exposes
      `/example-resources` and you add `/users/me`. Align the paths and payloads.
- [ ] **Shared types.** Keep the pagination/error/field-casing shapes identical (or generate FE types
      from the backend OpenAPI).

## Local full-stack dev

```bash
# terminal 1 — backend (needs Postgres + Redis running locally)
cd backend && make install-dev && uv run alembic upgrade head && make run-dev   # :8000

# terminal 2 — backend worker (only if you use Celery tasks)
cd backend && make run-worker

# terminal 3 — frontend
cd frontend && npm ci && cp .env.example .env && npm run dev                      # :5173 → :8000
```
