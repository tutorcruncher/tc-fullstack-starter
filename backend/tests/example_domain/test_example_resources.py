from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from sqlmodel import select

from app.example_domain.models.example_resource import (
    ExampleResource,
    ExampleResourceParticipant,
    ResourceStatus,
)
from tests.conftest import AuthenticatedTestClient, count_queries
from tests.example_domain.factories import ExampleResourceFactory, ExampleResourceParticipantFactory
from tests.organization.factories import AdminFactory, MemberFactory, OrganizationFactory


def _iso(dt):
    """Render a datetime the way FastAPI serialises it in a JSON response."""
    return dt.isoformat().replace('+00:00', 'Z')


def _organization_dict(organization):
    """The full ``OrganizationBasic`` shape as it appears nested in a list response."""
    return {
        'id': organization.id,
        'name': organization.name,
        'billing_status': organization.billing_status.value,
        'trial_expiry_dt': organization.trial_expiry_dt,
        'is_demo': organization.is_demo,
        'created_dt': _iso(organization.created_dt),
        'updated_dt': _iso(organization.updated_dt),
    }


class TestListExampleResources:
    def test_list_empty(self, auth_client: AuthenticatedTestClient, db):
        """An organization with no resources returns an empty paginated response."""
        r = auth_client.get(auth_client.app.url_path_for('example-resource-list'))
        assert r.status_code == 200
        assert r.json() == {'items': [], 'total': 0, 'page': 1, 'page_size': 50}

    def test_list_returns_full_structure(self, auth_client: AuthenticatedTestClient, db):
        """The list returns the full ExampleResourceList structure with participant counts."""
        organization = auth_client.user.organization
        resource = ExampleResourceFactory.create_with_db(
            db, organization=organization, name='Alpha', description='First', status=ResourceStatus.ACTIVE
        )
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource)
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource)

        r = auth_client.get(auth_client.app.url_path_for('example-resource-list'))

        assert r.status_code == 200
        assert r.json() == {
            'items': [
                {
                    'id': resource.id,
                    'name': 'Alpha',
                    'description': 'First',
                    'status': 'active',
                    'organization_id': organization.id,
                    'is_demo': False,
                    'created_dt': _iso(resource.created_dt),
                    'updated_dt': _iso(resource.updated_dt),
                    'participant_count': 2,
                    'organization': _organization_dict(organization),
                },
            ],
            'total': 1,
            'page': 1,
            'page_size': 50,
        }

    def test_list_excludes_other_organizations(self, auth_client: AuthenticatedTestClient, db):
        """A user only sees their own organization's resources."""
        ExampleResourceFactory.create_with_db(db, organization=auth_client.user.organization, name='Mine')
        other_org = OrganizationFactory.create_with_db(db, name='Other Org')
        ExampleResourceFactory.create_with_db(db, organization=other_org, name='Theirs')

        r = auth_client.get(auth_client.app.url_path_for('example-resource-list'))

        data = r.json()
        assert data['total'] == 1
        assert [item['name'] for item in data['items']] == ['Mine']

    def test_list_filter_by_search(self, auth_client: AuthenticatedTestClient, db):
        """The search filter matches the resource name case-insensitively."""
        organization = auth_client.user.organization
        match = ExampleResourceFactory.create_with_db(db, organization=organization, name='Zebra')
        ExampleResourceFactory.create_with_db(db, organization=organization, name='Other')

        r = auth_client.get(auth_client.app.url_path_for('example-resource-list'), params={'search': 'zeb'})

        data = r.json()
        assert data['total'] == 1
        assert data['items'][0]['id'] == match.id

    def test_list_filter_created_range(self, auth_client: AuthenticatedTestClient, db):
        """created_from / created_to bound the list by creation date."""
        organization = auth_client.user.organization
        resource = ExampleResourceFactory.create_with_db(db, organization=organization)
        stored = db.exec(select(ExampleResource).where(ExampleResource.id == resource.id)).one()
        stored.created_dt = datetime(2024, 1, 1, tzinfo=UTC)
        db.add(stored)
        db.commit()

        in_range = auth_client.get(
            auth_client.app.url_path_for('example-resource-list'),
            params={'created_from': '2023-12-01T00:00:00Z', 'created_to': '2024-02-01T00:00:00Z'},
        )
        out_of_range = auth_client.get(
            auth_client.app.url_path_for('example-resource-list'), params={'created_from': '2024-06-01T00:00:00Z'}
        )

        assert in_range.json()['total'] == 1
        assert out_of_range.json()['total'] == 0

    def test_list_filter_by_organization_id(self, auth_client: AuthenticatedTestClient, db):
        """The organization_id filter narrows the list to a single organization."""
        organization = auth_client.user.organization
        match = ExampleResourceFactory.create_with_db(db, organization=organization, name='Mine')

        r = auth_client.get(
            auth_client.app.url_path_for('example-resource-list'), params={'organization_id': organization.id}
        )

        data = r.json()
        assert data['total'] == 1
        assert data['items'][0]['id'] == match.id

    def test_list_pagination(self, auth_client: AuthenticatedTestClient, db):
        """page_size and page slice the list."""
        organization = auth_client.user.organization
        for _ in range(3):
            ExampleResourceFactory.create_with_db(db, organization=organization)

        page1 = auth_client.get(
            auth_client.app.url_path_for('example-resource-list'), params={'page_size': 2, 'page': 1}
        )
        page2 = auth_client.get(
            auth_client.app.url_path_for('example-resource-list'), params={'page_size': 2, 'page': 2}
        )

        assert page1.json()['total'] == 3
        assert len(page1.json()['items']) == 2
        assert len(page2.json()['items']) == 1

    def test_list_query_count_constant_across_page_size(self, auth_client: AuthenticatedTestClient, db):
        """The query count is identical for page_size=1 and page_size=200 (no N+1)."""
        organization = auth_client.user.organization
        for _ in range(5):
            resource = ExampleResourceFactory.create_with_db(db, organization=organization)
            ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource)
            ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource)

        with count_queries(db) as small:
            auth_client.get(auth_client.app.url_path_for('example-resource-list'), params={'page_size': 1})
        with count_queries(db) as large:
            auth_client.get(auth_client.app.url_path_for('example-resource-list'), params={'page_size': 200})

        assert small.count == large.count

    def test_unauthenticated_cannot_list(self, client, db):
        """An unauthenticated request is rejected with 401."""
        r = client.get(client.app.url_path_for('example-resource-list'))
        assert r.status_code == 401
        assert r.json() == {'detail': 'Not authenticated'}


class TestExampleResourceListOptions:
    def test_options_returns_filter_and_order_metadata(self, auth_client: AuthenticatedTestClient, db):
        """OPTIONS merges the filter and ordering metadata for the list endpoint."""
        organization = auth_client.user.organization

        r = auth_client.options(auth_client.app.url_path_for('example-resource-list-options'))

        assert r.status_code == 200
        assert r.json() == {
            'search': {'type': 'str', 'required': False},
            'created_from': {'type': 'datetime', 'required': False},
            'created_to': {'type': 'datetime', 'required': False},
            'organization_id': {
                'type': 'int',
                'required': False,
                'choices': [{'id': organization.id, 'name': organization.name}],
            },
            'order_by': {
                'type': 'str',
                'required': False,
                'choices': [{'id': 'name', 'name': 'name'}, {'id': 'created_dt', 'name': 'created_dt'}],
                'default': 'name',
            },
            'order_direction': {
                'type': 'OrderDirection',
                'required': False,
                'choices': [{'id': 'asc', 'name': 'asc'}, {'id': 'desc', 'name': 'desc'}],
                'default': 'desc',
            },
        }


class TestExampleResourceDetail:
    def test_detail_returns_full_structure_with_participants(self, auth_client: AuthenticatedTestClient, db):
        """Detail returns the full ExampleResourceDetail structure with its participants."""
        organization = auth_client.user.organization
        resource = ExampleResourceFactory.create_with_db(db, organization=organization, name='Beta')
        participant = ExampleResourceParticipantFactory.create_with_db(
            db, example_resource=resource, name='Pat', email='pat@example.com'
        )

        r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', example_resource_id=resource.id))

        assert r.status_code == 200
        assert r.json() == {
            'id': resource.id,
            'name': 'Beta',
            'description': None,
            'status': 'draft',
            'organization_id': organization.id,
            'is_demo': False,
            'created_dt': _iso(resource.created_dt),
            'updated_dt': _iso(resource.updated_dt),
            'participants': [{'id': participant.id, 'name': 'Pat', 'email': 'pat@example.com'}],
        }

    def test_detail_cross_tenant_returns_404(self, auth_client: AuthenticatedTestClient, db):
        """A resource in another organization returns 404 (not 403) so existence isn't leaked."""
        other_org = OrganizationFactory.create_with_db(db, name='Other Org')
        other = ExampleResourceFactory.create_with_db(db, organization=other_org)

        r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', example_resource_id=other.id))

        assert r.status_code == 404
        assert r.json() == {'detail': 'Example resource not found'}

    def test_detail_missing_returns_404(self, auth_client: AuthenticatedTestClient, db):
        """A non-existent id returns 404."""
        r = auth_client.get(auth_client.app.url_path_for('example-resource-detail', example_resource_id=999999))
        assert r.status_code == 404
        assert r.json() == {'detail': 'Example resource not found'}


class TestCreateExampleResource:
    @patch('app.example_domain.api.example_resources.process_example_resource.delay')
    def test_create_returns_basic_and_dispatches_task(self, mock_delay, auth_client: AuthenticatedTestClient, db):
        """Create returns the basic shape, persists the resource, and dispatches the task."""
        r = auth_client.post(
            auth_client.app.url_path_for('create-example-resource'),
            json={'name': 'Gamma', 'description': 'New', 'status': 'active'},
        )

        assert r.status_code == 201
        stored = db.exec(
            select(ExampleResource).where(ExampleResource.organization_id == auth_client.user.organization_id)
        ).one()
        assert r.json() == {
            'id': stored.id,
            'name': 'Gamma',
            'description': 'New',
            'status': 'active',
            'organization_id': auth_client.user.organization_id,
            'is_demo': False,
            'created_dt': _iso(stored.created_dt),
            'updated_dt': _iso(stored.updated_dt),
        }
        mock_delay.assert_called_once_with(stored.id)

    def test_create_dispatches_task_eagerly(self, auth_client: AuthenticatedTestClient, db):
        """With eager Celery the dispatched task runs synchronously and processes the resource."""
        with patch('app.example_domain.tasks.logger') as mock_logger:
            r = auth_client.post(
                auth_client.app.url_path_for('create-example-resource'),
                json={'name': 'Delta', 'status': 'draft'},
            )

        assert r.status_code == 201
        mock_logger.info.assert_called_once()

    def test_create_requires_name(self, auth_client: AuthenticatedTestClient, db):
        """A blank name is rejected by validation with 422."""
        r = auth_client.post(auth_client.app.url_path_for('create-example-resource'), json={'name': ''})
        assert r.status_code == 422


class TestUpdateExampleResource:
    def test_update_changes_fields(self, auth_client: AuthenticatedTestClient, db):
        """Update mutates the resource and returns the basic shape."""
        resource = ExampleResourceFactory.create_with_db(db, organization=auth_client.user.organization, name='Old')

        r = auth_client.put(
            auth_client.app.url_path_for('update-example-resource', example_resource_id=resource.id),
            json={'name': 'New', 'description': 'Updated', 'status': 'archived'},
        )

        assert r.status_code == 200
        data = r.json()
        assert data['name'] == 'New'
        assert data['description'] == 'Updated'
        assert data['status'] == 'archived'

    def test_update_cross_tenant_returns_404(self, auth_client: AuthenticatedTestClient, db):
        """Updating another org's resource returns 404 and leaves it intact."""
        other_org = OrganizationFactory.create_with_db(db, name='Other Org')
        other = ExampleResourceFactory.create_with_db(db, organization=other_org, name='Theirs')

        r = auth_client.put(
            auth_client.app.url_path_for('update-example-resource', example_resource_id=other.id),
            json={'name': 'Hijacked', 'status': 'active'},
        )

        assert r.status_code == 404


class TestDeleteExampleResource:
    def test_delete_own_resource(self, auth_client: AuthenticatedTestClient, db):
        """An owner can delete their resource, which is then gone from the DB."""
        resource = ExampleResourceFactory.create_with_db(db, organization=auth_client.user.organization)

        r = auth_client.delete(auth_client.app.url_path_for('delete-example-resource', example_resource_id=resource.id))

        assert r.status_code == 204
        assert not db.exists(ExampleResource, id=resource.id)

    def test_delete_cross_tenant_returns_404(self, auth_client: AuthenticatedTestClient, db):
        """Deleting another org's resource returns 404 and leaves it intact."""
        other_org = OrganizationFactory.create_with_db(db, name='Other Org')
        other = ExampleResourceFactory.create_with_db(db, organization=other_org)

        r = auth_client.delete(auth_client.app.url_path_for('delete-example-resource', example_resource_id=other.id))

        assert r.status_code == 404
        assert db.exists(ExampleResource, id=other.id)

    def test_delete_missing_returns_404(self, auth_client: AuthenticatedTestClient, db):
        """Deleting a non-existent resource returns 404."""
        r = auth_client.delete(auth_client.app.url_path_for('delete-example-resource', example_resource_id=999999))
        assert r.status_code == 404


class TestExampleResourceModelQueries:
    """Tests for the org-scoping classmethods on the domain models."""

    def test_request_query_superadmin_sees_all_organizations(self, db):
        """A superadmin's request_query is unscoped and returns every organization's resources."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        ExampleResourceFactory.create_with_db(db, organization=org_a)
        ExampleResourceFactory.create_with_db(db, organization=org_b)
        superadmin = AdminFactory.create_with_db(db, organization=org_a, is_superadmin=True)

        results = db.exec(ExampleResource.request_query(_request_for(superadmin))).all()

        assert {r.organization_id for r in results} == {org_a.id, org_b.id}

    def test_request_query_member_scoped_to_own_organization(self, db):
        """A non-superadmin's request_query returns only their own organization's resources."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        own = ExampleResourceFactory.create_with_db(db, organization=org_a)
        ExampleResourceFactory.create_with_db(db, organization=org_b)
        member = MemberFactory.create_with_db(db, organization=org_a)

        results = db.exec(ExampleResource.request_query(_request_for(member))).all()

        assert [r.id for r in results] == [own.id]

    def test_participant_request_query_scoped_to_own_organization(self, db):
        """The participant request_query joins the parent resource and scopes by organization."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        resource_a = ExampleResourceFactory.create_with_db(db, organization=org_a)
        resource_b = ExampleResourceFactory.create_with_db(db, organization=org_b)
        own = ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource_a)
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource_b)
        member = MemberFactory.create_with_db(db, organization=org_a)

        results = db.exec(ExampleResourceParticipant.request_query(_request_for(member))).all()

        assert [p.id for p in results] == [own.id]

    def test_participant_request_query_superadmin_sees_all(self, db):
        """A superadmin's participant request_query returns participants across organizations."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        resource_a = ExampleResourceFactory.create_with_db(db, organization=org_a)
        resource_b = ExampleResourceFactory.create_with_db(db, organization=org_b)
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource_a)
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource_b)
        superadmin = AdminFactory.create_with_db(db, organization=org_a, is_superadmin=True)

        results = db.exec(ExampleResourceParticipant.request_query(_request_for(superadmin))).all()

        assert len(results) == 2

    def test_participant_query_for_pub_api_excludes_demo_and_other_orgs(self, db):
        """The participant public query is org-scoped and excludes demo resources' participants."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        real = ExampleResourceFactory.create_with_db(db, organization=org_a)
        demo = ExampleResourceFactory.create_with_db(db, organization=org_a, is_demo=True)
        other = ExampleResourceFactory.create_with_db(db, organization=org_b)
        own = ExampleResourceParticipantFactory.create_with_db(db, example_resource=real)
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=demo)
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=other)

        results = db.exec(ExampleResourceParticipant.query_for_pub_api(org_a.id)).all()

        assert [p.id for p in results] == [own.id]


def _request_for(user):
    """Build a minimal request-like object carrying ``user`` for the request_query classmethods."""
    return SimpleNamespace(state=SimpleNamespace(user=user))
