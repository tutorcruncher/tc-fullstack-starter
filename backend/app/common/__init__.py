"""Shared application primitives: model base, field factories, errors, pagination, filters.

Re-exported here so domain code can ``from app.common import AppModel, FKField, HTTP404`` etc.
without reaching into submodules. The re-exports are resolved lazily via module-level
``__getattr__`` (PEP 562): importing ``app.common`` itself pulls in nothing, so this package can
be imported during early model setup without triggering ``app.common.api.filters`` (which imports
``app.auth.models``) and the import cycle that would otherwise create.

Static type checkers do not follow ``__getattr__`` re-exports — for typed code prefer importing
directly from the owning submodule (``from app.common.models import AppModel``).
"""

import importlib

# Maps each re-exported name to the submodule it lives in. ``__getattr__`` imports the owning
# submodule on first access only, keeping ``import app.common`` side-effect free.
_EXPORTS = {
    'AppModel': 'app.common.models',
    'UTCDateTime': 'app.common.fields',
    'UTCDatetimeField': 'app.common.fields',
    'EnumField': 'app.common.fields',
    'FKField': 'app.common.fields',
    'escape_like': 'app.common.utils',
    'inclusive_end_of_day': 'app.common.utils',
    'sanitize_for_postgres': 'app.common.utils',
    'PaginatedResponse': 'app.common.api.paginate',
    'OrderDirection': 'app.common.api.filters',
    'ListOrder': 'app.common.api.filters',
    'ListFilter': 'app.common.api.filters',
    'FKIntMeta': 'app.common.api.filters',
    'FKFilterField': 'app.common.api.filters',
    'HTTP400': 'app.common.api.errors',
    'HTTP401': 'app.common.api.errors',
    'HTTP402': 'app.common.api.errors',
    'HTTP403': 'app.common.api.errors',
    'HTTP404': 'app.common.api.errors',
    'HTTP409': 'app.common.api.errors',
    'HTTP422': 'app.common.api.errors',
    'HTTP429': 'app.common.api.errors',
    'HTTP500': 'app.common.api.errors',
    'get_client_ip': 'app.common.api.rate_limit',
    'rate_limit': 'app.common.api.rate_limit',
    'confirm_rate_limit': 'app.common.api.rate_limit',
    'public_api_rate_limit': 'app.common.api.rate_limit',
    'rate_limit_by_ip': 'app.common.api.rate_limit',
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    module_path = _EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    return getattr(importlib.import_module(module_path), name)
