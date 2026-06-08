# tc-fullstack-starter — agent guide

This is a **full-stack monorepo template** with two independent apps. There is no shared toolchain —
work **within one folder at a time** and follow **that folder's** `CLAUDE.md`, which is the
authoritative guide for its stack:

- **[`backend/`](backend/CLAUDE.md)** — FastAPI · SQLModel · Celery. Python 3.12, `uv`, `ruff`, `ty`,
  `pytest`. Postgres + Redis. Run commands from `backend/` (`make …`, `uv run …`).
- **[`frontend/`](frontend/CLAUDE.md)** — React Router v7 (SSR) · React 19 · Tailwind v4 · Vite.
  TypeScript, `npm`, `eslint`, `prettier`, `jest`, Playwright. Run commands from `frontend/` (`npm …`).

## Rules for working here

1. **Stay in one stack.** Don't run `uv`/`pytest`/`ruff` outside `backend/`, or `npm`/`jest`/`eslint`
   outside `frontend/`. Each folder has its own lockfile, config, and CLAUDE.md.
2. **Follow the folder's CLAUDE.md and `.claude/rules/`** for all conventions (they are detailed and
   stack-specific). This root file only routes you.
3. **For anything that spans both halves** — login/auth, calling the API, CORS, the request/response
   contract (pagination shape, error format, field casing), SSR data loading — read
   **[`INTEGRATION.md`](INTEGRATION.md)** first and keep both sides consistent.
4. **CI is path-scoped** (`.github/workflows/backend.yml`, `frontend.yml`, `frontend-e2e.yml`): a change
   under `backend/**` runs backend CI, a change under `frontend/**` runs frontend CI. Keep the gates
   green for the half you touched (backend: 100% patch coverage; frontend: 80/75/70/75).

## What to customize first

- **Backend:** the example domain (`app/example_domain/` — rename `ExampleResource`), `Settings`
  (`app/core/config.py`), and the auth/roles to fit your model.
- **Frontend:** `app/types/` + `app/data/api.ts` (rename `Item`/`itemsApi`), the `@theme` tokens in
  `app/app.css`, and `APP_NAME` in `app/helpers/meta.ts`.
- **Both:** align the resource name, base URL, and auth per `INTEGRATION.md`.
