from typing import Any, cast

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait


def fast_wait(driver: Any) -> WebDriverWait:
    """A real wait over a fake driver: polls the condition, gives up quickly."""
    return WebDriverWait(cast(WebDriver, driver), timeout=0.1, poll_frequency=0.01)
