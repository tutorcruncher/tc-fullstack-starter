"""Tests for the FastAPI application entrypoint: healthcheck, CORS, docs and the public sub-app mount."""

import importlib
from unittest.mock import patch

from fastapi.testclient import TestClient

import app.main as main_module
from app.core.config import settings
from app.main import app


class TestHealthcheck:
    def test_health_returns_200(self, client: TestClient):
        """The unauthenticated healthcheck at '/' returns a healthy status."""
        r = client.get(client.app.url_path_for('health'))

        assert r.status_code == 200
        assert r.json() == {'status': 'healthy'}

    def test_health_requires_no_auth(self, client: TestClient):
        """The healthcheck is reachable with no Authorization header."""
        r = client.get(client.app.url_path_for('health'))

        assert r.status_code == 200


class TestCORSConfiguration:
    def test_cors_preflight_allows_get(self, client: TestClient):
        """A CORS preflight for GET is allowed and reflects the configured origin."""
        allowed_origin = settings.allowed_origins.split(',')[0]
        r = client.options(
            client.app.url_path_for('health'),
            headers={'Origin': allowed_origin, 'Access-Control-Request-Method': 'GET'},
        )

        assert r.status_code == 200
        assert r.headers['access-control-allow-origin'] == allowed_origin
        assert 'GET' in r.headers['access-control-allow-methods']

    def test_cors_preflight_allows_post(self, client: TestClient):
        """A CORS preflight for POST is allowed on the main app."""
        allowed_origin = settings.allowed_origins.split(',')[0]
        r = client.options(
            client.app.url_path_for('health'),
            headers={'Origin': allowed_origin, 'Access-Control-Request-Method': 'POST'},
        )

        assert r.status_code == 200
        assert 'POST' in r.headers['access-control-allow-methods']

    def test_cors_preflight_allows_authorization_header(self, client: TestClient):
        """The Authorization header is permitted via CORS preflight."""
        allowed_origin = settings.allowed_origins.split(',')[0]
        r = client.options(
            client.app.url_path_for('health'),
            headers={
                'Origin': allowed_origin,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization',
            },
        )

        assert r.status_code == 200
        assert 'authorization' in r.headers['access-control-allow-headers'].lower()

    def test_cors_simple_request_reflects_credentials(self, client: TestClient):
        """A simple GET from an allowed origin reflects the credentials header."""
        allowed_origin = settings.allowed_origins.split(',')[0]
        r = client.get(client.app.url_path_for('health'), headers={'Origin': allowed_origin})

        assert r.status_code == 200
        assert r.headers['access-control-allow-origin'] == allowed_origin
        assert r.headers['access-control-allow-credentials'] == 'true'


class TestMainAppDocs:
    def test_scalar_docs_reachable(self, client: TestClient):
        """The main app Scalar reference at '/scalar' returns HTML."""
        r = client.get('/scalar')

        assert r.status_code == 200
        assert 'text/html' in r.headers['content-type']

    def test_openapi_schema_reachable(self, client: TestClient):
        """The main app OpenAPI schema is reachable and describes the API."""
        r = client.get('/openapi.json')

        assert r.status_code == 200
        assert r.headers['content-type'] == 'application/json'
        data = r.json()
        assert data['info']['title'] == 'FastAPI SQLModel Starter'
        assert data['info']['version'] == '0.1.0'


class TestLifespan:
    @patch('app.main.logfire.instrument_fastapi')
    @patch('app.main.configure_logfire')
    @patch('app.main.init_sentry')
    @patch('app.main.create_db_and_tables')
    def test_lifespan_with_logfire_token_runs_full_startup(
        self, mock_create_tables, mock_init_sentry, mock_configure_logfire, mock_instrument, monkeypatch
    ):
        """With a logfire token set, the lifespan creates tables, inits sentry and instruments logfire."""
        monkeypatch.setattr(settings, 'logfire_token', 'test-token')

        with TestClient(app) as c:
            r = c.get(c.app.url_path_for('health'))
            assert r.status_code == 200

        mock_create_tables.assert_called_once_with()
        mock_init_sentry.assert_called_once_with()
        mock_configure_logfire.assert_called_once_with()
        mock_instrument.assert_called_once_with(app)

    @patch('app.main.logfire.instrument_fastapi')
    @patch('app.main.configure_logfire')
    @patch('app.main.init_sentry')
    @patch('app.main.create_db_and_tables')
    def test_lifespan_without_logfire_token_skips_instrumentation(
        self, mock_create_tables, mock_init_sentry, mock_configure_logfire, mock_instrument, monkeypatch
    ):
        """Without a logfire token, the lifespan still starts up but skips logfire instrumentation."""
        monkeypatch.setattr(settings, 'logfire_token', None)

        with TestClient(app) as c:
            r = c.get(c.app.url_path_for('health'))
            assert r.status_code == 200

        mock_create_tables.assert_called_once_with()
        mock_init_sentry.assert_called_once_with()
        mock_configure_logfire.assert_not_called()
        mock_instrument.assert_not_called()


class TestPublicAppLogfireInstrumentation:
    @patch('app.main.logfire.instrument_fastapi')
    def test_public_app_instrumented_when_token_set_at_import(self, mock_instrument, monkeypatch):
        """When ``logfire_token`` is set at import time, the public sub-app is instrumented."""
        monkeypatch.setattr(settings, 'logfire_token', 'test-token')
        try:
            importlib.reload(main_module)
            mock_instrument.assert_any_call(main_module.public_app)
        finally:
            importlib.reload(main_module)


class TestPublicSubApp:
    def test_public_openapi_is_key_free(self, public_api_client):
        """GET /api/v1/openapi.json returns 200 with no Authorization header."""
        make_client, _ = public_api_client
        client = make_client('')
        r = TestClient(client.app).get('/api/v1/openapi.json')

        assert r.status_code == 200
        assert r.headers['content-type'] == 'application/json'
        data = r.json()
        assert data['info']['title'] == 'FastAPI SQLModel Starter Public API'
        assert data['info']['version'] == '1.0.0'

    def test_public_scalar_docs_is_key_free(self, public_api_client):
        """GET /api/v1/scalar returns 200 HTML with no Authorization header."""
        make_client, _ = public_api_client
        client = make_client('')
        r = TestClient(client.app).get('/api/v1/scalar')

        assert r.status_code == 200
        assert 'text/html' in r.headers['content-type']

    def test_public_data_route_requires_key(self, public_api_client):
        """A public data route returns 401 when no API key is provided."""
        make_client, _ = public_api_client
        client = make_client('')
        r = TestClient(client.app).get(client.app.url_path_for('public-example-resource-list'))

        assert r.status_code == 401
