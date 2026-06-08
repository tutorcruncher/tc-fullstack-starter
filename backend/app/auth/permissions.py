from typing import Callable

from fastapi import Depends, Request

from app.auth.jwt import auth_user
from app.auth.models import User, UserRole
from app.common.api.errors import HTTP403


class PermissionCheck:
    """A composable role check usable as a FastAPI dependency.

    Combine checks with ``|`` (OR) and ``&`` (AND) to build route guards:

        # Single role
        Depends(Permission.is_admin)

        # Either role
        Depends(Permission.is_admin | Permission.is_member)

        # Both conditions (e.g. once feature-flag checks are added)
        Depends(Permission.is_admin & Permission.is_superadmin)
    """

    def __init__(self, check_func: Callable[[User], bool], name: str):
        self.check_func = check_func
        self.name = name

    def __or__(self, other: 'PermissionCheck') -> 'PermissionCheck':
        """Combine with ``|`` for OR logic."""

        def combined_check(user: User) -> bool:
            return self.check_func(user) or other.check_func(user)

        return PermissionCheck(combined_check, f'{self.name} or {other.name}')

    def __and__(self, other: 'PermissionCheck') -> 'PermissionCheck':
        """Combine with ``&`` for AND logic."""

        def combined_check(user: User) -> bool:
            return self.check_func(user) and other.check_func(user)

        return PermissionCheck(combined_check, f'{self.name} and {other.name}')

    def __call__(self, request: Request, user: User = Depends(auth_user)) -> User:
        """Authenticate, then enforce the check; raise HTTP403 if it fails."""
        if self.check_func(user):
            return user
        raise HTTP403(f'{self.name} access required')


class _AnonymousPermission:
    """Marker dependency for routes that intentionally allow unauthenticated access."""

    name = 'Anonymous'

    def __call__(self) -> None:
        pass


def role_check(role: UserRole) -> PermissionCheck:
    """Build a ``PermissionCheck`` that passes for a given role (or any superadmin).

    Use this to gate routes on custom roles you add to ``UserRole`` without hand-writing a
    new ``PermissionCheck`` each time.
    """
    return PermissionCheck(lambda user: user.role == role or user.is_superadmin, role.value.capitalize())


class Permission:
    """Role-based access guards applied as route dependencies.

    Usage:
        # As a route dependency
        @router.get('/data', dependencies=[Depends(Permission.is_admin)])

        # Any authenticated user
        @router.get('/data', dependencies=[Depends(Permission.is_member)])

        # Anonymous / public routes
        app.include_router(anon_router, dependencies=[Depends(Permission.anonymous)])
    """

    is_admin = PermissionCheck(lambda user: user.is_admin or user.is_superadmin, 'Admin')

    is_member = PermissionCheck(lambda user: True, 'Member')

    is_superadmin = PermissionCheck(lambda user: user.is_superadmin, 'Superadmin')

    everyone = PermissionCheck(lambda user: True, 'Everyone')

    anonymous = _AnonymousPermission()
