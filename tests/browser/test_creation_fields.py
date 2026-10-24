"""Wizard fields on fakes: what each one types, clicks and passes on."""
from datetime import datetime
from types import SimpleNamespace
from typing import cast

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver

from justin.browser.event_creation import event_creation_schema
from justin.browser.event_creation.event_creation_schema import AccessSelect, DateSpinGroup, \
    OptionalDateSpinGroup, OrganizerSelect, TitleInput
from justin.browser.shared.react_select import set_react_select
from tests.browser.fakes import fast_wait

pytestmark = pytest.mark.usefixtures("no_pauses")


class FakeElement:
    def __init__(self, name: str, displayed: bool = True) -> None:
        self.name = name
        self.displayed = displayed
        self.typed = ""
        self.clicks = 0

    def is_displayed(self) -> bool:
        return self.displayed

    def is_enabled(self) -> bool:
        return True

    def click(self) -> None:
        self.clicks += 1

    def send_keys(self, text: str) -> None:
        self.typed += text


class FakeDriver:
    """Elements by css selector; records what the page's JS was asked to click."""

    def __init__(self, elements: dict[str, list[FakeElement]] | None = None) -> None:
        self.elements = elements or {}
        self.js_clicked: list[str] = []
        self.focused: list[str] = []
        self.scripts: list[tuple] = []
        self.switch_to = SimpleNamespace(active_element=FakeElement("active"))

    def find_elements(self, by: str, selector: str) -> list[FakeElement]:
        return self.elements.get(selector, [])

    def find_element(self, by: str, selector: str) -> FakeElement:
        return self.elements[selector][0]

    def execute_script(self, script: str, *args) -> None:
        self.scripts.append((script, *args))

        if script == "arguments[0].click()":
            self.js_clicked.append(args[0].name)
        elif script == "arguments[0].focus()":
            self.focused.append(args[0].name)


SPIN_LABELS = ["День", "Месяц", "Год", "Час", "Минута"]


def _spin_driver(count: int = 1) -> FakeDriver:
    return FakeDriver({
        f'[aria-label="{label}"]': [FakeElement(f"{label}{i}") for i in range(count)]
        for label in SPIN_LABELS
    })


def _typed(driver: FakeDriver, n: int) -> dict[str, str]:
    return {label: driver.elements[f'[aria-label="{label}"]'][n].typed for label in SPIN_LABELS}


class TestDateSpinGroup:
    def test_each_part_goes_to_its_spinbutton_zero_padded(self) -> None:
        driver = _spin_driver()

        DateSpinGroup().set_value(datetime(2026, 3, 7, 9, 5), cast(WebDriver, driver), fast_wait(driver))

        assert _typed(driver, 0) == {
            "День": "07",
            "Месяц": "03",
            "Год": "2026",
            "Час": "09",
            "Минута": "05",
        }

    def test_parts_are_filled_day_first(self) -> None:
        """The spinbuttons hand the focus on to the next one: the order is the form's own."""
        driver = _spin_driver()

        DateSpinGroup().set_value(datetime(2026, 3, 7, 9, 5), cast(WebDriver, driver), fast_wait(driver))

        assert driver.focused == [f"{label}0" for label in SPIN_LABELS]

    def test_n_picks_the_group(self) -> None:
        driver = _spin_driver(count=2)

        DateSpinGroup(n=1).set_value(datetime(2026, 3, 7, 9, 5), cast(WebDriver, driver), fast_wait(driver))

        assert _typed(driver, 0) == dict.fromkeys(SPIN_LABELS, "")
        assert _typed(driver, 1)["Год"] == "2026"

    def test_hidden_spinbutton_is_waited_for(self) -> None:
        """A zero-size spinbutton is in the DOM before the form is drawn — typing into it is lost."""
        driver = _spin_driver()
        driver.elements['[aria-label="День"]'][0].displayed = False

        with pytest.raises(TimeoutException):
            DateSpinGroup().set_value(datetime(2026, 3, 7), cast(WebDriver, driver), fast_wait(driver))


class TestOptionalDateSpinGroup:
    def test_none_touches_nothing(self) -> None:
        driver = _spin_driver(count=2)

        OptionalDateSpinGroup().set_value(None, cast(WebDriver, driver), fast_wait(driver))

        assert driver.js_clicked == []
        assert _typed(driver, 1) == dict.fromkeys(SPIN_LABELS, "")

    def test_value_opens_end_date_and_fills_second_group(self) -> None:
        driver = _spin_driver(count=2)
        driver.elements["//*[contains(text(), 'Enter end date')]"] = [FakeElement("end")]

        OptionalDateSpinGroup().set_value(datetime(2026, 3, 7, 13, 0), cast(WebDriver, driver), fast_wait(driver))

        assert driver.js_clicked == ["end"]
        assert _typed(driver, 1)["Час"] == "13"
        assert _typed(driver, 0) == dict.fromkeys(SPIN_LABELS, "")


class TestAccessSelect:
    @pytest.mark.parametrize("is_closed,clicked", [
        (True, ["select", "closed"]),
        (False, []),
    ], ids=["closed_picks_option_one", "open_keeps_the_form_default"])
    def test_clicks(self, is_closed: bool, clicked: list[str]) -> None:
        driver = FakeDriver({
            '[name="access"]': [FakeElement("select")],
            '[role="option"][value="1"]': [FakeElement("closed")],
        })

        AccessSelect().set_value(is_closed, cast(WebDriver, driver), fast_wait(driver))

        assert driver.js_clicked == clicked


class TestOrganizerSelect:
    @pytest.fixture
    def calls(self, monkeypatch) -> list[tuple]:
        calls: list[tuple] = []
        monkeypatch.setattr(event_creation_schema, "set_react_select",
                            lambda driver, name, value: calls.append((name, value)))
        return calls

    @pytest.mark.parametrize("organiser_id", [42, -42], ids=["positive", "negative_group_id"])
    def test_select_gets_the_bare_id(self, calls: list[tuple], organiser_id: int) -> None:
        """pyvko's Group.id is negative; the select's options are positive group ids."""
        driver = FakeDriver()

        OrganizerSelect().set_value(organiser_id, cast(WebDriver, driver), fast_wait(driver))

        assert calls == [("eventGroupId", "42")]

    def test_none_keeps_the_default(self, calls: list[tuple]) -> None:
        driver = FakeDriver()

        OrganizerSelect().set_value(None, cast(WebDriver, driver), fast_wait(driver))

        assert calls == []


class TestSetReactSelect:
    def test_script_gets_name_then_value(self) -> None:
        driver = FakeDriver()

        set_react_select(cast(WebDriver, driver), "eventGroupId", "42")

        assert [arguments for _, *arguments in driver.scripts] == [["eventGroupId", "42"]]


class TestTitleInput:
    def test_types_into_the_focused_input(self) -> None:
        """The testid sits on a wrapper span — keys sent to it are not interactable."""
        wrapper = FakeElement("wrapper")
        driver = FakeDriver({"[data-testid='title_input']": [wrapper]})

        TitleInput("title_input").set_value("Party", cast(WebDriver, driver), fast_wait(driver))

        assert wrapper.clicks == 1
        assert wrapper.typed == ""
        assert driver.switch_to.active_element.typed == "Party"
