"""Tests for the Redis client factory in ``app/core/redis.py``."""

import ssl
from unittest.mock import patch

from app.core.config import settings
from app.core.redis import get_redis_client


class TestGetRedisClient:
    @patch('app.core.redis.redis.from_url')
    def test_plain_redis_url_builds_client_without_ssl(self, mock_from_url, monkeypatch):
        """A ``redis://`` URL builds a client with no SSL keyword arguments."""
        monkeypatch.setattr(settings, 'redis_url', 'redis://localhost:6379/0')

        client = get_redis_client()

        assert client is mock_from_url.return_value
        mock_from_url.assert_called_once_with('redis://localhost:6379/0')

    @patch('app.core.redis.redis.from_url')
    def test_rediss_url_builds_client_with_ssl_disabled_verification(self, mock_from_url, monkeypatch):
        """A ``rediss://`` URL builds a client with SSL cert verification disabled."""
        monkeypatch.setattr(settings, 'redis_url', 'rediss://secure-host:6380/0')

        client = get_redis_client()

        assert client is mock_from_url.return_value
        mock_from_url.assert_called_once_with(
            'rediss://secure-host:6380/0', ssl_cert_reqs=ssl.CERT_NONE, ssl_check_hostname=False
        )
