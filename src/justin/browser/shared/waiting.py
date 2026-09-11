"""Ожидание, которое под отладчиком рассказывает, чего дождаться не удалось."""
from typing import Any, Callable

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.explorers.page_explorer import PageExplorer
from justin.browser.shared.run_mode import is_debug


class Wait(WebDriverWait):
    """Голый таймаут не говорит, что было на странице.

    Дамп снимается только под отладчиком: в проде он вываливается человеку под руку
    посреди работы и ничем не помогает. Подменяется в одном месте — new_wait() —
    поэтому весь сахар из elements.py получает это поведение без обёрток.
    """

    def until(self, method: Callable, message: str = "") -> Any:
        try:
            return super().until(method, message)
        except TimeoutException:
            if is_debug():
                PageExplorer(self._driver).explore()

            raise
