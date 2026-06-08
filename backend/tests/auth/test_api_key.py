from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select
from starlette.requests import Request

from app.auth.api_key import _touch_last_used, api_key_auth
from app.auth.auth import billing_status_active, organization_billing_active
from app.auth.keys import API_KEY_PREFIX, generate_api_key, hash_api_key
from app.common.api.errors import HTTP401, HTTP402
from app.core.config import settings
from app.organization.models.api_key import OrganizationApiKey
from app.organization.models.organization import BillingStatus, Organization
from tests.organization.factories import OrganizationApiKeyFactory, OrganizationFactory


def _make_request() -> Request:
    """Build a minimal ASGI Request so api_key_auth can set request.state.*."""
    return Request({'type': 'http', 'method': 'GET', 'headers': [], 'path': '/api/v1', 'query_string': b''})


def _creds(token: str) -> HTTPAuthorizationCredentials:
    """Wrap a bearer token the way HTTPBearer hands it to the dependency."""
    return HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)


class TestGenerateApiKey:
    """Tests for the generate_api_key / hash_api_key roundtrip."""

    def test_generate_api_key_roundtrip(self):
        """Test that the full key carries the prefix and verifies against its stored hash and last4."""
        full_key, last4, hashed_key = generate_api_key()

        assert full_key.startswith(API_KEY_PREFIX)
        assert last4 == full_key[-4:]
        assert hashed_key == hash_api_key(full_key)
        assert len(hashed_key) == 64

    def test_generate_api_key_unique_each_call(self):
        """Test that each generated key is distinct."""
        first, _, _ = generate_api_key()
        second, _, _ = generate_api_key()

        assert first != second

    def test_hash_api_key_deterministic(self):
        """Test that hashing the same token twice yields the same digest."""
        assert hash_api_key('app_live_constant') == hash_api_key('app_live_constant')


class TestBillingStatusActive:
    """Tests for the billing_status_active predicate across every billing state."""

    def test_active_status_is_active(self):
        """Test that an ACTIVE organization counts as active."""
        assert billing_status_active(BillingStatus.ACTIVE, None) is True

    def test_always_free_status_is_active(self):
        """Test that an ALWAYS_FREE organization counts as active."""
        assert billing_status_active(BillingStatus.ALWAYS_FREE, None) is True

    def test_trial_with_future_expiry_is_active(self):
        """Test that a TRIAL with a future expiry counts as active."""
        assert billing_status_active(BillingStatus.TRIAL, datetime.now(UTC) + timedelta(days=3)) is True

    def test_trial_with_null_expiry_is_active(self):
        """Test that a TRIAL with no expiry is treated as not-yet-expired."""
        assert billing_status_active(BillingStatus.TRIAL, None) is True

    def test_trial_with_past_expiry_is_inactive(self):
        """Test that a TRIAL whose expiry has passed counts as inactive."""
        assert billing_status_active(BillingStatus.TRIAL, datetime.now(UTC) - timedelta(days=1)) is False

    def test_expired_status_is_inactive(self):
        """Test that an EXPIRED organization counts as inactive."""
        assert billing_status_active(BillingStatus.EXPIRED, None) is False


class TestOrganizationBillingActive:
    """Tests for the org-keyed organization_billing_active gate."""

    def test_active_organization_is_active(self, db):
        """Test that an ACTIVE organization is active."""
        organization = OrganizationFactory.create_with_db(db, billing_status=BillingStatus.ACTIVE)

        assert organization_billing_active(organization.id, db) is True

    def test_always_free_organization_is_active(self, db):
        """Test that an ALWAYS_FREE organization is active."""
        organization = OrganizationFactory.create_with_db(db, billing_status=BillingStatus.ALWAYS_FREE)

        assert organization_billing_active(organization.id, db) is True

    def test_unexpired_trial_organization_is_active(self, db):
        """Test that a TRIAL organization with a future expiry is active."""
        organization = OrganizationFactory.create_with_db(
            db, billing_status=BillingStatus.TRIAL, trial_expiry_dt=datetime.now(UTC) + timedelta(days=3)
        )

        assert organization_billing_active(organization.id, db) is True

    def test_expired_trial_organization_is_inactive(self, db):
        """Test that a TRIAL organization with a past expiry is inactive."""
        organization = OrganizationFactory.create_with_db(
            db, billing_status=BillingStatus.TRIAL, trial_expiry_dt=datetime.now(UTC) - timedelta(days=1)
        )

        assert organization_billing_active(organization.id, db) is False

    def test_expired_organization_is_inactive(self, db):
        """Test that an EXPIRED organization is inactive."""
        organization = OrganizationFactory.create_with_db(db, billing_status=BillingStatus.EXPIRED)

        assert organization_billing_active(organization.id, db) is False

    def test_unknown_organization_fails_closed(self, db):
        """Test that an unknown organization id is treated as inactive."""
        assert organization_billing_active(999999, db) is False


class TestApiKeyAuth:
    """Unit tests for the api_key_auth dependency, calling it directly."""

    async def test_valid_key_authenticates(self, db):
        """Test that a valid key on an active org returns its organization and sets request state."""
        organization = OrganizationFactory.create_with_db(db, billing_status=BillingStatus.ACTIVE)
        key_row, full_key = OrganizationApiKeyFactory.create_with_db(db, organization=organization)

        request = _make_request()
        result = await api_key_auth(request, db, _creds(full_key))

        assert isinstance(result, Organization)
        assert result.id == organization.id
        assert request.state.organization.id == organization.id
        assert request.state.organization_id == organization.id
        assert request.state.api_key.id == key_row.id
        assert not hasattr(request.state, 'user')

    async def test_missing_creds_returns_401(self, db):
        """Test that a request with no credentials raises HTTP401."""
        with pytest.raises(HTTP401) as exc_info:
            await api_key_auth(_make_request(), db, None)

        assert exc_info.value.detail == 'API key required'

    async def test_bad_prefix_returns_401(self, db):
        """Test that a token without the app_live_ prefix raises HTTP401."""
        with pytest.raises(HTTP401) as exc_info:
            await api_key_auth(_make_request(), db, _creds('not-a-valid-token'))

        assert exc_info.value.detail == 'Invalid API key'

    async def test_unknown_key_returns_401(self, db):
        """Test that a well-formed token matching no stored key raises HTTP401."""
        with pytest.raises(HTTP401) as exc_info:
            await api_key_auth(_make_request(), db, _creds('app_live_doesnotexist'))

        assert exc_info.value.detail == 'Invalid API key'

    async def test_inactive_billing_returns_402(self, db):
        """Test that a key on an org with expired billing raises HTTP402."""
        organization = OrganizationFactory.create_with_db(db, billing_status=BillingStatus.EXPIRED)
        _, full_key = OrganizationApiKeyFactory.create_with_db(db, organization=organization)

        with pytest.raises(HTTP402) as exc_info:
            await api_key_auth(_make_request(), db, _creds(full_key))

        assert exc_info.value.detail == 'Organization billing is not active'

    async def test_last_used_dt_stamped_on_first_use(self, db):
        """Test that last_used_dt is stamped on the first authenticated request."""
        organization = OrganizationFactory.create_with_db(db, billing_status=BillingStatus.ACTIVE)
        key_row, full_key = OrganizationApiKeyFactory.create_with_db(db, organization=organization)
        assert key_row.last_used_dt is None

        await api_key_auth(_make_request(), db, _creds(full_key))

        refreshed = db.exec(select(OrganizationApiKey).where(OrganizationApiKey.id == key_row.id)).one()
        assert refreshed.last_used_dt is not None


class TestTouchLastUsed:
    """Tests for the throttled, best-effort _touch_last_used helper."""

    def test_stamps_when_never_used(self, db):
        """Test that _touch_last_used writes last_used_dt when it was previously None."""
        organization = OrganizationFactory.create_with_db(db)
        key_row, _ = OrganizationApiKeyFactory.create_with_db(db, organization=organization)
        now = datetime.now(UTC)

        _touch_last_used(db, key_row, now)

        refreshed = db.exec(select(OrganizationApiKey).where(OrganizationApiKey.id == key_row.id)).one()
        assert refreshed.last_used_dt is not None

    def test_skips_within_throttle_window(self, db):
        """Test that _touch_last_used does not write if used within the throttle window."""
        organization = OrganizationFactory.create_with_db(db)
        recent = datetime.now(UTC) - timedelta(minutes=1)
        key_row, _ = OrganizationApiKeyFactory.create_with_db(db, organization=organization, last_used_dt=recent)

        with patch.object(type(db), 'add', side_effect=AssertionError('should not write')):
            _touch_last_used(db, key_row, datetime.now(UTC))

    def test_swallows_commit_error(self, db):
        """Test that _touch_last_used never raises when the commit fails (read stays read-only)."""
        organization = OrganizationFactory.create_with_db(db)
        key_row, _ = OrganizationApiKeyFactory.create_with_db(db, organization=organization)

        with patch.object(type(db), 'commit', side_effect=Exception('db down')):
            _touch_last_used(db, key_row, datetime.now(UTC))


class TestApiKeyAuthViaPublicRoute:
    """Integration tests for api_key_auth as a router dependency on the public API."""

    def test_valid_key_returns_200(self, public_api_client, db):
        """Test that a valid key authenticates against a public route and returns its org's data."""
        make_client, _ = public_api_client
        organization = OrganizationFactory.create_with_db(db, billing_status=BillingStatus.ACTIVE)
        _, full_key = OrganizationApiKeyFactory.create_with_db(db, organization=organization)
        client = make_client(full_key)

        r = client.get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 200
        assert r.json() == {'items': [], 'total': 0, 'page': 1, 'page_size': settings.dft_page_size}

    def test_missing_key_returns_401(self, public_api_client, db):
        """Test that a request with no Authorization header returns 401."""
        make_client, _ = public_api_client
        client = make_client('app_live_unused')

        r = client.get(client.app.url_path_for('public-example-resource-list'), headers={'Authorization': ''})

        assert r.status_code == 401
        assert r.json() == {'detail': 'API key required'}

    def test_bad_prefix_returns_401(self, public_api_client, db):
        """Test that a token without the app_live_ prefix returns 401."""
        make_client, _ = public_api_client
        client = make_client('not-a-valid-token')

        r = client.get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 401
        assert r.json() == {'detail': 'Invalid API key'}

    def test_unknown_key_returns_401(self, public_api_client, db):
        """Test that a well-formed but unknown token returns 401."""
        make_client, _ = public_api_client
        client = make_client('app_live_doesnotexist')

        r = client.get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 401
        assert r.json() == {'detail': 'Invalid API key'}

    def test_inactive_billing_returns_402(self, public_api_client, db):
        """Test that a key on an org with expired billing returns 402."""
        make_client, _ = public_api_client
        organization = OrganizationFactory.create_with_db(db, billing_status=BillingStatus.EXPIRED)
        _, full_key = OrganizationApiKeyFactory.create_with_db(db, organization=organization)
        client = make_client(full_key)

        r = client.get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 402
        assert r.json() == {'detail': 'Organization billing is not active'}
