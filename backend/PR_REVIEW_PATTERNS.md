# PR Review Patterns

These patterns were **mined from 900+ real PR review comments** on the codebase this starter
was generalized from — they are what reviewers actually pick up on. Treat this as a
**pre-PR self-review checklist**: before you open a PR, walk the relevant sections and
confirm your diff complies. Each item gives the imperative rule, the *why*, how often it
came up in review (`frequency`), and whether it is already written down elsewhere
(`[documented]`) or is a pattern reviewers enforce that wasn't previously captured (`[new]`).

`[new]` items are the ones most likely to bite you, because they aren't yet baked into the
other docs — read those especially carefully.

---

## 1. Tenancy & queries

- [ ] **Filter every list/detail query through `Model.request_query(request, db)` (internal)
  or `Model.query_for_pub_api(organization_id)` (public); never replicate org/role filters
  inline.** `[documented]` · frequency: high
  *Why:* `request_query` bakes in org-scoping, role, and billing checks. Duplicating filters
  inline risks permission/tenant leaks and drifts from the central policy.

- [ ] **Use `escape_like()` on all user input in `LIKE`/`ilike` queries.** `[documented]` ·
  frequency: high
  *Why:* unescaped `%` and `_` act as wildcards, leaking unintended rows.

- [ ] **Redact internal/sensitive fields (internal ids, `hashed_*`, `is_demo`, deleted
  flags, prompts, agent metadata) from every public response and from anything sent to a
  third party; build dedicated public schemas by explicit construction, never
  `model_validate` on the ORM object.** `[documented]` · frequency: medium
  *Why:* the public API and external integrations must not leak internal identifiers or
  system internals; explicit construction prevents accidental passthrough.

## 2. Performance

- [ ] **Use `PaginatedResponse` with two-step paginate-then-fetch: cheap `LIMIT`/`OFFSET`
  page query first, then `selectinload`/aggregations scoped to `WHERE id IN (page_ids)`.
  Never fetch all then paginate in memory.** `[documented]` · frequency: high
  *Why:* keeps per-page latency constant regardless of table size and prevents full-table
  joins. The dominant performance convention in the codebase.

- [ ] **Preserve `selectinload`/`joinedload` options whenever a query is rebuilt via
  `.subquery()` or a fresh `select()`; accessing relationships in a loop without eager
  loading is an N+1 regression reviewers reject.** `[new]` · frequency: high
  *Why:* `.subquery()` discards ORM-level options, so later relationship access triggers one
  lazy load per row.

- [ ] **Add `.limit(1)` to any query that uses `order_by(...).first()` to fetch a single
  recent row.** `[new]` · frequency: high
  *Why:* without `LIMIT` the DB may scan/sort the whole table; `.limit(1)` lets it stop
  after one match on large datasets.

- [ ] **Defer `db.commit()` outside loops (batch, then commit once); `db.create_or_update`
  already commits, so don't double-commit per iteration. Check org feature flags before
  enqueuing high-volume tasks.** `[new]` · frequency: high
  *Why:* per-iteration commits drastically slow bulk syncs; unconditional enqueues that later
  no-op waste Redis/Celery capacity.

- [ ] **Collapse duplicate queries and multiple loops over the same data into one pass; query
  objects directly instead of fetching ids then re-querying; avoid `distinct()` unless
  required for correctness; refresh stale objects after a commit before accessing
  relationships.** `[new]` · frequency: medium
  *Why:* each extra query/loop/`distinct` is wasted CPU/IO; post-commit objects are detached
  and need a refresh to reload relationships.

## 3. API design

- [ ] **Use 404 (not 403) for cross-tenant access to a resource in another organization; gate
  admin routes with router/route-level `dependencies=[Depends(Permission.is_admin)]` rather
  than handler-body checks.** `[documented]` · frequency: high
  *Why:* 404 doesn't leak endpoint/resource existence to other tenants; declarative
  permission deps are visible in the signature and can't be bypassed.

- [ ] **Declare `response_model` on every endpoint and return the ORM row directly; use the
  `_Base`/`Table`/`Basic` split so secret fields (`hashed_key`, internal ids) live only on
  the table class and can't leak.** `[documented]` · frequency: high
  *Why:* FastAPI serializes to the declared schema, removing hand-mapping boilerplate and
  preventing accidental field exposure.

- [ ] **Always use `url_path_for` / `request.url_for` with kebab-case route names; never
  hardcode URL paths (in app code or tests).** `[documented]` · frequency: high
  *Why:* hardcoded paths break silently on route changes; named routes are validated at
  startup and in tests.

## 4. Testing

- [ ] **Create test data with factories (`create_with_db`), never raw `db.add()` +
  `commit()`; prefer `db.create()` over `add`/`commit`/`refresh` in app code; never assign
  explicit ids.** `[documented]` · frequency: high
  *Why:* factories centralize relationships/defaults; `TRUNCATE RESTART IDENTITY` resets PKs
  so hardcoded ids break under xdist randomization.

- [ ] **Assert the complete response structure, not individual fields; no inline comments in
  tests (docstring only); name response vars `r`; use `auth_client` by default, role clients
  only for permission tests.** `[documented]` · frequency: high
  *Why:* full-structure assertions document the contract and catch unintended field changes;
  clean self-documenting tests are the house style.

- [ ] **Add a `count_queries` / `AssertNumQueries` test for any list endpoint, asserting an
  identical query count at `page_size=1` and `page_size=200` to prove no N+1. Maintain 98%
  overall coverage and 100% patch coverage.** `[documented]` · frequency: high
  *Why:* the fixed query-count test is the enforced proof that paginate-then-fetch is
  correct; codecov gates patch coverage at 100%.

- [ ] **Mock only external API boundaries (HTTP / third-party); never mock internal service
  logic. Use `@patch` as a decorator, not inline `with patch()`. Patch `time.sleep` and
  disable `task_eager_propagates` when testing Celery retry/backoff.** `[documented]` ·
  frequency: high
  *Why:* mocking internals defeats integration testing; decorator patches are composable;
  eager propagation otherwise masks `Retry` exceptions and backoff slows tests.

- [ ] **Remove dead/legacy/test-only fixtures and throwaway models; use factories instead of
  dedicated test tables.** `[new]` · frequency: medium
  *Why:* dead fixtures and test-only tables increase cognitive load and pollute the
  schema/migrations.

## 5. Code style

- [ ] **Keep all imports at module level (no function-level imports except documented
  circular-import / `TYPE_CHECKING` cases); never add `from __future__ import
  annotations`.** `[documented]` · frequency: high
  *Why:* function-level imports are cargo-cult and hide dependencies; deferred annotations
  break SQLModel/SQLAlchemy mappers, FastAPI DI, and pydantic introspection.

- [ ] **Replace non-trivial ternaries with multi-line `if/else`; extract magic
  numbers/strings into `ALL_CAPS` module constants (e.g. `KEY_TEMPLATE = 'queue:{}'`); use
  docstrings for intent and comments only for genuinely complex code.** `[documented]` ·
  frequency: medium
  *Why:* readability and single-source-of-truth for values; docstrings are tooling-visible
  and don't drift like comments.

- [ ] **Don't refactor beyond the PR's scope; flag out-of-scope improvements for a follow-up.
  Split large files into focused units. Don't mark an imported class private (leading
  underscore) — if it's imported it's public.** `[new]` · frequency: medium
  *Why:* scope creep dilutes review and adds risk; underscore-but-imported is misleading
  about the module's API.

## 6. Security & correctness

- [ ] **Default new feature flags / org settings to `False` (opt-in), never
  `server_default=true` (opt-out); deduplicate idempotent webhook handling before inserting
  derived rows.** `[new]` · frequency: medium
  *Why:* opt-out flags silently enable a feature for all tenants on deploy; broker retries
  double-process webhooks without a dedup guard.

  *(See also the cross-tenant 404 rule in §3 and the redaction rule in §1 — both are
  security-critical.)*

## 7. Migrations

- [ ] **Never combine multiple migrations on one PR; when merging `main` into a feature
  branch, delete any blank merge migration and re-chain the feature migration's
  `down_revision` onto main's head (no `alembic merge heads`).** `[new]` · frequency: high
  *Why:* blank merge migrations clutter history and complicate reverts; a single linear chain
  keeps deploys deterministic.

## 8. Tooling

- [ ] **Use ty's native ignore codes (e.g. `# ty: ignore[invalid-argument-type]`,
  `[unresolved-attribute]`, `[invalid-parameter-default]`, `[invalid-type-form]`); add
  type-narrowing asserts (`assert obj.id is not None`) for DB ids. mypy-style codes silence
  nothing.** `[documented]` · frequency: high
  *Why:* ty doesn't recognize mypy codes; SQLModel/SQLAlchemy stub gaps need the specific ty
  codes; DB ids are `Optional[int]` in stubs but `int` after a fetch.

- [ ] **Pin every new/updated dependency to an exact version (`package==x.y.z`) including dev
  groups, then run `uv lock`. Run `make lint` after each piece of code.** `[documented]` ·
  frequency: high
  *Why:* reproducible builds; ruff lint + format must pass before CI to avoid style churn.
