---
paths:
  - "tests/**/*.py"
---

# Test Client Usage Rules

Use `auth_client` by default for testing APIs.

## Key Points

- Default to `auth_client` (admin-level access) for most tests.
- Use a role-specific client (`member_client`) or the unauthenticated `client` only when
  testing a permission boundary.
- All authenticated clients are `AuthenticatedTestClient` instances exposing `.user`.

## Default Client

### ✅ Good - Using auth_client by default
```python
def test_create_resource(auth_client, db):
    """Test creating an example resource."""
    r = auth_client.post(
        auth_client.app.url_path_for('create-example-resource'),
        json={'name': 'Onboarding'},
    )

    assert r.status_code == 201
```

## Permission Testing

### ✅ Good - Using a role client when testing permissions
```python
def test_member_cannot_create_api_key(member_client, db):
    """Test that a non-admin member is forbidden from creating API keys."""
    r = member_client.post(member_client.app.url_path_for('api-key-create'), json={'name': 'CI'})

    assert r.status_code == 403
```

### ✅ Good - Cross-tenant access returns 404
```python
def test_resource_in_other_org_is_404(auth_client, db):
    """Test that a resource in another organization is not visible (404, not 403)."""
    other_org = OrganizationFactory.create_with_db(db)
    resource = ExampleResourceFactory.create_with_db(db, organization=other_org)

    r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', resource_id=resource.id))

    assert r.status_code == 404
```

## Available Test Clients

| Client | Role | Use Case |
|--------|------|----------|
| `auth_client` | Admin | Default for most API tests |
| `admin_client` | Admin | Explicitly testing admin-only endpoints |
| `member_client` | Member | Testing non-admin permission restrictions |
| `public_api_client` | (org API key) | Public `/api/v1` endpoints |
| `client` | None | Unauthenticated requests |

All authenticated clients expose `.user` (e.g. `auth_client.user.id`,
`auth_client.user.organization_id`). The `public_api_client` is paired with
`OrganizationApiKeyFactory` for the API-key header.

## Rationale

`auth_client` has admin-level access, which covers most testing scenarios. Reach for a
role-specific or unauthenticated client only when the test is specifically about a permission
boundary.
