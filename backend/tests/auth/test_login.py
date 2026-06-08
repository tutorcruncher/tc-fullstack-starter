from types import SimpleNamespace
from unittest.mock import patch

import jwt
import pytest
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.testclient import TestClient

from app.auth.jwt import CustomHTTPBearer
from app.auth.login import create_access_token, get_password_hash
from app.auth.models import UserRole
from app.auth.permissions import Permission, PermissionCheck, role_check
from app.core.config import settings
from app.core.database import DBSession
from app.main import app
from tests.conftest import AuthenticatedTestClient, _create_authenticated_client_for_user
from tests.organization.factories import AdminFactory, MemberFactory

perm_test_router = APIRouter(prefix='/test-permissions', tags=['test-permissions'])


@perm_test_router.get('/admin-only', dependencies=[Depends(Permission.is_admin)], name='test-admin-only')
def admin_only_route():
    return {'access': 'admin'}


@perm_test_router.get('/member-only', dependencies=[Depends(Permission.is_member)], name='test-member-only')
def member_only_route():
    return {'access': 'member'}


@perm_test_router.get('/superadmin-only', dependencies=[Depends(Permission.is_superadmin)], name='test-superadmin-only')
def superadmin_only_route():
    return {'access': 'superadmin'}


@perm_test_router.get(
    '/admin-or-member', dependencies=[Depends(Permission.is_admin | Permission.is_member)], name='test-admin-or-member'
)
def admin_or_member_route():
    return {'access': 'admin_or_member'}


@perm_test_router.get(
    '/admin-and-superadmin',
    dependencies=[Depends(Permission.is_admin & Permission.is_superadmin)],
    name='test-admin-and-superadmin',
)
def admin_and_superadmin_route():
    return {'access': 'admin_and_superadmin'}


app.include_router(perm_test_router, dependencies=[Depends(Permission.is_member)])


class TestLogin:
    def test_login_success(self, client: TestClient, test_organization, db: DBSession):
        """A valid email and password returns a bearer access token."""
        AdminFactory.create_with_db(db, email='admin@test.com', organization=test_organization)
        r = client.post(
            client.app.url_path_for('login'),
            json={'email': 'admin@test.com', 'password': 'testing-password'},
        )
        assert r.status_code == 200
        data = r.json()
        assert data['token_type'] == 'bearer'
        assert data['access_token']

    def test_login_wrong_password(self, client: TestClient, test_organization, db: DBSession):
        """A wrong password returns 401 with a generic message that doesn't leak which field failed."""
        AdminFactory.create_with_db(db, email='admin@test.com', organization=test_organization)
        r = client.post(
            client.app.url_path_for('login'),
            json={'email': 'admin@test.com', 'password': 'wrong-password'},
        )
        assert r.status_code == 401
        assert r.json() == {'detail': 'Incorrect email or password'}

    def test_login_unknown_email(self, client: TestClient, db: DBSession):
        """An unknown email returns the same generic 401 as a wrong password."""
        r = client.post(
            client.app.url_path_for('login'),
            json={'email': 'nobody@test.com', 'password': 'whatever-password'},
        )
        assert r.status_code == 401
        assert r.json() == {'detail': 'Incorrect email or password'}

    @patch('app.auth.login.verify_password', return_value=False)
    def test_login_runs_verify_password_when_user_missing(self, mock_verify, client: TestClient, db: DBSession):
        """Timing-resistant: verify_password runs even when the email doesn't exist (defeats enumeration)."""
        r = client.post(
            client.app.url_path_for('login'),
            json={'email': 'nobody@test.com', 'password': 'whatever-password'},
        )
        assert r.status_code == 401
        assert mock_verify.call_count == 1

    def test_login_rate_limit_after_max_attempts(self, client: TestClient, db: DBSession):
        """The sixth attempt from one IP inside the window returns 429."""
        for _ in range(5):
            r = client.post(
                client.app.url_path_for('login'),
                json={'email': 'nobody@test.com', 'password': 'whatever-password'},
            )
            assert r.status_code == 401
        r = client.post(
            client.app.url_path_for('login'),
            json={'email': 'nobody@test.com', 'password': 'whatever-password'},
        )
        assert r.status_code == 429
        assert r.json() == {'detail': 'Too many attempts. Please try again later.'}

    def test_login_oversize_password_returns_422(self, client: TestClient, db: DBSession):
        """An oversize password is rejected by validation before it reaches the argon2 verify."""
        r = client.post(
            client.app.url_path_for('login'),
            json={'email': 'a@b.com', 'password': 'p' * 1000},
        )
        assert r.status_code == 422
        assert any('password' in entry['loc'] for entry in r.json()['detail'])


class TestPasswordAndTokenHelpers:
    def test_get_password_hash_rejects_oversize_password(self):
        """A password longer than the permitted bound raises ValueError before hashing."""
        with pytest.raises(ValueError, match='Password must be between'):
            get_password_hash('p' * 1000)

    def test_get_password_hash_rejects_empty_password(self):
        """An empty password is below the minimum length and raises ValueError."""
        with pytest.raises(ValueError, match='Password must be between'):
            get_password_hash('')

    def test_create_access_token_without_expiry_uses_default_expiry(self):
        """When no explicit expiry is passed, the token still carries an ``exp`` claim."""
        token = create_access_token({'email': 'someone@test.com'})

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload['email'] == 'someone@test.com'
        assert 'exp' in payload


class TestPermissionCombinator:
    def test_or_creates_combined_check(self):
        """The | operator produces a PermissionCheck whose name joins both with 'or'."""
        combined = Permission.is_admin | Permission.is_member
        assert isinstance(combined, PermissionCheck)
        assert combined.name == 'Admin or Member'

    def test_and_creates_combined_check(self):
        """The & operator produces a PermissionCheck whose name joins both with 'and'."""
        combined = Permission.is_admin & Permission.is_superadmin
        assert isinstance(combined, PermissionCheck)
        assert combined.name == 'Admin and Superadmin'

    def test_chained_or(self):
        """Chaining | operators threads the names together."""
        combined = Permission.is_admin | Permission.is_member | Permission.is_superadmin
        assert combined.name == 'Admin or Member or Superadmin'

    def test_role_check_builds_named_permission_for_role(self):
        """role_check returns a PermissionCheck named after the role that passes for that role."""
        check = role_check(UserRole.ADMIN)
        assert isinstance(check, PermissionCheck)
        assert check.name == 'Admin'
        assert check.check_func(SimpleNamespace(role=UserRole.ADMIN, is_superadmin=False)) is True
        assert check.check_func(SimpleNamespace(role=UserRole.MEMBER, is_superadmin=False)) is False
        assert check.check_func(SimpleNamespace(role=UserRole.MEMBER, is_superadmin=True)) is True


class TestRoleGating:
    def test_admin_route_allows_admin(self, admin_client: AuthenticatedTestClient, db: DBSession):
        """An admin can reach an admin-gated route."""
        r = admin_client.get(admin_client.app.url_path_for('test-admin-only'))
        assert r.status_code == 200
        assert r.json() == {'access': 'admin'}

    def test_admin_route_forbids_member(self, member_client: AuthenticatedTestClient, db: DBSession):
        """A member is forbidden from an admin-gated route with 403."""
        r = member_client.get(member_client.app.url_path_for('test-admin-only'))
        assert r.status_code == 403
        assert r.json() == {'detail': 'Admin access required'}

    def test_admin_route_allows_superadmin(self, client: TestClient, test_organization, db: DBSession):
        """A superadmin bypasses the admin role requirement."""
        superadmin = MemberFactory.create_with_db(
            db, email='super@test.com', is_superadmin=True, organization=test_organization
        )
        superadmin_client = _create_authenticated_client_for_user(client, superadmin)
        r = superadmin_client.get(superadmin_client.app.url_path_for('test-admin-only'))
        assert r.status_code == 200
        assert r.json() == {'access': 'admin'}

    def test_member_route_allows_member(self, member_client: AuthenticatedTestClient, db: DBSession):
        """Any authenticated user passes the member check."""
        r = member_client.get(member_client.app.url_path_for('test-member-only'))
        assert r.status_code == 200
        assert r.json() == {'access': 'member'}

    def test_superadmin_route_forbids_admin(self, admin_client: AuthenticatedTestClient, db: DBSession):
        """A plain admin is forbidden from a superadmin-only route."""
        r = admin_client.get(admin_client.app.url_path_for('test-superadmin-only'))
        assert r.status_code == 403
        assert r.json() == {'detail': 'Superadmin access required'}

    def test_or_route_allows_member(self, member_client: AuthenticatedTestClient, db: DBSession):
        """An OR combinator passes when either side passes."""
        r = member_client.get(member_client.app.url_path_for('test-admin-or-member'))
        assert r.status_code == 200
        assert r.json() == {'access': 'admin_or_member'}

    def test_and_route_forbids_plain_admin(self, admin_client: AuthenticatedTestClient, db: DBSession):
        """An AND combinator fails when only one side passes (admin but not superadmin)."""
        r = admin_client.get(admin_client.app.url_path_for('test-admin-and-superadmin'))
        assert r.status_code == 403
        assert r.json() == {'detail': 'Admin and Superadmin access required'}

    def test_and_route_allows_admin_superadmin(self, client: TestClient, test_organization, db: DBSession):
        """An AND combinator passes only when both sides pass (an admin who is also superadmin)."""
        admin_superadmin = AdminFactory.create_with_db(
            db, email='adminsuper@test.com', is_superadmin=True, organization=test_organization
        )
        admin_superadmin_client = _create_authenticated_client_for_user(client, admin_superadmin)
        r = admin_superadmin_client.get(admin_superadmin_client.app.url_path_for('test-admin-and-superadmin'))
        assert r.status_code == 200
        assert r.json() == {'access': 'admin_and_superadmin'}

    def test_unauthenticated_is_rejected(self, client: TestClient, db: DBSession):
        """A gated route rejects an unauthenticated request with 401."""
        r = client.get(client.app.url_path_for('test-admin-only'))
        assert r.status_code == 401
        assert r.json() == {'detail': 'Not authenticated'}


class TestAuthCredentialHandling:
    def test_malformed_authorization_header_returns_401(self, client: TestClient, db: DBSession):
        """A non-Bearer Authorization header is normalised from 403 to 401 'Not authenticated'."""
        r = client.get(
            client.app.url_path_for('test-member-only'),
            headers={'Authorization': 'Basic abc123'},
        )
        assert r.status_code == 401
        assert r.json() == {'detail': 'Not authenticated'}

    def test_invalid_token_returns_401(self, client: TestClient, db: DBSession):
        """A token that fails to decode is rejected with 401 'Could not validate credentials'."""
        r = client.get(
            client.app.url_path_for('test-member-only'),
            headers={'Authorization': 'Bearer not-a-real-jwt'},
        )
        assert r.status_code == 401
        assert r.json() == {'detail': 'Could not validate credentials'}

    def test_token_missing_required_claim_returns_401(self, client: TestClient, db: DBSession):
        """A validly-signed token missing the required identity claims fails TokenData validation."""
        token = jwt.encode({'email': 'someone@test.com'}, settings.secret_key, algorithm=settings.algorithm)
        r = client.get(
            client.app.url_path_for('test-member-only'),
            headers={'Authorization': f'Bearer {token}'},
        )
        assert r.status_code == 401
        assert r.json() == {'detail': 'Could not validate credentials'}


class TestCustomHTTPBearer:
    @patch('app.auth.jwt.HTTPBearer.__call__')
    async def test_normalises_403_to_401(self, mock_super_call):
        """A 403 from the parent bearer scheme is normalised to a 401 'Not authenticated'."""
        mock_super_call.side_effect = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')
        bearer = CustomHTTPBearer()

        with pytest.raises(HTTPException) as exc_info:
            await bearer(SimpleNamespace())

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == 'Not authenticated'

    @patch('app.auth.jwt.HTTPBearer.__call__')
    async def test_reraises_non_403_http_exception(self, mock_super_call):
        """A non-403 HTTPException from the parent bearer scheme is re-raised unchanged."""
        mock_super_call.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated'
        )
        bearer = CustomHTTPBearer()

        with pytest.raises(HTTPException) as exc_info:
            await bearer(SimpleNamespace())

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenIdentity:
    def test_stale_role_in_token_is_rejected(self, client: TestClient, test_organization, db: DBSession):
        """A token whose role no longer matches the DB user is rejected (401)."""
        member = MemberFactory.create_with_db(db, email='member2@test.com', organization=test_organization)
        member_client = _create_authenticated_client_for_user(client, member)
        member.role = UserRole.ADMIN
        db.add(member)
        db.commit()

        r = member_client.get(member_client.app.url_path_for('test-member-only'))
        assert r.status_code == 401
        assert r.json() == {'detail': 'Could not validate credentials'}
