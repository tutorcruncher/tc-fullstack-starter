---
paths:
  - "app/**/api/*.py"
  - "app/common/api/filters.py"
---

# List Filtering and Ordering

List endpoints filter and order through the helpers in `app/common/api/filters.py`:
`ListFilter`, `ListOrder`, `OrderDirection`, `FKFilterField`, `FKIntMeta`. These also power
the `OPTIONS` discovery response so consumers can learn the valid filters/sorts without
scraping 422 messages.

## ListFilter

Subclass `ListFilter` (a pydantic `BaseModel`) and implement `apply(query, user)`. Use the
project helpers: `escape_like` for search, `inclusive_end_of_day` for date-range upper bounds,
and `FKFilterField(Model)` for foreign-key filters (which `get_options` resolves into choice
lists, scoped via the target model's `request_query`).

```python
from app.common.api.filters import FKFilterField, ListFilter
from app.common.utils import escape_like, inclusive_end_of_day

class ExampleResourceListFilter(ListFilter):
    """Query filters for the example-resource list endpoint."""

    search: str | None = None
    created_from: date | None = None
    created_to: date | None = None
    organization_id: FKFilterField(Organization) = None  # ty: ignore[invalid-type-form]

    def apply(self, query: SelectOfScalar, user: User) -> SelectOfScalar:
        if self.search:
            query = query.where(ExampleResource.name.ilike(f'%{escape_like(self.search)}%'))
        if self.created_from:
            query = query.where(ExampleResource.created_dt >= self.created_from)
        if self.created_to:
            query = query.where(ExampleResource.created_dt <= inclusive_end_of_day(self.created_to))
        if self.organization_id:
            query = query.where(ExampleResource.organization_id == self.organization_id)
        return query
```

Wire it as a dependency: `filters: ExampleResourceListFilter = Depends()`.

## ListOrder

Subclass `ListOrder` and declare `model` + `fields` (lowercase, validated at subclass
creation to avoid Enum key collisions). A deterministic `model.id` tiebreaker is always
appended so pagination is stable even when the primary sort column has duplicates.

```python
from app.common.api.filters import ListOrder, OrderDirection

class ExampleResourceListOrder(ListOrder):
    """Ordering options for the example-resource list endpoint."""

    model = ExampleResource
    fields = ['name', 'created_dt']
    order_direction = OrderDirection.ASC
```

Convention: time-based primary sorts default to `DESC` (`created_dt`), alphabetical ones to
`ASC` (`name`).

## OPTIONS discovery endpoint

Expose a single `OPTIONS` route per list that merges `ListFilter.get_options(request, db)`
and `ListOrder.get_options()`. FK choice lists go through the target model's `request_query`,
so the OPTIONS payload is itself tenant-scoped.

```python
@router.options('', name='example-resource-list-options')
def list_options(request: Request, db: DBSession = Depends(get_db)) -> dict:
    """Return the valid filter and ordering options for the example-resource list."""
    return {
        **ExampleResourceListFilter.get_options(request, db),
        **ExampleResourceListOrder.get_options(),
    }
```
