"""Чтение состояния переключателя и проверка того, что клик долетел.

Без браузера: элементы подменены заглушками, потому что оба дефекта — про логику,
а не про VK. Оба ловились только живьём и оба выглядели как «всё применилось».
"""
import pytest
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from justin.browser.sections import schema as section_schema
from justin.browser.sections.schema import Toggle, _switch_state


class FakeElement:
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
        return [self.nested] if self.nested is not None else []


class FakeDriver:
    """Клик по умолчанию срабатывает; landing=False имитирует не долетевший JS-клик."""

    def __init__(self, element: FakeElement, landing: bool = True):
        self.element = element
        self.landing = landing

    def find_element(self, by, css: str) -> FakeElement:
        return self.element

    def execute_script(self, script: str, *args) -> None:
        self.element.clicks += 1

        if self.landing:
            self.element.checked = "false" if self.element.checked == "true" else "true"


class StaleOnceDriver(FakeDriver):
    """Список перерисовывается вокруг переключателя — первая проверка после клика протухает."""

    def __init__(self, element: FakeElement):
        super().__init__(element)
        self.stale_left = 1

    def find_element(self, by, css: str) -> FakeElement:
        if self.element.clicks and self.stale_left:
            self.stale_left -= 1
            raise StaleElementReferenceException("re-rendered")

        return self.element


def test_state_read_from_element() -> None:
    assert _switch_state(FakeElement("true")) is True
    assert _switch_state(FakeElement("false")) is False


def test_state_read_from_nested_switch() -> None:
    """Часть testid'ов висит на ячейке, а не на самом переключателе."""
    assert _switch_state(FakeElement(None, nested=FakeElement("false"))) is False


def test_unknown_state_raises() -> None:
    """Раньше отсутствие состояния читалось как «включено» — и включение молча пропускалось."""
    with pytest.raises(NoSuchElementException):
        _switch_state(FakeElement(None))


def test_toggle_applies_value() -> None:
    element = FakeElement("false")
    Toggle("form_x_toggle").set_value(True, FakeDriver(element), None)

    assert element.clicks == 1
    assert _switch_state(element) is True


def test_toggle_skips_when_already_set() -> None:
    element = FakeElement("true")
    Toggle("form_x_toggle").set_value(True, FakeDriver(element), None)

    assert element.clicks == 0


def test_toggle_tolerates_stale_element_after_click() -> None:
    element = FakeElement("false")
    Toggle("form_x_toggle").set_value(True, StaleOnceDriver(element), None)

    assert _switch_state(element) is True


def test_toggle_raises_when_click_did_not_land(monkeypatch) -> None:
    monkeypatch.setattr(section_schema, "_STATE_TIMEOUT", 0.3)
    element = FakeElement("false")

    with pytest.raises(ValueError):
        Toggle("form_x_toggle").set_value(True, FakeDriver(element, landing=False), None)
