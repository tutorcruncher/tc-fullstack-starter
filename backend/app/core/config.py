from pathlib import Path
from typing import Optional

from pydantic import ConfigDict, RedisDsn, model_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent.parent
PROJECT_DIR = BASE_DIR / 'app'

# Shared dev/test default for the app JWT secret. Must be >= 32 bytes for PyJWT HS256.
# It is INTENTIONALLY insecure: `_validate_secrets` refuses to boot in non-dev/test mode
# while this value is still in place, forcing every deployment to set a real secret.
DEFAULT_DEV_JWT_SECRET = 'local-dev-jwt-secret-not-for-production-use-32b!!'

INSECURE_DEFAULT_SECRETS = {
    'secret_key': DEFAULT_DEV_JWT_SECRET,
}


class InsecureDefaultSecretError(Exception):
    """Raised when security-sensitive settings have insecure default values in non-test mode."""

    pass


class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env', case_sensitive=False, extra='ignore')  # ty: ignore[invalid-key]

    # Environment
    environment: str = 'development'  # development, staging, production

    # Database
    database_url: str = 'postgresql://postgres@localhost/myapp'

    # Redis
    redis_url: RedisDsn = 'redis://localhost:6379/0'  # ty: ignore[invalid-assignment]

    # API settings
    host: str = '0.0.0.0'
    port: int = 8000
    base_url: str = 'http://localhost:8000'

    # For testing and development
    dev_mode: bool = False
    testing: bool = False

    # Public website URL (also must be included in allowed_origins)
    website_url: str = 'http://localhost:3000'

    # CORS
    allowed_origins: str = 'http://localhost:5173,http://localhost:8000,http://localhost:3000'

    # JWT authentication
    secret_key: str = DEFAULT_DEV_JWT_SECRET
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 12  # 12 hours

    # Frontend
    frontend_url: str = 'http://localhost:5173'

    # Sentry
    sentry_dsn: Optional[str] = None

    # Logfire
    logfire_token: Optional[str] = None
    logfire_environment: str = 'development'
    logfire_service_name: str = 'fastapi-sqlmodel-starter'
    logfire_traces_url: str = 'https://logfire-api.pydantic.dev/v1/traces'

    # Celery
    run_jobs_sync: bool = False

    # Pagination
    dft_page_size: int = 50

    # Public API (read-only per-org API keys)
    public_api_rate_limit_per_minute: int = 600  # Per-organization request cap per window
    public_api_rate_limit_window_seconds: int = 60  # Length of the fixed rate-limit window

    def model_post_init(self, __context) -> None:
        if self.database_url.startswith('postgres://'):
            object.__setattr__(self, 'database_url', self.database_url.replace('postgres://', 'postgresql://'))

        self._validate_secrets()

    def _validate_secrets(self) -> None:
        """Validate that security-sensitive settings do not use insecure defaults in non-test mode."""
        if self.testing or self.dev_mode:
            return

        insecure_settings = []
        for setting_name, insecure_default in INSECURE_DEFAULT_SECRETS.items():
            current_value = getattr(self, setting_name)
            if current_value == insecure_default:
                insecure_settings.append(setting_name)

        if insecure_settings:
            settings_list = ', '.join(sorted(insecure_settings))
            raise InsecureDefaultSecretError(
                f'Security-sensitive settings have insecure default values: {settings_list}. '
                f'Set these environment variables to secure values before running in non-test mode.'
            )

    @model_validator(mode='after')
    def _validate_website_url_in_allowed_origins(self) -> 'Settings':
        """Enforce that ``website_url`` also appears in ``allowed_origins``.

        Raises:
            ValueError: If ``website_url`` is missing from ``allowed_origins``.
        """
        website = self.website_url.strip()
        allowed = {o.strip() for o in self.allowed_origins.split(',') if o.strip()}
        if website not in allowed:
            raise ValueError(
                f'website_url must also appear in allowed_origins; missing from allowed_origins: {website}'
            )
        return self


settings = Settings()
