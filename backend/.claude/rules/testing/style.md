---
paths:
  - "tests/**/*.py"
---

# Test Code Style Rules

Tests should be clean, readable, and follow consistent style patterns.

## Key Points

- No inline comments — only a docstring at the top of the test function.
- Maximum line length: 120 characters.
- Use `@patch` as a decorator, not `with patch()` blocks.
- Name the response variable `r`, not `response`.
- Maintain 98% overall coverage and 100% patch coverage.

## No Inline Comments

### ✅ Correct - Clean code without comments
```python
assert r.json() == {
    'id': resource.id,
    'name': 'Onboarding',
    'status': 'draft',
}
```

### ❌ Wrong - Unnecessary inline comments
```python
assert r.json() == {
    'id': resource.id,  # auto-generated id
    'name': 'Onboarding',  # the name we sent
    'status': 'draft',  # default status
}
```

## Docstrings Only

### ✅ Correct - Clear test with only a docstring
```python
def test_create_resource_returns_201(auth_client, db):
    """Test that creating a resource with valid data returns 201."""
    r = auth_client.post(auth_client.app.url_path_for('create-example-resource'), json={'name': 'Onboarding'})

    assert r.status_code == 201
    assert r.json()['name'] == 'Onboarding'
```

## Mocking Patterns

Mock only external boundaries (third-party HTTP, payment providers). Never mock internal
service logic — drive the real code path and mock just the network edge.

### ✅ Good - Using the @patch decorator
```python
from unittest.mock import patch

@patch('app.integrations.external_service.ExternalClient')
def test_external_call(mock_client, auth_client, db):
    mock_client.return_value.fetch.return_value = {'id': 123}
    ...
```

### ❌ Bad - Using a with patch() block
```python
def test_external_call(auth_client, db):
    with patch('app.integrations.external_service.ExternalClient') as mock_client:
        ...
```

## No-N+1 Proof

Add a `count_queries` test to every list endpoint asserting the query count is identical at
`page_size=1` and `page_size=200` — this is the enforced proof that paginate-then-fetch is
correct.

```python
def test_resource_list_no_n_plus_one(auth_client, db):
    """Test that listing resources runs the same number of queries regardless of page size."""
    for _ in range(5):
        ExampleResourceFactory.create_with_db(db, organization=auth_client.user.organization)

    with count_queries(db) as small:
        auth_client.get(auth_client.app.url_path_for('example-resource-list'), params={'page_size': 1})
    with count_queries(db) as large:
        auth_client.get(auth_client.app.url_path_for('example-resource-list'), params={'page_size': 200})

    assert small.count == large.count
```

## Running Tests

**Always run pytest with `-n auto`** (pytest-xdist) — single-file, single-test, debugging,
coverage, everything. One worker per core; the overhead on tiny runs is negligible and it
prevents the "forgot `-n auto` on the full suite" foot-gun. **Never** pass `--tb` flags — run
with full tracebacks so failures are debuggable.

```bash
uv run pytest -n auto
uv run pytest -n auto tests/example_domain/test_example_resources.py
uv run pytest -n auto -k 'test_create'
uv run pytest -n auto --cov=app --cov-report=term-missing --cov-fail-under=98
```

## Coverage Requirements

- **Overall**: minimum 98%.
- **Patch coverage**: 100% — every new branch, including error/except paths, needs a test.
- **Critical paths**: 100% for authentication, authorization, and data validation.
