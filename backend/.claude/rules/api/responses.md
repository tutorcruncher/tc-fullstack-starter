---
paths:
  - "app/**/api/*.py"
  - "app/**/public_api/*.py"
---

# API URL and Response Patterns

Always use `url_path_for` for URL references and `PaginatedResponse` for list endpoints.
Declare a `response_model` on every endpoint and return the ORM row directly.

## URL Generation with url_path_for

**ALWAYS use `url_path_for` instead of hardcoded URL paths.** This keeps URLs correct when routes change.

```python
from starlette.requests import Request

@router.get('/some-route')
def some_route(request: Request):
    other_url = request.url_for('other-route-name')
    return {'redirect_url': other_url}
```

### Route Naming Convention

Use descriptive kebab-case names:

```python
@router.get('/example-resources/{resource_id}', name='example-resource-detail')
@router.post('/example-resources', name='create-example-resource')
@router.put('/example-resources/{resource_id}', name='update-example-resource')
```

### Benefits

- **Type Safety**: FastAPI catches missing route names at startup
- **Maintainability**: Route changes only need to be updated in one place
- **Consistency**: All URLs follow the same pattern

## response_model + return the ORM row

Declare `response_model` on every endpoint and return the raw ORM instance. FastAPI
serializes it to the declared schema — no hand-mapping, and fields the schema omits never
leak. This pairs with the `_Base` / `Table` / `Basic` model split: secrets (`hashed_key`,
`hashed_password`, internal ids) live **only** on the table class, so a `Basic` schema
physically cannot expose them.

### ✅ Good

```python
@router.get('/example-resources/{resource_id}', response_model=ExampleResourceBasic, name='example-resource-detail')
def get_resource(resource_id: int, request: Request, db: DBSession = Depends(get_db)) -> ExampleResource:
    resource = db.exec(ExampleResource.request_query(request, db).where(ExampleResource.id == resource_id)).first()
    if not resource:
        raise HTTP404('Example resource not found')
    return resource
```

### ❌ Bad - hand-mapping fields into a dict

```python
return {'id': resource.id, 'name': resource.name, 'status': resource.status}
```

## PaginatedResponse for List Endpoints

All list endpoints must use `PaginatedResponse`:

```python
from app.common.api.paginate import PaginatedResponse
from app.core.config import settings

@router.get('', response_model=PaginatedResponse[ExampleResourceList], name='example-resource-list')
def get_resources(request: Request, db: DBSession = Depends(get_db), page: int = 1) -> PaginatedResponse[ExampleResourceList]:
    ...
    return PaginatedResponse[ExampleResourceList](items=items, total=total, page=page, page_size=settings.dft_page_size)
```

`PaginatedResponse` fields: `items: list[T]`, `total: int`, `page: int`, `page_size: int`.

See `database/pagination.md` for the full two-step pagination pattern.
