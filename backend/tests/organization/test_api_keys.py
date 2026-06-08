from sqlmodel import select

from app.auth.keys import API_KEY_PREFIX, hash_api_key
from app.core.database import DBSession
from app.organization.api.api_keys import MAX_API_KEYS_PER_ORG
from app.organization.models.api_key import OrganizationApiKey
from tests.conftest import AuthenticatedTestClient
from tests.organization.factories import OrganizationApiKeyFactory, OrganizationFactory


class TestListApiKeys:
    def test_list_empty(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """An organization with no keys returns an empty paginated response."""
        r = auth_client.get(auth_client.app.url_path_for('api-key-list'))
        assert r.status_code == 200
        assert r.json() == {'items': [], 'total': 0, 'page': 1, 'page_size': 50}

    def test_list_returns_org_keys_newest_first(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Keys are listed newest-first and never expose the token or its hash."""
        organization = auth_client.user.organization
        first, _ = OrganizationApiKeyFactory.create_with_db(db, organization=organization, name='First')
        second, _ = OrganizationApiKeyFactory.create_with_db(db, organization=organization, name='Second')

        r = auth_client.get(auth_client.app.url_path_for('api-key-list'))
        assert r.status_code == 200
        assert r.json() == {
            'items': [
                {
                    'id': second.id,
                    'name': 'Second',
                    'last4': second.last4,
                    'created_dt': second.created_dt.isoformat().replace('+00:00', 'Z'),
                    'last_used_dt': None,
                },
                {
                    'id': first.id,
                    'name': 'First',
                    'last4': first.last4,
                    'created_dt': first.created_dt.isoformat().replace('+00:00', 'Z'),
                    'last_used_dt': None,
                },
            ],
            'total': 2,
            'page': 1,
            'page_size': 50,
        }

    def test_list_excludes_other_organizations(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """An admin only sees their own organization's keys."""
        OrganizationApiKeyFactory.create_with_db(db, organization=auth_client.user.organization, name='Mine')
        other_org = OrganizationFactory.create_with_db(db, name='Other Org')
        OrganizationApiKeyFactory.create_with_db(db, organization=other_org, name='Theirs')

        r = auth_client.get(auth_client.app.url_path_for('api-key-list'))
        assert r.status_code == 200
        data = r.json()
        assert data['total'] == 1
        assert [item['name'] for item in data['items']] == ['Mine']

    def test_member_cannot_list(self, member_client: AuthenticatedTestClient, db: DBSession):
        """A non-admin member is forbidden from the admin-gated key endpoints."""
        r = member_client.get(member_client.app.url_path_for('api-key-list'))
        assert r.status_code == 403
        assert r.json() == {'detail': 'Admin access required'}

    def test_unauthenticated_cannot_list(self, client, db: DBSession):
        """An unauthenticated request is rejected with 401."""
        r = client.get(client.app.url_path_for('api-key-list'))
        assert r.status_code == 401
        assert r.json() == {'detail': 'Not authenticated'}


class TestCreateApiKey:
    def test_create_returns_full_key_once(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Create returns the full key exactly once; only the hash and last4 are stored."""
        r = auth_client.post(auth_client.app.url_path_for('api-key-create'), json={'name': 'CI key'})
        assert r.status_code == 201
        data = r.json()
        full_key = data['key']
        assert full_key.startswith(API_KEY_PREFIX)

        stored = db.exec(select(OrganizationApiKey).where(OrganizationApiKey.id == data['id'])).one()
        assert data == {
            'id': stored.id,
            'name': 'CI key',
            'last4': full_key[-4:],
            'created_dt': stored.created_dt.isoformat().replace('+00:00', 'Z'),
            'last_used_dt': None,
            'key': full_key,
        }
        assert stored.hashed_key == hash_api_key(full_key)
        assert stored.last4 == full_key[-4:]
        assert stored.organization_id == auth_client.user.organization_id

    def test_created_key_is_not_retrievable_again(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """The full token never appears in any subsequent list/detail response."""
        create = auth_client.post(auth_client.app.url_path_for('api-key-create'), json={'name': 'CI key'})
        full_key = create.json()['key']

        r = auth_client.get(auth_client.app.url_path_for('api-key-list'))
        assert r.status_code == 200
        assert full_key not in r.text
        assert 'hashed_key' not in r.text
        assert 'key' not in r.json()['items'][0]

    def test_create_caps_at_max_per_org(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """The eleventh key for an organization is rejected with 400."""
        for _ in range(MAX_API_KEYS_PER_ORG):
            OrganizationApiKeyFactory.create_with_db(db, organization=auth_client.user.organization)

        r = auth_client.post(auth_client.app.url_path_for('api-key-create'), json={'name': 'Over the cap'})
        assert r.status_code == 400
        assert r.json() == {'detail': f'Maximum of {MAX_API_KEYS_PER_ORG} API keys per organization reached'}

    def test_create_at_cap_minus_one_succeeds(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """The tenth key is still permitted (the cap is inclusive)."""
        for _ in range(MAX_API_KEYS_PER_ORG - 1):
            OrganizationApiKeyFactory.create_with_db(db, organization=auth_client.user.organization)

        r = auth_client.post(auth_client.app.url_path_for('api-key-create'), json={'name': 'Tenth'})
        assert r.status_code == 201

    def test_member_cannot_create(self, member_client: AuthenticatedTestClient, db: DBSession):
        """A non-admin member cannot mint keys."""
        r = member_client.post(member_client.app.url_path_for('api-key-create'), json={'name': 'Nope'})
        assert r.status_code == 403


class TestDeleteApiKey:
    def test_delete_own_key(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """An admin can delete their organization's key, which is then gone from the DB."""
        key_row, _ = OrganizationApiKeyFactory.create_with_db(db, organization=auth_client.user.organization)

        r = auth_client.delete(auth_client.app.url_path_for('api-key-delete', api_key_id=key_row.id))
        assert r.status_code == 204
        assert not db.exists(OrganizationApiKey, id=key_row.id)

    def test_delete_missing_key_returns_404(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Deleting a non-existent key returns 404."""
        r = auth_client.delete(auth_client.app.url_path_for('api-key-delete', api_key_id=999999))
        assert r.status_code == 404
        assert r.json() == {'detail': 'API key not found'}

    def test_cannot_delete_other_organizations_key(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Deleting another org's key returns 404 (not 403) and leaves the key intact."""
        other_org = OrganizationFactory.create_with_db(db, name='Other Org')
        key_row, _ = OrganizationApiKeyFactory.create_with_db(db, organization=other_org)

        r = auth_client.delete(auth_client.app.url_path_for('api-key-delete', api_key_id=key_row.id))
        assert r.status_code == 404
        assert db.exists(OrganizationApiKey, id=key_row.id)

    def test_member_cannot_delete(self, member_client: AuthenticatedTestClient, db: DBSession):
        """A non-admin member cannot delete keys."""
        key_row, _ = OrganizationApiKeyFactory.create_with_db(db, organization=member_client.user.organization)
        r = member_client.delete(member_client.app.url_path_for('api-key-delete', api_key_id=key_row.id))
        assert r.status_code == 403
