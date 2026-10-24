"""Sugar over Selenium: locators and waits without three storeys of brackets.

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{x}']")))

becomes

    present(wait, by_testid(x))
"""
from typing import Callable

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from justin.browser.shared.pacing import BETWEEN_KEYS, pause
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[str, str]


def by_css(selector: str) -> Locator:
    return By.CSS_SELECTOR, selector


def by_testid(value: str) -> Locator:
    return by_css(f"[data-testid='{value}']")


def by_xpath(expression: str) -> Locator:
    return By.XPATH, expression


def present(wait: WebDriverWait, locator: Locator) -> WebElement:
    return wait.until(EC.presence_of_element_located(locator))


def visible(wait: WebDriverWait, locator: Locator) -> WebElement:
    return wait.until(EC.visibility_of_element_located(locator))


def clickable(wait: WebDriverWait, locator: Locator) -> WebElement:
    return wait.until(EC.element_to_be_clickable(locator))


def gone(wait: WebDriverWait, locator: Locator) -> None:
    wait.until_not(EC.presence_of_element_located(locator))


def found[T](wait: WebDriverWait, finder: Callable[[WebDriver], T | None]) -> T:
    """For conditions a locator cannot express: finder searches itself and returns what it
    found, or None while it is too early. `or False` is for the type checker only: until
    strips Literal[False] from its result type, so a bare None would leak into T."""
    return wait.until(lambda driver: finder(driver) or False)


def type_into(element: WebElement, text: str) -> None:
    """Character by character, with micro-pauses: a line that appears at once is not human."""
    for character in text:
        element.send_keys(character)

        pause(BETWEEN_KEYS)
