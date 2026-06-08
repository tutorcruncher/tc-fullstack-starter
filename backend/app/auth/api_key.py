import logging
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.auth.auth import organization_billing_active
from app.auth.keys import API_KEY_PREFIX, hash_api_key
from app.common.api.errors import HTTP401, HTTP402
from app.core.database import DBSession, get_db
from app.organization.models.api_key import OrganizationApiKey
from app.organization.models.organization import Organization

logger = logging.getLogger(__name__)

_LAST_USED_THROTTLE = timedelta(minutes=5)

# auto_error=False so HTTPBearer returns None (instead of raising its own 403) when the
# Authorization header is missing or malformed, letting api_key_auth raise a consistent 401.
_api_key_scheme = HTTPBearer(auto_error=False)


def _touch_last_used(db: DBSession, api_key: OrganizationApiKey, now: datetime) -> None:
    """Best-effort, throttled update of ``last_used_dt``.

    Skips the write if the key was used within the throttle window. Never raises — a failed
    update must not 500 a read-only GET, so any error is logged and swallowed, keeping the
    public API genuinely read-only and avoiding row contention under a polling client.
    """
    if api_key.last_used_dt is not None and (now - api_key.last_used_dt) < _LAST_USED_THROTTLE:
        return
    try:
        api_key.last_used_dt = now
        db.add(api_key)
        db.commit()
    except Exception:
        db.rollback()
        logger.warning('Failed to update api key last_used_dt for key %s', api_key.id)


async def api_key_auth(
    request: Request,
    db: DBSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(_api_key_scheme),
) -> Organization:
    """Authenticate a public-API request by per-organization API key.

    Parses ``Authorization: Bearer app_live_<token>`` and looks the key up by the SHA-256
    hash of the presented token (O(1), indexed), then gates on active billing. On success,
    sets ``request.state.organization`` / ``organization_id`` / ``api_key`` (never
    ``request.state.user``) and returns the ``Organization``.

    Raises:
        HTTP401: Missing/malformed header, or an unknown key.
        HTTP402: The organization's billing is not active.
    """
    if creds is None:
        raise HTTP401('API key required')

    token = creds.credentials
    if not token.startswith(API_KEY_PREFIX):
        raise HTTP401('Invalid API key')

    api_key = db.exec(
        select(OrganizationApiKey)
        .where(OrganizationApiKey.hashed_key == hash_api_key(token))
        .options(joinedload(OrganizationApiKey.organization))  # ty: ignore[invalid-argument-type]
    ).one_or_none()
    if api_key is None:
        raise HTTP401('Invalid API key')

    if not organization_billing_active(api_key.organization_id, db):
        raise HTTP402('Organization billing is not active')

    organization = api_key.organization

    request.state.organization = organization
    request.state.organization_id = api_key.organization_id
    request.state.api_key = api_key

    _touch_last_used(db, api_key, datetime.now(UTC))
    return organization
