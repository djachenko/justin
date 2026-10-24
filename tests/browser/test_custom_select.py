"""VKUI CustomSelect on fakes: picking by value and checking the label took."""
from typing import cast

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from justin.browser.shared import custom_select
from justin.browser.shared.custom_select import option_by_value, set_custom_select, set_custom_select_at
from tests.browser.fakes import fast_wait

pytestmark = pytest.mark.usefixtures("no_pauses")


class FakeHolder:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get_attribute(self, name: str) -> str:
        assert name == "value"
        return self.value


class FakeOption:
    def __init__(self, holder: FakeHolder, text: str, displayed: bool = True, applies: bool = True) -> None:
        self.holder = holder
        self.text = text
        self.displayed = displayed
        self.applies = applies

    def is_displayed(self) -> bool:
        return self.displayed

    def click(self) -> None:
        if self.applies:
            self.holder.value = self.text.strip()


class FakeDriver:
    def __init__(self, options: dict[str, list[FakeOption]]) -> None:
        self.options = options
        self.js_clicked: list[object] = []

    def find_elements(self, by: str, selector: str) -> list[FakeOption]:
        return self.options.get(selector, [])

    def execute_script(self, script: str, element) -> None:
        self.js_clicked.append(element)


class TestOptionByValue:
    def test_value_is_the_id_suffix(self) -> None:
        assert option_by_value("3") == "[role='option'][id$='-3']"


class TestSetCustomSelect:
    def test_visible_option_is_picked(self) -> None:
        """VKUI keeps a hidden copy of the list — clicking it changes nothing."""
        holder = FakeHolder()
        hidden = FakeOption(holder, "Ghost", displayed=False)
        visible = FakeOption(holder, " Enabled ")
        driver = FakeDriver({
            "[role='option'][id$='-1']": [hidden, visible],
        })

        set_custom_select(cast(WebDriver, driver), fast_wait(driver), cast(WebElement, holder), "1")

        assert driver.js_clicked == [holder]
        assert holder.value == "Enabled"

    def test_label_mismatch_raises(self) -> None:
        holder = FakeHolder("Disabled")
        driver = FakeDriver({
            "[role='option'][id$='-1']": [FakeOption(holder, "Enabled", applies=False)],
        })

        with pytest.raises(ValueError, match="Enabled"):
            set_custom_select(cast(WebDriver, driver), fast_wait(driver), cast(WebElement, holder), "1")

    def test_missing_option_times_out(self) -> None:
        holder = FakeHolder()
        driver = FakeDriver({})

        with pytest.raises(TimeoutException):
            set_custom_select(cast(WebDriver, driver), fast_wait(driver), cast(WebElement, holder), "1")


class FakeContainer:
    def __init__(self, holders: list[FakeHolder]) -> None:
        self.holders = holders

    def find_elements(self, by: str, selector: str) -> list[FakeHolder]:
        assert (by, selector) == (By.CSS_SELECTOR, "input[role='combobox']")
        return self.holders


class TestSetCustomSelectAt:
    @pytest.mark.parametrize("position", [0, 1])
    def test_holder_by_position(self, monkeypatch, position: int) -> None:
        holders = [FakeHolder(), FakeHolder()]
        calls: list[tuple] = []
        monkeypatch.setattr(custom_select, "set_custom_select",
                            lambda driver, wait, holder, value: calls.append((holder, value)))
        driver = FakeDriver({})

        set_custom_select_at(cast(WebDriver, driver), fast_wait(driver),
                             cast(WebElement, FakeContainer(holders)), position, "25")

        assert calls == [(holders[position], "25")]
