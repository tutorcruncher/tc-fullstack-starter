import logging
from contextlib import asynccontextmanager

import logfire
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

from app.auth.api.login import anon_router as auth_anon_router
from app.auth.jwt import auth_user
from app.auth.permissions import Permission
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.logging import configure_logfire, configure_logging
from app.core.sentry import init_sentry
from app.example_domain.api.example_resources import router as example_resources_router
from app.example_domain.public_api import example_resources_public_router
from app.organization.api.api_keys import router as api_keys_router

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables (tests), register Celery tasks, init observability."""
    logger.info('Starting up FastAPI SQLModel Starter...')
    create_db_and_tables()
    logger.info('Database tables created')

    # Celery tasks must be imported during startup so the task registry is populated.
    from app.example_domain import tasks  # noqa: F401

    logger.info('Celery tasks registered')

    init_sentry()

    if settings.logfire_token:
        configure_logfire()
        logfire.instrument_fastapi(app)

    yield

    logger.info('Shutting down FastAPI SQLModel Starter...')


app = FastAPI(title='FastAPI SQLModel Starter', version='0.1.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.allowed_origins.split(','),
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'Accept', 'Origin', 'X-Requested-With'],
)


@app.get('/scalar', include_in_schema=False)
async def scalar_docs() -> HTMLResponse:
    """Serve the Scalar API reference for the main (authenticated) API."""
    return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)


@app.get('/', name='health', dependencies=[Depends(Permission.anonymous)])
async def health() -> dict:
    """Unauthenticated healthcheck."""
    return {'status': 'healthy'}


# -------------------------------------------------------------------
# 'auth' routers (anonymous)
# -------------------------------------------------------------------
app.include_router(auth_anon_router, dependencies=[Depends(Permission.anonymous)])


# -------------------------------------------------------------------
# 'organization' + 'example_domain' routers (authenticated)
# -------------------------------------------------------------------
app.include_router(api_keys_router, dependencies=[Depends(auth_user)])
app.include_router(example_resources_router, dependencies=[Depends(auth_user)])


# -------------------------------------------------------------------
# Public API ('/api/v1') — read-only, per-organization API keys
# -------------------------------------------------------------------
# A separate FastAPI instance so its OpenAPI schema and Scalar docs stay public: auth is a
# router-level dependency on each public router (api_key_auth + public_api_rate_limit), never
# applied to the sub-app, so /api/v1/openapi.json and /api/v1/scalar are readable without a key.
public_app = FastAPI(title='FastAPI SQLModel Starter Public API', version='1.0.0')

public_app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.allowed_origins.split(','),
    allow_credentials=True,
    allow_methods=['GET', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'Accept', 'Origin', 'X-Requested-With'],
)


@public_app.get('/scalar', include_in_schema=False)
async def public_scalar_docs() -> HTMLResponse:
    """Serve the Scalar API reference for the public API at /api/v1/scalar."""
    return get_scalar_api_reference(openapi_url='/api/v1/openapi.json', title=public_app.title)


public_app.include_router(example_resources_public_router)

if settings.logfire_token:
    logfire.instrument_fastapi(public_app)

app.mount('/api/v1', public_app)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('app.main:app', host=settings.host, port=settings.port, reload=True)
