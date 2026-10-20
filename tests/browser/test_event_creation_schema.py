from dataclasses import fields
from typing import cast

import pytest
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

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
from justin.shared.vk import VK_URL
from datetime import datetime


type Step = EventStep1Schema | EventStep2Schema

STEPS: list[Step] = [EventStep1Schema(), EventStep2Schema()]
STEP_IDS = [type(step).__name__ for step in STEPS]

STEP_ELEMENTS = [(step, f.name) for step in STEPS for f in fields(step)]


class TestFieldCoverage:
    @pytest.mark.parametrize("schema,settings_cls", [
        (EventStep1Schema(), EventStep1Settings),
        (EventStep2Schema(), EventStep2Settings),
    ], ids=STEP_IDS)
    def test_schema_covers_settings(self, schema: Step, settings_cls: type) -> None:
        schema_fields = {f.name for f in fields(schema)}
        settings_fields = {f.name for f in fields(settings_cls)}

        assert schema_fields == settings_fields


class TestElementTypes:
    def test_step1(self) -> None:
        schema = EventStep1Schema()

        assert isinstance(schema.title, TitleInput)
        assert isinstance(schema.is_closed, AccessSelect)
        assert isinstance(schema.start_dt, DateSpinGroup)
        assert isinstance(schema.end_dt, OptionalDateSpinGroup)
        assert isinstance(schema.organiser_id, OrganizerSelect)

    def test_step2(self) -> None:
        assert isinstance(EventStep2Schema().category, CategorySelect)

    @pytest.mark.parametrize("schema,name", STEP_ELEMENTS,
                             ids=[f"{type(step).__name__}.{name}" for step, name in STEP_ELEMENTS])
    def test_step_element_has_set_value(self, schema: Step, name: str) -> None:
        el = getattr(schema, name)

        assert callable(getattr(el, "set_value", None)), f"{type(el).__name__} missing set_value"


class TestSchemaStructure:
    def test_creation_schema_step_types(self) -> None:
        schema = EventCreationSchema()

        assert isinstance(schema.step1, EventStep1Schema)
        assert isinstance(schema.step2, EventStep2Schema)
        assert isinstance(schema.step3, EventStep3Schema)

    @pytest.mark.parametrize("schema", STEPS, ids=STEP_IDS)
    def test_step_has_fill_and_submit(self, schema: Step) -> None:
        assert callable(getattr(schema, "fill", None))
        assert callable(getattr(schema, "submit", None))

    def test_step3_has_event_id_and_submit(self) -> None:
        schema = EventStep3Schema()

        assert callable(getattr(schema, "event_id", None))
        assert callable(getattr(schema, "submit", None))


class TestSettingsDefaults:
    def test_step2_defaults_to_circus(self) -> None:
        settings = EventCreationSettings(
            step1=EventStep1Settings(
                title="Test",
                start_dt=datetime(2026, 1, 1, 12, 0),
            ),
        )

        assert settings.step2.category == Category.CIRCUS


class TestCategory:
    @pytest.mark.parametrize("category", list(Category))
    def test_values_are_non_empty_strings(self, category: Category) -> None:
        assert isinstance(category.value, str)
        assert category.value


class FakeDriver:
    """Lands on the given urls one read at a time, then stays on the last one."""

    def __init__(self, urls: list[str]) -> None:
        self.urls = urls

    @property
    def current_url(self) -> str:
        if len(self.urls) > 1:
            return self.urls.pop(0)

        return self.urls[0]


class TestEventId:
    @pytest.mark.parametrize("urls,event_id", [
        ([f"{VK_URL}/event111111111"], 111111111),
        ([f"{VK_URL}/club222222222"], 222222222),
        ([f"{VK_URL}/groups_create", f"{VK_URL}/groups_create", f"{VK_URL}/event111111111"], 111111111),
    ], ids=["event", "club", "after_redirect"])
    def test_parsed_from_landing_url(self, urls: list[str], event_id: int) -> None:
        driver = cast(WebDriver, FakeDriver(urls))
        wait = WebDriverWait(driver, timeout=0.1, poll_frequency=0.01)

        assert EventStep3Schema().event_id(driver, wait) == event_id

    def test_other_url_raises(self) -> None:
        driver = cast(WebDriver, FakeDriver([f"{VK_URL}/somepage"]))
        wait = WebDriverWait(driver, timeout=0.1, poll_frequency=0.01)

        with pytest.raises(ValueError):
            EventStep3Schema().event_id(driver, wait)
