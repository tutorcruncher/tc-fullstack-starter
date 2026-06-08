from typing import Optional

from sqlmodel import SQLModel
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.core.database import DBSession


class AppModel(SQLModel):
    """Abstract base for all domain models.

    Every concrete table model overrides both ``request_query`` (internal, role/tenant
    scoped from ``request.state.user``) and ``query_for_pub_api`` (public, org-scoped from
    an API key). Centralising access control on the model keeps tenant/role filters out of
    individual endpoints, where they tend to drift and leak.
    """

    @classmethod
    def request_query(cls, request: Request, db: Optional[DBSession] = None) -> SelectOfScalar:
        """Return the query of all rows the current user may access.

        Should return a Select object. ``db`` is passed through in case an override needs a
        separate query to build the scope. Uses ``request.state.user`` to determine access;
        superadmins see everything, otherwise rows are scoped to the user's organization.
        """
        raise NotImplementedError

    @classmethod
    def query_for_pub_api(cls, organization_id: int) -> SelectOfScalar:
        """Return the org-scoped public-API query for a model.

        Unlike ``request_query`` this is **not** role-scoped — the public API has no user; a
        per-org key returns *all* of that org's (non-demo, non-deleted) data. Excludes
        soft-deleted/anonymised users and demo/seed rows. Returns a Select object.
        """
        raise NotImplementedError
