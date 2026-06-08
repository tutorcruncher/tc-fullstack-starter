---
paths:
  - "app/**/public_api/*.py"
---

# Public API (read-only, per-org API keys)

The public API (`/api/v1`) exposes an organization's data to external/machine consumers,
authenticated by **per-organization API keys**. It is **read-only (GET only)** and
**org-scoped** — a key returns *all* of that org's data (not role-filtered like the internal
API). Code lives in each domain module's `public_api/` subpackage.

## Auth model

- Keys are a single opaque `app_live_<token>`. Only the SHA-256 hash of the full token
  (`hashed_key`, unique + indexed) and `last4` (for display) are stored on
  `OrganizationApiKey`. Auth hashes the presented token and does one O(1) indexed lookup by
  `hashed_key` — the token is high-entropy, so a fast unsalted hash is sufficient and (unlike
  argon2) can be indexed. Key helpers live in `app/auth/keys.py` (`hash_api_key`,
  `generate_api_key`, `API_KEY_PREFIX`).
- `app/auth/api_key.py::api_key_auth` is attached as a **router-level** dependency on each
  public router. It sets `request.state.organization` / `organization_id` / `api_key` and
  **never** `request.state.user`. So public queries use the org-scoped path and bypass all
  role logic.
- Billing gate: `organization_billing_active(organization_id, db)` (in `app/auth/auth.py`)
  returns True for ACTIVE / ALWAYS_FREE / unexpired-TRIAL organizations. Not-active → HTTP402.
- `last_used_dt` is updated best-effort and throttled (~5 min) by `_touch_last_used`; failures
  are swallowed so a read never 500s.
- **Per-organization rate limiting** via `public_api_rate_limit`, also a router-level
  dependency ordered **after** `api_key_auth` so it can read `request.state.organization_id`.
  See `api/rate-limiting.md`. Keyed on the org, not the key, so minting more keys (cap: 10)
  can't raise the ceiling.

## Org-scoped queries — `Model.query_for_pub_api(organization_id)`

The org-scoped public query is a **classmethod on the model itself**, sibling to
`request_query` (both declared on `AppModel` as `raise NotImplementedError`). Each returns a
`select(...)` scoped to the org by `organization_id`. **Never** use `request_query` (it is
role-scoped and reads `request.state.user`). Filter out soft-deleted users
(`deleted_dt IS NULL`), superadmins, and **demo data** (`is_demo == False`).

Detail endpoints reuse the same builder + `.where(Model.id == obj_id)` and raise **HTTP404**
(not 403) on a cross-org id. Use **function-level imports inside the classmethod** only where
needed to avoid circular imports. There is no `public_api/queries.py` module.

```python
@classmethod
def query_for_pub_api(cls, organization_id: int) -> SelectOfScalar:
    return select(cls).where(cls.organization_id == organization_id, cls.is_demo == False)  # noqa: E712
```

## Schemas — `public_api/example_resources.py`

Dedicated explicit public schemas, **always built by explicit construction** (never
`model_validate(<orm object>)`), so **no** `model_config = {'from_attributes': True}`.
**Do NOT reuse internal schemas** (`ExampleResourceBasic`/`ExampleResourceList`/`UserBasic`) —
they may carry role-conditional fields and internal identifiers. Redact: `hashed_*`, internal
ids, `is_demo`, `deleted_dt`, and any internal/onboarding flags. Add `description=` on
non-obvious fields and a view docstring — Scalar renders both. List/detail schemas follow the
`PublicXList` / `PublicXDetail` convention, with the detail subclassing the list and adding
the heavier embedded data.

## Views

- `APIRouter(prefix='/<resource>', dependencies=[Depends(api_key_auth), Depends(public_api_rate_limit)])`.
  The sub-app is mounted at `/api/v1`, so do **not** repeat `/api/v1` in the router prefix.
  Route names use the `public-` prefix (`public-example-resource-list`,
  `public-example-resource-detail`).
- List endpoints: `PaginatedResponse[...]`, two-step paginate-then-fetch, `total` via the
  count-subquery, `page_size` max 200, and an `updated_since` filter.
- `updated_since` matches `updated_dt` on mutable resources; append-only resources filter on
  `created_dt`.
- `public_api/__init__.py` imports the view modules (side effect) so their routes attach to
  the routers.

## Sub-app mounting (`app/main.py`)

The public API is a **separate `FastAPI()` instance** (`public_app`) mounted at `/api/v1`,
with its own route-name registry. `api_key_auth` is applied at the **router level** (not as a
sub-app-level dependency) so `/api/v1/openapi.json` and `/api/v1/scalar` stay **public**
(consumers read the contract before authenticating).

## Sub-app facts (avoid both bugs and over-engineering)

What **self-handles** on the mounted sub-app (no extra wiring needed):
- `HTTPException` (401/402/404/429) and 422 validation errors — Starlette installs
  `ExceptionMiddleware` per instance.
- `parent.url_path_for('public-...')` resolves mounted routes — tests use
  `client.app.url_path_for(...)`.

What does **not** propagate to a mounted sub-app (must be handled explicitly):
- Parent **middleware** (CORS) — add it to `public_app` too.
- `logfire.instrument_fastapi` — call it on `public_app` separately.
- `dependency_overrides` — in tests, override `get_db` on `public_app` (the
  `public_api_client` fixture does this); resolve routes via the parent app.

## Tests — mirror app structure

`tests/{module}/public_api/`. Use the `public_api_client` fixture (overrides `get_db` on the
sub-app) and `OrganizationApiKeyFactory` (returns `(key_row, full_key)`). Assert full response
structures, cross-tenant 404, demo exclusion, and `count_queries` identical for `page_size=1`
and `page_size=200` (proves no N+1). Public docs/openapi must return 200 with no auth header;
a data route must 401 without a key.
