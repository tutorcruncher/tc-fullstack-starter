# FastAPI SQLModel Starter

A reusable, production-shaped starter for building multi-tenant backends with
**FastAPI + SQLModel + Celery + PostgreSQL**. It ships a complete vertical slice —
authentication, a tenant (`Organization`), an example domain resource with full CRUD plus a
read-only public API, background tasks, migrations and tests — so you have a working,
convention-following pattern to copy for every layer of a new feature.

This repo is opinionated on purpose. The conventions are documented in detail and are meant
to be followed exactly; they are what keep a growing codebase consistent and reviewable.

## Built for coding agents

The fastest way to use this starter is to **hand the whole repository to a coding agent and
say: "build me a project that does X."** [`CLAUDE.md`](./CLAUDE.md) is the agent entry point —
it documents every convention (URL naming, multi-tenancy via `request_query`,
paginate-then-fetch list endpoints, the `_Base`/`Table`/`Basic` schema split, the public-API
pattern, testing rules, and `ty` type-checking). The agent should generalize the existing
patterns rather than invent new ones; the `app/example_domain/` slice is the template to copy.

Two companion docs make the agent's self-review concrete:

- [`STYLE_GUIDE.md`](./STYLE_GUIDE.md) — the consolidated code-style reference.
- [`PR_REVIEW_PATTERNS.md`](./PR_REVIEW_PATTERNS.md) — a ranked checklist of what code
  reviewers actually pick up on, mined from 900+ real PR review comments. Self-check against
  it before opening a PR.

## Stack

| Layer | Choice |
|-------|--------|
| Web framework | FastAPI (`fastapi[standard]`) |
| ORM / models | SQLModel (SQLAlchemy + Pydantic) |
| Database | PostgreSQL |
| Migrations | Alembic (config under `[tool.alembic]` in `pyproject.toml`) |
| Background tasks | Celery with a Redis broker |
| Auth | Web Bearer JWT (PyJWT) + argon2 password hashing (`pwdlib`); per-org API keys for the public API |
| Observability | Logfire + Sentry |
| Tooling | `uv`, `ruff` (lint + format), `ty` (type-check), `pytest` (+ `pytest-xdist`, `factory-boy`) |
| Python | 3.12+ |

## What's in the box

- **Multi-tenancy** — one `Organization` per `User`; every query is scoped through
  `Model.request_query(request)` (internal) or `Model.query_for_pub_api(org_id)` (public).
- **Auth** — `POST /auth/login` issues a JWT; `auth_user` validates it and sets
  `request.state.user`. Role-based `Permission` dependencies (`is_admin` / `is_member` /
  `is_superadmin`).
- **Example domain** — `ExampleResource` with child `ExampleResourceParticipant`s,
  demonstrating CRUD, list filters/ordering, the paginate-then-fetch pattern, and a Celery
  task dispatched on create.
- **Read-only public API** at `/api/v1`, authenticated by per-organization API keys, with
  its own Scalar docs at `/api/v1/scalar`, per-org rate limiting, and dedicated redacted
  schemas.
- **Tests** mirroring the app structure, using factories, full-structure assertions, role
  clients, and a `count_queries` helper that proves list endpoints have no N+1.

> **Template placeholders to change per project:** the API-key prefix (`app_live_`), the
> `logfire_service_name` default (`fastapi-sqlmodel-starter`), and the FastAPI `title`. These
> live in `app/core/config.py` / `app/auth/keys.py` / `app/main.py` and are flagged in
> `.env.example`.

## Quickstart

### 1. Prerequisites

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv)
- A running PostgreSQL and Redis (locally, or via Docker):

```bash
docker run -d --name starter-postgres -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 postgres:16
docker run -d --name starter-redis -p 6379:6379 redis:7
```

### 2. Install dependencies

```bash
make install-dev      # uv sync --dev + pre-commit install
```

### 3. Configure the environment

```bash
cp .env.example .env
```

Edit `.env` to point at your Postgres/Redis and set a real `SECRET_KEY` for non-dev runs
(the app refuses to boot in non-dev/test mode while the insecure default secret is in place).

### 4. Apply migrations

```bash
uv run alembic upgrade head
```

### 5. Run the app and the worker

```bash
make run-dev          # uvicorn app.main:app --reload   (http://localhost:8000)
make run-worker       # celery -A app.worker worker -l info
```

- Internal API docs (Scalar): `http://localhost:8000/scalar`
- Public API docs (Scalar): `http://localhost:8000/api/v1/scalar`
- Healthcheck: `GET http://localhost:8000/`

### 6. Run the checks

```bash
make test             # uv run pytest -n auto
make test-cov         # with coverage, fails under 98%
make lint             # ruff check + ruff format --check + ty check
```

## Agent workflow

1. Read [`CLAUDE.md`](./CLAUDE.md) and the relevant files under `.claude/rules/`.
2. Study the `app/example_domain/` slice — it is the canonical pattern for every layer.
3. For a new feature, add a sibling module and copy the pattern: model (`_Base`/`Table`/`Basic`)
   → schemas → `api/` router → optional `public_api/` router → `tasks.py` → tests.
4. Wire new model modules into `app/__init__.py` so `SQLModel.metadata` is complete, and
   include new routers in `app/main.py`.
5. Generate a migration (`uv run alembic revision --autogenerate -m '...'`), verify a single
   head, and apply it.
6. Run `make lint` and `make test-cov` (100% patch coverage on new code).
7. Self-check against [`PR_REVIEW_PATTERNS.md`](./PR_REVIEW_PATTERNS.md) before opening a PR.

## Deployment & the "migrations run on deploy" model

This project assumes **migrations run on deploy**: the deploy pipeline runs
`alembic upgrade head` before the new application code starts serving, so application code
can always assume the database schema is up to date.

Consequences for the code you write:

- **Do not** add fallback code for "old" database states.
- **Do not** add runtime checks for whether a column/table exists.
- If a migration adds a column with a non-null default, assume every row has that value.

The starter ships **CI only** (`.github/workflows/test.yml`) — no deploy workflows. CI runs
`alembic upgrade head` against a fresh database to prove the initial migration applies
cleanly, then runs the test suite.

> **Dual schema path (intentional):** tests build the schema with `create_test_schema`
> (`SQLModel.metadata.create_all`) for speed and isolation, while production and CI use
> Alembic. CI applying `alembic upgrade head` keeps the two paths from drifting.

## Where to go next

- [`CLAUDE.md`](./CLAUDE.md) — full conventions and the rules-reference table.
- [`STYLE_GUIDE.md`](./STYLE_GUIDE.md) — consolidated code style.
- [`PR_REVIEW_PATTERNS.md`](./PR_REVIEW_PATTERNS.md) — ranked pre-PR self-review checklist.
- `.claude/rules/` — category-grouped rules with examples (api, code-style, database, tasks,
  testing, tooling).
