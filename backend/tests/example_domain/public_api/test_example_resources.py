from datetime import UTC, datetime

import pytest
from sqlmodel import select

from app.example_domain.models.example_resource import ExampleResource, ResourceStatus
from tests.conftest import count_queries
from tests.example_domain.factories import ExampleResourceFactory, ExampleResourceParticipantFactory
from tests.organization.factories import OrganizationApiKeyFactory, OrganizationFactory


def _iso(dt):
    """Render a datetime the way FastAPI serialises it in a JSON response."""
    return dt.isoformat().replace('+00:00', 'Z')


@pytest.fixture(name='org_with_key')
def org_with_key_fixture(db, public_api_client):
    """Factory returning ``(organization, ApiKeyTestClient)`` for a fresh org + key."""
    make_client, _ = public_api_client

    def _make(**org_kwargs):
        organization = OrganizationFactory.create_with_db(db, **org_kwargs)
        _, full_key = OrganizationApiKeyFactory.create_with_db(db, organization=organization)
        return organization, make_client(full_key)

    return _make


class TestPublicExampleResourceList:
    def test_list_returns_full_structure(self, public_api_client, db, org_with_key):
        """The public list returns the full PublicExampleResourceList structure with counts."""
        organization, client = org_with_key()
        resource = ExampleResourceFactory.create_with_db(
            db, organization=organization, name='Alpha', description='First', status=ResourceStatus.ACTIVE
        )
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource)
        ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource)

        r = client.get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 200
        assert r.json() == {
            'items': [
                {
                    'id': resource.id,
                    'name': 'Alpha',
                    'description': 'First',
                    'status': 'active',
                    'organization_id': organization.id,
                    'created_dt': _iso(resource.created_dt),
                    'updated_dt': _iso(resource.updated_dt),
                    'participant_count': 2,
                },
            ],
            'total': 1,
            'page': 1,
            'page_size': 50,
        }

    def test_list_empty(self, public_api_client, db, org_with_key):
        """An organization with no resources returns an empty paginated response."""
        _organization, client = org_with_key()

        r = client.get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 200
        assert r.json() == {'items': [], 'total': 0, 'page': 1, 'page_size': 50}

    def test_list_filter_by_search(self, public_api_client, db, org_with_key):
        """The public search filter matches the resource name case-insensitively."""
        organization, client = org_with_key()
        match = ExampleResourceFactory.create_with_db(db, organization=organization, name='Zebra')
        ExampleResourceFactory.create_with_db(db, organization=organization, name='Other')

        r = client.get(client.app.url_path_for('public-example-resource-list'), params={'search': 'zeb'})

        data = r.json()
        assert data['total'] == 1
        assert data['items'][0]['id'] == match.id

    def test_list_excludes_demo_resources(self, public_api_client, db, org_with_key):
        """Demo/seed resources are excluded from the public list."""
        organization, client = org_with_key()
        ExampleResourceFactory.create_with_db(db, organization=organization, name='Real')
        ExampleResourceFactory.create_with_db(db, organization=organization, name='Demo', is_demo=True)

        r = client.get(client.app.url_path_for('public-example-resource-list'))

        data = r.json()
        assert data['total'] == 1
        assert data['items'][0]['name'] == 'Real'

    def test_list_cross_tenant_isolation(self, public_api_client, db, org_with_key):
        """An org-A key never sees org-B resources."""
        organization_a, client_a = org_with_key()
        organization_b = OrganizationFactory.create_with_db(db)
        ExampleResourceFactory.create_with_db(db, organization=organization_b, name='OrgB')
        own = ExampleResourceFactory.create_with_db(db, organization=organization_a, name='OrgA')

        r = client_a.get(client_a.app.url_path_for('public-example-resource-list'))

        data = r.json()
        assert data['total'] == 1
        assert data['items'][0]['id'] == own.id

    def test_list_filter_updated_since(self, public_api_client, db, org_with_key):
        """updated_since returns only resources updated on/after the cutoff."""
        organization, client = org_with_key()
        old = ExampleResourceFactory.create_with_db(db, organization=organization, name='Old')
        recent = ExampleResourceFactory.create_with_db(db, organization=organization, name='Recent')
        old_resource = db.exec(select(ExampleResource).where(ExampleResource.id == old.id)).one()
        old_resource.updated_dt = datetime(2024, 1, 1, tzinfo=UTC)
        db.add(old_resource)
        recent_resource = db.exec(select(ExampleResource).where(ExampleResource.id == recent.id)).one()
        recent_resource.updated_dt = datetime(2025, 1, 1, tzinfo=UTC)
        db.add(recent_resource)
        db.commit()

        r = client.get(
            client.app.url_path_for('public-example-resource-list'),
            params={'updated_since': '2024-06-01T00:00:00Z'},
        )

        data = r.json()
        assert data['total'] == 1
        assert data['items'][0]['id'] == recent.id

    def test_list_query_count_constant_across_page_size(self, public_api_client, db, org_with_key):
        """The query count is identical for page_size=1 and page_size=200 (no N+1).

        A throwaway request first warms the ``last_used_dt`` throttle so neither measured
        request writes it, keeping the two counts comparable.
        """
        organization, client = org_with_key()
        for _ in range(5):
            resource = ExampleResourceFactory.create_with_db(db, organization=organization)
            ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource)
            ExampleResourceParticipantFactory.create_with_db(db, example_resource=resource)

        client.get(client.app.url_path_for('public-example-resource-list'))

        with count_queries(db) as small:
            client.get(client.app.url_path_for('public-example-resource-list'), params={'page_size': 1})
        with count_queries(db) as large:
            client.get(client.app.url_path_for('public-example-resource-list'), params={'page_size': 200})

        assert small.count == large.count


class TestPublicExampleResourceDetail:
    def test_detail_returns_full_structure_with_participants(self, public_api_client, db, org_with_key):
        """Detail returns the full PublicExampleResourceDetail structure with its participants."""
        organization, client = org_with_key()
        resource = ExampleResourceFactory.create_with_db(db, organization=organization, name='Beta')
        participant = ExampleResourceParticipantFactory.create_with_db(
            db, example_resource=resource, name='Pat', email='pat@example.com'
        )

        r = client.get(client.app.url_path_for('public-example-resource-detail', example_resource_id=resource.id))

        assert r.status_code == 200
        assert r.json() == {
            'id': resource.id,
            'name': 'Beta',
            'description': None,
            'status': 'draft',
            'organization_id': organization.id,
            'created_dt': _iso(resource.created_dt),
            'updated_dt': _iso(resource.updated_dt),
            'participant_count': 1,
            'participants': [{'id': participant.id, 'name': 'Pat', 'email': 'pat@example.com'}],
        }

    def test_detail_cross_tenant_returns_404(self, public_api_client, db, org_with_key):
        """A resource in another org is 404 (not 403) via an org-A key."""
        organization_a, client_a = org_with_key()
        organization_b = OrganizationFactory.create_with_db(db)
        other = ExampleResourceFactory.create_with_db(db, organization=organization_b)

        r = client_a.get(client_a.app.url_path_for('public-example-resource-detail', example_resource_id=other.id))

        assert r.status_code == 404

    def test_detail_demo_resource_returns_404(self, public_api_client, db, org_with_key):
        """A demo resource id is 404 — demo data is never exposed."""
        organization, client = org_with_key()
        demo = ExampleResourceFactory.create_with_db(db, organization=organization, is_demo=True)

        r = client.get(client.app.url_path_for('public-example-resource-detail', example_resource_id=demo.id))

        assert r.status_code == 404

    def test_detail_missing_returns_404(self, public_api_client, db, org_with_key):
        """A non-existent id returns 404."""
        _organization, client = org_with_key()

        r = client.get(client.app.url_path_for('public-example-resource-detail', example_resource_id=999999))

        assert r.status_code == 404


class TestPublicAuth:
    def test_list_requires_key(self, client):
        """A data route returns 401 with no Authorization header (auth is router-level)."""
        r = client.get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 401
        assert r.json() == {'detail': 'API key required'}

    def test_list_rejects_invalid_key(self, public_api_client, db):
        """A malformed key is rejected with 401."""
        make_client, _public_app = public_api_client
        client = make_client('not-a-valid-key')

        r = client.get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 401
        assert r.json() == {'detail': 'Invalid API key'}


class TestPublicDocs:
    def test_openapi_reachable_without_key(self, client):
        """/api/v1/openapi.json returns 200 with no Authorization header."""
        r = client.get('/api/v1/openapi.json')

        assert r.status_code == 200
        schema = r.json()
        assert schema['info']['title'] == 'FastAPI SQLModel Starter Public API'

    def test_scalar_reachable_without_key(self, client):
        """/api/v1/scalar (Scalar docs) returns 200 with no Authorization header."""
        r = client.get('/api/v1/scalar')

        assert r.status_code == 200
        assert 'text/html' in r.headers['content-type']
