#!/usr/bin/env python3
"""Thin CLI around Alembic so migrations can be created and applied via ``uv run``.

Usage:
    uv run python migrations/client.py create   # autogenerate a new revision from the models
    uv run python migrations/client.py upgrade  # apply all pending migrations (alembic upgrade head)
    uv run python migrations/client.py show     # print history + current revision

The Alembic config lives under ``[tool.alembic]`` in ``pyproject.toml`` (there is no standalone
``alembic.ini``); ``create()`` reads it to build the ``Config`` in-process, while ``upgrade()``
shells out to the ``alembic`` console script.
"""

import subprocess
import sys
import tomllib
from pathlib import Path

from alembic import command
from alembic.config import Config

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / 'pyproject.toml'


def _alembic_config() -> Config:
    """Build an Alembic ``Config`` from the ``[tool.alembic]`` table in pyproject.toml."""
    with open(PYPROJECT_PATH, 'rb') as f:
        alembic_data = tomllib.load(f).get('tool', {}).get('alembic', {})

    config = Config()
    config.set_main_option('script_location', alembic_data.get('script_location', 'migrations'))
    return config


def create() -> None:
    """Check the models are in sync, then autogenerate a new revision."""
    print('Checking that the models are up to date...')
    command.check(_alembic_config())
    print('Autogenerating migration...')
    command.revision(_alembic_config(), autogenerate=True)


def upgrade() -> bool:
    """Apply all pending migrations via ``alembic upgrade head``."""
    print('Applying migrations...')
    result = subprocess.run(['uv', 'run', 'alembic', 'upgrade', 'head'], capture_output=True, text=True)
    if result.returncode == 0:
        print('Migrations applied successfully')
        print(result.stdout)
        return True
    print('Failed to apply migrations:')
    print(result.stderr)
    return False


def show() -> None:
    """Print the migration history and the current revision."""
    print('Migration history:')
    subprocess.run(['uv', 'run', 'alembic', 'history'])
    print('\nCurrent revision:')
    subprocess.run(['uv', 'run', 'alembic', 'current'])


def main() -> None:
    """Dispatch the CLI subcommand (create/upgrade/show)."""
    if len(sys.argv) < 2:
        print('Usage:')
        print('  uv run python migrations/client.py create')
        print('  uv run python migrations/client.py upgrade')
        print('  uv run python migrations/client.py show')
        return

    subcommand = sys.argv[1]
    if subcommand == 'create':
        create()
    elif subcommand == 'upgrade':
        upgrade()
    elif subcommand == 'show':
        show()
    else:
        print(f'Unknown command: {subcommand}')


if __name__ == '__main__':
    main()
