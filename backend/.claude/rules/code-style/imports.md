---
paths:
  - "**/*.py"
---

# Import Rules

All imports must be at the module level. Never use imports inside functions.

## Key Points

- All imports at module level
- No function-level imports unless technically necessary
- Use `TYPE_CHECKING` for type-only imports to avoid circular imports
- Never add `from __future__ import annotations`

## Module-Level Imports

### ✅ Correct
```python
from datetime import datetime
from sqlmodel import select
from app.auth.models import User

def create_user(name: str) -> User:
    user = User(name=name, created_dt=datetime.now())
    return user
```

### ❌ Wrong
```python
def create_user(name: str) -> User:
    from datetime import datetime  # Wrong - import inside function
    from sqlmodel import select    # Wrong - import inside function
    from app.auth.models import User  # Wrong - import inside function

    user = User(name=name, created_dt=datetime.now())
    return user
```

## Circular Import Resolution

Only use local imports when necessary to avoid a circular import — the canonical case is a
`query_for_pub_api` / `request_query` classmethod that needs a sibling model:

### ⚠️ Acceptable Exception
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.organization.models.organization import Organization

@classmethod
def request_query(cls, request, db=None):
    from app.organization.models.organization import Organization  # local import avoids circular import

    ...
```

## Import Order

Follow PEP 8 import ordering:

1. Standard library imports
2. Related third-party imports
3. Local application imports

Separate each group with a blank line.

## Never use `from __future__ import annotations`

**Don't add `from __future__ import annotations` to any file.** The minimum Python version
already supports PEP 604 unions (`X | Y`) and PEP 585 generics (`list[int]`) natively, and the
deferred-evaluation behaviour the future import introduces breaks tools that rely on real
annotations at import time (SQLModel/SQLAlchemy mappers, FastAPI dependency resolution,
pydantic).

### ❌ Wrong
```python
from __future__ import annotations

from dataclasses import dataclass
```

### ✅ Correct
```python
from dataclasses import dataclass
```
