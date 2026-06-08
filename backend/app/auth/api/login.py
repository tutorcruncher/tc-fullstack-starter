from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.auth.login import INVALID_CREDENTIALS_MESSAGE, MAX_PASSWORD_LENGTH, authenticate_user, create_access_token_for
from app.common.api.errors import HTTP401
from app.common.api.rate_limit import rate_limit_by_ip
from app.core.database import DBSession, get_db

# EmailStr already enforces RFC 5321's 254-char limit; bound the password too so an attacker
# can't push a huge payload into the argon2 verify on the (unauthenticated) login route.
MAX_EMAIL_LENGTH = 254

anon_router = APIRouter(prefix='/auth', tags=['authentication', 'anon'])


class UserLogin(BaseModel):
    """Login request body."""

    email: EmailStr = Field(max_length=MAX_EMAIL_LENGTH)
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)

    model_config = ConfigDict(json_schema_extra={'example': {'email': 'user@example.com', 'password': 'password'}})


class Token(BaseModel):
    """Login response carrying the bearer access token."""

    access_token: str
    token_type: str = 'bearer'


@anon_router.post(
    '/login',
    response_model=Token,
    name='login',
    dependencies=[Depends(rate_limit_by_ip('login', window_seconds=60, max_attempts=5))],
)
def login(credentials: UserLogin, session: DBSession = Depends(get_db)) -> Token:
    """Authenticate by email and password and return a web access token.

    The per-IP rate limit throttles even failed attempts to defeat credential stuffing;
    ``authenticate_user`` is timing-resistant so the response time can't be used to
    enumerate valid emails.
    """
    user = authenticate_user(session, credentials.email, credentials.password)
    if not user:
        raise HTTP401(INVALID_CREDENTIALS_MESSAGE, headers={'WWW-Authenticate': 'Bearer'})

    return Token(access_token=create_access_token_for(user))
