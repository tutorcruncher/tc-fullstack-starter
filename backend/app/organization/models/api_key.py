from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.common.fields import FKField, UTCDatetimeField
from app.common.models import AppModel
from app.core.database import DBSession

if TYPE_CHECKING:  # pragma: no cover
    from app.organization.models.organization import Organization


class _OrganizationApiKey(AppModel):
    """Shared, non-secret fields for a per-organization public API key."""

    name: str = Field(description='Human-readable label for the key, set by the admin')
    last4: str = Field(description='Last 4 characters of the token, for display only')

    created_dt: datetime = UTCDatetimeField(now_add=True)
    last_used_dt: Optional[datetime] = UTCDatetimeField(
        default=None, description='Last time the key authenticated a request (best-effort, throttled)'
    )


class OrganizationApiKey(_OrganizationApiKey, table=True):
    """A per-organization API key for the read-only public API.

    The full token (``app_live_<random>``) is shown to the admin exactly once at creation.
    We only persist:

    * ``hashed_key`` — the SHA-256 hex digest of the full token; unique and indexed. Auth is
      a single O(1) lookup by ``hash_api_key(presented_token)``. It lives **only** on this
      table class so it can never leak through a response schema.
    * ``last4`` — the final 4 chars of the token, for display in the management UI.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    organization_id: int = FKField('organization.id', ondelete='CASCADE')
    hashed_key: str = Field(unique=True, index=True, description='SHA-256 hex digest of the full token')

    organization: 'Organization' = Relationship(back_populates='api_keys')

    @classmethod
    def request_query(cls, request: Request, db: DBSession = None) -> SelectOfScalar['OrganizationApiKey']:  # ty: ignore[invalid-method-override, invalid-parameter-default]
        """API keys scoped to the requesting user's organization.

        Superadmins see every key; everyone else sees only their own organization's keys.
        """
        user = request.state.user
        if user.is_superadmin:
            return select(OrganizationApiKey)
        return select(OrganizationApiKey).where(OrganizationApiKey.organization_id == user.organization_id)

    @classmethod
    def query_for_pub_api(cls, organization_id: int) -> SelectOfScalar['OrganizationApiKey']:
        """Public-API query: keys belonging to the authenticated organization."""
        return select(OrganizationApiKey).where(OrganizationApiKey.organization_id == organization_id)


class OrganizationApiKeyBasic(_OrganizationApiKey):
    """An API key as returned to admins — never includes the token or its hash."""

    id: int


class OrganizationApiKeyCreateResponse(OrganizationApiKeyBasic):
    """Create response — exposes the full token exactly once, never retrievable again."""

    key: str = Field(description='The full API key. Shown once at creation and never again — store it securely.')
