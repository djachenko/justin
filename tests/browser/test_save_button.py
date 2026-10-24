"""The Save button is found by its label alone."""
from typing import cast

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from justin.browser.shared.save_button import click_save, click_save_if_present, find_save_buttons
from tests.browser.fakes import fast_wait

pytestmark = pytest.mark.usefixtures("no_pauses")


class FakeButton:
    def __init__(self, text: str, displayed: bool = True) -> None:
        self.text = text
        self.displayed = displayed

    def is_displayed(self) -> bool:
        return self.displayed


class FakeDriver:
    def __init__(self, buttons: list[FakeButton]) -> None:
        self.buttons = buttons
        self.js_clicked: list[FakeButton] = []

    def find_elements(self, by: str, selector: str) -> list[FakeButton]:
        assert (by, selector) == (By.CSS_SELECTOR, "button, [role='button']")
        return self.buttons

    def execute_script(self, script: str, button: FakeButton) -> None:
        self.js_clicked.append(button)


class TestFindSaveButtons:
    def test_visible_buttons_labelled_save_in_either_language(self) -> None:
        english = FakeButton("Save")
        russian = FakeButton(" Сохранить ")
        buttons = [FakeButton("Cancel"), english, FakeButton("Save", displayed=False), russian,
                   FakeButton("Save and close")]

        assert find_save_buttons(cast(WebDriver, FakeDriver(buttons))) == [english, russian]


class TestClickSave:
    def test_clicks_the_first(self) -> None:
        first = FakeButton("Save")
        driver = FakeDriver([FakeButton("Cancel"), first, FakeButton("Save")])

        click_save(cast(WebDriver, driver), fast_wait(driver))

        assert driver.js_clicked == [first]

    def test_missing_button_times_out(self) -> None:
        driver = FakeDriver([FakeButton("Cancel")])

        with pytest.raises(TimeoutException):
            click_save(cast(WebDriver, driver), fast_wait(driver))


class TestClickSaveIfPresent:
    def test_no_button_is_fine(self) -> None:
        driver = FakeDriver([FakeButton("Cancel")])

        click_save_if_present(cast(WebDriver, driver))

        assert driver.js_clicked == []

    def test_clicks_the_first(self) -> None:
        first = FakeButton("Save")
        driver = FakeDriver([first, FakeButton("Save")])

        click_save_if_present(cast(WebDriver, driver))

        assert driver.js_clicked == [first]
