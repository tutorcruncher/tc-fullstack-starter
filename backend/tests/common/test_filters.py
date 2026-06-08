from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import List, Optional

import pytest
from pydantic import Field as PydanticField
from sqlmodel import select

from app.common.api.errors import HTTP422
from app.common.api.filters import FKFilterField, FKIntMeta, ListFilter, ListOrder, OrderDirection
from app.example_domain.api.example_resources import ExampleResourceListFilter, ExampleResourceListOrder
from app.example_domain.models.example_resource import ExampleResource, ResourceStatus
from app.organization.models.organization import Organization
from tests.example_domain.factories import ExampleResourceFactory
from tests.organization.factories import AdminFactory, OrganizationFactory


def _request_for(user):
    """Build a minimal request-like object carrying ``user`` for the request_query classmethods."""
    return SimpleNamespace(state=SimpleNamespace(user=user))


@dataclass
class _TiebreakerOrder(ListOrder):
    """Ordering with a non-id tiebreaker field to exercise the secondary-sort branch."""

    model = ExampleResource
    fields = ['status', 'name']
    tiebreaker_fields = ['name']
    order_direction = OrderDirection.ASC


@dataclass
class _IdTiebreakerOrder(ListOrder):
    """Ordering whose declared tiebreaker is ``id`` so no extra id tiebreaker is appended."""

    model = ExampleResource
    fields = ['name']
    tiebreaker_fields = ['id']


@dataclass
class _IdPrimaryOrder(ListOrder):
    """Ordering whose primary sort is ``id`` so no extra id tiebreaker is appended."""

    model = ExampleResource
    fields = ['id', 'name']


class _EnumAndListFilter(ListFilter):
    """A filter exposing an Enum and a list field to exercise both ``get_options`` branches."""

    status: Optional[ResourceStatus] = PydanticField(default=None)
    tags: Optional[List[str]] = PydanticField(default=None)
    name: str = PydanticField()

    def apply(self, query, user):
        """Unused — this filter only exercises ``get_options`` and ``get_field_type``."""
        return query


class TestOrderDirection:
    """Tests for the OrderDirection enum."""

    def test_values(self):
        """The enum exposes asc/desc string members."""
        assert OrderDirection.ASC.value == 'asc'
        assert OrderDirection.DESC.value == 'desc'
        assert [d.value for d in OrderDirection] == ['asc', 'desc']


class TestListOrderApply:
    """Tests for ListOrder.apply ordering behaviour against seeded resources."""

    def test_default_order_uses_first_field_and_appends_id_tiebreaker(self, db):
        """With no order_by the first declared field is used, descending, with an id tiebreaker."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        first = ExampleResourceFactory.create_with_db(db, organization=organization, name='Alpha')
        second = ExampleResourceFactory.create_with_db(db, organization=organization, name='Zeta')

        query = ExampleResourceListOrder().apply(select(ExampleResource))
        results = db.exec(query).all()

        assert [r.id for r in results] == [second.id, first.id]

    def test_explicit_order_by_ascending(self, db):
        """An explicit order_by with ASC direction orders by that column ascending."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        alpha = ExampleResourceFactory.create_with_db(db, organization=organization, name='Alpha')
        zeta = ExampleResourceFactory.create_with_db(db, organization=organization, name='Zeta')

        ordering = ExampleResourceListOrder(order_by='name', order_direction=OrderDirection.ASC)
        results = db.exec(ordering.apply(select(ExampleResource))).all()

        assert [r.id for r in results] == [alpha.id, zeta.id]

    def test_order_by_accepts_enum_member(self, db):
        """order_by may be passed as the OrderBy enum member directly."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        alpha = ExampleResourceFactory.create_with_db(db, organization=organization, name='Alpha')
        zeta = ExampleResourceFactory.create_with_db(db, organization=organization, name='Zeta')

        ordering = ExampleResourceListOrder(
            order_by=ExampleResourceListOrder.OrderBy.NAME, order_direction=OrderDirection.ASC
        )
        results = db.exec(ordering.apply(select(ExampleResource))).all()

        assert [r.id for r in results] == [alpha.id, zeta.id]

    def test_apply_accepts_unused_user_argument(self, db):
        """apply accepts a user argument for parity with overrides and ignores it."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        resource = ExampleResourceFactory.create_with_db(db, organization=organization, name='Solo')
        user = AdminFactory.create_with_db(db, organization=organization)

        results = db.exec(ExampleResourceListOrder().apply(select(ExampleResource), user)).all()

        assert [r.id for r in results] == [resource.id]

    def test_tiebreaker_field_breaks_ties_within_primary_sort(self, db):
        """A declared tiebreaker field orders rows sharing the primary sort value ascending."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        zeta = ExampleResourceFactory.create_with_db(
            db, organization=organization, name='Zeta', status=ResourceStatus.DRAFT
        )
        alpha = ExampleResourceFactory.create_with_db(
            db, organization=organization, name='Alpha', status=ResourceStatus.DRAFT
        )

        results = db.exec(_TiebreakerOrder().apply(select(ExampleResource))).all()

        assert [r.id for r in results] == [alpha.id, zeta.id]

    def test_tiebreaker_skipped_when_equal_to_primary_order_field(self, db):
        """When the primary order_by equals a tiebreaker field, that tiebreaker is not duplicated."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        alpha = ExampleResourceFactory.create_with_db(db, organization=organization, name='Alpha')
        zeta = ExampleResourceFactory.create_with_db(db, organization=organization, name='Zeta')

        ordering = _TiebreakerOrder(order_by='name', order_direction=OrderDirection.ASC)
        results = db.exec(ordering.apply(select(ExampleResource))).all()

        assert [r.id for r in results] == [alpha.id, zeta.id]

    def test_no_id_tiebreaker_appended_when_id_in_tiebreaker_fields(self, db):
        """An id tiebreaker declared explicitly is not appended a second time."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        first = ExampleResourceFactory.create_with_db(db, organization=organization, name='Alpha')
        second = ExampleResourceFactory.create_with_db(db, organization=organization, name='Alpha')

        results = db.exec(_IdTiebreakerOrder().apply(select(ExampleResource))).all()

        assert [r.id for r in results] == [first.id, second.id]

    def test_no_id_tiebreaker_appended_when_primary_sort_is_id(self, db):
        """When the primary sort column is id itself, no extra id tiebreaker is appended."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        first = ExampleResourceFactory.create_with_db(db, organization=organization, name='Alpha')
        second = ExampleResourceFactory.create_with_db(db, organization=organization, name='Zeta')

        ordering = _IdPrimaryOrder(order_by='id', order_direction=OrderDirection.DESC)
        results = db.exec(ordering.apply(select(ExampleResource))).all()

        assert [r.id for r in results] == [second.id, first.id]

    def test_invalid_order_by_raises_http422(self):
        """An unknown order_by string raises HTTP422 listing the valid fields."""
        with pytest.raises(HTTP422) as exc:
            ExampleResourceListOrder(order_by='not_a_field')

        assert exc.value.detail == 'Invalid order_by value. Must be one of: name, created_dt'


class TestListOrderSubclassValidation:
    """Tests for ListOrder.__init_subclass__ guard rails."""

    def test_missing_model_or_fields_raises_type_error(self):
        """A subclass without model and fields attributes is rejected at class creation."""
        with pytest.raises(TypeError) as exc:

            @dataclass
            class _BadOrder(ListOrder):
                pass

        assert 'must define model and fields' in str(exc.value)

    def test_non_lowercase_fields_raise_type_error(self):
        """Non-lowercase field names are rejected to avoid Enum key collisions."""
        with pytest.raises(TypeError) as exc:

            @dataclass
            class _UppercaseOrder(ListOrder):
                model = ExampleResource
                fields = ['Name']

        assert 'must be lowercase' in str(exc.value)


class TestListOrderGetOptions:
    """Tests for ListOrder.get_options metadata introspection."""

    def test_returns_order_by_and_direction_metadata(self):
        """get_options returns the choices, default field and default direction."""
        assert ExampleResourceListOrder.get_options() == {
            'order_by': {
                'type': 'str',
                'required': False,
                'choices': [{'id': 'name', 'name': 'name'}, {'id': 'created_dt', 'name': 'created_dt'}],
                'default': 'name',
            },
            'order_direction': {
                'type': 'OrderDirection',
                'required': False,
                'choices': [{'id': 'asc', 'name': 'asc'}, {'id': 'desc', 'name': 'desc'}],
                'default': 'desc',
            },
        }


class TestListFilterApply:
    """Tests for ListFilter.apply adding WHERE clauses against seeded resources."""

    def test_search_filters_by_name_case_insensitively(self, db):
        """The search filter matches the resource name case-insensitively."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        match = ExampleResourceFactory.create_with_db(db, organization=organization, name='Zebra')
        ExampleResourceFactory.create_with_db(db, organization=organization, name='Giraffe')
        user = AdminFactory.create_with_db(db, organization=organization)

        query = ExampleResourceListFilter(search='zeb').apply(select(ExampleResource), user)
        results = db.exec(query).all()

        assert [r.id for r in results] == [match.id]

    def test_created_range_bounds_the_query(self, db):
        """created_from and created_to bound the query by creation datetime."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        inside = ExampleResourceFactory.create_with_db(
            db, organization=organization, created_dt=datetime(2024, 1, 1, tzinfo=UTC)
        )
        ExampleResourceFactory.create_with_db(
            db, organization=organization, created_dt=datetime(2024, 6, 1, tzinfo=UTC)
        )
        user = AdminFactory.create_with_db(db, organization=organization)

        filters = ExampleResourceListFilter(
            created_from=datetime(2023, 12, 1, tzinfo=UTC), created_to=datetime(2024, 2, 1, tzinfo=UTC)
        )
        results = db.exec(filters.apply(select(ExampleResource), user)).all()

        assert [r.id for r in results] == [inside.id]

    def test_organization_id_narrows_the_query(self, db):
        """The organization_id filter narrows the query to one organization."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        wanted = ExampleResourceFactory.create_with_db(db, organization=org_a)
        ExampleResourceFactory.create_with_db(db, organization=org_b)
        superadmin = AdminFactory.create_with_db(db, organization=org_a, is_superadmin=True)

        filters = ExampleResourceListFilter(organization_id=org_a.id)
        results = db.exec(filters.apply(select(ExampleResource), superadmin)).all()

        assert [r.id for r in results] == [wanted.id]

    def test_no_filters_returns_query_unchanged(self, db):
        """With no filters set, apply leaves the query unchanged."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        resource = ExampleResourceFactory.create_with_db(db, organization=organization)
        user = AdminFactory.create_with_db(db, organization=organization)

        results = db.exec(ExampleResourceListFilter().apply(select(ExampleResource), user)).all()

        assert [r.id for r in results] == [resource.id]

    def test_base_apply_is_not_implemented(self):
        """The base ListFilter.apply raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            ListFilter().apply(select(ExampleResource), None)


class TestListFilterGetOptions:
    """Tests for ListFilter.get_options field introspection and FK choice population."""

    def test_populates_fk_choices_via_request_query(self, db):
        """FK fields produce id/name choices scoped by the model's request_query."""
        organization = OrganizationFactory.create_with_db(db, name='Visible Org')
        OrganizationFactory.create_with_db(db, name='Hidden Org')
        user = AdminFactory.create_with_db(db, organization=organization)
        request = _request_for(user)

        assert ExampleResourceListFilter.get_options(request, db) == {
            'search': {'type': 'str', 'required': False},
            'created_from': {'type': 'datetime', 'required': False},
            'created_to': {'type': 'datetime', 'required': False},
            'organization_id': {
                'type': 'int',
                'required': False,
                'choices': [{'id': organization.id, 'name': organization.name}],
            },
        }

    def test_superadmin_sees_all_fk_choices(self, db):
        """A superadmin's request_query returns every organization as an FK choice."""
        org_a = OrganizationFactory.create_with_db(db, name='A')
        org_b = OrganizationFactory.create_with_db(db, name='B')
        superadmin = AdminFactory.create_with_db(db, organization=org_a, is_superadmin=True)

        options = ExampleResourceListFilter.get_options(_request_for(superadmin), db)

        assert options['organization_id']['choices'] == [
            {'id': org_a.id, 'name': org_a.name},
            {'id': org_b.id, 'name': org_b.name},
        ]

    def test_enum_and_list_and_required_field_metadata(self, db):
        """Enum fields produce value choices, list fields unwrap, and required fields are flagged."""
        organization = OrganizationFactory.create_with_db(db, name='Org')
        user = AdminFactory.create_with_db(db, organization=organization)

        assert _EnumAndListFilter.get_options(_request_for(user), db) == {
            'status': {
                'type': 'ResourceStatus',
                'required': False,
                'choices': [
                    {'id': 'draft', 'name': 'draft'},
                    {'id': 'active', 'name': 'active'},
                    {'id': 'archived', 'name': 'archived'},
                ],
            },
            'tags': {'type': 'str', 'required': False},
            'name': {'type': 'str', 'required': True},
        }


class TestGetFieldType:
    """Tests for ListFilter.get_field_type unwrapping Optional, unions and lists."""

    def test_unwraps_optional_field(self):
        """An Optional[str] field unwraps to str."""
        field_info = ExampleResourceListFilter.model_fields['search']
        assert ListFilter.get_field_type(field_info) is str

    def test_unwraps_pipe_union_field(self):
        """A ``str | None`` field unwraps to str via the UnionType branch."""

        class _PipeFilter(ListFilter):
            value: str | None = PydanticField(default=None)

            def apply(self, query, user):
                """Unused."""
                return query

        field_info = _PipeFilter.model_fields['value']
        assert ListFilter.get_field_type(field_info) is str

    def test_unwraps_list_field(self):
        """A list field unwraps to its element type."""
        field_info = _EnumAndListFilter.model_fields['tags']
        assert ListFilter.get_field_type(field_info) is str


class TestFKFilterField:
    """Tests for FKFilterField / FKIntMeta producing the annotated FK type."""

    def test_default_name_field(self):
        """FKFilterField attaches FKIntMeta with the default name field."""
        annotated = FKFilterField(Organization)
        meta = annotated.__metadata__[0]
        assert isinstance(meta, FKIntMeta)
        assert meta.model is Organization
        assert meta.name_field == 'name'

    def test_custom_name_field(self):
        """FKFilterField honours a custom name_field."""
        annotated = FKFilterField(Organization, name_field='billing_status')
        meta = annotated.__metadata__[0]
        assert meta.model is Organization
        assert meta.name_field == 'billing_status'
