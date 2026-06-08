from dataclasses import dataclass
from enum import Enum
from types import UnionType
from typing import Annotated, ClassVar, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.auth.models import User
from app.common.api.errors import HTTP422
from app.common.models import AppModel
from app.core.database import DBSession


class OrderDirection(str, Enum):
    """Order direction."""

    ASC = 'asc'
    DESC = 'desc'


@dataclass
class ListOrder:
    """Base class for list-endpoint ordering.

    Subclasses declare:
      * ``model`` — the SQLModel class being ordered.
      * ``fields`` — column names the caller may pass as ``order_by`` (lowercase only; a
        case-insensitive collision — e.g. ``created_dt`` and ``Created_dt`` — would silently
        overwrite each other in the Enum, so this is enforced at subclass creation time).
      * ``tiebreaker_fields`` (optional) — additional columns appended as secondary sort keys.
      * ``order_direction`` default — convention is ``DESC`` for time-based primary sorts
        (``created_dt``) and ``ASC`` for alphabetical ones (``name``). Override the dataclass
        default on the subclass to change it.

    Tiebreaker fields are always applied ASC regardless of ``order_direction``; they exist to
    produce a deterministic order within rows that share the primary sort value, not to express
    a user-facing directional sort. A deterministic ``model.id`` tiebreaker is always appended
    so pagination is stable even when the primary sort column has duplicates.
    """

    model: ClassVar[type[AppModel]]
    fields: ClassVar[list[str]]
    tiebreaker_fields: ClassVar[list[str]] = []
    order_direction: OrderDirection = OrderDirection.DESC
    order_by: str | Enum | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'model') or not hasattr(cls, 'fields'):
            raise TypeError(f'{cls.__name__} must define model and fields class attributes')
        if 'tiebreaker_fields' not in cls.__dict__:
            cls.tiebreaker_fields = []
        non_lowercase = [f for f in cls.fields if f != f.lower()]
        if non_lowercase:
            raise TypeError(
                f'{cls.__name__}.fields must be lowercase to avoid Enum key collisions; '
                f'got non-lowercase entries: {non_lowercase}'
            )
        cls.OrderBy = Enum(f'{cls.__name__}OrderBy', {f.upper(): f for f in cls.fields})

    def __post_init__(self):
        if isinstance(self.order_by, str):
            try:
                self.order_by = self.OrderBy[self.order_by.upper()]
            except KeyError:
                raise HTTP422(f'Invalid order_by value. Must be one of: {", ".join(self.fields)}') from None

    def apply(self, query: SelectOfScalar, user: User | None = None) -> SelectOfScalar:
        """Apply the configured ORDER BY clauses to ``query``.

        ``user`` is unused by the base implementation but accepted for parity with overrides
        that scope ordering by the calling user's role.
        """
        if self.order_by:
            order_by_field = self.order_by.value  # ty: ignore[unresolved-attribute]
        else:
            order_by_field = self.fields[0]
        order_column = getattr(self.model, order_by_field)
        order_clause = order_column.desc() if self.order_direction == OrderDirection.DESC else order_column.asc()
        query = query.order_by(order_clause)

        for field_name in self.tiebreaker_fields:
            if field_name != order_by_field:
                tiebreaker_column = getattr(self.model, field_name)
                query = query.order_by(tiebreaker_column.asc())

        if order_by_field != 'id' and 'id' not in self.tiebreaker_fields:
            query = self._append_id_tiebreaker(query)

        return query

    def _append_id_tiebreaker(self, query: SelectOfScalar) -> SelectOfScalar:
        """Append ``model.id ASC`` as the final deterministic tiebreaker for stable pagination."""
        return query.order_by(self.model.id.asc())  # ty: ignore[unresolved-attribute]

    @classmethod
    def get_options(cls) -> dict:
        """Return ordering metadata for OPTIONS responses.

        Lets API consumers discover the valid ``order_by`` / ``order_direction`` values
        without scraping 422 error messages.
        """
        default_direction = cls.__dataclass_fields__['order_direction'].default
        return {
            'order_by': {
                'type': 'str',
                'required': False,
                'choices': [{'id': f, 'name': f} for f in cls.fields],
                'default': cls.fields[0],
            },
            'order_direction': {
                'type': 'OrderDirection',
                'required': False,
                'choices': [{'id': d.value, 'name': d.value} for d in OrderDirection],
                'default': default_direction.value,
            },
        }


@dataclass(frozen=True)
class FKIntMeta:
    """Metadata for foreign key filter fields.

    Attach via Annotated to tell ``get_options()`` which model to query for choices and which
    field to use as the display name.
    """

    model: Type[AppModel]
    name_field: str = 'name'


def FKFilterField(model: Type[AppModel], *, name_field: str = 'name'):
    return Annotated[Optional[int], FKIntMeta(model=model, name_field=name_field)]


class ListFilter(BaseModel):
    def apply(self, query: SelectOfScalar, user: User) -> SelectOfScalar:
        raise NotImplementedError()

    @classmethod
    def get_field_type(cls, field_info: FieldInfo):
        annotation = field_info.annotation

        if get_origin(annotation) is Union:
            annotations = get_args(annotation)
            assert annotations[1] is type(None)
            annotation = get_args(annotation)[0]
        elif isinstance(annotation, UnionType):
            type_args = get_args(annotation)
            annotation = next((arg for arg in type_args if arg is not type(None)), type_args[0])

        if get_origin(annotation) is list:
            annotation = get_args(annotation)[0]

        return annotation

    @classmethod
    def get_options(cls, request: Request, db: DBSession) -> dict:
        """Get filter options for FK fields.

        Uses each model's ``request_query`` to apply proper access control and tenant filtering.
        """
        data = {}
        for field_name, field_info in cls.model_fields.items():
            field_type = cls.get_field_type(field_info)
            field_kwargs = {'type': field_type.__name__, 'required': field_info.is_required()}
            fk_meta = next((m for m in field_info.metadata if isinstance(m, FKIntMeta)), None)
            if fk_meta:
                Model = fk_meta.model
                opts = db.exec(Model.request_query(request, db)).all()
                field_kwargs['choices'] = [{'id': opt.id, 'name': getattr(opt, fk_meta.name_field)} for opt in opts]
            elif isinstance(field_type, type) and issubclass(field_type, Enum):
                field_kwargs['choices'] = [{'id': e.value, 'name': e.value} for e in field_type]
            data[field_name] = field_kwargs
        return data
