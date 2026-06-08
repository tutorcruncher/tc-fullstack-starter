import hashlib
import secrets

API_KEY_PREFIX = 'app_live_'
_TOKEN_RANDOM_BYTES = 32


def hash_api_key(full_key: str) -> str:
    """Return the SHA-256 hex digest of a full API key.

    This is the value stored in ``OrganizationApiKey.hashed_key`` and the value auth
    looks the key up by. The token is high-entropy (256 random bits), so an
    unsalted fast hash is sufficient — a salted/slow hash (argon2) would only force
    a full-table scan since it can't be indexed.
    """
    return hashlib.sha256(full_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new public API key.

    The token has the shape ``app_live_<random>`` — a single opaque high-entropy
    string. We never store the token itself, only its SHA-256 hash and the last 4
    chars (for display).

    Returns:
        A ``(full_key, last4, hashed_key)`` tuple. ``full_key`` is shown to the admin
        exactly once; the caller persists the other two.
    """
    full_key = f'{API_KEY_PREFIX}{secrets.token_urlsafe(_TOKEN_RANDOM_BYTES)}'
    return full_key, full_key[-4:], hash_api_key(full_key)
