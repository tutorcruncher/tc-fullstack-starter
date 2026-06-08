from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.common.fields import EnumField, FKField, UTCDatetimeField
from app.common.models import AppModel
from app.core.database import DBSession

if TYPE_CHECKING:  # pragma: no cover
    from app.organization.models.organization import Organization


class UserRole(str, Enum):
    """A user's role within their organization.

    ``ADMIN`` can manage the organization (e.g. mint API keys); ``MEMBER`` is a regular
    authenticated user. Cross-cutting elevated access is the separate ``is_superadmin``
    flag, not a role — so a superadmin can also carry a normal role. Extend this enum (and
    ``app.auth.permissions``) to add finer-grained roles.
    """

    ADMIN = 'admin'
    MEMBER = 'member'


class _User(AppModel):
    """Shared, non-secret user fields.

    ``hashed_password`` is intentionally absent here and declared only on the ``User`` table
    class so it can never leak through a response schema that inherits from ``_User``.
    """

    first_name: Optional[str] = None
    last_name: str
    email: EmailStr = Field(description='Login identifier, unique across all users')
    role: UserRole = EnumField(UserRole)
    is_superadmin: bool = Field(default=False, description='Cross-organization elevated access')
    is_demo: bool = Field(default=False, description='Demo/seed user, excluded from the public API')
    organization_id: int = FKField('organization.id', ondelete='CASCADE')
    created_dt: datetime = UTCDatetimeField(now_add=True, index=True)
    updated_dt: Optional[datetime] = UTCDatetimeField(auto_now=True)
    deleted_dt: Optional[datetime] = UTCDatetimeField(
        default=None, exclude=True, description='When the user was anonymised/deleted'
    )

    @property
    def full_name(self) -> str:
        """Return the user's full name, joining first and last name when both are present."""
        parts = [p for p in (self.first_name, self.last_name) if p]
        return ' '.join(parts)

    @property
    def is_admin(self) -> bool:
        """Whether the user has the ADMIN role (does not account for superadmin)."""
        return self.role == UserRole.ADMIN


class User(_User, table=True):
    """The user table. One user belongs to exactly one organization.

    Multi-organization membership is an intentional non-goal of the starter — model it as a
    ``UserOrganization`` join table and scope ``request_query`` to the set of org ids if you
    need it. The single ``organization_id`` keeps tenant scoping a one-line WHERE clause.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, description='Login identifier, unique across all users')
    hashed_password: str = Field(description='Argon2 password hash; never serialised to a response')

    organization: 'Organization' = Relationship(back_populates='users')

    @classmethod
    def request_query(cls, request: Request, db: DBSession = None) -> SelectOfScalar['User']:  # ty: ignore[invalid-method-override, invalid-parameter-default]
        """Users the requesting user may see.

        Superadmins see every user; everyone else sees only the non-deleted users in their
        own organization. Tenant scoping lives here so endpoints never re-implement the
        ``organization_id`` filter and risk leaking another tenant's users.
        """
        user = request.state.user
        if user.is_superadmin:
            return select(User)
        return select(User).where(
            User.organization_id == user.organization_id,
            User.deleted_dt == None,  # noqa: E711
        )

    @classmethod
    def query_for_pub_api(cls, organization_id: int) -> SelectOfScalar['User']:
        """Org-scoped public-API query: an org's own real users.

        Excludes soft-deleted users, superadmins (internal/staff) and demo/seed rows — the
        public API exposes an organization's genuine member data only.
        """
        return select(User).where(
            User.organization_id == organization_id,
            User.deleted_dt == None,  # noqa: E711
            User.is_superadmin == False,  # noqa: E712
            User.is_demo == False,  # noqa: E712
        )


class UserBasic(_User):
    """Public-facing user shape used in responses — carries the id but never the password hash."""

    id: int
