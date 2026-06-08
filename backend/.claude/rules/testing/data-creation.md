---
paths:
  - "tests/**/*.py"
---

# Test Data Creation Rules

Use `db.create()` and FactoryBoy factories for test data. Never assign explicit IDs.

## Key Points

- Use `db.create()` instead of separate `add`, `commit`, `refresh` calls.
- Use factories for anything with relationships or defaults.
- Let the ORM assign IDs — the test DB is `TRUNCATE ... RESTART IDENTITY` between tests, so
  hardcoded ids break under xdist randomization.

## db.create() Usage

### ✅ Good
```python
def test_create_resource(db):
    resource = db.create(ExampleResource(name='Onboarding', organization_id=org.id))
    assert resource.id is not None
```

### ❌ Bad
```python
def test_create_resource(db):
    resource = ExampleResource(name='Onboarding', organization_id=org.id)
    db.add(resource)
    db.commit()
    db.refresh(resource)
```

## Factory Usage

Factories use the `create_with_db(db, **kwargs)` pattern (the only public API on
`SQLModelFactory`).

### ✅ Good - Using factories
```python
def test_resource_with_participants(db):
    organization = OrganizationFactory.create_with_db(db, name='Acme')
    resource = ExampleResourceFactory.create_with_db(db, name='Onboarding', organization=organization)
    ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource, name='Alice')
    ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource, name='Bob')

    assert resource.id is not None
    assert len(resource.participants) == 2
```

Available factories include `OrganizationFactory`, `UserFactory` / `AdminFactory` /
`MemberFactory`, `OrganizationApiKeyFactory` (returns `(key_row, full_key)`),
`ExampleResourceFactory`, and `ExampleResourceParticipantFactory`.

## No Explicit IDs

### ✅ Good - Let the ORM assign IDs
```python
resource = ExampleResourceFactory.create_with_db(db, name='Onboarding')
# resource.id is now assigned by the database
```

### ❌ Bad - Explicit ID
```python
resource = ExampleResource(id=1, name='Onboarding')  # Never do this
```

## Don't add throwaway test tables

Use factories over the real models. Do not introduce test-only models or dedicated fixture
tables — they pollute the schema and migrations.
