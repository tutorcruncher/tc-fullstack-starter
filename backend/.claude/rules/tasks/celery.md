---
paths:
  - "app/**/tasks.py"
  - "app/worker.py"
---

# Celery Task Patterns

## Task Definition

Define tasks with an explicit, namespaced `name` using the `@celery_app.task` decorator:

```python
from app.core.celery import celery_app
from app.core.database import get_session

@celery_app.task(name='example_domain.tasks.process_example_resource')
def process_example_resource(example_resource_id: int) -> None:
    with get_session() as db:
        resource = db.get_or_404(ExampleResource, id=example_resource_id)
        # ... task work ...
```

Key rules:
- Always provide an explicit `name='...'` string (dotted, module-prefixed).
- Use the `get_session()` context manager for database access (NOT `get_db()`).
- Task arguments must be JSON-serializable — pass IDs, never model instances.

## Database Sessions in Tasks

Tasks run outside the request lifecycle, so use `get_session()` as a context manager. It
auto-commits on success and rolls back on an exception:

```python
from app.core.database import get_session

@celery_app.task(name='example_domain.tasks.process_example_resource')
def process_example_resource(example_resource_id: int) -> None:
    with get_session() as db:
        resource = db.get_or_404(ExampleResource, id=example_resource_id)
        ...
```

**Never** use `get_db()` in a task — that is the FastAPI dependency for request-scoped
sessions.

## Dispatching from a route

Enqueue with `.delay(...)` (or `.apply_async(...)`), passing primitive ids:

```python
@router.post('', response_model=ExampleResourceBasic, status_code=201, name='create-example-resource')
def create_resource(request: Request, body: ExampleResourceCreate, db: DBSession = Depends(get_db)):
    resource = db.create(ExampleResource(**body.model_dump(), organization_id=request.state.user.organization_id))
    process_example_resource.delay(resource.id)
    return resource
```

Avoid enqueuing high-volume tasks that will immediately no-op — guard the dispatch on whatever
flag/condition the task checks, rather than enqueuing and bailing inside the worker.

## Worker wiring

`app/worker.py` re-exports `celery_app as app`, imports the task modules so the tasks register,
and initializes Sentry + Logfire in each child via a `@worker_process_init.connect` handler.

## Testing

In tests the `eager_celery` fixture sets `task_always_eager=True`, so tasks run synchronously
in-process. No special setup is needed — call the code that dispatches the task and assert the
result. When testing **retry/backoff** specifically, patch `time.sleep` and disable
`task_eager_propagates` so the `Retry` exception is exercised rather than re-raised.
