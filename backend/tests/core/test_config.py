"""Tests for security validation and normalization of config settings."""

import pytest

from app.core.config import DEFAULT_DEV_JWT_SECRET, INSECURE_DEFAULT_SECRETS, InsecureDefaultSecretError, Settings


class TestDatabaseUrlRewrite:
    """Tests for the postgres:// -> postgresql:// rewrite in model_post_init."""

    def test_postgres_scheme_is_rewritten_to_postgresql(self):
        """A postgres:// database_url is rewritten to postgresql:// on init."""
        settings = Settings(testing=True, database_url='postgres://user@localhost/db', _env_file=None)

        assert settings.database_url == 'postgresql://user@localhost/db'

    def test_postgresql_scheme_is_left_unchanged(self):
        """A database_url already using postgresql:// is left as-is."""
        settings = Settings(testing=True, database_url='postgresql://user@localhost/db', _env_file=None)

        assert settings.database_url == 'postgresql://user@localhost/db'


class TestSecretValidation:
    """Tests for security-sensitive settings validation."""

    def test_settings_with_testing_true_allows_insecure_defaults(self, monkeypatch):
        """Settings should accept the insecure secret_key default when testing=True."""
        monkeypatch.delenv('secret_key', raising=False)
        monkeypatch.delenv('SECRET_KEY', raising=False)

        settings = Settings(testing=True, _env_file=None)

        assert settings.secret_key == DEFAULT_DEV_JWT_SECRET

    def test_settings_with_dev_mode_true_allows_insecure_defaults(self, monkeypatch):
        """Settings should accept the insecure secret_key default when dev_mode=True."""
        monkeypatch.delenv('secret_key', raising=False)
        monkeypatch.delenv('SECRET_KEY', raising=False)

        settings = Settings(testing=False, dev_mode=True, _env_file=None)

        assert settings.secret_key == DEFAULT_DEV_JWT_SECRET

    def test_settings_with_testing_false_rejects_insecure_defaults(self, monkeypatch):
        """Settings should raise when the secret_key default is unchanged and not dev/test."""
        monkeypatch.delenv('secret_key', raising=False)
        monkeypatch.delenv('SECRET_KEY', raising=False)
        monkeypatch.delenv('dev_mode', raising=False)
        monkeypatch.delenv('DEV_MODE', raising=False)

        with pytest.raises(InsecureDefaultSecretError) as exc_info:
            Settings(testing=False, dev_mode=False, _env_file=None)

        error_message = str(exc_info.value)
        assert 'Security-sensitive settings have insecure default values' in error_message
        assert 'secret_key' in error_message

    def test_settings_with_secure_values_succeeds(self):
        """Settings should succeed with a secure secret_key in non-test mode."""
        settings = Settings(
            testing=False, dev_mode=False, secret_key='my-super-secure-secret-key-12345', _env_file=None
        )

        assert settings.secret_key == 'my-super-secure-secret-key-12345'

    def test_error_message_is_actionable(self, monkeypatch):
        """The error message should tell users to set secure environment variables."""
        monkeypatch.delenv('secret_key', raising=False)
        monkeypatch.delenv('SECRET_KEY', raising=False)
        monkeypatch.delenv('dev_mode', raising=False)
        monkeypatch.delenv('DEV_MODE', raising=False)

        with pytest.raises(InsecureDefaultSecretError) as exc_info:
            Settings(testing=False, dev_mode=False, _env_file=None)

        assert 'non-test mode' in str(exc_info.value)

    def test_insecure_default_secrets_constant_has_all_secrets(self):
        """Verify the INSECURE_DEFAULT_SECRETS constant contains the expected keys."""
        assert set(INSECURE_DEFAULT_SECRETS.keys()) == {'secret_key'}
        assert INSECURE_DEFAULT_SECRETS['secret_key'] == DEFAULT_DEV_JWT_SECRET


class TestWebsiteUrlValidator:
    """Tests for the website_url is-in-allowed_origins startup validator."""

    def test_default_website_url_is_in_default_allowed_origins(self):
        """The default website_url is in the default allowed_origins."""
        settings = Settings(testing=True, _env_file=None)

        assert settings.website_url == 'http://localhost:3000'
        assert 'http://localhost:3000' in settings.allowed_origins

    def test_website_url_in_allowed_origins_succeeds(self):
        """Settings should construct cleanly when website_url is in allowed_origins."""
        settings = Settings(
            testing=True,
            allowed_origins='http://localhost:3000,https://www.example.com',
            website_url='https://www.example.com',
            _env_file=None,
        )

        assert settings.website_url == 'https://www.example.com'

    def test_website_url_missing_from_allowed_origins_raises(self):
        """Settings should raise when website_url is set but not in allowed_origins."""
        with pytest.raises(ValueError) as exc_info:
            Settings(
                testing=True,
                allowed_origins='http://localhost:3000',
                website_url='https://www.example.com',
                _env_file=None,
            )

        error_message = str(exc_info.value)
        assert 'website_url must also appear in allowed_origins' in error_message
        assert 'https://www.example.com' in error_message


class TestDefaultValues:
    """Tests for the default values of pagination and public-API settings."""

    def test_default_values(self):
        """Default pagination and public-API rate-limit values are as expected."""
        settings = Settings(testing=True, _env_file=None)

        assert settings.dft_page_size == 50
        assert settings.public_api_rate_limit_per_minute == 600
        assert settings.public_api_rate_limit_window_seconds == 60
