from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select as sa_select
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.auth.api_key import api_key_auth
from app.common.api.errors import HTTP404
from app.common.api.paginate import PaginatedResponse
from app.common.api.rate_limit import public_api_rate_limit
from app.common.utils import escape_like
from app.core.config import settings
from app.core.database import DBSession, get_db
from app.example_domain.models.example_resource import (
    ExampleResource,
    ExampleResourceParticipant,
    ResourceStatus,
)
from app.organization.models.organization import Organization

public_router = APIRouter(
    prefix='/example-resources',
    tags=['example_domain'],
    dependencies=[Depends(api_key_auth), Depends(public_api_rate_limit)],
)


class PublicExampleResourceParticipant(BaseModel):
    """A participant attached to an example resource, exposed via the public API.

    Built by explicit construction (never ``model_validate`` on the ORM row) so internal
    fields can never pass through. The internal ``example_resource_id`` is redacted.
    """

    id: int
    name: str
    email: str


class PublicExampleResourceList(BaseModel):
    """An example resource in a public-API list response (participant count only).

    Internal fields (``is_demo``) are deliberately omitted.
    """

    id: int
    name: str
    description: str | None = None
    status: ResourceStatus
    organization_id: int
    created_dt: datetime
    updated_dt: datetime | None = Field(default=None, description='Last time the resource was updated')
    participant_count: int = Field(description='Number of participants attached to the resource')


class PublicExampleResourceDetail(PublicExampleResourceList):
    """An example resource detail: the list shape plus its participants."""

    participants: List[PublicExampleResourceParticipant] = Field(default_factory=list)


def _apply_resource_filters(
    query: SelectOfScalar['ExampleResource'], *, updated_since: datetime | None, search: str | None
) -> SelectOfScalar['ExampleResource']:
    """Apply the public resource-list filters to an org-scoped query."""
    if updated_since is not None:
        query = query.where(ExampleResource.updated_dt >= updated_since)  # ty: ignore[unsupported-operator]
    if search:
        query = query.where(ExampleResource.name.ilike(f'%{escape_like(search)}%'))  # ty: ignore[unresolved-attribute]
    return query


def _build_public_resource_list(resource: ExampleResource, participant_count: int) -> PublicExampleResourceList:
    """Build the public list schema for a resource by explicit construction (no passthrough)."""
    assert resource.id is not None
    return PublicExampleResourceList(
        id=resource.id,
        name=resource.name,
        description=resource.description,
        status=resource.status,
        organization_id=resource.organization_id,
        created_dt=resource.created_dt,
        updated_dt=resource.updated_dt,
        participant_count=participant_count,
    )


def _build_public_participant(participant: ExampleResourceParticipant) -> PublicExampleResourceParticipant:
    """Build the public participant schema, redacting the internal ``example_resource_id``."""
    assert participant.id is not None
    return PublicExampleResourceParticipant(id=participant.id, name=participant.name, email=participant.email)


@public_router.get('', response_model=PaginatedResponse[PublicExampleResourceList], name='public-example-resource-list')
def get_public_example_resource_list(
    request: Request,
    db: DBSession = Depends(get_db),
    page: Annotated[int, Query(ge=1, description='Page number')] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description='Items per page (max 200)')] = settings.dft_page_size,
    updated_since: Annotated[
        datetime | None, Query(description='Only resources updated on/after this datetime (incremental sync)')
    ] = None,
    search: Annotated[str | None, Query(description='Case-insensitive match on the resource name')] = None,
) -> PaginatedResponse[PublicExampleResourceList]:
    """List the organization's example resources with participant counts.

    Participants are not loaded here (the detail endpoint adds them); ``updated_since``
    matches ``updated_dt``.
    """
    organization: Organization = request.state.organization
    assert organization.id is not None
    base_query = _apply_resource_filters(
        ExampleResource.query_for_pub_api(organization.id).order_by(ExampleResource.id),  # ty: ignore[invalid-argument-type]
        updated_since=updated_since,
        search=search,
    )
    page_resources = db.exec(base_query.limit(page_size).offset((page - 1) * page_size)).all()

    if page_resources:
        resource_ids = [r.id for r in page_resources]
        participant_counts = {
            resource_id: count
            for resource_id, count in db.exec(
                sa_select(ExampleResourceParticipant.example_resource_id, func.count(ExampleResourceParticipant.id))  # ty: ignore[no-matching-overload, invalid-argument-type]
                .where(ExampleResourceParticipant.example_resource_id.in_(resource_ids))  # ty: ignore[unresolved-attribute]
                .group_by(ExampleResourceParticipant.example_resource_id)
            )
        }
        items = [
            _build_public_resource_list(resource, participant_counts.get(resource.id, 0)) for resource in page_resources
        ]
    else:
        items = []

    total = db.exec(select(func.count()).select_from(base_query.order_by(None).subquery())).one()
    return PaginatedResponse[PublicExampleResourceList](items=items, total=total, page=page, page_size=page_size)


@public_router.get(
    '/{example_resource_id}', response_model=PublicExampleResourceDetail, name='public-example-resource-detail'
)
def get_public_example_resource_detail(
    example_resource_id: int, request: Request, db: DBSession = Depends(get_db)
) -> PublicExampleResourceDetail:
    """Get a single example resource with its participants. Cross-org ids raise 404."""
    organization: Organization = request.state.organization
    assert organization.id is not None
    resource = db.exec(
        ExampleResource.query_for_pub_api(organization.id)
        .options(selectinload(ExampleResource.participants))  # ty: ignore[invalid-argument-type]
        .where(ExampleResource.id == example_resource_id)
    ).one_or_none()
    if resource is None:
        raise HTTP404('Example resource not found')
    return PublicExampleResourceDetail(
        **_build_public_resource_list(resource, len(resource.participants)).model_dump(),
        participants=[_build_public_participant(p) for p in resource.participants],
    )
