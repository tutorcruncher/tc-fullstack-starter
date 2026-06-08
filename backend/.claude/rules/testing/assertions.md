---
paths:
  - "tests/**/*.py"
---

# Test Assertion Rules

Check entire data structures in test responses, not just individual keys.

## Key Points

- Assert the complete response structure, not individual fields.
- Inline expected values directly in the assertion.
- Don't check key existence before asserting a value (KeyError tells you the same thing).
- Name the response variable `r`, not `response`.

## Complete Structure Checks

### ✅ Good - Checking the entire structure
```python
def test_get_resource(auth_client, db):
    """Test that a resource is returned with its full shape."""
    resource = ExampleResourceFactory.create_with_db(db, name='Onboarding', organization=auth_client.user.organization)

    r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', resource_id=resource.id))

    assert r.status_code == 200
    assert r.json() == {
        'id': resource.id,
        'name': 'Onboarding',
        'description': None,
        'status': 'draft',
        'organization_id': auth_client.user.organization_id,
        'created_dt': r.json()['created_dt'],
        'updated_dt': r.json()['updated_dt'],
        'participants': [],
    }
```

### ❌ Bad - Checking only individual keys
```python
def test_get_resource(auth_client, db):
    r = auth_client.get(...)
    assert r.json()['name'] == 'Onboarding'  # Misses every other field
```

## Inline Expected Values

### ✅ Good - Inline expected values directly
```python
assert data == {
    'participants': [
        {'id': alice.id, 'name': 'Alice', 'email': 'alice@example.com'},
        {'id': bob.id, 'name': 'Bob', 'email': 'bob@example.com'},
    ],
}
```

### ❌ Bad - Unnecessary intermediate variable
```python
by_id = {p['id']: p for p in data['participants']}
assert data == {'participants': [by_id[alice.id], by_id[bob.id]]}
```

## No Redundant Existence Checks

### ✅ Good - Direct value assertions
```python
counts_by_id = {row['id']: row['participant_count'] for row in data['items']}
assert counts_by_id[resource_a.id] == 2
assert counts_by_id[resource_b.id] == 0
```

### ❌ Bad - Redundant checks
```python
assert resource_a.id in counts_by_id  # Redundant — KeyError already tells you this
assert counts_by_id[resource_a.id] == 2
```

**Rationale**: if the key is missing, Python raises `KeyError` and the test fails with a clear
message — the `in` check adds nothing.
