"""Tests for the org-scoping classmethods and helpers on the ``User`` model."""

from datetime import UTC, datetime
from types import SimpleNamespace

from app.auth.models import User
from app.core.database import DBSession
from tests.organization.factories import AdminFactory, MemberFactory, OrganizationFactory


class TestUserFullName:
    def test_full_name_joins_first_and_last(self):
        """full_name joins the first and last name with a space when both are present."""
        user = User(first_name='Alice', last_name='Smith', email='alice@test.com', role='member', organization_id=1)
        assert user.full_name == 'Alice Smith'

    def test_full_name_omits_missing_first_name(self):
        """full_name drops a missing first name and returns just the last name."""
        user = User(first_name=None, last_name='Smith', email='smith@test.com', role='member', organization_id=1)
        assert user.full_name == 'Smith'


class TestUserRequestQuery:
    def test_request_query_superadmin_sees_all_users(self, db: DBSession):
        """A superadmin's request_query is unscoped and returns users across every organization."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        member_a = MemberFactory.create_with_db(db, organization=org_a)
        member_b = MemberFactory.create_with_db(db, organization=org_b)
        superadmin = AdminFactory.create_with_db(db, organization=org_a, is_superadmin=True)

        results = db.exec(User.request_query(_request_for(superadmin))).all()

        assert {member_a.id, member_b.id, superadmin.id} <= {u.id for u in results}

    def test_request_query_member_scoped_to_own_organization(self, db: DBSession):
        """A non-superadmin's request_query returns only their own organization's non-deleted users."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        own = MemberFactory.create_with_db(db, organization=org_a)
        MemberFactory.create_with_db(db, organization=org_b)

        results = db.exec(User.request_query(_request_for(own))).all()

        assert {u.organization_id for u in results} == {org_a.id}
        assert own.id in {u.id for u in results}

    def test_request_query_member_excludes_deleted_users(self, db: DBSession):
        """A non-superadmin's request_query excludes soft-deleted users in their organization."""
        org = OrganizationFactory.create_with_db(db, name='A')
        active = MemberFactory.create_with_db(db, organization=org)
        deleted = MemberFactory.create_with_db(db, organization=org, deleted_dt=datetime.now(UTC))

        results = db.exec(User.request_query(_request_for(active))).all()

        result_ids = {u.id for u in results}
        assert active.id in result_ids
        assert deleted.id not in result_ids


class TestUserQueryForPubApi:
    def test_query_for_pub_api_excludes_demo_superadmin_deleted_and_other_orgs(self, db: DBSession):
        """The public query returns an org's real members, excluding demo, superadmin and deleted users."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        real = MemberFactory.create_with_db(db, organization=org_a)
        MemberFactory.create_with_db(db, organization=org_a, is_demo=True)
        MemberFactory.create_with_db(db, organization=org_a, is_superadmin=True)
        MemberFactory.create_with_db(db, organization=org_a, deleted_dt=datetime.now(UTC))
        MemberFactory.create_with_db(db, organization=org_b)

        results = db.exec(User.query_for_pub_api(org_a.id)).all()

        assert [u.id for u in results] == [real.id]


def _request_for(user):
    """Build a minimal request-like object carrying ``user`` for the request_query classmethods."""
    return SimpleNamespace(state=SimpleNamespace(user=user))
