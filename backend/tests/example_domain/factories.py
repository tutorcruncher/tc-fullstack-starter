import factory

from app.example_domain.models.example_resource import (
    ExampleResource,
    ExampleResourceParticipant,
    ResourceStatus,
)
from tests.base_factory import SQLModelFactory


class ExampleResourceFactory(SQLModelFactory):
    """Factory for the ``ExampleResource`` domain entity.

    Pass ``organization=<org>`` to attach the resource to a tenant; it is resolved to
    ``organization_id`` before persisting.
    """

    class Meta:
        model = ExampleResource

    name = factory.Sequence(lambda n: f'Example Resource {n}')
    description = None
    status = ResourceStatus.DRAFT
    is_demo = False

    @classmethod
    def create_with_db(cls, db, **kwargs):
        """Create a resource, resolving an ``organization=`` shortcut to ``organization_id``."""
        organization = kwargs.pop('organization', None)
        if organization is not None:
            kwargs['organization_id'] = organization.id
        return super().create_with_db(db, **kwargs)


class ExampleResourceParticipantFactory(SQLModelFactory):
    """Factory for ``ExampleResourceParticipant`` children of an ``ExampleResource``.

    Pass ``example_resource=<resource>`` to attach the participant to its parent; it is
    resolved to ``example_resource_id`` before persisting.
    """

    class Meta:
        model = ExampleResourceParticipant

    name = factory.Faker('name')
    email = factory.Sequence(lambda n: f'participant_{n}@example.com')

    @classmethod
    def create_with_db(cls, db, **kwargs):
        """Create a participant, resolving an ``example_resource=`` shortcut to its id."""
        example_resource = kwargs.pop('example_resource', None)
        if example_resource is not None:
            kwargs['example_resource_id'] = example_resource.id
        return super().create_with_db(db, **kwargs)
