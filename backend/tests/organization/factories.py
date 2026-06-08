import factory

from app.auth.keys import generate_api_key
from app.auth.login import get_password_hash
from app.auth.models import User, UserRole
from app.organization.models.api_key import OrganizationApiKey
from app.organization.models.organization import Organization
from tests.base_factory import SQLModelFactory

DEFAULT_PASSWORD = 'testing-password'


class OrganizationFactory(SQLModelFactory):
    """Factory for the tenant ``Organization``."""

    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f'Test Organization {n}')


class UserFactory(SQLModelFactory):
    """Factory for a MEMBER ``User``.

    All roles share a known password (``DEFAULT_PASSWORD``) so login tests can authenticate
    without re-hashing. Pass ``organization=<org>`` to attach the user to a tenant.
    """

    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Sequence(lambda n: f'User_{n}')
    role = UserRole.MEMBER
    is_superadmin = False
    hashed_password = factory.LazyFunction(lambda: get_password_hash(DEFAULT_PASSWORD))

    @factory.LazyAttribute
    def email(self):
        """Derive a unique email from the first and last name."""
        return f'{self.first_name}_{self.last_name}@example.com'.lower().replace(' ', '_')

    @classmethod
    def create_with_db(cls, db, **kwargs):
        """Create a user, resolving an ``organization=`` shortcut to ``organization_id``."""
        organization = kwargs.pop('organization', None)
        if organization is not None:
            kwargs['organization_id'] = organization.id
        return super().create_with_db(db, **kwargs)


class AdminFactory(UserFactory):
    """Factory for an ADMIN ``User``."""

    last_name = factory.Sequence(lambda n: f'Admin_{n}')
    role = UserRole.ADMIN


class MemberFactory(UserFactory):
    """Factory for a MEMBER ``User`` (explicit alias of the base member role)."""

    last_name = factory.Sequence(lambda n: f'Member_{n}')
    role = UserRole.MEMBER


class OrganizationApiKeyFactory(SQLModelFactory):
    """Factory for ``OrganizationApiKey``.

    Deviates from the single-object ``create_with_db`` contract: it generates and hashes a
    real token inside the factory and returns ``(key_row, full_key)`` so tests can authenticate
    with the plaintext key (which is never stored). Callers unpack the tuple.
    """

    class Meta:
        model = OrganizationApiKey

    name = factory.Sequence(lambda n: f'Test Key {n}')

    @classmethod
    def create_with_db(cls, db, **kwargs):
        """Create a key row and return ``(key_row, full_key)``; ``full_key`` is never persisted."""
        organization = kwargs.pop('organization', None)
        if organization is not None:
            kwargs['organization_id'] = organization.id

        full_key, last4, hashed_key = generate_api_key()
        kwargs.setdefault('hashed_key', hashed_key)
        kwargs.setdefault('last4', last4)

        key_row = super().create_with_db(db, **kwargs)
        return key_row, full_key
