"""Redis client utility."""

import ssl

import redis

from app.core.config import settings


def get_redis_client() -> redis.Redis:
    """Get a Redis client configured from settings.

    Handles both redis:// and rediss:// (SSL) connections.

    Returns:
        Configured Redis client
    """
    redis_url = str(settings.redis_url)
    if redis_url.startswith('rediss://'):
        return redis.from_url(redis_url, ssl_cert_reqs=ssl.CERT_NONE, ssl_check_hostname=False)
    else:
        return redis.from_url(redis_url)
