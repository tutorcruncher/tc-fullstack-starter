"""Redis-based rate limiting dependencies for FastAPI routes."""

from fastapi import Request

from app.common.api.errors import HTTP429
from app.core.config import settings
from app.core.redis import get_redis_client


def get_client_ip(request: Request) -> str:
    """Return the originating client IP from the proxy chain.

    **ONLY SAFE BEHIND A TRUSTED PROXY THAT APPENDS THE REAL CLIENT IP.** This function trusts
    the rightmost ``X-Forwarded-For`` entry unconditionally. That is correct behind a load
    balancer / router that always appends the real client IP, but on any deployment where the
    request can reach the app *without* such a proxy (local dev, a bare VM/pod with no ALB), an
    attacker can spoof ``X-Forwarded-For`` to bypass IP-keyed rate limits. If your topology does
    not guarantee a trusted proxy, gate this behind a ``trusted_proxy`` allowlist before relying
    on the result for security decisions.

    A trusted proxy appends the real client IP as the rightmost ``X-Forwarded-For`` entry (the
    existing list may have been set by the client and is untrustworthy), so we take the rightmost.
    Without this, IP-keyed rate limiting collapses to a single global bucket (the proxy IP from
    ``request.client.host``).
    """
    xff = request.headers.get('x-forwarded-for')
    if xff:
        rightmost = xff.rsplit(',', 1)[-1].strip()
        if rightmost:
            return rightmost
    return request.client.host if request.client else 'unknown'


def rate_limit(prefix: str, ttl_seconds: int = 60):
    """Rate limit dependency factory. 1 request per ttl_seconds per user.

    Only checks whether the user is rate-limited and rejects with 429 if so. The rate limit key
    is NOT set here — call ``confirm_rate_limit(request)`` in the endpoint after a successful
    operation so that failed requests (e.g. a duplicate-name 409) do not consume the rate limit.

    Uses ``request.state.user`` since ``auth_user`` is already applied at router level.
    Redis key: ``rate_limit:{prefix}:{user_id}`` with TTL.

    Args:
        prefix: Key prefix to namespace different rate limits.
        ttl_seconds: Time-to-live in seconds for the rate limit window.

    Returns:
        A FastAPI dependency callable.
    """

    def _rate_limit(request: Request) -> None:
        user = request.state.user
        redis_client = get_redis_client()
        key = f'rate_limit:{prefix}:{user.id}'
        if redis_client.exists(key):
            raise HTTP429('Rate limit exceeded. Please try again later.')
        request.state.rate_limit_key = key
        request.state.rate_limit_ttl = ttl_seconds
        request.state.rate_limit_redis = redis_client

    return _rate_limit


def confirm_rate_limit(request: Request) -> None:
    """Set the rate limit key after a successful operation.

    Call this at the end of an endpoint handler, just before returning, so that only successful
    requests are counted against the rate limit.
    """
    key = getattr(request.state, 'rate_limit_key', None)
    if key:
        redis_client = request.state.rate_limit_redis
        ttl = request.state.rate_limit_ttl
        redis_client.set(key, '1', ex=ttl)


def public_api_rate_limit(request: Request) -> None:
    """Per-organization fixed-window rate limit for the public API.

    Counts requests per organization across all its keys (so an org can't multiply its quota by
    minting more keys) in a fixed window of ``settings.public_api_rate_limit_window_seconds``.
    Relies on ``api_key_auth`` having set ``request.state.organization_id``, so it must run after
    it in the router dependency list.

    Keyed on the organization, not the IP, because a single org may call from many IPs (or share
    one via NAT) — so an IP-based limit at the edge would be wrong.
    """
    organization_id = request.state.organization_id
    redis_client = get_redis_client()
    key = f'rate_limit:public_api:{organization_id}'
    count = redis_client.incr(key)
    redis_client.expire(key, settings.public_api_rate_limit_window_seconds, nx=True)
    if count > settings.public_api_rate_limit_per_minute:
        raise HTTP429('Rate limit exceeded. Please try again later.')


def rate_limit_by_ip(prefix: str, window_seconds: int, max_attempts: int):
    """N attempts per IP per window. Uses INCR + idempotent EXPIRE for atomic counting.

    Unlike ``rate_limit()``, every attempt is counted — there is no ``confirm_rate_limit()`` step.
    Use this for anonymous auth endpoints where you want to throttle even failed attempts to
    defeat credential stuffing / brute force.

    The TTL is set with ``NX`` on every call (idempotent, no-op once set) so a worker crash
    between INCR and EXPIRE can't leave a TTL-less key permanently throttling that IP.

    Args:
        prefix: Key prefix to namespace different rate limits.
        window_seconds: Length of the window in seconds.
        max_attempts: Maximum attempts permitted per IP per window.

    Returns:
        A FastAPI dependency callable.
    """

    def _rate_limit_by_ip(request: Request) -> None:
        ip = get_client_ip(request)
        key = f'rate_limit:{prefix}:{ip}'
        redis_client = get_redis_client()
        count = redis_client.incr(key)
        redis_client.expire(key, window_seconds, nx=True)
        if count > max_attempts:
            raise HTTP429('Too many attempts. Please try again later.')

    return _rate_limit_by_ip
