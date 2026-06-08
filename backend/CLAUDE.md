# FastAPI SQLModel Starter — Development Guide for AI Agents

## This is a starter template

Hand this repository to a coding agent and say **"build me a project that does X"**. The
agent should treat every convention in this file (and in `.claude/rules/`) as binding and
follow it exactly. The repo ships a small but complete vertical slice — auth, a tenant
(`Organization`), an `example_domain` resource with CRUD + a read-only public API, Celery
tasks, migrations and tests — so a new feature has a working pattern to copy for every
layer. **Generalize the existing patterns; do not invent new ones.**

This is a FastAPI backend that manages organizations (tenants), users, and example
resources. The codebase follows strict conventions for URL generation, testing patterns,
multi-tenancy, and code quality to ensure maintainability and consistency.

## Table of Contents

1. [Critical URL Rules](#critical-url-rules)
2. [Test Development Rules](#test-development-rules)
3. [Code Style Guidelines](#code-style-guidelines)
4. [Permission System](#permission-system)
5. [Database Patterns](#database-patterns)
6. [API Response Patterns](#api-response-patterns)
7. [Development Workflow](#development-workflow)
8. [Common Commands](#common-commands)
9. [Type Checking with ty](#type-checking-with-ty)

---

## Critical URL Rules

### 1. URL Reference Rules

**ALWAYS use `url_path_for` for URL references within the system.**

When referencing URLs within the system, always use FastAPI's `url_path_for` function
instead of hardcoding URL paths. This ensures consistency, maintainability, and prevents
broken links when routes change.

#### Implementation

```python
from fastapi import APIRouter
from starlette.requests import Request

router = APIRouter()

@router.get('/some-route', name='some-route')
def some_route(request: Request):
    other_url = request.url_for('other-route-name')
    return {'redirect_url': other_url}
```

#### Route Naming Convention

When defining routes, use descriptive kebab-case names:

```python
@router.get('/example-resources/{example_resource_id}', name='example-resource-detail')
@router.post('/example-resources', name='create-example-resource')
@router.put('/example-resources/{example_resource_id}', name='update-example-resource')
```

#### Benefits

1. **Type Safety**: FastAPI catches missing route names at startup
2. **Maintainability**: Route changes only need to be updated in one place
3. **Consistency**: All URLs follow the same pattern
4. **Documentation**: Route names serve as self-documenting code

---

## Test Development Rules

### 1. Test URL Generation Rules

**ALWAYS use `client.app.url_path_for()` in tests instead of hardcoded URLs.**

#### ✅ Good - Using url_path_for in tests
```python
def test_get_example_resource(auth_client, db, example_resource):
    r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', example_resource_id=example_resource.id))
    assert r.status_code == 200
```

#### ❌ Bad - Hardcoded URLs in tests
```python
def test_get_example_resource(auth_client, db, example_resource):
    r = auth_client.get(f'/example-resources/{example_resource.id}')  # Breaks if the route changes
    assert r.status_code == 200
```

### 2. Test Data Creation Rules

**Always use `db.create()` instead of `add`, `commit`, and `refresh` in tests.**

#### ✅ Good - Using db.create()

```python
def test_create_user(db):
    user = db.create(User(
        first_name='Alice',
        last_name='Smith',
        email='alice.smith@example.com',
        role=UserRole.MEMBER,
        organization_id=organization.id,
        hashed_password=get_password_hash('password123'),
    ))
    assert user.id is not None
    assert user.id > 0
```

#### ❌ Bad - Using add, commit, refresh separately

```python
def test_create_user(db):
    user = User(first_name='Alice', last_name='Smith', email='alice.smith@example.com')
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.id is not None
```

### 3. Test Data Structure Rules

**Always check the entire data structure in test responses, not just individual keys.**

#### ✅ Good - Checking entire structure
```python
def test_get_example_resource(auth_client, db, example_resource):
    r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', example_resource_id=example_resource.id))
    assert r.status_code == 200
    assert r.json() == {
        'id': example_resource.id,
        'name': 'Example',
        'description': None,
        'status': 'draft',
        'organization_id': example_resource.organization_id,
        'created_dt': r.json()['created_dt'],
        'updated_dt': None,
        'participants': [],
    }
```

#### ❌ Bad - Checking only individual keys
```python
def test_get_example_resource(auth_client, db, example_resource):
    r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', example_resource_id=example_resource.id))
    data = r.json()
    assert data['name'] == 'Example'  # Only checks one field; misses the rest of the contract
```

### 4. Test Factory Rules

**Always use FactoryBoy factories when creating test data instead of manual object creation.**

```python
def test_create_resource_with_participants(db):
    organization = OrganizationFactory.create_with_db(db, name='Acme')
    resource = ExampleResourceFactory.create_with_db(db, name='Onboarding', organization_id=organization.id)
    ExampleResourceParticipantFactory.create_with_db(db, example_resource_id=resource.id, name='Alice')

    assert resource.id is not None
    assert len(resource.participants) == 1
```

### 5. Test Object Creation Rules

**Never create objects with explicit IDs in tests. Let the ORM handle ID assignment.**
The test DB is truncated with `RESTART IDENTITY` between tests, so hardcoded ids break
under xdist randomization.

### 6. Test Coverage Requirements

**Maintain test coverage above 98% for the entire application, 100% patch coverage on new code.**

**Always run pytest with `-n auto`** (pytest-xdist) — single file, single test, coverage, everything.

```bash
uv run pytest -n auto
uv run pytest -n auto --cov=app --cov-report=term-missing
```

Coverage targets:
- **Overall**: minimum 98%
- **Critical paths**: 100% for authentication, authorization, and data validation
- **API endpoints**: 100% for all endpoints
- **Patch coverage**: 100% — every new branch (including error/except paths) needs a test
  that executes it. If a branch can't be reached through normal setup, mock the specific
  call to force it.

### 7. Test Code Style Rules

- **No comments in tests except docstrings** at the top of functions.
- **No inline comments unless genuinely complex.**
- **Max line length 120 characters.** Do not break lines shorter than 120 unnecessarily.
- **Name response variables `r`**, not `response`.
- **Inline expected values directly** in assertions — no intermediate `expected = {...}` variable.
- **Use `auth_client` by default**; use `admin_client` / `member_client` only when testing
  permission restrictions.
- **Use `@patch` as a decorator**, not an inline `with patch()` block.
- **Don't check key existence before asserting its value** — a `KeyError` gives the same signal.

#### ✅ Correct - Clean test with only a docstring
```python
def test_create_user_with_valid_data_returns_201(auth_client, db):
    """Test that creating a user with valid data returns 201."""
    r = auth_client.post(auth_client.app.url_path_for('create-user'), json={'first_name': 'John', 'last_name': 'Doe'})
    assert r.status_code == 201
    assert r.json()['email'] == 'john.doe@example.com'
```

---

## Code Style Guidelines

See `STYLE_GUIDE.md` for the full reference. Highlights:

- Use type hints throughout. Prefer `X | None` over `Optional[X]`.
- Single quotes, 120-column lines.
- Module-level imports only (see [Import Rules](#import-rules)).
- Docstrings for intent; comments only for genuinely complex code.
- Prefer multi-line `if/else` over ternary operators.
- Extract magic numbers/strings into `ALL_CAPS` module constants.
- Use the `_Base` / `Table` / `Basic` schema split (see below) so secrets never leak.

### Deployment Model — migrations run on deploy

This project uses a "migrations run on deploy" model:

- Database migrations are applied automatically during deployment.
- Application code can assume the database schema is up-to-date.
- Do **NOT** add fallback code to handle "old" database states.
- Do **NOT** add runtime checks for schema existence (e.g., "if column exists").

If a migration adds a new column with a non-null default, the application code should
assume all rows have that value after deployment.

### Schema split — `_Base` / `Table` / `Basic`

Define each model as a non-table `_Model(AppModel)` base carrying the shared columns, a
`Model(_Model, table=True)` table class that adds `id`, secrets, and relationships, and a
public `ModelBasic(_Model)` that adds `id` but omits secrets. Set `response_model=ModelBasic`
on endpoints and return the ORM row directly — FastAPI serializes to the declared schema, so
secret fields (`hashed_password`, `hashed_key`) that live only on the table class can never leak.

### Conditional Expressions

**Prefer multi-line if/else statements over ternary operators.**

```python
if auto_now:
    onupdate = lambda: datetime.now(tz=timezone.utc)
else:
    onupdate = None
```

### Import Rules

**Never use imports inside functions. All imports must be at the module level.** The only
acceptable exception is a `TYPE_CHECKING` block or a local import strictly required to break
a circular import (the same pattern used inside `User.request_query`).

**Never add `from __future__ import annotations`.** Python 3.12 supports PEP 604 unions and
PEP 585 generics natively, and deferred annotations break SQLModel/SQLAlchemy mappers,
FastAPI dependency resolution, and pydantic introspection.

### Documentation Rules

**Use docstrings for function and class documentation. Only use comments for complex code
that requires explanation.** Document non-obvious model fields with `description=`.

---

## Permission System

### Overview

The application uses a role-based permission system defined in `app/auth/permissions.py`.
Permissions are applied as **FastAPI dependencies on individual routes** (or at the router
level), not inside handler bodies. Router-level dependencies use `auth_user` for
authentication only.

Roles are intentionally minimal: `UserRole.ADMIN` and `UserRole.MEMBER`, plus an
`is_superadmin` flag that bypasses all role checks. Add your own roles by extending
`UserRole` and `Permission`.

### Usage

```python
from fastapi import Depends
from app.auth.permissions import Permission

# Single role check on a route
@router.get('/admin-data', dependencies=[Depends(Permission.is_admin)])
def admin_data(): ...

# Combined roles with | (OR)
@router.post('/thing', dependencies=[Depends(Permission.is_admin | Permission.is_member)])
def create_thing(): ...

# Any authenticated user (applied at router level in main.py)
app.include_router(my_router, dependencies=[Depends(auth_user)])
```

### Available Permissions

| Permission | Grants access to |
|---|---|
| `Permission.is_admin` | Admins and superadmins |
| `Permission.is_member` | Any authenticated user (members or admins) and superadmins |
| `Permission.is_superadmin` | Superadmins only |
| `Permission.everyone` | Any authenticated user |
| `Permission.anonymous` | Unauthenticated/public routes (no-op marker) |

### Key Rules

1. **Router-level**: Use `Depends(auth_user)` for authentication only.
2. **Route-level**: Use `Depends(Permission.is_admin)` etc. for authorization.
3. **Combine with `|`**: `Permission.is_admin | Permission.is_member` for OR logic.
4. **Combine with `&`**: `Permission.is_admin & Permission.is_superadmin` for AND logic.
5. **Superadmin bypass**: All role permissions (except `Permission.everyone`) automatically grant superadmin access.
6. **Error response**: Returns 403 with a message like `"Admin access required"`.
7. **Cross-tenant access returns 404, not 403** — don't leak the existence of another tenant's resource.

### Where NOT to use Permission dependencies

- **Data-level filtering** — that belongs in `request_query`, not a route dependency.
- **Business-logic checks** (e.g., whether a resource is in a given state) — these are data
  validation, not role checks.

### Public API (separate auth path)

The read-only public API (`/api/v1`) does **not** use `auth_user`/`Permission` — it
authenticates with per-org API keys via `app/auth/api_key.py::api_key_auth` (router-level),
which sets `request.state.organization_id` (never `request.state.user`). See
[Public API summary](#public-api-summary) below and `.claude/rules/api/public-api.md`.

### Auth model — web JWT only

`auth_user` validates a web Bearer JWT carrying `{id, email, role, exp}` and sets
`request.state.user`. There is intentionally **no** PKCE/mobile flow, refresh tokens, or
token revocation in the starter — keeping the auth surface minimal. **Extension points**
(documented, not implemented): PKCE/mobile login, refresh-token rotation, and multi-org
membership (the starter is one-organization-per-user; multi-org would replace
`User.organization_id` with a membership table and scope `request_query` by the set of the
user's organizations).

---

## Database Patterns

### Session Management

Always use dependency injection for database sessions in endpoints, and the
`get_session()` context manager in Celery tasks:

```python
from fastapi import Depends
from app.core.database import DBSession, get_db, get_session

@router.get('/example-resources')
def list_resources(db: DBSession = Depends(get_db)):
    return db.exec(ExampleResource.request_query(request)).all()

@celery_app.task(name='example_domain.tasks.process_example_resource')
def process_example_resource(example_resource_id: int) -> None:
    with get_session() as db:
        ...
```

### DBSession Utility Methods

- `db.create(instance)` — add, commit, and refresh in one call.
- `db.exists(Model, **kwargs)` — boolean existence check.
- `db.get_or_404(Model, id=...)` — fetch or raise `HTTP404`.
- `db.get_or_create(Model, defaults=None, **kwargs)` — returns `(instance, created)`.
- `db.create_or_update(Model, defaults=None, **kwargs)` — returns `(instance, created)`; it
  **already commits**, so don't double-commit per iteration in a loop.

### Authorization-scoped queries

**Every internal list/detail query goes through `Model.request_query(request, db)`; every
public-API query goes through `Model.query_for_pub_api(organization_id)`.** Never replicate
org/role filters inline — `request_query` bakes in tenant-scoping and role logic, so
duplicating it risks permission/tenant leaks and drifts from the central policy.

```python
class ExampleResource(_ExampleResource, table=True):
    @classmethod
    def request_query(cls, request, db=None):
        if request.state.user.is_superadmin:
            return select(cls)
        return select(cls).where(cls.organization_id == request.state.user.organization_id)
```

### Pagination Optimization Pattern (paginate-first)

**ALWAYS use `PaginatedResponse` for list endpoints and fetch expensive related data ONLY
for items on the current page.** This two-step approach keeps per-page latency constant
regardless of total dataset size:

1. **Get the paginated subset**: query only the basic items for the current page (`LIMIT`/`OFFSET`).
2. **Fetch related data**: run expensive joins/aggregations **only** for those page items
   (`WHERE id IN (page_ids)`).

```python
from sqlalchemy import func
from sqlmodel import select
from app.common.api.paginate import PaginatedResponse
from app.core.config import settings

@router.get('', response_model=PaginatedResponse[ExampleResourceList], name='example-resource-list')
def list_resources(request: Request, db: DBSession = Depends(get_db), page: int = 1):
    """List the current user's example resources with a participant count."""
    base_query = ExampleResource.request_query(request).order_by(ExampleResource.name)
    page_objs = db.exec(base_query.limit(settings.dft_page_size).offset((page - 1) * settings.dft_page_size)).all()

    if page_objs:
        obj_ids = [obj.id for obj in page_objs]
        counts = dict(
            db.exec(
                select(ExampleResourceParticipant.example_resource_id, func.count())
                .where(ExampleResourceParticipant.example_resource_id.in_(obj_ids))
                .group_by(ExampleResourceParticipant.example_resource_id)
            )
        )
        items = [ExampleResourceList(**obj.model_dump(), participant_count=counts.get(obj.id, 0)) for obj in page_objs]
    else:
        items = []

    total = db.exec(select(func.count()).select_from(base_query.subquery())).one()
    return PaginatedResponse[ExampleResourceList](items=items, total=total, page=page, page_size=settings.dft_page_size)
```

#### Key principles

1. **Paginate first** — get the page subset before doing anything expensive.
2. **Scope expensive queries** — `WHERE id IN (...)` to limit joins/aggregations to page items.
3. **Use lookup dicts** — build dictionaries from aggregations for O(1) lookup.
4. **Handle empty pages** — guard the second query with `if page_objs:`.
5. **Preserve eager-loading** — if you rebuild a query via `.subquery()` or a fresh
   `select()`, re-apply `selectinload(...)`; otherwise relationship access in the response
   loop is an N+1.
6. **Add a `count_queries` test** asserting an identical query count at `page_size=1` and
   `page_size=200` — that is the enforced proof there is no N+1.

---

## API Response Patterns

### Declare `response_model` and return the ORM row

Set `response_model=` on every endpoint and return the SQLModel row directly. The `Basic`
schema (no secrets) controls serialization, removing hand-mapping boilerplate and preventing
accidental field exposure.

### Pagination response shape

List endpoints return `PaginatedResponse[T]` with `items`, `total`, `page`, `page_size`.
`page` is `Query(1, ge=1)` and `page_size` is capped (`le=200`).

### Error handling

Use the custom HTTP error classes from `app.common.api.errors` — never raise
`HTTPException` directly:

```python
from app.common.api.errors import HTTP404

resource = db.get_or_404(ExampleResource, id=resource_id)
```

Available: `HTTP400`, `HTTP401`, `HTTP402`, `HTTP403`, `HTTP404`, `HTTP409`, `HTTP422`,
`HTTP429`, `HTTP500`.

When logging an external API response body, always truncate to prevent log bloat:

```python
logger.error('API call failed: %s %s', r.status_code, r.text[:1000])
```

Public/health endpoints must **not** leak internal details (raw exceptions, hostnames,
connection strings) in error responses. Log the detail; return a generic message.

---

## Public API summary

The read-only public API (`/api/v1`) exposes an organization's data to external/machine
consumers, authenticated by **per-organization API keys** (`app_live_<token>`). It is
**read-only (GET only)** and **org-scoped** — a key returns all of that org's non-demo data,
not role-filtered. Code lives in each domain module's `public_api/` subpackage.

- **Auth**: `app/auth/api_key.py::api_key_auth` is a router-level dependency that hashes the
  presented token (SHA-256), does one indexed lookup by `hashed_key`, gates on
  `organization_billing_active`, and sets `request.state.organization` / `organization_id` /
  `api_key` — **never** `request.state.user`. Bad key → HTTP401; inactive billing → HTTP402.
- **Rate limiting**: `public_api_rate_limit` (router-level, after `api_key_auth`) is a
  fixed-window Redis counter keyed on the **org** (not the key), so minting more keys can't
  raise the ceiling. Over-limit → HTTP429.
- **Queries**: use `Model.query_for_pub_api(request.state.organization_id)` — never
  `request_query`. It excludes demo and soft-deleted rows. Detail endpoints reuse the
  builder + `.where(Model.id == obj_id)` and raise **HTTP404** (not 403) for a cross-org id.
- **Schemas**: dedicated `PublicXList` / `PublicXDetail` schemas, **built by explicit
  construction** (no `from_attributes`, never `model_validate(orm_obj)`). Redact internal ids,
  `hashed_*`, `is_demo`, and soft-delete flags.
- **Mounting**: a separate `FastAPI()` instance (`public_app`) mounted at `/api/v1` with its
  own CORS + logfire instrumentation. `/api/v1/openapi.json` and `/api/v1/scalar` stay public
  (auth is router-level) so consumers can read the contract before authenticating.

See `.claude/rules/api/public-api.md` for the full reference.

---

## Development Workflow

1. **Before making changes**: read existing code to understand patterns. The
   `example_domain` slice is the canonical reference.
2. **When adding a feature**: copy the existing pattern for each layer (model → schema →
   api → public_api → task → tests). Don't introduce new patterns.
3. **After making changes**: run `make lint` (ruff check + format-check + ty).
4. **Before committing**: ensure all tests pass and patch coverage is 100%.
5. **Before opening a PR**: self-check against `PR_REVIEW_PATTERNS.md`.

### Python dependencies

**Pin every new or updated dependency** in `pyproject.toml` with an exact version
(`package==x.y.z`), including dev groups. Run `uv lock` after changes so `uv.lock` matches.

### Migrations

Generate and apply migrations with the standard alembic commands (config lives under
`[tool.alembic]` in `pyproject.toml`). **Never combine multiple migrations on one PR.** When
merging `main` into a feature branch, delete any blank merge migration and re-chain the
feature migration's `down_revision` onto main's head — do **not** run `alembic merge heads`.
After touching migrations, verify there is exactly one head (`alembic heads`).

New feature flags / org settings should default to `False` (opt-in), never
`server_default=true` (opt-out), so a deploy doesn't silently enable a feature for all tenants.

---

## Common Commands

### Running Tests

**Always use `-n auto`** (pytest-xdist).

```bash
uv run pytest -n auto
uv run pytest -n auto --cov=app --cov-report=term-missing --cov-fail-under=98
uv run pytest -n auto tests/example_domain/test_example_resources.py
uv run pytest -n auto -k 'example_resource'
```

**Never use `--tb` arguments** — always run with full tracebacks so you can see real issues.

### Linting and Type Checking

```bash
make lint          # ruff check + ruff format --check + ty check
make format        # ruff check --fix + ruff format
make type-check    # ty check .
```

### Database Migrations

```bash
uv run alembic revision --autogenerate -m 'description'
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic heads
```

### Running the App

```bash
make run-dev       # uvicorn app.main:app --reload
make run-worker    # celery -A app.worker worker -l info
```

---

## Type Checking with ty

[ty](https://github.com/astral-sh/ty) is Astral's fast type checker. All code must pass
`make type-check` before merging.

Always use **ty's native ignore syntax with specific rule codes**:
`# ty: ignore[invalid-argument-type]`, not `# type: ignore` or mypy-style codes (`arg-type`,
`attr-defined`) — ty does not recognise those and they silence nothing.

### Common ignore patterns

SQLModel/SQLAlchemy stubs don't fully type relationships and column operations:

```python
selectinload(ExampleResource.participants)          # ty: ignore[invalid-argument-type]
ExampleResource.id.desc()                            # ty: ignore[unresolved-attribute]
ExampleResource.id.in_(obj_ids)                      # ty: ignore[unresolved-attribute]
ExampleResource.name.ilike(pattern)                  # ty: ignore[unresolved-attribute]
```

Type-narrow DB ids — they are `int | None` in the stubs but `int` after a fetch:

```python
assert resource.id is not None  # a row fetched from the DB always has an id
```

FastAPI parameter patterns:

```python
page: int = Query(1, ge=1, description='Page number')         # ty: ignore[invalid-parameter-default]
organization_id: FKFilterField(Organization) = Field(None)   # ty: ignore[invalid-type-form]
```

Type checking runs in CI (`make type-check` in `.github/workflows/test.yml`). All PRs must pass.

---

## Rules Reference

Detailed coding rules with examples live in `.claude/rules/`:

| Category | Files | Key Rules |
|----------|-------|-----------|
| **API** | `api/error-handling.md`, `api/responses.md`, `api/public-api.md`, `api/rate-limiting.md` | Custom HTTP errors, `url_path_for`, response patterns, log truncation, read-only public API (per-org keys, `/api/v1` sub-app), per-org rate limiting |
| **Code Style** | `code-style/documentation.md`, `code-style/imports.md` | Docstrings over comments, module-level imports only, no `__future__` annotations |
| **Database** | `database/session.md`, `database/security.md`, `database/pagination.md`, `database/filters.md` | `db.create()`, `escape_like()`, `request_query`, paginate-first pattern, list filters |
| **Tasks** | `tasks/celery.md` | Task definition, `get_session()` vs `get_db()`, per-org dispatch |
| **Testing** | `testing/url-generation.md`, `testing/data-creation.md`, `testing/assertions.md`, `testing/client-usage.md`, `testing/style.md` | `url_path_for` in tests, factories, full-structure assertions, `auth_client` default, 98% coverage |
| **Tooling** | `tooling/typing.md` | ty native ignore codes, type-narrowing asserts |

Top-level docs: `STYLE_GUIDE.md` (consolidated code style) and `PR_REVIEW_PATTERNS.md`
(the ranked "what reviewers actually pick up on" checklist — self-check against it before
opening a PR).

---

## Project Structure

```
fastapi-sqlmodel-starter/
├── app/
│   ├── auth/                 # Authentication & authorization
│   │   ├── api/login.py      # POST /auth/login (anon_router)
│   │   ├── models.py         # User, UserRole, UserBasic
│   │   ├── permissions.py    # Permission / PermissionCheck
│   │   ├── jwt.py            # auth_user, TokenData, CustomHTTPBearer
│   │   ├── login.py          # password hashing, authenticate_user, tokens
│   │   ├── keys.py           # API key generate/hash helpers
│   │   ├── api_key.py        # api_key_auth (public API dependency)
│   │   └── auth.py           # organization_billing_active
│   ├── common/               # Shared utilities
│   │   ├── models.py         # AppModel base (request_query / query_for_pub_api)
│   │   ├── fields.py         # UTCDatetimeField, EnumField, FKField
│   │   ├── utils.py          # escape_like, inclusive_end_of_day, sanitize_for_postgres
│   │   └── api/              # errors, paginate, filters, rate_limit
│   ├── core/                 # Config, database, Celery, Redis, logging, Sentry
│   ├── organization/         # Tenant model + API keys API
│   ├── example_domain/       # Reference vertical slice (model, api, public_api, tasks)
│   ├── main.py               # FastAPI app + mounted /api/v1 public_app
│   └── worker.py             # Celery worker entry point
├── migrations/               # Alembic env, client CLI, versions/
├── tests/                    # Mirrors the app structure (+ conftest, base_factory)
├── .claude/rules/            # Detailed, category-grouped coding rules
├── pyproject.toml            # Dependencies + [tool.alembic] + tool config
├── CLAUDE.md                 # This file
├── STYLE_GUIDE.md            # Consolidated code style
├── PR_REVIEW_PATTERNS.md     # Ranked review checklist
└── README.md
```

---

## Important Notes for AI Agents

1. **Always verify route names exist** before using `url_path_for`.
2. **Check test fixtures** in `tests/conftest.py` before writing tests.
3. **Run tests after changes** to ensure nothing breaks.
4. **Use type hints** everywhere.
5. **Follow existing patterns** — the `example_domain` slice is the template for new features.
6. **Never create files unless necessary**; prefer editing an existing file.
7. **Never proactively create documentation files** unless explicitly requested.
8. **Keep module `CLAUDE.md`/rules in sync** with code when you make significant changes.

This guide ensures consistency, maintainability, and quality. Always reference it and the
`.claude/rules/` files when working on this project.
