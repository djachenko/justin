"""Ожидание, которое под отладчиком рассказывает, чего дождаться не удалось."""
from typing import Any, Callable

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.explorers.page_explorer import PageExplorer
from justin.browser.shared.run_mode import is_debug


def wait_for(driver: WebDriver, wait: WebDriverWait, condition: Callable) -> Any:
    """Голый таймаут не говорит, что было на странице.

    Дамп снимается только под отладчиком: в проде он вываливается человеку под руку
    посреди работы и ничем не помогает.
    """
    try:
        return wait.until(condition)
    except TimeoutException:
        if is_debug():
            PageExplorer(driver).explore()

        raise
