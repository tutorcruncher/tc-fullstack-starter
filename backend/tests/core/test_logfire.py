"""Tests covering logging and Logfire configuration in ``app/core/logging.py``.

``configure_logging`` installs a single stdout handler at INFO on the root logger.
``configure_logfire`` is a no-op unless ``settings.logfire_token`` is set, in which case it
configures Logfire (scrubbing depending on ``dev_mode``) and instruments sqlalchemy, celery,
requests and httpx.
"""

import logging
import sys
from unittest.mock import patch

from logfire import ScrubbingOptions

from app.core.database import engine
from app.core.logging import configure_logfire, configure_logging


def test_configure_logging_installs_single_stdout_info_handler():
    """``configure_logging`` sets the root logger to INFO with one stdout StreamHandler."""
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_handlers = root_logger.handlers[:]
    root_logger.handlers = []
    try:
        configure_logging()

        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream is sys.stdout
        assert handler.level == logging.INFO
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)


@patch('app.core.logging.logfire')
@patch('app.core.logging.settings')
def test_configure_logfire_without_token_is_a_noop(mock_settings, mock_logfire):
    """Without ``logfire_token``, Logfire is neither configured nor instrumented."""
    mock_settings.logfire_token = None

    configure_logfire()

    mock_logfire.configure.assert_not_called()
    mock_logfire.instrument_sqlalchemy.assert_not_called()
    mock_logfire.instrument_celery.assert_not_called()
    mock_logfire.instrument_requests.assert_not_called()
    mock_logfire.instrument_httpx.assert_not_called()


@patch('app.core.logging.logfire')
@patch('app.core.logging.settings')
def test_configure_logfire_with_token_not_dev_mode_enables_scrubbing(mock_settings, mock_logfire):
    """With a token and ``dev_mode`` False, scrubbing is enabled and all instrumentors run."""
    mock_settings.logfire_token = 'test-token'
    mock_settings.dev_mode = False
    mock_settings.logfire_environment = 'production'
    mock_settings.logfire_service_name = 'fastapi-sqlmodel-starter'

    configure_logfire()

    mock_logfire.configure.assert_called_once_with(
        token='test-token',
        environment='production',
        service_name='fastapi-sqlmodel-starter',
        distributed_tracing=True,
        scrubbing=mock_logfire.configure.call_args.kwargs['scrubbing'],
    )
    assert isinstance(mock_logfire.configure.call_args.kwargs['scrubbing'], ScrubbingOptions)
    mock_logfire.instrument_sqlalchemy.assert_called_once_with(engine=engine)
    mock_logfire.instrument_celery.assert_called_once_with()
    mock_logfire.instrument_requests.assert_called_once_with()
    mock_logfire.instrument_httpx.assert_called_once_with()


@patch('app.core.logging.logfire')
@patch('app.core.logging.settings')
def test_configure_logfire_with_token_dev_mode_disables_scrubbing(mock_settings, mock_logfire):
    """With a token and ``dev_mode`` True, scrubbing is disabled but instrumentors still run."""
    mock_settings.logfire_token = 'test-token'
    mock_settings.dev_mode = True
    mock_settings.logfire_environment = 'development'
    mock_settings.logfire_service_name = 'fastapi-sqlmodel-starter'

    configure_logfire()

    mock_logfire.configure.assert_called_once_with(
        token='test-token',
        environment='development',
        service_name='fastapi-sqlmodel-starter',
        distributed_tracing=True,
        scrubbing=False,
    )
    mock_logfire.instrument_sqlalchemy.assert_called_once_with(engine=engine)
    mock_logfire.instrument_celery.assert_called_once_with()
    mock_logfire.instrument_requests.assert_called_once_with()
    mock_logfire.instrument_httpx.assert_called_once_with()
