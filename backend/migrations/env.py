import logging
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

sys.path.insert(0, str(Path(__file__).parent.parent))

# Importing the app package registers every model with SQLModel.metadata (see app/__init__.py),
# so autogenerate has the full table set to diff against the database.
import app  # noqa: E402, F401
from app.core.config import settings  # noqa: E402

config = context.config

# Exclude test-only tables (any whose name starts with ``test_``) from the target metadata so
# autogenerate never tries to add/drop throwaway tables created by the test suite.
filtered_metadata = SQLModel.metadata.__class__()
for table in SQLModel.metadata.tables.values():
    if not table.name.startswith('test_'):
        table.to_metadata(filtered_metadata)

target_metadata = filtered_metadata

logging.getLogger('alembic').setLevel(logging.WARNING)


def get_database_url() -> str:
    """Return the database URL, preferring the test database when running under pytest."""
    if settings.testing:
        return os.getenv('TEST_DATABASE_URL', settings.database_url)
    return os.getenv('DATABASE_URL', settings.database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a live DBAPI connection)."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live connection."""
    connectable = create_engine(get_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
