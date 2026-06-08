---
paths:
  - "**/*.py"
---

# Type Checking with ty

The project type-checks with [ty](https://github.com/astral-sh/ty) (Astral's fast type
checker). All changes must pass `make type-check` (`uv run ty check .`) before merging.

## Always use ty's native ignore codes

Use **ty's** native ignore syntax with specific rule codes — never `# type: ignore` or
mypy-style codes (`arg-type`, `attr-defined`), which silence nothing under ty.

```python
selectinload(ExampleResource.participants)  # ty: ignore[invalid-argument-type]
ExampleResource.id.in_(resource_ids)  # ty: ignore[unresolved-attribute]
```

To auto-add the right comments after a ty upgrade exposes new diagnostics, run
`uv run ty check --add-ignore .`.

## SQLAlchemy / SQLModel stub limitations

SQLModel/SQLAlchemy stubs don't fully type relationships or column operations. These need an
ignore:

```python
# Relationships and eager loading
selectinload(ExampleResource.participants)  # ty: ignore[invalid-argument-type]

# Column operations (filtering, ordering)
ExampleResource.created_dt.desc()  # ty: ignore[unresolved-attribute]
Organization.id.in_(org_ids)  # ty: ignore[unresolved-attribute]
ExampleResource.name.ilike(pattern)  # ty: ignore[unresolved-attribute]

# Join operations
.join(Organization, User.organization_id == Organization.id)  # ty: ignore[invalid-argument-type]
```

## Type narrowing with assertions

Database model ids are `int | None` in the stubs but guaranteed `int` once fetched. Narrow
with an assertion rather than an ignore:

```python
assert user.id is not None  # a user loaded from the DB always has an id
assert resource.id is not None
```

## FastAPI parameter patterns

ty cannot always resolve FastAPI `Query`/`Field` defaults or the dynamically-built
`FKFilterField`:

```python
from fastapi import Query

page_size: int = Query(None, ge=1, le=200)  # ty: ignore[invalid-parameter-default]

organization_id: FKFilterField(Organization) = None  # ty: ignore[invalid-type-form]
```

## When to add a type ignore

1. **SQLAlchemy operations** — `[invalid-argument-type]`, `[unresolved-attribute]` for
   relationships, column ops, and joins.
2. **FastAPI Query/Field defaults** — `[invalid-parameter-default]`.
3. **`FKFilterField`** — `[invalid-type-form]` (dynamic `Annotated` type).
4. **Intentional method overrides** — `[invalid-method-override]` in model class hierarchies.

Prefer a type-narrowing `assert` over an ignore wherever the value really is non-`None` after
the preceding code. Keep ignores specific (always with the rule code) and local to the line
that needs them.
