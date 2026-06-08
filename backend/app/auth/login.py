from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from sqlmodel import select

from app.auth.models import User
from app.core.config import settings
from app.core.database import DBSession

pwd_context = PasswordHash.recommended()

# Shared user-facing message for any auth failure — wrong password or unknown email.
# Deliberately generic so the response doesn't leak which field was wrong (defeats email
# enumeration). It lives here as the single source of truth for the login path.
INVALID_CREDENTIALS_MESSAGE = 'Incorrect email or password'

# Length bounds the argon2 work per request so an attacker can't force us to hash MB-sized
# payloads, and the lower bound rejects empties. argon2 itself imposes no max, so this is ours.
MIN_PASSWORD_LENGTH = 1
MAX_PASSWORD_LENGTH = 256

# Hash used in the user-missing branch of authenticate_user so the password verify runs in
# both branches. Closes the timing side-channel that would otherwise let attackers enumerate
# valid emails — pwdlib defaults to argon2id, which is intentionally slow (~150-300ms).
_DUMMY_HASH = pwd_context.hash('timing-resistance-dummy-password')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its argon2 hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password with argon2id.

    Raises:
        ValueError: If the password length is outside the permitted bounds.
    """
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(f'Password must be between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters')
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT carrying ``data`` plus an ``exp`` claim."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def _dummy_verify_for_timing(password: str) -> None:
    """Run a throwaway argon2 verify to keep login timing constant.

    Called in the user-not-found branch of ``authenticate_user`` so that branch spends the
    same ~150-300ms as the user-found branch. Without this, a fast "no such email" response
    would let an attacker enumerate which emails have accounts. The result is discarded.
    """
    verify_password(password, _DUMMY_HASH)


def authenticate_user(session: DBSession, email: str, password: str) -> User | None:
    """Authenticate a user by email and password.

    Runs ``verify_password`` in BOTH branches (user found vs not found) so the timing
    side-channel that lets attackers enumerate valid emails is closed. The argon2id verifies
    are intentionally slow (~150-300ms) — the rate limit in front of the login endpoint is
    what bounds the DoS amplification.
    """
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        _dummy_verify_for_timing(password)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token_for(user: User) -> str:
    """Issue a web access-token JWT for ``user`` using the configured expiry."""
    assert user.id is not None
    return create_access_token(
        data={'email': user.email, 'role': user.role.value, 'id': user.id},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
