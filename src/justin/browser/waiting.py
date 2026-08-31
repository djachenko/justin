"""Ожидание, которое рассказывает, чего дождаться не удалось."""
from typing import Any, Callable

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.page_explorer import PageExplorer


def wait_or_explore(driver: WebDriver, wait: WebDriverWait, condition: Callable) -> Any:
    """A bare timeout says nothing about what VK actually rendered — dump the page first."""
    try:
        return wait.until(condition)
    except TimeoutException:
        PageExplorer(driver).explore()
        raise
