"""Sentry initialization and configuration."""

import logging

from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)


def before_send(event, hint):
    """Filter out expected operational errors before sending to Sentry.

    Worker shutdown signals (SIGTERM) and ``WorkerShutdown`` exceptions are expected
    during deploys/restarts and would otherwise be noise.
    """
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        if exc_type.__name__ == 'WorkerLostError':
            error_msg = str(exc_value)
            if 'signal 15 (SIGTERM)' in error_msg:
                logger.debug('Filtered WorkerLostError from Sentry: %s', error_msg)
                return None

        if exc_type.__name__ == 'WorkerShutdown':
            logger.debug('Filtered WorkerShutdown from Sentry')
            return None

    return event


def init_sentry() -> None:
    """Initialize the Sentry SDK with Celery + logging integrations if a DSN is configured."""
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            integrations=[
                CeleryIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            before_send=before_send,
        )
        logger.info('Sentry initialized')
