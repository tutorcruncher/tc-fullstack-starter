from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, TypeDecorator
from sqlmodel import Field


class UTCDateTime(TypeDecorator):
    """Always store datetimes in UTC, always return UTC datetimes."""

    cache_ok = True
    impl = DateTime(timezone=True)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.astimezone(timezone.utc)


def UTCDatetimeField(now_add: bool = False, auto_now: bool = False, **kwargs):
    """Create a UTC datetime field.

    Args:
        now_add: If True, set the current datetime on creation only
        auto_now: If True, set the current datetime on every update (and creation)
        **kwargs: Additional arguments passed to the Column
    """
    if now_add or auto_now:

        def default_factory():
            return datetime.now(tz=timezone.utc)
    else:

        def default_factory():
            return None

    if auto_now:
        kwargs['onupdate'] = lambda: datetime.now(tz=timezone.utc)

    desc = kwargs.pop('description', None)
    exclude = kwargs.pop('exclude', None)
    return Field(
        sa_column=Column(UTCDateTime(), **kwargs),
        default_factory=default_factory,
        description=desc,
        exclude=exclude,
    )


def EnumField(enum_class: type[Enum], **kwargs):
    """Create a Field with proper SQLAlchemy enum configuration that stores enum values."""
    desc = kwargs.pop('description', None)
    return Field(
        sa_column=Column(SQLEnum(enum_class, values_callable=lambda x: [e.value for e in x]), **kwargs),
        description=desc,
    )


def FKField(
    foreign_key: str,
    ondelete: str,
    description: str | None = None,
    nullable: bool = False,
    primary_key: bool = False,
    **kwargs,
):
    """Create an auto-indexed integer foreign-key Field.

    ``ondelete`` is required (no default) to force every FK to declare its delete behaviour.
    """
    return Field(
        sa_column=Column(
            Integer,
            ForeignKey(foreign_key, ondelete=ondelete),
            index=True,
            nullable=nullable,
            primary_key=primary_key,
            **kwargs,
        ),
        description=description,
    )
