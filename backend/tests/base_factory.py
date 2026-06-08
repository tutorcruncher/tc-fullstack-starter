import factory

from app.core.database import DBSession


class SQLModelFactory(factory.Factory):
    """Base factory for SQLModel objects.

    ``create_with_db(db, **kwargs)`` is the only public entry point. ``factory.Factory``'s
    own ``create()``/``build()`` are not used directly because a SQLModel row needs a live
    session to be persisted, and the session is per-test — so it is bound at call time rather
    than configured on the factory class.
    """

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Instantiate the model and persist it using the bound session.

        Requires a session to have been bound via ``create_with_db``; calling the underlying
        ``factory`` API directly raises ``NotImplementedError`` from ``_get_db_session``.
        """
        db = cls._get_db_session()
        obj = model_class(*args, **kwargs)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @classmethod
    def _get_db_session(cls) -> DBSession:
        """Return the session bound by ``create_with_db`` (raises until one is bound)."""
        raise NotImplementedError('Database session not available. Use create_with_db().')

    @classmethod
    def create_with_db(cls, db: DBSession, **kwargs):
        """Create and persist an instance using ``db``.

        Temporarily binds ``db`` as the session ``_create`` reads, then restores the previous
        binding so factories never leak a session between tests.
        """
        original_method = cls._get_db_session

        def get_db_session():
            return db

        cls._get_db_session = get_db_session
        try:
            return cls.create(**kwargs)
        finally:
            cls._get_db_session = original_method
