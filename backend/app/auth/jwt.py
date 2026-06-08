import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlmodel import select

from app.auth.models import User, UserRole
from app.common.api.errors import HTTP401
from app.core.config import settings
from app.core.database import DBSession, get_db


class TokenData(BaseModel):
    """The identity triple carried in a web access token."""

    email: str
    role: UserRole
    id: int

    model_config = ConfigDict(json_schema_extra={'example': {'email': 'user@example.com', 'role': 'member', 'id': 123}})


class CustomHTTPBearer(HTTPBearer):
    """HTTPBearer that returns 401 (not 403) for a missing/malformed Authorization header.

    The default ``HTTPBearer`` raises 403 when the header is absent, which conflates
    "not authenticated" with "forbidden". We normalise it to 401 so unauthenticated
    requests get a consistent status across the API.
    """

    def __init__(self):
        super().__init__(auto_error=True)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        try:
            return await super().__call__(request)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_403_FORBIDDEN:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
            raise


async def auth_user(
    request: Request,
    session: DBSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials = Depends(CustomHTTPBearer()),
) -> User:
    """Authenticate a web request from its Bearer JWT and set ``request.state.user``.

    Decodes the token, then validates the full identity triple ``(id, email, role)`` against
    the database row so a stale or tampered token (e.g. one issued before a role change) is
    rejected. PKCE / mobile token revocation are intentionally out of scope for the starter —
    add an ``aud`` claim and a revocation timestamp if you need them.

    Raises:
        HTTP401: The token is missing, invalid, expired, or no longer matches a user.
    """
    try:
        payload = jwt.decode(creds.credentials, settings.secret_key, algorithms=[settings.algorithm])
        token_data = TokenData(**payload)
    except (PyJWTError, ValidationError):
        raise HTTP401('Could not validate credentials')

    user = session.exec(
        select(User).where(
            User.id == token_data.id,
            User.email == token_data.email,
            User.role == token_data.role,
        )
    ).one_or_none()
    if user is None:
        raise HTTP401('Could not validate credentials')

    request.state.user = user
    return user
