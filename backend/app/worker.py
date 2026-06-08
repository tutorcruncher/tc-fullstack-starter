"""Celery worker entry point.

Run with ``celery -A app.worker worker``. Importing the task modules here registers them
with the worker's task registry (the same modules are imported in the FastAPI lifespan so
the web process can enqueue them).
"""

from celery.signals import worker_process_init

from app.core.celery import celery_app
from app.core.config import settings
from app.core.logging import configure_logfire
from app.core.sentry import init_sentry
from app.example_domain import tasks  # noqa: F401


@worker_process_init.connect
def init_worker_process(**kwargs):
    """Initialise Sentry and Logfire after fork so background threads start in the child process.

    On macOS, starting threads (HTTP connections, OTel exporters) in the parent process before
    fork causes SIGABRT crashes (objc_initializeAfterForkError). Both Sentry and Logfire must
    be initialised in the child process after fork.
    """
    init_sentry()

    if settings.logfire_token:
        configure_logfire()


# Expose the celery app for the -A flag.
app = celery_app

if __name__ == '__main__':
    celery_app.start()
