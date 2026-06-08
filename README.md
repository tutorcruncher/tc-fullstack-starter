# tc-fullstack-starter

TutorCruncher's full-stack starter template — a **FastAPI + SQLModel + Celery** backend and a
**React Router v7** frontend, distilled and curated from our production apps and conventions.

Hand this repo to a coding agent and say *"build me a project that does X"*: it works within the
relevant folder, follows that stack's `CLAUDE.md`, and wires the two together per `INTEGRATION.md`.

```
tc-fullstack-starter/
├── README.md            # you are here
├── INTEGRATION.md       # how the two halves talk (auth, CORS, API contract, SSR) — read this for full-stack work
├── CLAUDE.md            # agent entry point → points at each stack's guide
├── .github/workflows/   # path-scoped CI: backend.yml, frontend.yml, frontend-e2e.yml
├── backend/             # FastAPI · SQLModel · Celery · Postgres · Redis   (Python, uv)
└── frontend/            # React Router v7 · React 19 · Tailwind v4 · Vite   (TypeScript, npm)
```

## The two halves

| | Backend (`backend/`) | Frontend (`frontend/`) |
|---|---|---|
| Stack | FastAPI · SQLModel · Celery | React Router v7 (SSR) · React 19 · Tailwind v4 |
| Lang / tooling | Python 3.12 · uv · ruff · ty · pytest | TypeScript · npm · ESLint · Prettier · Jest · Playwright |
| Dev server | `:8000` (uvicorn) | `:5173` (vite dev) |
| Auth | JWT (internal) + per-org API keys (public `/api/v1`) | bearer token via the typed `api.ts` client |
| Tests | `pytest` — 100% coverage gate | `jest` — 80/75/70/75 gate + Playwright e2e |
| Guide | [`backend/CLAUDE.md`](backend/CLAUDE.md) | [`frontend/CLAUDE.md`](frontend/CLAUDE.md) |

## Quick start

Each folder is **self-contained** — work in it directly. Run both for a full-stack loop:

```bash
# Backend (needs local Postgres + Redis) — http://localhost:8000
cd backend && make install-dev && uv run alembic upgrade head && make run-dev

# Frontend — http://localhost:5173 (talks to the backend on :8000 by default)
cd frontend && npm ci && cp .env.example .env && npm run dev
```

See each folder's `README.md` for the full per-stack quick start, and **`INTEGRATION.md`** before
doing anything that spans both (login, calling the API, CORS, the request/response contract).

## How a project gets built here

1. Decide which half (or both) your project needs.
2. Point the agent at the folder(s); it follows the stack's `CLAUDE.md`, `STYLE_GUIDE.md`, and rules.
3. For full-stack work, the agent follows `INTEGRATION.md` to keep auth, CORS, and the API contract aligned.
4. CI is **path-scoped**: backend changes run `backend.yml`, frontend changes run `frontend.yml`.

## Using one half standalone

The folders don't depend on each other. To extract one into its own repo, copy the folder out and
re-add its workflow from `.github/workflows/` (drop it back into the new repo's `.github/workflows/`,
removing the `paths:`/`working-directory:` monorepo scoping).
