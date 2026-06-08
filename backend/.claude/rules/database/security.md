---
paths:
  - "app/**/*.py"
---

# Database Security Patterns

Escape user input in LIKE queries and scope every query through `request_query` /
`query_for_pub_api`.

## SQL LIKE Query Safety

**ALWAYS escape user input in LIKE/ilike queries to prevent LIKE injection.**

### ✅ Good - Escaped user input
```python
from app.common.utils import escape_like

query = query.where(ExampleResource.name.ilike(f'%{escape_like(search_term)}%'))
```

### ❌ Bad - Raw user input
```python
query = query.where(ExampleResource.name.ilike(f'%{search_term}%'))  # DANGEROUS
```

### What `escape_like()` does

- `%` → `\%` (percent wildcard)
- `_` → `\_` (single-character wildcard)
- `\` → `\\` (the escape character itself)

### Why this matters

An unescaped `%` matches ALL records (data leak); an unescaped `_` acts as a
single-character wildcard.

## Access Control — internal API

Use `Model.request_query(request, db)` on every list and detail endpoint so users only see
data they are authorized to see. `request_query` is a classmethod on `AppModel` (in
`app/common/models.py`) that each concrete model overrides. It reads `request.state.user`:
superadmins see everything, everyone else is scoped to their own
`request.state.user.organization_id` (and `deleted_dt IS NULL`).

```python
@router.get('/example-resources')
def list_resources(request: Request, db: DBSession = Depends(get_db)):
    return db.exec(ExampleResource.request_query(request, db)).all()
```

This pattern:
- Reads `request.state.user` internally to determine access (takes `request`, not `user`)
- Bakes org-scoping into one place — never replicate the org filter inline
- Should be used for **all** internal list and detail endpoints

## Access Control — public API

The public API authenticates by org API key and sets `request.state.organization_id` (never
`request.state.user`). Scope those queries through `Model.query_for_pub_api(organization_id)`,
the sibling classmethod. **Never** call `request_query` on a public route — it expects a user.

```python
@public_router.get('')
def list_resources(request: Request, db: DBSession = Depends(get_db)):
    return db.exec(ExampleResource.query_for_pub_api(request.state.organization_id)).all()
```

## Secret fields live only on the table class

Use the `_Base` / `Table` / `Basic` model split so secrets (`hashed_password`, `hashed_key`)
are declared **only** on the `table=True` class. A `Basic` response schema then physically
cannot serialize them, even if a handler returns the ORM row directly.
