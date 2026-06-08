from datetime import datetime, timezone
from enum import Enum
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text
from sqlmodel import Field, SQLModel, select

from app.common.fields import EnumField, FKField, UTCDatetimeField
from app.core.database import DBSession


class FieldsColour(str, Enum):
    """Enum used to exercise ``EnumField`` value storage."""

    RED = 'red'
    GREEN = 'green'


class MockDatetimeModel(SQLModel, table=True):
    """Standalone model exercising the three ``UTCDatetimeField`` flavours."""

    __tablename__ = 'test_fields_datetime'

    id: int = Field(default=None, primary_key=True)
    created_at: datetime = UTCDatetimeField(now_add=True)
    updated_at: datetime = UTCDatetimeField(auto_now=True)
    scheduled_time: datetime = UTCDatetimeField()


class MockEnumModel(SQLModel, table=True):
    """Standalone model exercising ``EnumField`` value storage."""

    __tablename__ = 'test_fields_enum'

    id: int = Field(default=None, primary_key=True)
    colour: FieldsColour = EnumField(FieldsColour)


class MockFKParent(SQLModel, table=True):
    """Parent table targeted by ``MockFKChild``'s foreign key."""

    __tablename__ = 'test_fields_fk_parent'

    id: int = Field(default=None, primary_key=True)


class MockFKChild(SQLModel, table=True):
    """Child model exercising ``FKField`` indexing and ``ondelete`` behaviour."""

    __tablename__ = 'test_fields_fk_child'

    id: int = Field(default=None, primary_key=True)
    parent_id: int = FKField('test_fields_fk_parent.id', ondelete='CASCADE')


@pytest.fixture(name='fields_tables')
def fields_tables_fixture(db: DBSession):
    """Ensure the test-only tables exist on this worker's database before use.

    Defined in the test file rather than conftest, so guarantee creation here (idempotent,
    ``checkfirst``) regardless of whether the session-scoped ``create_all`` saw the model.
    """
    bind = db.get_bind()
    for model in (MockFKParent, MockFKChild, MockDatetimeModel, MockEnumModel):
        model.__table__.create(bind, checkfirst=True)
    return db


class TestUTCDateTime:
    """Test the ``UTCDateTime`` type decorator binds and returns aware UTC datetimes."""

    def test_naive_datetime_treated_as_utc(self, fields_tables: DBSession):
        """Test that a naive datetime is stored and returned as aware UTC."""
        record = MockDatetimeModel(scheduled_time=datetime(2024, 1, 15, 10, 0, 0))
        fields_tables.create(record)

        assert record.scheduled_time == datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert record.scheduled_time.tzinfo == timezone.utc

    def test_aware_datetime_converted_to_utc(self, fields_tables: DBSession):
        """Test that an aware non-UTC datetime is converted to UTC on bind."""
        tokyo_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=ZoneInfo('Asia/Tokyo'))
        record = MockDatetimeModel(scheduled_time=tokyo_time)
        fields_tables.create(record)

        assert record.scheduled_time == datetime(2024, 1, 15, 5, 30, 0, tzinfo=timezone.utc)
        assert record.scheduled_time.tzinfo == timezone.utc

    def test_already_utc_datetime_unchanged(self, fields_tables: DBSession):
        """Test that an already-UTC datetime is preserved unchanged."""
        utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        record = MockDatetimeModel(scheduled_time=utc_time)
        fields_tables.create(record)

        assert record.scheduled_time == utc_time
        assert record.scheduled_time.tzinfo == timezone.utc

    def test_retrieved_datetime_is_utc(self, fields_tables: DBSession):
        """Test that a datetime read back from the database is aware UTC."""
        est_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=ZoneInfo('America/New_York'))
        record = MockDatetimeModel(scheduled_time=est_time)
        fields_tables.create(record)

        fields_tables.expunge_all()
        retrieved = fields_tables.exec(select(MockDatetimeModel).where(MockDatetimeModel.id == record.id)).one()

        assert retrieved.scheduled_time == datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
        assert retrieved.scheduled_time.tzinfo == timezone.utc

    def test_none_value_handled(self, fields_tables: DBSession):
        """Test that a None datetime binds and returns as None."""
        record = MockDatetimeModel(scheduled_time=None)
        fields_tables.create(record)

        fields_tables.expunge_all()
        retrieved = fields_tables.exec(select(MockDatetimeModel).where(MockDatetimeModel.id == record.id)).one()

        assert retrieved.scheduled_time is None


class TestUTCDatetimeField:
    """Test the ``UTCDatetimeField`` ``now_add`` and ``auto_now`` stamping behaviour."""

    def test_now_add_stamps_on_insert(self, fields_tables: DBSession):
        """Test that now_add stamps the current UTC datetime on insert."""
        record = MockDatetimeModel(scheduled_time=None)
        fields_tables.create(record)

        assert record.created_at is not None
        assert record.created_at.tzinfo == timezone.utc
        assert abs((datetime.now(tz=timezone.utc) - record.created_at).total_seconds()) < 5

    def test_now_add_unchanged_on_update(self, fields_tables: DBSession):
        """Test that a now_add field is not re-stamped on subsequent updates."""
        record = MockDatetimeModel(scheduled_time=None)
        fields_tables.create(record)
        original_created_at = record.created_at

        record.scheduled_time = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        fields_tables.create(record)

        assert record.created_at == original_created_at

    def test_auto_now_updates_on_update(self, fields_tables: DBSession):
        """Test that auto_now re-stamps the field on every update."""
        record = MockDatetimeModel(scheduled_time=None)
        fields_tables.create(record)
        original_updated_at = record.updated_at
        assert original_updated_at is not None
        assert original_updated_at.tzinfo == timezone.utc

        record.scheduled_time = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        fields_tables.create(record)

        assert record.updated_at is not None
        assert record.updated_at.tzinfo == timezone.utc
        assert record.updated_at > original_updated_at


class TestEnumField:
    """Test that ``EnumField`` persists the enum value rather than its name."""

    def test_enum_field_stores_value(self, fields_tables: DBSession):
        """Test that the stored column holds the enum's value, not its name."""
        record = MockEnumModel(colour=FieldsColour.GREEN)
        fields_tables.create(record)

        stored = fields_tables.exec(
            text(f'SELECT colour FROM test_fields_enum WHERE id = {record.id}')  # noqa: S608
        ).first()
        assert record.colour == FieldsColour.GREEN == 'green' == stored[0]

    def test_enum_field_query_uses_value(self):
        """Test that querying by enum compiles to the enum's value."""
        query = select(MockEnumModel).where(MockEnumModel.colour == FieldsColour.GREEN)
        compiled = str(query.compile(compile_kwargs={'literal_binds': True}))

        assert "colour = 'green'" in compiled
        assert 'GREEN' not in compiled


class TestFKField:
    """Test that ``FKField`` produces an indexed column with the requested ``ondelete``."""

    def test_fk_field_is_indexed(self):
        """Test that the foreign-key column is auto-indexed."""
        parent_column = MockFKChild.__table__.columns['parent_id']
        assert parent_column.index is True

    def test_fk_field_ondelete(self):
        """Test that the foreign key carries the requested ondelete behaviour."""
        parent_column = MockFKChild.__table__.columns['parent_id']
        foreign_key = next(iter(parent_column.foreign_keys))
        assert foreign_key.ondelete == 'CASCADE'
        assert foreign_key.target_fullname == 'test_fields_fk_parent.id'

    def test_fk_field_cascade_deletes_children(self, fields_tables: DBSession):
        """Test that deleting a parent cascades to its FKField children in the database."""
        parent = fields_tables.create(MockFKParent())
        child = fields_tables.create(MockFKChild(parent_id=parent.id))
        child_id = child.id

        fields_tables.exec(text(f'DELETE FROM test_fields_fk_parent WHERE id = {parent.id}'))  # noqa: S608
        fields_tables.commit()

        remaining = fields_tables.exec(select(MockFKChild).where(MockFKChild.id == child_id)).one_or_none()
        assert remaining is None
