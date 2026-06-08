---
paths:
  - "**/*.py"
---

# Documentation Rules

Use docstrings for documentation, not comments. Use type hints throughout.

## Key Points

- Use docstrings for function/class documentation
- Only use comments for genuinely complex code that requires explanation
- Use type hints throughout the codebase
- Follow PEP 8 style guidelines

## Docstrings

### ✅ Good - Using docstrings
```python
def create_example_resource(body: ExampleResourceCreate, organization_id: int, db: DBSession) -> ExampleResource:
    """Create an example resource for an organization.

    Args:
        body: Validated request body with the resource fields.
        organization_id: The owning organization.
        db: Database session.

    Returns:
        ExampleResource: The newly created resource.

    Raises:
        HTTP400: If the organization is over its resource cap.
    """
    resource = db.create(ExampleResource(**body.model_dump(), organization_id=organization_id))
    process_example_resource.delay(resource.id)
    return resource
```

## Type Hints

Always use type hints for function arguments and return values:

```python
def get_resource(resource_id: int, db: DBSession) -> ExampleResource | None:
    return db.get(ExampleResource, resource_id)
```

## Type Hint Style

Always use `X | None` instead of `Optional[X]`. This project targets Python 3.12+ where the
`|` syntax is native. When editing existing code that uses `Optional`, convert it to
`X | None` and drop the now-unused `from typing import Optional` import.

### Good
```python
def get_resource(resource_id: int) -> ExampleResource | None:
    ...

class Config:
    name: str | None = None
    data: dict | None = None
```

### Bad
```python
from typing import Optional

def get_resource(resource_id: int) -> Optional[ExampleResource]:
    ...
```

## Model and Field Documentation

Pydantic and SQLModel fields whose purpose isn't obvious from the name alone **must** be
documented. Use the `description=` parameter on the field, or a class-level docstring that
explains the non-obvious fields. This is especially important for public-API schemas — Scalar
renders both `description=` and the view docstring.

### ✅ Good - Field descriptions explain purpose
```python
class ExampleResourceCreate(BaseModel):
    """Request body for creating an example resource."""

    name: str = Field(..., description='Human-readable name, maximum 100 characters')
    status: ResourceStatus = Field(default=ResourceStatus.DRAFT, description='Lifecycle state of the resource')
```

### When to document fields

- **Always document**: fields with domain-specific meaning, fields whose purpose differs from
  what the name suggests, anything surfaced on the public API.
- **Skip if obvious**: `id`, `name`, `email`, `created_dt`, `first_name`, `last_name`.

## General Requirements

- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Handle errors with appropriate HTTP status codes
- Use dependency injection for database sessions and authentication

## Deployment Model

This project uses "migrations run on deploy":
- Database migrations are applied automatically during deployment
- Application code can assume the schema is up-to-date
- Do NOT add fallback code to handle "old" database states
- Do NOT add runtime checks for schema existence (e.g. "if column exists")
