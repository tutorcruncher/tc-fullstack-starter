import logging
import ssl

import kombu.exceptions
import redis.exceptions
from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(__name__, broker=str(settings.redis_url), backend=str(settings.redis_url))

broker_use_ssl = {}
redis_backend_use_ssl = {}
if str(settings.redis_url).startswith('rediss://'):
    broker_use_ssl = {'ssl_cert_reqs': ssl.CERT_NONE, 'ssl_check_hostname': False}
    redis_backend_use_ssl = {'ssl_cert_reqs': ssl.CERT_NONE, 'ssl_check_hostname': False}

celery_app.conf.update(
    # Serialization: use JSON for all messages
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    event_serializer='json',
    # SSL configuration for broker and backend
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=redis_backend_use_ssl,
    # Auto-retry on transient connection errors
    task_autoretry_for=(
        kombu.exceptions.OperationalError,
        redis.exceptions.ConnectionError,
        redis.exceptions.TimeoutError,
    ),
    task_retry_kwargs={'max_retries': 3},
    task_default_retry_delay=10,
    task_retry_backoff=True,  # exponential backoff between retries
    task_retry_backoff_max=300,  # cap backoff at 5 minutes
    task_retry_jitter=True,  # add randomness to avoid thundering herd
    # Broker connection resilience
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=None,
    broker_connection_timeout=30,
    broker_transport_options={
        'health_check_interval': 30,
        'socket_keepalive': True,
        'socket_connect_timeout': 10,
        'socket_timeout': 10,
        'retry_on_timeout': True,
    },
    result_backend_transport_options={
        'retry_policy': {
            'timeout': 5.0,
            'max_retries': 3,
        }
    },
    # Task execution limits
    task_soft_time_limit=300,  # 5 min soft limit (raises SoftTimeLimitExceeded)
    task_time_limit=600,  # 10 min hard limit (kills worker)
    # Reliability: ack after task completes, reject if worker crashes
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Worker tuning
    worker_prefetch_multiplier=1,  # fetch one task at a time for fair scheduling
    worker_max_tasks_per_child=1000,  # restart worker process after 1000 tasks to reclaim memory
    worker_disable_rate_limits=True,
    worker_cancel_long_running_tasks_on_connection_loss=False,
    # Add scheduled tasks here, e.g.:
    # 'nightly-cleanup': {'task': 'example_domain.tasks.cleanup', 'schedule': crontab(hour=2, minute=0)}
    beat_schedule={},
)

if settings.run_jobs_sync:
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)
