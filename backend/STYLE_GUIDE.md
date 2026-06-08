# Style Guide

The consolidated code-style reference for this starter. It distills the rules in `CLAUDE.md`
and `.claude/rules/code-style/`. Where this guide and a `.claude/rules/` file overlap, they
say the same thing — this is the single page to skim before writing code.

## Formatting

- **Single quotes** for strings (`'value'`, not `"value"`). `ruff format` enforces this.
- **Max line length 120 characters.** Do **not** break lines shorter than 120 unnecessarily.
- One statement per line; let `ruff format` handle wrapping.
- Run `make lint` (ruff check + `ruff format --check` + ty) after each piece of code, and
  `make format` to auto-fix.

## Imports

- **Module-level imports only.** Never import inside a function body.
  - The only exceptions are a `TYPE_CHECKING` block, or a local import strictly required to
    break a circular import (e.g. inside `User.request_query`). Document why.
- **Never add `from __future__ import annotations`.** Python 3.12 supports `X | Y` unions and
  `list[int]` generics natively, and deferred annotations break SQLModel/SQLAlchemy mappers,
  FastAPI dependency resolution, and pydantic introspection at import time.
- Follow PEP 8 import ordering: stdlib, third-party, local — separated by blank lines.

```python
# ✅ Correct
from datetime import datetime
from sqlmodel import select
from app.auth.models import User

def create_user(name: str) -> User:
    return User(name=name, created_dt=datetime.now())
```

```python
# ❌ Wrong
def create_user(name: str) -> User:
    from datetime import datetime          # no function-level imports
    from app.auth.models import User
    return User(name=name, created_dt=datetime.now())
```

## Type hints

- Type-hint **every** function signature (arguments and return).
- Prefer `X | None` over `Optional[X]`. When editing code that uses `Optional`, convert it
  and drop the now-unused `from typing import Optional`.
- Use ty's **native** ignore codes (`# ty: ignore[invalid-argument-type]`, etc.), never
  mypy-style codes. Add type-narrowing asserts for DB ids (`assert obj.id is not None`).

## Conditionals

**Prefer multi-line `if/else` over a ternary** for anything non-trivial.

```python
# ✅ Correct
if auto_now:
    onupdate = lambda: datetime.now(tz=timezone.utc)
else:
    onupdate = None
```

```python
# ❌ Avoid
onupdate = (lambda: datetime.now(tz=timezone.utc)) if auto_now else None
```

## Constants for magic values

Extract magic numbers and strings into `ALL_CAPS` module-level constants — one source of
truth, and the name documents intent.

```python
# ✅ Correct
RATE_LIMIT_KEY_TEMPLATE = 'rate_limit:public_api:{org_id}'
MAX_API_KEYS_PER_ORG = 10
```

```python
# ❌ Avoid
key = f'rate_limit:public_api:{org_id}'   # repeated string literal
if len(keys) >= 10:                       # bare magic number
    ...
```

## Naming

- Descriptive variable and function names. No single-letter names outside tight loops.
  (The one deliberate convention is `r` for the response object **in tests**.)
- Public functions and classes get docstrings. Trivial ones don't need them.
- **Don't mark an imported symbol private** (leading underscore). If a module imports it,
  it's part of that module's API and shouldn't have a `_` prefix.

## Documentation

- **Docstrings over comments.** Use docstrings to explain intent; comments only for
  genuinely complex code, and they explain *why*, not *what*.
- Document non-obvious model/schema fields with `description=` (skip the universally
  obvious ones like `id`, `name`, `email`, `created_dt`).
- No inline comments in tests — a docstring at the top of the test function is enough.

```python
# ✅ Correct
def authenticate_user(session: DBSession, email: str, password: str) -> User | None:
    """Return the user if the credentials are valid, else None (timing-resistant)."""
    ...
```

## Schema split — `_Base` / `Table` / `Basic`

Split every model into three classes so secrets can't leak into responses:

- `_Model(AppModel)` — non-table base with the shared columns.
- `Model(_Model, table=True)` — adds `id`, **secret fields** (`hashed_password`,
  `hashed_key`), relationships, and the `request_query` / `query_for_pub_api` classmethods.
- `ModelBasic(_Model)` — adds `id` only (no secrets); the public-facing response shape.

Set `response_model=ModelBasic` on endpoints and **return the ORM row directly** — FastAPI
serializes through the declared schema, so fields that exist only on the table class are
never exposed. This also removes hand-mapping boilerplate.

```python
class _User(AppModel):
    email: str
    first_name: str
    last_name: str
    role: UserRole = EnumField(UserRole)

class User(_User, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str            # secret — only on the table class

class UserBasic(_User):
    id: int                         # no hashed_password
```

## `is None` / `is not None`

Use identity checks for `None`, never `==`/`!=`. For SQLModel column comparisons in a query,
`== None` is required (SQLAlchemy translates it to `IS NULL`) — that is the documented
exception, and it earns a `# noqa`-style allowance only inside query builders.

```python
# ✅ Python-level
if user.deleted_dt is None:
    ...

# ✅ Query-level (SQLAlchemy needs ==/!= here)
select(User).where(User.deleted_dt == None)  # noqa: E711
```

## Scope discipline

- **Don't refactor beyond the task.** No drive-by docstrings, comments, type hints, or
  reformatting of code you didn't otherwise touch. Flag out-of-scope improvements for a
  follow-up instead of bundling them.
- **No speculative abstractions.** Solve the problem in front of you; don't add parameters,
  config flags, or layers for hypothetical future needs.
- **Split large files** into focused units rather than letting one module sprawl.
- **No backwards-compatibility shims** for code you're removing, and no fallback handling
  for database states that can't occur under the "migrations run on deploy" model.

## Tests

Full testing conventions live in `.claude/rules/testing/` and `CLAUDE.md`. The style
essentials:

- Name the response variable `r`, not `response`.
- Create data with **factories** (`create_with_db`), never raw `db.add()` + `commit()`;
  prefer `db.create()` in app code. Never assign explicit ids.
- Assert the **complete** response structure, not individual fields. Inline the expected
  values directly — no intermediate `expected = {...}` variable.
- **No comments except a docstring** at the top of the test.
- Use `auth_client` by default; reach for `admin_client` / `member_client` only when testing
  permission restrictions.
- Use `url_path_for` for every URL — never hardcode a path.
- Use `@patch` as a decorator, not an inline `with patch()` block. Mock only external
  boundaries, never internal business logic.
- Add a `count_queries` test for list endpoints asserting identical query counts at
  `page_size=1` and `page_size=200`.
