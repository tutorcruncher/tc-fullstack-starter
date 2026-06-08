---
paths:
  - "tests/**/*.py"
---

# Test URL Generation Rules

Always use `client.app.url_path_for()` in tests instead of hardcoded URLs.

## Key Points

- Use route names, not hardcoded paths.
- Route names use kebab-case (e.g. `example-resource-detail`, `create-example-resource`).
- FastAPI validates route names at startup, so a renamed route fails loudly.

## Examples

### ✅ Good - Using url_path_for
```python
def test_get_resource(auth_client, db):
    resource = ExampleResourceFactory.create_with_db(db, organization=auth_client.user.organization)

    r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', resource_id=resource.id))

    assert r.status_code == 200
```

### ❌ Bad - Hardcoded URLs
```python
def test_get_resource(auth_client, db):
    r = auth_client.get(f'/example-resources/{resource.id}')  # Breaks silently if the route changes
    assert r.status_code == 200
```

## Public API routes

Public-API routes live on the mounted sub-app but resolve through the parent app's
`url_path_for`, using the `public-` prefixed names:

```python
r = public_api_client.get(public_api_client.app.url_path_for('public-example-resource-list'))
```

## Rationale

- **Type Safety**: FastAPI catches missing route names at startup.
- **Maintainability**: route changes only need updating in one place.
- **Consistency**: all URLs follow the same pattern.
