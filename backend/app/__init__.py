"""Application package.

Importing every model module here guarantees that ``SQLModel.metadata`` is fully
populated before anything that reads it runs — Alembic autogenerate (which diffs the
metadata against the database) and the test suite's ``create_test_schema`` (which calls
``SQLModel.metadata.create_all``). If a model is not imported somewhere on the path to
those entry points, its table silently disappears from the diff/schema, so we register
them all here once.
"""

from app.auth.models import User  # noqa: F401
from app.example_domain.models.example_resource import (  # noqa: F401
    ExampleResource,
    ExampleResourceParticipant,
)
from app.organization.models.api_key import OrganizationApiKey  # noqa: F401
from app.organization.models.organization import Organization  # noqa: F401
