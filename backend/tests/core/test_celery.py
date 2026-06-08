"""Tests for the Celery application configuration in app.core.celery."""

import importlib
import ssl
from unittest.mock import patch

import kombu.exceptions
import pytest
import redis.exceptions

import app.core.celery as celery_module
from app.core.celery import celery_app
from app.core.config import settings


class TestCeleryBrokerConfig:
    """Tests for the broker and result-backend configuration."""

    def test_broker_and_backend_point_at_redis(self):
        """Test that the broker and result backend both point at the same Redis URL."""
        assert celery_app.conf.broker_url == celery_app.conf.result_backend
        assert celery_app.conf.broker_url.startswith('redis://')

    def test_broker_use_ssl_disabled_for_plain_redis(self):
        """Test that SSL options are empty when the Redis URL is not rediss://."""
        assert celery_app.conf.broker_use_ssl == {}
        assert celery_app.conf.redis_backend_use_ssl == {}


class TestCelerySerializationConfig:
    """Tests for the JSON serialization configuration."""

    def test_serialization_is_json_everywhere(self):
        """Test that task, result, and event serialization all use JSON."""
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.event_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']


class TestCeleryRetryConfig:
    """Tests for the auto-retry and connection-resilience configuration."""

    def test_autoretry_for_transient_connection_errors(self):
        """Test that tasks auto-retry on the expected transient connection errors."""
        assert celery_app.conf.task_autoretry_for == (
            kombu.exceptions.OperationalError,
            redis.exceptions.ConnectionError,
            redis.exceptions.TimeoutError,
        )

    def test_retry_policy_values(self):
        """Test the retry count, delay, backoff, and jitter configuration."""
        assert celery_app.conf.task_retry_kwargs == {'max_retries': 3}
        assert celery_app.conf.task_default_retry_delay == 10
        assert celery_app.conf.task_retry_backoff is True
        assert celery_app.conf.task_retry_backoff_max == 300
        assert celery_app.conf.task_retry_jitter is True

    def test_broker_connection_resilience(self):
        """Test the broker connection retry and transport-option configuration."""
        assert celery_app.conf.broker_connection_retry is True
        assert celery_app.conf.broker_connection_retry_on_startup is True
        assert celery_app.conf.broker_connection_max_retries is None
        assert celery_app.conf.broker_connection_timeout == 30
        assert celery_app.conf.broker_transport_options == {
            'health_check_interval': 30,
            'socket_keepalive': True,
            'socket_connect_timeout': 10,
            'socket_timeout': 10,
            'retry_on_timeout': True,
        }
        assert celery_app.conf.result_backend_transport_options == {'retry_policy': {'timeout': 5.0, 'max_retries': 3}}


class TestCeleryExecutionConfig:
    """Tests for execution limits, reliability, and worker-tuning configuration."""

    def test_task_time_limits(self):
        """Test the soft and hard task time limits."""
        assert celery_app.conf.task_soft_time_limit == 300
        assert celery_app.conf.task_time_limit == 600

    def test_reliability_settings(self):
        """Test that tasks ack late and are rejected when a worker is lost."""
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True

    def test_worker_tuning_settings(self):
        """Test the worker prefetch, recycling, and rate-limit configuration."""
        assert celery_app.conf.worker_prefetch_multiplier == 1
        assert celery_app.conf.worker_max_tasks_per_child == 1000
        assert celery_app.conf.worker_disable_rate_limits is True
        assert celery_app.conf.worker_cancel_long_running_tasks_on_connection_loss is False

    def test_beat_schedule_is_empty(self):
        """Test that no scheduled tasks are configured by default."""
        assert celery_app.conf.beat_schedule == {}


class TestCeleryEagerMode:
    """Tests for synchronous (eager) task execution under run_jobs_sync."""

    def test_eager_mode_enabled_in_test_environment(self):
        """Test that the test session runs tasks eagerly and propagates their exceptions."""
        assert celery_app.conf.task_always_eager is True
        assert celery_app.conf.task_eager_propagates is True


@pytest.fixture(name='reloadable_celery_module')
def reloadable_celery_module_fixture():
    """Yield the celery module for reload-based branch tests, restoring the original app after.

    Reloading rebinds ``app.core.celery.celery_app`` to a fresh ``Celery`` instance, so the
    module attribute is restored to the original (eager-configured) object afterwards to keep
    task dispatch in the shared session pointed at the in-process eager app.
    """
    original_app = celery_module.celery_app
    yield celery_module
    celery_module.celery_app = original_app


class TestCeleryConfigBranches:
    """Tests for import-time configuration branches not exercised by the default test settings."""

    def test_run_jobs_sync_enables_eager_mode_on_import(self, reloadable_celery_module):
        """Test that importing with run_jobs_sync enabled turns on eager task execution."""
        with patch.object(settings, 'run_jobs_sync', True):
            reloaded = importlib.reload(reloadable_celery_module)

        assert reloaded.celery_app.conf.task_always_eager is True
        assert reloaded.celery_app.conf.task_eager_propagates is True

    def test_rediss_url_enables_ssl_options_on_import(self, reloadable_celery_module):
        """Test that a rediss:// URL configures SSL options for the broker and backend."""
        with patch.object(settings, 'redis_url', 'rediss://localhost:6379/1'):
            reloaded = importlib.reload(reloadable_celery_module)

        assert reloaded.celery_app.conf.broker_use_ssl == {
            'ssl_cert_reqs': ssl.CERT_NONE,
            'ssl_check_hostname': False,
        }
        assert reloaded.celery_app.conf.redis_backend_use_ssl == {
            'ssl_cert_reqs': ssl.CERT_NONE,
            'ssl_check_hostname': False,
        }
