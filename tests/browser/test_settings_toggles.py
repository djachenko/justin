import pytest

from justin.browser.event_settings import event_settings_schema
from justin.browser.event_settings.event_settings_schema import _set_checkbox_label, _set_idd_toggle


class FakeSwitch:
    """A checkbox-label: the click flips the inner input."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def find_element(self, by, css: str) -> "FakeSwitch":
        return self

    def is_selected(self) -> bool:
        return self.enabled

    def click(self) -> None:
        self.enabled = not self.enabled


class FakeDropdown:
    """An idd_wrap: the click only opens the list, the state comes from the picked item."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def find_element(self, by, css: str) -> "FakeDropdown | FakeItem":
        if "idd_item" not in css:
            return self

        return FakeItem(self, css.endswith("1']"))

    def get_attribute(self, name: str) -> str:
        return str(int(self.enabled))

    def click(self) -> None:
        pass


class FakeItem:
    def __init__(self, dropdown: FakeDropdown, value: bool) -> None:
        self.dropdown = dropdown
        self.value = value

    def click(self) -> None:
        self.dropdown.enabled = self.value


type Toggle = FakeSwitch | FakeDropdown


class FakeDriver:
    def __init__(self, toggle: Toggle, landing: bool = True) -> None:
        self.toggle = toggle
        self.landing = landing
        self.clicks = 0

    def find_element(self, by, css: str) -> Toggle:
        return self.toggle

    def execute_script(self, script: str, element: FakeSwitch | FakeDropdown | FakeItem) -> None:
        self.clicks += 1

        if self.landing:
            element.click()


class FakeWait:
    def __init__(self, driver: FakeDriver) -> None:
        self.driver = driver

    def until(self, condition):
        return condition(self.driver)


def set_checkbox_label(driver: FakeDriver, enabled: bool) -> None:
    _set_checkbox_label(driver, "cta", enabled)


def set_idd_toggle(driver: FakeDriver, enabled: bool) -> None:
    _set_idd_toggle(driver, FakeWait(driver), "addresses", enabled)


SETTERS = [(set_checkbox_label, FakeSwitch), (set_idd_toggle, FakeDropdown)]


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(event_settings_schema, "pause", lambda *_, **__: None)
    monkeypatch.setattr(event_settings_schema, "_STATE_TIMEOUT", 0.3)


@pytest.mark.parametrize("setter,fake", SETTERS, ids=["set_checkbox_label", "set_idd_toggle"])
class TestSetters:
    def test_value_is_applied(self, setter, fake) -> None:
        toggle = fake(enabled=False)

        setter(FakeDriver(toggle), True)

        assert toggle.enabled

    def test_already_set_value_is_skipped(self, setter, fake) -> None:
        driver = FakeDriver(fake(enabled=True))

        setter(driver, True)

        assert driver.clicks == 0

    def test_click_that_did_not_land_raises(self, setter, fake) -> None:
        """Used to pass silently: the click was fired and never checked."""
        with pytest.raises(ValueError):
            setter(FakeDriver(fake(enabled=False), landing=False), True)
