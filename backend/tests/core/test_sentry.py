"""Tests for Sentry initialization and the before_send event filter."""

from unittest.mock import patch

from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.sentry import before_send, init_sentry


class TestInitSentry:
    @patch('app.core.sentry.settings')
    @patch('sentry_sdk.init')
    def test_init_sentry_with_dsn(self, mock_sentry_init, mock_settings):
        """Test that init_sentry initializes Sentry when a DSN is configured."""
        mock_settings.sentry_dsn = 'https://test@test.ingest.sentry.io/123456'
        mock_settings.environment = 'production'

        init_sentry()

        mock_sentry_init.assert_called_once()
        call_kwargs = mock_sentry_init.call_args.kwargs
        assert call_kwargs['dsn'] == 'https://test@test.ingest.sentry.io/123456'
        assert call_kwargs['environment'] == 'production'
        assert call_kwargs['before_send'] is before_send
        assert len(call_kwargs['integrations']) == 2
        assert isinstance(call_kwargs['integrations'][0], CeleryIntegration)
        assert isinstance(call_kwargs['integrations'][1], LoggingIntegration)

    @patch('app.core.sentry.settings')
    @patch('sentry_sdk.init')
    def test_init_sentry_without_dsn(self, mock_sentry_init, mock_settings):
        """Test that init_sentry is a no-op when no DSN is configured."""
        mock_settings.sentry_dsn = None

        init_sentry()

        mock_sentry_init.assert_not_called()


class TestBeforeSend:
    def test_before_send_returns_event_without_exc_info(self):
        """Test that before_send returns the event unchanged when there is no exc_info."""
        event = {'message': 'something happened'}

        assert before_send(event, {}) is event

    def test_before_send_filters_worker_lost_sigterm(self):
        """Test that before_send drops WorkerLostError caused by SIGTERM."""
        exc = type('WorkerLostError', (Exception,), {})('Worker exited prematurely: signal 15 (SIGTERM).')
        hint = {'exc_info': (type(exc), exc, None)}

        assert before_send({'message': 'worker lost'}, hint) is None

    def test_before_send_keeps_worker_lost_other_signal(self):
        """Test that before_send keeps WorkerLostError that is not a SIGTERM shutdown."""
        exc = type('WorkerLostError', (Exception,), {})('Worker exited prematurely: signal 9 (SIGKILL).')
        hint = {'exc_info': (type(exc), exc, None)}
        event = {'message': 'worker lost'}

        assert before_send(event, hint) is event

    def test_before_send_filters_worker_shutdown(self):
        """Test that before_send drops WorkerShutdown exceptions."""
        exc = type('WorkerShutdown', (Exception,), {})('shutting down')
        hint = {'exc_info': (type(exc), exc, None)}

        assert before_send({'message': 'shutdown'}, hint) is None

    def test_before_send_keeps_other_exceptions(self):
        """Test that before_send keeps exceptions that are not worker lifecycle signals."""
        exc = ValueError('boom')
        hint = {'exc_info': (type(exc), exc, None)}
        event = {'message': 'real error'}

        assert before_send(event, hint) is event
