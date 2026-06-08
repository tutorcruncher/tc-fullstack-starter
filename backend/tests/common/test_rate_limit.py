import pytest
from starlette.requests import Request

from app.common.api.errors import HTTP429
from app.common.api.rate_limit import (
    confirm_rate_limit,
    get_client_ip,
    public_api_rate_limit,
    rate_limit,
    rate_limit_by_ip,
)
from app.core.config import settings
from app.core.redis import get_redis_client


def _build_request(headers: list[tuple[bytes, bytes]] | None = None, client: tuple[str, int] | None = None) -> Request:
    """Build a minimal Starlette request with optional headers and client address."""
    scope = {
        'type': 'http',
        'method': 'GET',
        'headers': headers or [],
        'path': '/',
        'query_string': b'',
    }
    if client is not None:
        scope['client'] = client
    return Request(scope)


def _org_request(organization_id: int) -> Request:
    """Build a request carrying the organization_id that api_key_auth would have set."""
    request = _build_request()
    request.state.organization_id = organization_id
    return request


class _FakeUser:
    """Stand-in for request.state.user, which the rate_limit dependency reads .id from."""

    def __init__(self, user_id: int):
        self.id = user_id


class TestGetClientIp:
    """Tests for resolving the originating client IP from the proxy chain."""

    def test_uses_rightmost_x_forwarded_for_entry(self):
        """Test that the rightmost X-Forwarded-For entry is trusted over earlier ones."""
        request = _build_request(headers=[(b'x-forwarded-for', b'1.1.1.1, 2.2.2.2, 3.3.3.3')])

        assert get_client_ip(request) == '3.3.3.3'

    def test_single_x_forwarded_for_entry(self):
        """Test that a single X-Forwarded-For entry is returned as-is."""
        request = _build_request(headers=[(b'x-forwarded-for', b'9.9.9.9')])

        assert get_client_ip(request) == '9.9.9.9'

    def test_blank_x_forwarded_for_falls_back_to_client_host(self):
        """Test that a blank X-Forwarded-For value falls back to request.client.host."""
        request = _build_request(headers=[(b'x-forwarded-for', b'   ')], client=('5.5.5.5', 1234))

        assert get_client_ip(request) == '5.5.5.5'

    def test_no_header_uses_client_host(self):
        """Test that the client host is used when no X-Forwarded-For header is present."""
        request = _build_request(client=('4.4.4.4', 4321))

        assert get_client_ip(request) == '4.4.4.4'

    def test_no_header_and_no_client_returns_unknown(self):
        """Test that 'unknown' is returned when there is neither a header nor a client."""
        request = _build_request()

        assert get_client_ip(request) == 'unknown'


class TestPublicApiRateLimit:
    """Tests for the per-organization public-API rate limit dependency."""

    def test_allows_requests_up_to_the_limit(self, monkeypatch):
        """Test that an org can make exactly the configured number of requests without a 429."""
        monkeypatch.setattr(settings, 'public_api_rate_limit_per_minute', 3)
        get_redis_client().delete('rate_limit:public_api:90001')
        request = _org_request(90001)

        for _ in range(3):
            public_api_rate_limit(request)

    def test_blocks_requests_over_the_limit(self, monkeypatch):
        """Test that the request after the limit is exceeded raises HTTP429."""
        monkeypatch.setattr(settings, 'public_api_rate_limit_per_minute', 2)
        get_redis_client().delete('rate_limit:public_api:90002')
        request = _org_request(90002)

        public_api_rate_limit(request)
        public_api_rate_limit(request)
        with pytest.raises(HTTP429) as exc_info:
            public_api_rate_limit(request)

        assert exc_info.value.detail == 'Rate limit exceeded. Please try again later.'

    def test_limit_is_scoped_per_organization(self, monkeypatch):
        """Test that one org exhausting its quota does not rate limit another org."""
        monkeypatch.setattr(settings, 'public_api_rate_limit_per_minute', 1)
        get_redis_client().delete('rate_limit:public_api:90003')
        get_redis_client().delete('rate_limit:public_api:90004')

        public_api_rate_limit(_org_request(90003))
        with pytest.raises(HTTP429):
            public_api_rate_limit(_org_request(90003))

        public_api_rate_limit(_org_request(90004))


class TestRateLimitTwoStep:
    """Tests for the rate_limit / confirm_rate_limit two-step per-user dependency."""

    def test_first_request_passes_and_does_not_set_key(self):
        """Test that the first check passes and leaves the key unset until confirmed."""
        get_redis_client().delete('rate_limit:report:91001')
        request = _build_request()
        request.state.user = _FakeUser(91001)

        rate_limit('report')(request)

        assert get_redis_client().exists('rate_limit:report:91001') == 0
        assert request.state.rate_limit_key == 'rate_limit:report:91001'
        assert request.state.rate_limit_ttl == 60

    def test_confirm_sets_the_key_and_second_request_is_blocked(self):
        """Test that confirming sets the key so the next request within the ttl raises HTTP429."""
        get_redis_client().delete('rate_limit:report:91002')
        first = _build_request()
        first.state.user = _FakeUser(91002)
        rate_limit('report')(first)
        confirm_rate_limit(first)

        assert get_redis_client().exists('rate_limit:report:91002') == 1

        second = _build_request()
        second.state.user = _FakeUser(91002)
        with pytest.raises(HTTP429) as exc_info:
            rate_limit('report')(second)

        assert exc_info.value.detail == 'Rate limit exceeded. Please try again later.'

    def test_confirm_respects_custom_ttl(self):
        """Test that confirm_rate_limit applies the ttl supplied to the rate_limit factory."""
        get_redis_client().delete('rate_limit:report:91003')
        request = _build_request()
        request.state.user = _FakeUser(91003)
        rate_limit('report', ttl_seconds=30)(request)
        confirm_rate_limit(request)

        assert get_redis_client().ttl('rate_limit:report:91003') == 30

    def test_confirm_without_a_pending_key_is_a_noop(self):
        """Test that confirm_rate_limit does nothing when no rate_limit check ran first."""
        request = _build_request()

        confirm_rate_limit(request)


class TestRateLimitByIp:
    """Tests for the per-IP atomic counter dependency."""

    def test_allows_attempts_up_to_max(self):
        """Test that attempts up to max_attempts pass without raising."""
        get_redis_client().delete('rate_limit:login:7.7.7.7')
        dependency = rate_limit_by_ip('login', window_seconds=60, max_attempts=3)
        request = _build_request(client=('7.7.7.7', 1000))

        for _ in range(3):
            dependency(request)

    def test_blocks_attempt_over_max(self):
        """Test that the attempt after max_attempts raises HTTP429."""
        get_redis_client().delete('rate_limit:login:8.8.8.8')
        dependency = rate_limit_by_ip('login', window_seconds=60, max_attempts=2)
        request = _build_request(client=('8.8.8.8', 1000))

        dependency(request)
        dependency(request)
        with pytest.raises(HTTP429) as exc_info:
            dependency(request)

        assert exc_info.value.detail == 'Too many attempts. Please try again later.'

    def test_counter_is_scoped_per_ip(self):
        """Test that one IP exhausting its attempts does not throttle a different IP."""
        get_redis_client().delete('rate_limit:login:1.2.3.4')
        get_redis_client().delete('rate_limit:login:5.6.7.8')
        dependency = rate_limit_by_ip('login', window_seconds=60, max_attempts=1)

        dependency(_build_request(headers=[(b'x-forwarded-for', b'1.2.3.4')]))
        with pytest.raises(HTTP429):
            dependency(_build_request(headers=[(b'x-forwarded-for', b'1.2.3.4')]))

        dependency(_build_request(headers=[(b'x-forwarded-for', b'5.6.7.8')]))

    def test_sets_window_ttl_on_the_counter(self):
        """Test that the window ttl is applied to the per-IP counter key."""
        get_redis_client().delete('rate_limit:login:9.0.9.0')
        dependency = rate_limit_by_ip('login', window_seconds=45, max_attempts=5)

        dependency(_build_request(headers=[(b'x-forwarded-for', b'9.0.9.0')]))

        assert get_redis_client().ttl('rate_limit:login:9.0.9.0') == 45
