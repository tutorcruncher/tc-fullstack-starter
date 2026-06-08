from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.common.fields import EnumField, FKField, UTCDatetimeField
from app.common.models import AppModel
from app.core.database import DBSession
from app.organization.models.organization import OrganizationBasic

if TYPE_CHECKING:  # pragma: no cover
    from app.organization.models.organization import Organization


class ResourceStatus(str, Enum):
    """The lifecycle state of an ``ExampleResource``."""

    DRAFT = 'draft'
    ACTIVE = 'active'
    ARCHIVED = 'archived'


class _ExampleResource(AppModel):
    """Shared, non-secret fields for the example resource.

    ``ExampleResource`` is the canonical domain entity in the starter: it belongs to an
    ``Organization`` (the tenant) and owns a list of ``ExampleResourceParticipant`` children.
    Rename it to your real entity and the rest of the patterns (org-scoping, two-step
    pagination, the public API slice, the Celery task) carry over unchanged.
    """

    name: str = Field(index=True)
    description: Optional[str] = None
    status: ResourceStatus = EnumField(ResourceStatus, default=ResourceStatus.DRAFT)
    organization_id: int = FKField('organization.id', ondelete='CASCADE')
    is_demo: bool = Field(default=False, description='Demo/seed resource, excluded from the public API')
    created_dt: datetime = UTCDatetimeField(now_add=True, index=True)
    updated_dt: Optional[datetime] = UTCDatetimeField(auto_now=True)


class ExampleResource(_ExampleResource, table=True):
    """The example resource table. One resource belongs to exactly one organization."""

    id: Optional[int] = Field(default=None, primary_key=True)

    organization: 'Organization' = Relationship(back_populates='example_resources')
    participants: List['ExampleResourceParticipant'] = Relationship(
        back_populates='example_resource', cascade_delete=True
    )

    @classmethod
    def request_query(cls, request: Request, db: DBSession = None) -> SelectOfScalar['ExampleResource']:  # ty: ignore[invalid-method-override, invalid-parameter-default]
        """Resources the requesting user may see.

        Superadmins see every resource; everyone else sees only their own organization's.
        Tenant scoping lives here so endpoints never re-implement the ``organization_id``
        filter and risk leaking another tenant's data.
        """
        user = request.state.user
        if user.is_superadmin:
            return select(ExampleResource)
        return select(ExampleResource).where(ExampleResource.organization_id == user.organization_id)

    @classmethod
    def query_for_pub_api(cls, organization_id: int) -> SelectOfScalar['ExampleResource']:
        """Org-scoped public-API query: an org's own non-demo resources.

        Excludes demo/seed rows — the public API exposes genuine resource data only.
        """
        return select(ExampleResource).where(
            ExampleResource.organization_id == organization_id,
            ExampleResource.is_demo == False,  # noqa: E712
        )


class ExampleResourceBasic(_ExampleResource):
    """The example resource as returned from create/update — carries the id, no relations."""

    id: int


class ExampleResourceList(ExampleResourceBasic):
    """A resource in a list response: the basic shape plus a participant count and its org."""

    participant_count: int = Field(description='Number of participants attached to the resource')
    organization: OrganizationBasic


class _ExampleResourceParticipant(AppModel):
    """Shared fields for a participant attached to an example resource."""

    name: str
    email: str


class ExampleResourceParticipant(_ExampleResourceParticipant, table=True):
    """A participant (a contact/member) attached to an example resource."""

    id: Optional[int] = Field(default=None, primary_key=True)
    example_resource_id: int = FKField('exampleresource.id', ondelete='CASCADE')

    example_resource: 'ExampleResource' = Relationship(back_populates='participants')

    @classmethod
    def request_query(cls, request: Request, db: DBSession = None) -> SelectOfScalar['ExampleResourceParticipant']:  # ty: ignore[invalid-method-override, invalid-parameter-default]
        """Participants the requesting user may see, scoped via their parent resource's org."""
        user = request.state.user
        query = select(ExampleResourceParticipant).join(ExampleResource)
        if user.is_superadmin:
            return query
        return query.where(ExampleResource.organization_id == user.organization_id)

    @classmethod
    def query_for_pub_api(cls, organization_id: int) -> SelectOfScalar['ExampleResourceParticipant']:
        """Org-scoped public-API query: participants of an org's own non-demo resources."""
        return (
            select(ExampleResourceParticipant)
            .join(ExampleResource)
            .where(
                ExampleResource.organization_id == organization_id,
                ExampleResource.is_demo == False,  # noqa: E712
            )
        )


class ExampleResourceParticipantBasic(_ExampleResourceParticipant):
    """A participant as returned in responses — carries the id."""

    id: int


class ExampleResourceDetail(ExampleResourceBasic):
    """A resource detail: the basic shape plus its full list of participants."""

    participants: List[ExampleResourceParticipantBasic] = Field(default_factory=list)
