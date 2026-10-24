"""Reading a switch state and checking that the click landed.

No browser: elements are replaced by fakes, because both defects are about logic, not VK.
Both were caught only live, and both looked like "everything applied".
"""
import pytest
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from justin.browser.sections import section_schema
from justin.browser.sections.section_schema import Toggle, _switch_state


class FakeElement:
    _FLIPPED = {"true": "false", "false": "true"}

    def __init__(self, checked: str | None, nested: "FakeElement | None" = None,
                 test_id: str = "form_x_toggle"):
        self.checked = checked
        self.nested = nested
        self.test_id = test_id
        self.clicks = 0

    def get_attribute(self, name: str) -> str | None:
        if name == "aria-checked":
            return self.checked

        if name == "data-testid":
            return self.test_id

        return None

    def find_elements(self, by, css: str) -> list["FakeElement"]:
        if self.nested is None:
            return []

        return [self.nested]

    def flip(self) -> None:
        if self.checked is None:
            raise ValueError("An element with no aria-checked does not toggle")

        self.checked = self._FLIPPED[self.checked]


class FakeDriver:

    def __init__(self, element: FakeElement, landing: bool = True):
        self.element = element
        self.landing = landing

    def find_element(self, by, css: str) -> FakeElement:
        return self.element

    def execute_script(self, script: str, *args) -> None:
        self.element.clicks += 1

        if self.landing:
            self.element.flip()


class StaleOnceDriver(FakeDriver):

    def __init__(self, element: FakeElement):
        super().__init__(element)
        self.stale_left = 1

    def find_element(self, by, css: str) -> FakeElement:
        if self.element.clicks and self.stale_left:
            self.stale_left -= 1
            raise StaleElementReferenceException("re-rendered")

        return self.element


class TestSwitchState:
    @pytest.mark.parametrize("checked,state", [("true", True), ("false", False)])
    def test_read_from_element(self, checked: str, state: bool) -> None:
        assert _switch_state(FakeElement(checked)) is state

    def test_read_from_nested_switch(self) -> None:
        assert _switch_state(FakeElement(None, nested=FakeElement("false"))) is False

    def test_unknown_state_raises(self) -> None:
        """A missing state used to read as enabled, and enabling was silently skipped."""
        with pytest.raises(NoSuchElementException):
            _switch_state(FakeElement(None))


class TestToggle:
    def test_value_is_applied(self) -> None:
        element = FakeElement("false")

        Toggle("form_x_toggle").set_value(True, FakeDriver(element), None)

        assert element.clicks == 1
        assert _switch_state(element) is True

    def test_already_set_value_is_skipped(self) -> None:
        element = FakeElement("true")

        Toggle("form_x_toggle").set_value(True, FakeDriver(element), None)

        assert element.clicks == 0

    def test_stale_element_after_click_is_tolerated(self) -> None:
        """The list re-renders around the switch: the first read after a click goes stale."""
        element = FakeElement("false")

        Toggle("form_x_toggle").set_value(True, StaleOnceDriver(element), None)

        assert _switch_state(element) is True

    def test_click_that_did_not_land_raises(self, monkeypatch) -> None:
        monkeypatch.setattr(section_schema, "_STATE_TIMEOUT", 0.3)

        element = FakeElement("false")

        with pytest.raises(ValueError):
            Toggle("form_x_toggle").set_value(True, FakeDriver(element, landing=False), None)
