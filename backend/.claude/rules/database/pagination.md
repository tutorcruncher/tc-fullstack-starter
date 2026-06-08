---
paths:
  - "app/**/api/*.py"
  - "app/**/public_api/*.py"
---

# Database Pagination Pattern

Use `PaginatedResponse` and fetch expensive data ONLY for the current page's items.

## Key Points

- **Step 1**: Get the paginated subset (LIMIT/OFFSET) — a cheap query.
- **Step 2**: Fetch related data ONLY for those specific page items.
- Never fetch all data then paginate in memory.

## Why This Matters

- With 1000 resources showing 50 per page, only query the 50 you will return.
- Complex joins are expensive — only run them for items on the page.
- Per-page latency stays constant as the dataset grows.

## Simple Aggregation Example

```python
from sqlalchemy import func, select as sa_select
from app.common.api.paginate import PaginatedResponse
from app.core.config import settings

@router.get('', response_model=PaginatedResponse[ExampleResourceList], name='example-resource-list')
def get_resources(request: Request, db: DBSession = Depends(get_db), page: int = 1) -> PaginatedResponse[ExampleResourceList]:
    # Step 1: get the paginated resources for this page
    base_query = ExampleResource.request_query(request, db).order_by(ExampleResource.name)
    paginated_query = base_query.limit(settings.dft_page_size).offset((page - 1) * settings.dft_page_size)
    page_resources = db.exec(paginated_query).all()

    # Step 2: count participants ONLY for resources on this page
    if page_resources:
        resource_ids = [r.id for r in page_resources]
        count_query = (
            sa_select(ExampleResourceParticipant.example_resource_id, func.count().label('count'))
            .where(ExampleResourceParticipant.example_resource_id.in_(resource_ids))
            .group_by(ExampleResourceParticipant.example_resource_id)
        )
        counts = {resource_id: count for resource_id, count in db.exec(count_query)}
        items = [
            ExampleResourceList(**r.model_dump(), participant_count=counts.get(r.id, 0), organization=r.organization)
            for r in page_resources
        ]
    else:
        items = []

    total = db.exec(sa_select(func.count()).select_from(base_query.subquery())).one()
    return PaginatedResponse[ExampleResourceList](items=items, total=total, page=page, page_size=settings.dft_page_size)
```

## Complex Joins Example

```python
@router.get('', response_model=PaginatedResponse[ExampleResourceList], name='example-resource-list')
def get_resources(request: Request, filters: ExampleResourceListFilter = Depends(), page: int = 1, db: DBSession = Depends(get_db)):
    # Step 1: get the paginated rows (cheap query)
    base_query = filters.apply(ExampleResource.request_query(request, db), request.state.user)
    base_page_objs = db.exec(base_query.limit(settings.dft_page_size).offset((page - 1) * settings.dft_page_size)).all()

    # Step 2: re-query with eager loading ONLY for this page's ids
    if base_page_objs:
        obj_ids = [obj.id for obj in base_page_objs]
        page_objs = db.exec(
            ExampleResource.request_query(request, db)
            .options(selectinload(ExampleResource.participants))
            .where(ExampleResource.id.in_(obj_ids))
        ).all()
        # build response from page_objs...
```

## Anti-Pattern

```python
# ❌ BAD: fetch ALL rows, then N+1 per row
resources = db.exec(ExampleResource.request_query(request, db)).all()  # All of them!
return [
    ExampleResourceList(
        **r.model_dump(),
        participant_count=db.exec(select(func.count()).where(...)).scalar(),  # N+1!
    )
    for r in resources
]
```

## Key Principles

1. **Paginate first**: get page items before any expensive operation.
2. **Scope expensive queries**: use `WHERE id IN (...)` for page items only.
3. **Use lookups**: build dictionaries for O(1) lookup when assembling responses.
4. **Preserve eager-load options**: rebuilding a query via `.subquery()` or a fresh `select()`
   drops `selectinload`/`joinedload` — re-apply them, or relationship access becomes N+1.
5. **`.limit(1)` on single-row reads**: any `order_by(...).first()` needs `.limit(1)` so the
   DB can stop after the first match.
6. **Handle empty pages**: check `if page_objs:` before running the step-2 query.
7. **Prove it**: add a `count_queries` test asserting identical query count at `page_size=1`
   and `page_size=200`.
