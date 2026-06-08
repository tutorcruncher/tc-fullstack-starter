from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select as sa_select
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.auth.models import User
from app.common.api.errors import HTTP404
from app.common.api.filters import FKFilterField, ListFilter, ListOrder
from app.common.api.paginate import PaginatedResponse
from app.common.utils import escape_like, inclusive_end_of_day
from app.core.config import settings
from app.core.database import DBSession, get_db
from app.example_domain.models.example_resource import (
    ExampleResource,
    ExampleResourceBasic,
    ExampleResourceDetail,
    ExampleResourceList,
    ExampleResourceParticipant,
    ExampleResourceParticipantBasic,
    ResourceStatus,
)
from app.example_domain.tasks import process_example_resource
from app.organization.models.organization import Organization, OrganizationBasic

router = APIRouter(prefix='/example-resources', tags=['example_domain'])


class ExampleResourceCreate(BaseModel):
    """Request body for creating an example resource."""

    name: str = Field(min_length=1, max_length=200, description='Human-readable name for the resource')
    description: Optional[str] = Field(default=None, max_length=2000)
    status: ResourceStatus = ResourceStatus.DRAFT


class ExampleResourceUpdate(BaseModel):
    """Request body for updating an example resource."""

    name: str = Field(min_length=1, max_length=200, description='Human-readable name for the resource')
    description: Optional[str] = Field(default=None, max_length=2000)
    status: ResourceStatus


class ExampleResourceListFilter(ListFilter):
    search: Optional[str] = Field(default=None, description='Case-insensitive match on the resource name')
    created_from: Optional[datetime] = Field(default=None, description='Only resources created on/after this datetime')
    created_to: Optional[datetime] = Field(default=None, description='Only resources created on/before this datetime')
    organization_id: FKFilterField(Organization) = None  # ty: ignore[invalid-type-form]

    def apply(self, query: SelectOfScalar['ExampleResource'], user: User) -> SelectOfScalar['ExampleResource']:
        """Apply the list filters to an access-scoped query."""
        if self.search:
            query = query.where(ExampleResource.name.ilike(f'%{escape_like(self.search)}%'))  # ty: ignore[unresolved-attribute]
        if self.created_from is not None:
            query = query.where(ExampleResource.created_dt >= self.created_from)
        if self.created_to is not None:
            query = query.where(ExampleResource.created_dt <= inclusive_end_of_day(self.created_to))
        if self.organization_id is not None:
            query = query.where(ExampleResource.organization_id == self.organization_id)
        return query


@dataclass
class ExampleResourceListOrder(ListOrder):
    """Ordering options for the example resource list (``name`` or ``created_dt``)."""

    model = ExampleResource
    fields = ['name', 'created_dt']


@router.options('', response_model=dict, name='example-resource-list-options')
def get_example_resource_list_options(request: Request, db: DBSession = Depends(get_db)) -> dict:
    """Return the filter and ordering option values for the resource list."""
    return {
        **ExampleResourceListFilter.get_options(request, db),
        **ExampleResourceListOrder.get_options(),
    }


@router.get('', response_model=PaginatedResponse[ExampleResourceList], name='example-resource-list')
def get_example_resource_list(
    request: Request,
    filters: ExampleResourceListFilter = Depends(),
    ordering: ExampleResourceListOrder = Depends(ExampleResourceListOrder),
    db: DBSession = Depends(get_db),
    page: Annotated[int, Query(ge=1, description='Page number')] = 1,
    page_size: Annotated[Optional[int], Query(ge=1, le=200, description='Items per page (max 200)')] = None,
) -> PaginatedResponse[ExampleResourceList]:
    """List the organization's example resources with their participant counts.

    Uses the two-step paginate-then-fetch pattern: a cheap page query first, then the
    participants and participant counts are loaded only for the resources on this page.
    """
    resolved_page_size = page_size or settings.dft_page_size
    base_query = ordering.apply(
        filters.apply(ExampleResource.request_query(request, db), request.state.user),
        request.state.user,
    )
    paginated_query = base_query.limit(resolved_page_size).offset((page - 1) * resolved_page_size)
    page_resources = db.exec(paginated_query).all()

    if page_resources:
        resource_ids = [r.id for r in page_resources]
        page_resources_unordered = db.exec(
            ExampleResource.request_query(request, db)
            .options(
                selectinload(ExampleResource.organization),  # ty: ignore[invalid-argument-type]
            )
            .where(ExampleResource.id.in_(resource_ids))  # ty: ignore[unresolved-attribute]
        ).all()
        resources_by_id = {r.id: r for r in page_resources_unordered}
        page_resources = [resources_by_id[rid] for rid in resource_ids]

        participant_counts = {
            resource_id: count
            for resource_id, count in db.exec(
                sa_select(ExampleResourceParticipant.example_resource_id, func.count(ExampleResourceParticipant.id))  # ty: ignore[no-matching-overload, invalid-argument-type]
                .where(ExampleResourceParticipant.example_resource_id.in_(resource_ids))  # ty: ignore[unresolved-attribute]
                .group_by(ExampleResourceParticipant.example_resource_id)
            )
        }
        items = [
            ExampleResourceList(
                **resource.model_dump(),
                participant_count=participant_counts.get(resource.id, 0),
                organization=OrganizationBasic(**resource.organization.model_dump()),
            )
            for resource in page_resources
        ]
    else:
        items = []

    total = db.exec(select(func.count()).select_from(base_query.order_by(None).subquery())).one()
    return PaginatedResponse[ExampleResourceList](items=items, total=total, page=page, page_size=resolved_page_size)


@router.get('/{example_resource_id}', response_model=ExampleResourceDetail, name='example-resource-detail')
def get_example_resource_detail(
    example_resource_id: int, request: Request, db: DBSession = Depends(get_db)
) -> ExampleResourceDetail:
    """Get a single example resource with its participants.

    A resource that belongs to another organization raises 404 (not 403) so endpoint and
    resource existence is never leaked across tenants.
    """
    resource = db.exec(
        ExampleResource.request_query(request, db)
        .options(selectinload(ExampleResource.participants))  # ty: ignore[invalid-argument-type]
        .where(ExampleResource.id == example_resource_id)
    ).one_or_none()
    if resource is None:
        raise HTTP404('Example resource not found')
    return ExampleResourceDetail(
        **resource.model_dump(),
        participants=[ExampleResourceParticipantBasic(**p.model_dump()) for p in resource.participants],
    )


@router.post('', status_code=201, response_model=ExampleResourceBasic, name='create-example-resource')
def create_example_resource(
    data: ExampleResourceCreate, request: Request, db: DBSession = Depends(get_db)
) -> ExampleResourceBasic:
    """Create an example resource for the requesting user's organization.

    Dispatches the ``process_example_resource`` Celery task with the new resource's id.
    """
    resource = db.create(ExampleResource(**data.model_dump(), organization_id=request.state.user.organization_id))
    process_example_resource.delay(resource.id)
    return ExampleResourceBasic(**resource.model_dump())


@router.put('/{example_resource_id}', response_model=ExampleResourceBasic, name='update-example-resource')
def update_example_resource(
    example_resource_id: int, data: ExampleResourceUpdate, request: Request, db: DBSession = Depends(get_db)
) -> ExampleResourceBasic:
    """Update an example resource. Cross-tenant ids raise 404."""
    resource = db.exec(
        ExampleResource.request_query(request, db).where(ExampleResource.id == example_resource_id)
    ).one_or_none()
    if resource is None:
        raise HTTP404('Example resource not found')
    for key, value in data.model_dump().items():
        setattr(resource, key, value)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return ExampleResourceBasic(**resource.model_dump())


@router.delete('/{example_resource_id}', status_code=204, name='delete-example-resource')
def delete_example_resource(example_resource_id: int, request: Request, db: DBSession = Depends(get_db)) -> None:
    """Delete an example resource (and its participants via cascade). Cross-tenant ids raise 404."""
    resource = db.exec(
        ExampleResource.request_query(request, db).where(ExampleResource.id == example_resource_id)
    ).one_or_none()
    if resource is None:
        raise HTTP404('Example resource not found')
    db.delete(resource)
    db.commit()
