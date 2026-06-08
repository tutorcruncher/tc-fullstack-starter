from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.common.fields import EnumField, UTCDatetimeField
from app.common.models import AppModel
from app.core.database import DBSession

if TYPE_CHECKING:  # pragma: no cover
    from app.auth.models import User
    from app.example_domain.models.example_resource import ExampleResource
    from app.organization.models.api_key import OrganizationApiKey


class BillingStatus(str, Enum):
    """An organization's billing state, used to gate data access (internal and public API)."""

    TRIAL = 'trial'
    ACTIVE = 'active'
    EXPIRED = 'expired'
    ALWAYS_FREE = 'always_free'


class _Organization(AppModel):
    """Shared fields for the tenant model. One organization owns many users and resources."""

    name: str
    billing_status: BillingStatus = EnumField(BillingStatus, default=BillingStatus.TRIAL)
    trial_expiry_dt: Optional[datetime] = UTCDatetimeField(
        default=None, description='When a TRIAL organization stops counting as active'
    )
    is_demo: bool = Field(default=False, description='Demo/seed organization')
    created_dt: datetime = UTCDatetimeField(now_add=True)
    updated_dt: Optional[datetime] = UTCDatetimeField(auto_now=True)


class Organization(_Organization, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    users: List['User'] = Relationship(back_populates='organization', cascade_delete=True)
    api_keys: List['OrganizationApiKey'] = Relationship(back_populates='organization', cascade_delete=True)
    example_resources: List['ExampleResource'] = Relationship(back_populates='organization', cascade_delete=True)

    @classmethod
    def request_query(cls, request: Request, db: DBSession = None) -> SelectOfScalar['Organization']:  # ty: ignore[invalid-method-override, invalid-parameter-default]
        """Organizations the requesting user may see.

        Superadmins see every organization; everyone else sees only their own.
        """
        user = request.state.user
        if user.is_superadmin:
            return select(Organization)
        return select(Organization).where(Organization.id == user.organization_id)

    @classmethod
    def query_for_pub_api(cls, organization_id: int) -> SelectOfScalar['Organization']:
        """Public-API query: the single organization the API key belongs to."""
        return select(Organization).where(Organization.id == organization_id)


class OrganizationBasic(_Organization):
    """Public-facing organization shape with the id."""

    id: int
