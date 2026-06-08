"""Tests for the org-scoping classmethods on the ``Organization`` and ``OrganizationApiKey`` models."""

from types import SimpleNamespace

from app.core.database import DBSession
from app.organization.models.api_key import OrganizationApiKey
from app.organization.models.organization import Organization
from tests.organization.factories import (
    AdminFactory,
    MemberFactory,
    OrganizationApiKeyFactory,
    OrganizationFactory,
)


class TestOrganizationRequestQuery:
    def test_request_query_superadmin_sees_all_organizations(self, db: DBSession):
        """A superadmin's request_query is unscoped and returns every organization."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        superadmin = AdminFactory.create_with_db(db, organization=org_a, is_superadmin=True)

        results = db.exec(Organization.request_query(_request_for(superadmin))).all()

        assert {org_a.id, org_b.id} <= {o.id for o in results}

    def test_request_query_member_scoped_to_own_organization(self, db: DBSession):
        """A non-superadmin's request_query returns only their own organization."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        OrganizationFactory.create_with_db(db, name='B')
        member = MemberFactory.create_with_db(db, organization=org_a)

        results = db.exec(Organization.request_query(_request_for(member))).all()

        assert [o.id for o in results] == [org_a.id]


class TestOrganizationQueryForPubApi:
    def test_query_for_pub_api_returns_only_the_key_organization(self, db: DBSession):
        """The public query returns only the single organization the API key belongs to."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        OrganizationFactory.create_with_db(db, name='B')

        results = db.exec(Organization.query_for_pub_api(org_a.id)).all()

        assert [o.id for o in results] == [org_a.id]


class TestOrganizationApiKeyRequestQuery:
    def test_request_query_superadmin_sees_all_keys(self, db: DBSession):
        """A superadmin's request_query is unscoped and returns keys across every organization."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        key_a, _ = OrganizationApiKeyFactory.create_with_db(db, organization=org_a)
        key_b, _ = OrganizationApiKeyFactory.create_with_db(db, organization=org_b)
        superadmin = AdminFactory.create_with_db(db, organization=org_a, is_superadmin=True)

        results = db.exec(OrganizationApiKey.request_query(_request_for(superadmin))).all()

        assert {key_a.id, key_b.id} == {k.id for k in results}

    def test_request_query_member_scoped_to_own_organization(self, db: DBSession):
        """A non-superadmin's request_query returns only their own organization's keys."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        own, _ = OrganizationApiKeyFactory.create_with_db(db, organization=org_a)
        OrganizationApiKeyFactory.create_with_db(db, organization=org_b)
        member = MemberFactory.create_with_db(db, organization=org_a)

        results = db.exec(OrganizationApiKey.request_query(_request_for(member))).all()

        assert [k.id for k in results] == [own.id]


class TestOrganizationApiKeyQueryForPubApi:
    def test_query_for_pub_api_returns_only_the_authenticated_orgs_keys(self, db: DBSession):
        """The public query returns only the keys belonging to the authenticated organization."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        own, _ = OrganizationApiKeyFactory.create_with_db(db, organization=org_a)
        OrganizationApiKeyFactory.create_with_db(db, organization=org_b)

        results = db.exec(OrganizationApiKey.query_for_pub_api(org_a.id)).all()

        assert [k.id for k in results] == [own.id]


def _request_for(user):
    """Build a minimal request-like object carrying ``user`` for the request_query classmethods."""
    return SimpleNamespace(state=SimpleNamespace(user=user))
