from datetime import datetime
from typing import Any, cast

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_creation.event_creation_settings import Category
from justin.browser.event_setup import event_setup_schema
from justin.browser.event_setup.event_setup_schema import (
    EventSetupSchema, _fill_date_field, _pick_from_result_list, _pick_year_and_month, _set_organiser,
)
from justin.browser.event_setup.event_setup_settings import EventSetupSettings
from tests.browser.fakes import fast_wait


pytestmark = pytest.mark.usefixtures("no_pauses")


class FakeElement:
    def __init__(self, text: str = "", value: str | None = None, displayed: bool = True,
                 on_click: Any = None) -> None:
        self.text = text
        self.value = value
        self.displayed = displayed
        self.on_click = on_click
        self.clicks = 0

    def get_attribute(self, name: str) -> str | None:
        if name == "value":
            return self.value

        return None

    def is_displayed(self) -> bool:
        return self.displayed

    def click(self) -> None:
        self.clicks += 1

        if self.on_click is not None:
            self.on_click()


class FakeCalendar:
    """Month mode shows twelve month cells and a header with the year; arrows move the year."""

    def __init__(self, year: int, arrows_work: bool = True, header: str = "{year}") -> None:
        self.year = year
        self.arrows_work = arrows_work
        self.header = header
        self.mode = "day"
        self.arrow_clicks: list[str] = []
        self.picked_month: int | None = None

    def _arrow(self, direction: str) -> FakeElement:
        def click() -> None:
            self.arrow_clicks.append(direction)

            if not self.arrows_work:
                return

            if direction == "left":
                self.year -= 1
            else:
                self.year += 1

        return FakeElement(on_click=click)

    def _month_cell(self, month: int) -> FakeElement:
        def click() -> None:
            self.picked_month = month
            self.mode = "day"

        return FakeElement(text=str(month), on_click=click)

    def find_element(self, by: str, value: str) -> FakeElement:
        assert value == "a.cal_month_sel"

        def click() -> None:
            self.mode = "month"

        return FakeElement(on_click=click)

    def find_elements(self, by: str, value: str) -> list[FakeElement]:
        if value == "td.day":
            if self.mode == "month":
                return [self._month_cell(month) for month in range(1, 13)]

            return [FakeElement(text=str(day)) for day in range(1, 31)]

        if value == "td.month":
            return [FakeElement(text=self.header.format(year=self.year))]

        if value == "a.arr.left":
            return [self._arrow("left")]

        if value == "a.arr.right":
            return [self._arrow("right")]

        raise AssertionError(f"unexpected locator {value!r}")


class TestPickYearAndMonth:
    @pytest.mark.parametrize("shown_year, target_year, arrows", [
        (2026, 2026, []),
        (2026, 2023, ["left", "left", "left"]),
        (2024, 2026, ["right", "right"]),
    ], ids=["same_year", "back", "forward"])
    def test_arrows_lead_to_the_year(self, shown_year: int, target_year: int, arrows: list[str]) -> None:
        calendar = FakeCalendar(shown_year)

        _pick_year_and_month(
            cast(WebDriver, None), fast_wait(None), cast(WebElement, calendar), datetime(target_year, 3, 5),
        )

        assert calendar.arrow_clicks == arrows
        assert calendar.year == target_year

    @pytest.mark.parametrize("month", [1, 3, 12])
    def test_month_is_picked_by_position(self, month: int) -> None:
        calendar = FakeCalendar(2026)

        _pick_year_and_month(
            cast(WebDriver, None), fast_wait(None), cast(WebElement, calendar), datetime(2026, month, 5),
        )

        assert calendar.picked_month == month

    def test_unreachable_year_gives_up(self) -> None:
        """A dead arrow must not spin forever — the step limit turns it into an error."""
        calendar = FakeCalendar(2026, arrows_work=False)

        with pytest.raises(NoSuchElementException, match="2020"):
            _pick_year_and_month(
                cast(WebDriver, None), fast_wait(None), cast(WebElement, calendar), datetime(2020, 3, 5),
            )

        assert len(calendar.arrow_clicks) == 20

    def test_header_without_year_is_an_error(self) -> None:
        calendar = FakeCalendar(2026, header="March")

        with pytest.raises(NoSuchElementException, match="no year"):
            _pick_year_and_month(
                cast(WebDriver, None), fast_wait(None), cast(WebElement, calendar), datetime(2026, 3, 5),
            )


class FakeDateDriver:
    def __init__(self, date_el: FakeElement) -> None:
        self.date_el = date_el

    def find_element(self, by: str, value: str) -> FakeElement:
        assert value == "[id='group_start_date_date_input']"

        return self.date_el


class FakeDateField(FakeElement):
    def __init__(self, following: list[FakeElement]) -> None:
        super().__init__()

        self.following = following

    def find_elements(self, by: str, value: str) -> list[FakeElement]:
        return self.following


class TestFillDateField:
    @pytest.fixture
    def picker(self, monkeypatch):
        """The datepicker writes what VK would show; selectors write the number picked."""
        shown = {"date": ""}

        def pick_date(driver, wait, date_el, dt):
            date_el.value = shown["date"]

        def pick_from_selector(driver, wait, selector_input, value):
            selector_input.value = str(value)

        monkeypatch.setattr(event_setup_schema, "_pick_date", pick_date)
        monkeypatch.setattr(event_setup_schema, "_pick_from_selector", pick_from_selector)

        return shown

    def _fill(self, dt: datetime) -> FakeDateField:
        field = FakeDateField([FakeElement(), FakeElement()])
        driver = FakeDateDriver(field)

        _fill_date_field(cast(WebDriver, driver), fast_wait(None), "group_start_date_date_input", dt)

        return field

    @pytest.mark.parametrize("shown", ["5 March 2026", "5 Mar 2026", "05.03.2026", " 5  March 2026 "])
    def test_shown_date_is_accepted(self, picker: dict[str, str], shown: str) -> None:
        picker["date"] = shown

        field = self._fill(datetime(2026, 3, 5, 18, 30))

        assert [el.value for el in field.following] == ["18", "30"]

    @pytest.mark.parametrize("shown", [
        "5 April 2026",
        "15 March 2026",
        "5 March 2023",
        "05.04.2026",
    ], ids=["wrong_month", "day_as_substring", "year_differs", "wrong_month_numeric"])
    def test_other_date_is_rejected(self, picker: dict[str, str], shown: str) -> None:
        picker["date"] = shown

        with pytest.raises(ValueError, match="Date not applied"):
            self._fill(datetime(2026, 3, 5, 18, 30))

    def test_unreadable_date_is_rejected(self, picker: dict[str, str]) -> None:
        picker["date"] = "5 мартa 2026"

        with pytest.raises(ValueError, match="not a date"):
            self._fill(datetime(2026, 3, 5, 18, 30))


class FakeListDriver:
    def __init__(self, items: list[FakeElement]) -> None:
        self.items = items
        self.scripts: list[str] = []

    def execute_script(self, script: str, *args: Any) -> None:
        self.scripts.append(script)

    def find_elements(self, by: str, value: str) -> list[FakeElement]:
        assert value == ".result_list li"

        return self.items


class TestPickFromResultList:
    @staticmethod
    def _item(field: FakeElement, text: str, shows: str | None = None, displayed: bool = True) -> FakeElement:
        """Clicking an option makes the field show its label — or `shows`, when VK picks another."""
        def click() -> None:
            field.value = shows or text

        return FakeElement(text=text, displayed=displayed, on_click=click)

    def test_the_visible_option_with_the_label_is_picked(self) -> None:
        field = FakeElement(value="")
        hidden = self._item(field, "Moscow", displayed=False)
        other = self._item(field, "Kazan")
        wanted = self._item(field, "Moscow")

        _pick_from_result_list(
            cast(WebDriver, FakeListDriver([hidden, other, wanted])), fast_wait(None), cast(WebElement, field), "Moscow",
        )

        assert (hidden.clicks, other.clicks, wanted.clicks) == (0, 0, 1)
        assert field.clicks == 1

    def test_field_showing_another_label_is_an_error(self) -> None:
        field = FakeElement(value="")
        item = self._item(field, "Moscow", shows="Moscow Oblast")

        with pytest.raises(ValueError, match="Moscow Oblast"):
            _pick_from_result_list(
                cast(WebDriver, FakeListDriver([item])), fast_wait(None), cast(WebElement, field), "Moscow",
            )

    def test_missing_option_times_out(self) -> None:
        field = FakeElement(value="")

        with pytest.raises(TimeoutException):
            _pick_from_result_list(
                cast(WebDriver, FakeListDriver([self._item(field, "Kazan")])), fast_wait(None), cast(WebElement, field), "Moscow",
            )


class FakeHostDriver:
    def __init__(self) -> None:
        self.field = FakeElement()
        self.located: list[str] = []
        self.written: list[Any] = []

    def find_element(self, by: str, value: str) -> FakeElement:
        self.located.append(value)

        return self.field

    def execute_script(self, script: str, *args: Any) -> None:
        self.written.append(args)


class TestSetOrganiser:
    def test_group_id_is_written_as_is(self) -> None:
        """pyvko keeps group ids negative; event_host takes them unchanged (checked live 2026-08-31)."""
        driver = FakeHostDriver()

        _set_organiser(cast(WebDriver, driver), -42)

        assert driver.located == ["input[name='event_host'], input[id='event_host']"]
        assert driver.written == [(driver.field, "-42")]


class FakeFormDriver:
    def __init__(self, calls: list[tuple]) -> None:
        self.calls = calls

    def get(self, url: str) -> None:
        self.calls.append(("get", url))

    def find_element(self, by: str, value: str) -> str:
        return value


class TestEventSetupSchema:
    @pytest.fixture
    def calls(self, monkeypatch) -> list[tuple]:
        calls: list[tuple] = []

        def record(name):
            def step(driver, *args):
                calls.append((name, *[arg for arg in args if not isinstance(arg, WebDriverWait)]))

            return step

        monkeypatch.setattr(event_setup_schema, "_wait_for_form", record("wait_for_form"))
        monkeypatch.setattr(event_setup_schema, "_set_category", record("category"))
        monkeypatch.setattr(event_setup_schema, "_set_organiser", record("organiser"))
        monkeypatch.setattr(event_setup_schema, "_set_access", record("access"))
        monkeypatch.setattr(event_setup_schema, "_set_city", record("city"))
        monkeypatch.setattr(event_setup_schema, "_fill_date_field", record("date"))
        monkeypatch.setattr(event_setup_schema, "click_save", record("save"))
        monkeypatch.setattr(event_setup_schema, "_clear_and_type",
                            lambda el, value: calls.append(("type", el, value)))

        return calls

    def test_every_setting_is_applied_then_saved(self, calls: list[tuple]) -> None:
        start = datetime(2026, 3, 5, 12, 0)
        end = datetime(2026, 3, 5, 16, 0)
        settings = EventSetupSettings(
            title="Chem days",
            description="About",
            category=Category.CIRCUS,
            organiser_id=-42,
            is_closed=True,
            start_dt=start,
            end_dt=end,
            website="https://example.org",
            phone="+7000",
            email="a@b.c",
            city="Moscow",
        )

        EventSetupSchema()(7, settings, cast(WebDriver, FakeFormDriver(calls)), fast_wait(None))

        assert calls == [
            ("get", "https://vk.ru/event7?act=edit"),
            ("wait_for_form",),
            ("type", "[id='group_edit_name']", "Chem days"),
            ("type", "[id='group_edit_desc']", "About"),
            ("type", "[id='group_website']", "https://example.org"),
            ("type", "[id='group_edit_phone']", "+7000"),
            ("type", "[id='event_mail']", "a@b.c"),
            ("category", Category.CIRCUS),
            ("organiser", -42),
            ("access", True),
            ("city", "Moscow"),
            ("date", "group_start_date_date_input", start),
            ("date", "group_finish_date_date_input", end),
            ("save",),
        ]

    def test_unset_fields_are_left_alone(self, calls: list[tuple]) -> None:
        EventSetupSchema()(7, EventSetupSettings(), cast(WebDriver, FakeFormDriver(calls)), fast_wait(None))

        assert calls == [
            ("get", "https://vk.ru/event7?act=edit"),
            ("wait_for_form",),
            ("save",),
        ]

    def test_open_event_is_applied(self, calls: list[tuple]) -> None:
        """False is a value, not an absent setting."""
        EventSetupSchema(
            )(7, EventSetupSettings(is_closed=False), cast(WebDriver, FakeFormDriver(calls)), fast_wait(None),
        )

        assert ("access", False) in calls
