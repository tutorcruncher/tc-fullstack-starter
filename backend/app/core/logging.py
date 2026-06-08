import logging
import sys

import logfire
from logfire import ScrubbingOptions

from app.core.config import settings
from app.core.database import engine


def configure_logging():
    """Configure logging for the entire application.

    Sets the root logger to INFO with a single stdout handler. Called at module import
    time in ``app/main.py`` so logs are formatted consistently from the first line.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s: %(message)s', datefmt='%H:%M:%S'))

    logger.addHandler(console_handler)


def configure_logfire():
    """Configure Logfire with the project token and environment settings.

    Only runs when ``settings.logfire_token`` is set (so local/test runs stay quiet).
    Scrubbing is enabled whenever ``dev_mode`` is False so attributes whose keys match
    sensitive-data patterns (password, token, secret, etc.) are masked before export in
    staging/production; in ``dev_mode`` it is disabled to keep local traces readable.
    Call this BEFORE ``logfire.instrument_fastapi(app)``.
    """
    if not settings.logfire_token:
        return
    if settings.dev_mode:
        scrubbing: ScrubbingOptions | bool = False
    else:
        scrubbing = ScrubbingOptions()
    logfire.configure(
        token=settings.logfire_token,
        environment=settings.logfire_environment,
        service_name=settings.logfire_service_name,
        distributed_tracing=True,
        scrubbing=scrubbing,
    )
    logfire.instrument_sqlalchemy(engine=engine)
    logfire.instrument_celery()
    logfire.instrument_requests()
    logfire.instrument_httpx()
