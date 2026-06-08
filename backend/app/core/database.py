from typing import TypeVar

from sqlalchemy import create_engine, exists, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import SelectOfScalar

from app.common.api.errors import HTTP404
from app.core.config import settings

T = TypeVar('T', bound=SQLModel)


class DBSession(Session):
    """Custom SQLModel session class that can be extended with additional methods if needed."""

    def create(self, instance):
        """Add, commit and refresh an instance in the session."""
        self.add(instance)
        self.commit()
        self.refresh(instance)
        return instance

    def exists(self, model: type[T], **kwargs) -> bool:
        """Check if an instance exists in the database.

        Args:
            model: The SQLModel class
            **kwargs: Fields to filter by

        Returns:
            True if an instance exists, False otherwise
        """
        wheres = [getattr(model, key) == value for key, value in kwargs.items()]
        return bool(self.exec(select(exists().where(*wheres))).one())

    def get_or_404(self, query_or_model: type[T] | SelectOfScalar, **kwargs) -> T:
        """Get an instance by filtering fields or raise an error if not found.

        Args:
            query_or_model: Either a SQLModel class or a SelectOfScalar query
            **kwargs: Fields to filter by

        Returns:
            The instance if found

        Raises:
            HTTP404: If no instance is found
        """
        if isinstance(query_or_model, SelectOfScalar):
            instance = self.exec(query_or_model.filter_by(**kwargs)).one_or_none()
            model_name = query_or_model.column_descriptions[0]['name']
        else:
            instance = self.exec(select(query_or_model).filter_by(**kwargs)).one_or_none()
            model_name = query_or_model.__name__
        if not instance:
            raise HTTP404(f'{model_name} not found')
        return instance

    def get_or_create(self, model: type[T], defaults: dict | None = None, **kwargs) -> tuple[T, bool]:
        """Get an existing instance or create a new one, similar to Django's get_or_create.

        Args:
            model: The SQLModel class
            defaults: Dictionary of field values to use when creating a new instance
            **kwargs: Fields to filter by when looking for an existing instance

        Returns:
            tuple of (instance, created) where created is True if a new instance was created
        """
        stmt = select(model)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(model, key) == value)

        instance = self.exec(stmt).one_or_none()
        if instance:
            return instance, False

        create_kwargs = {**kwargs, **(defaults or {})}
        instance = model(**create_kwargs)

        try:
            self.add(instance)
            self.commit()
            self.refresh(instance)
            return instance, True
        except IntegrityError:
            self.rollback()
            instance = self.exec(stmt).one()
            return instance, False

    def create_or_update(self, model: type[T], defaults: dict | None = None, **kwargs) -> tuple[T, bool]:
        """Create a new instance or update an existing one, similar to Django's update_or_create.

        Args:
            model: The SQLModel class
            defaults: Dictionary of field values to use when creating or updating
            **kwargs: Fields to filter by when looking for an existing instance

        Returns:
            tuple of (instance, created) where created is True if a new instance was created
        """
        stmt = select(model)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(model, key) == value)

        instance = self.exec(stmt).one_or_none()
        defaults = defaults or {}

        if instance:
            for key, value in defaults.items():
                setattr(instance, key, value)
            self.commit()
            self.refresh(instance)
            return instance, False

        create_kwargs = {**kwargs, **defaults}
        instance = model(**create_kwargs)

        try:
            self.add(instance)
            self.commit()
            self.refresh(instance)
            return instance, True
        except IntegrityError:
            self.rollback()
            instance = self.exec(stmt).one()
            for key, value in defaults.items():
                setattr(instance, key, value)
            self.commit()
            self.refresh(instance)
            return instance, False


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(class_=DBSession, autocommit=False, autoflush=False, bind=engine)

SessionCls = SessionLocal  # Indirection so tests can swap in a test-scoped session factory.


def get_session() -> DBSession:
    """Return a standalone session for Celery tasks and scripts: ``with get_session() as db:``."""
    return SessionCls()


def create_db_and_tables():
    """Idempotently create the pg_trgm extension and all SQLModel tables (used by tests)."""
    if engine.dialect.name == 'postgresql':
        with engine.begin() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))
    SQLModel.metadata.create_all(engine)


def get_db():
    """FastAPI dependency yielding a request-scoped session, closed in ``finally``."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
