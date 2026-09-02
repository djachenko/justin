from dataclasses import fields

import pytest

from justin.browser.event_creation.event_creation_schema import (
    AccessSelect,
    CategorySelect,
    DateSpinGroup,
    EventCreationSchema,
    EventStep1Schema,
    EventStep2Schema,
    EventStep3Schema,
    OptionalDateSpinGroup,
    OrganizerSelect,
    TitleInput,
)
from justin.browser.event_creation.event_creation_settings import (
    Category,
    EventCreationSettings,
    EventStep1Settings,
    EventStep2Settings,
)
from datetime import datetime


# --- field coverage ---

def test_step1_schema_covers_step1_settings() -> None:
    schema_fields = {f.name for f in fields(EventStep1Schema())}
    settings_fields = {f.name for f in fields(EventStep1Settings)}
    assert schema_fields == settings_fields


def test_step2_schema_covers_step2_settings() -> None:
    schema_fields = {f.name for f in fields(EventStep2Schema())}
    settings_fields = {f.name for f in fields(EventStep2Settings)}
    assert schema_fields == settings_fields


# --- element types ---

def test_step1_element_types() -> None:
    schema = EventStep1Schema()
    assert isinstance(schema.title, TitleInput)
    assert isinstance(schema.is_closed, AccessSelect)
    assert isinstance(schema.start_dt, DateSpinGroup)
    assert isinstance(schema.end_dt, OptionalDateSpinGroup)
    assert isinstance(schema.organiser_id, OrganizerSelect)


def test_step2_element_types() -> None:
    assert isinstance(EventStep2Schema().category, CategorySelect)


def test_all_step_elements_have_set_value() -> None:
    for schema in [EventStep1Schema(), EventStep2Schema()]:
        for f in fields(schema):
            el = getattr(schema, f.name)
            assert callable(getattr(el, "set_value", None)), (
                f"{type(schema).__name__}.{f.name} ({type(el).__name__}) missing set_value"
            )


# --- schema structure ---

def test_creation_schema_step_types() -> None:
    schema = EventCreationSchema()
    assert isinstance(schema.step1, EventStep1Schema)
    assert isinstance(schema.step2, EventStep2Schema)
    assert isinstance(schema.step3, EventStep3Schema)


def test_step1_step2_have_fill_and_submit() -> None:
    for schema in [EventStep1Schema(), EventStep2Schema()]:
        assert callable(getattr(schema, "fill", None))
        assert callable(getattr(schema, "submit", None))


def test_step3_has_event_id_and_submit() -> None:
    schema = EventStep3Schema()
    assert callable(getattr(schema, "event_id", None))
    assert callable(getattr(schema, "submit", None))


# --- settings defaults ---

def test_event_creation_settings_default_step2() -> None:
    settings = EventCreationSettings(
        step1=EventStep1Settings(title="Test", start_dt=datetime(2026, 1, 1, 12, 0))
    )
    assert settings.step2.category == Category.CIRCUS


# --- category enum ---

@pytest.mark.parametrize("category", list(Category))
def test_category_values_are_non_empty_strings(category: Category) -> None:
    assert isinstance(category.value, str)
    assert category.value


def test_step3_parse_event_id() -> None:
    schema = EventStep3Schema()
    assert schema._parse_event_id("https://vk.com/event239352224") == 239352224
    assert schema._parse_event_id("https://vk.com/club237647473") == 237647473


def test_step3_parse_event_id_invalid() -> None:
    schema = EventStep3Schema()
    with pytest.raises(ValueError):
        schema._parse_event_id("https://vk.com/somepage")
