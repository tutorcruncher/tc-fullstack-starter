---
paths:
  - "app/**/*.py"
---

# DBSession Utility Methods

Use the `DBSession` helper methods (in `app/core/database.py`) for common database operations.

## Available Methods

### `db.create(instance)`

Add, commit, and refresh an instance in one call:

```python
resource = db.create(ExampleResource(name='Onboarding', organization_id=organization.id))
# resource.id is now set
```

### `db.get_or_404(model, **kwargs)`

Get an instance or raise HTTP404:

```python
resource = db.get_or_404(ExampleResource, id=resource_id)
# Raises HTTP404 if not found
```

### `db.exists(model, **kwargs) -> bool`

Check whether an instance exists:

```python
if db.exists(User, email='alice@example.com'):
    raise HTTP409('Email already in use')
```

### `db.get_or_create(model, defaults=None, **kwargs)`

Get an existing instance or create a new one (like Django's `get_or_create`):

```python
organization, created = db.get_or_create(
    Organization,
    name='Acme',
    defaults={'billing_status': BillingStatus.TRIAL},
)
# defaults are only used when creating, not when getting
```

### `db.create_or_update(model, defaults=None, **kwargs)`

Create a new instance or update an existing one (like Django's `update_or_create`):

```python
api_key, created = db.create_or_update(
    OrganizationApiKey,
    organization_id=organization.id,
    name='CI key',
    defaults={'last4': last4, 'hashed_key': hashed_key},
)
# defaults are applied on both create AND update. This commits — do NOT commit again.
```

## Session Management

### In API routes (dependency injection)

```python
from app.core.database import DBSession, get_db

@router.get('/example-resources')
def list_resources(db: DBSession = Depends(get_db)):
    return db.exec(select(ExampleResource)).all()
```

### In Celery tasks (context manager)

```python
from app.core.database import get_session

@celery_app.task(name='example_domain.tasks.process_example_resource')
def process_example_resource(example_resource_id: int) -> None:
    with get_session() as db:
        resource = db.get_or_404(ExampleResource, id=example_resource_id)
        # session auto-commits on success, rolls back on exception
```

`get_db()` is for request-scoped sessions (FastAPI dependency). `get_session()` is for
standalone sessions (Celery tasks, scripts).

## Commit batching

Defer `db.commit()` outside loops — batch the writes and commit once. `db.create` and
`db.create_or_update` already commit, so do not commit again per iteration. Per-iteration
commits drastically slow bulk operations.
