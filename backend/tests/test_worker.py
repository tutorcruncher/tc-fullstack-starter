"""Tests for the Celery worker process initialisation hook.

These tests verify the post-fork initialisation contract for ``init_worker_process``:
Sentry is always initialised, and Logfire is only configured when a token is present.
"""

from unittest.mock import patch

from app.core.celery import celery_app
from app.worker import app, init_worker_process


@patch('app.worker.configure_logfire')
@patch('app.worker.settings')
@patch('app.worker.init_sentry')
def test_init_worker_process_instruments_logfire_when_token_set(
    mock_init_sentry, mock_settings, mock_configure_logfire
):
    """When ``logfire_token`` is set, Sentry and Logfire are both initialised after fork."""
    mock_settings.logfire_token = 'test-token'

    init_worker_process()

    mock_init_sentry.assert_called_once_with()
    mock_configure_logfire.assert_called_once_with()


@patch('app.worker.configure_logfire')
@patch('app.worker.settings')
@patch('app.worker.init_sentry')
def test_init_worker_process_skips_logfire_when_token_missing(mock_init_sentry, mock_settings, mock_configure_logfire):
    """When ``logfire_token`` is empty, Sentry is initialised but Logfire is skipped."""
    mock_settings.logfire_token = ''

    init_worker_process()

    mock_init_sentry.assert_called_once_with()
    mock_configure_logfire.assert_not_called()


def test_worker_app_is_celery_app():
    """The module re-exports the Celery app as ``app`` for the ``celery -A app.worker`` flag."""
    assert app is celery_app
