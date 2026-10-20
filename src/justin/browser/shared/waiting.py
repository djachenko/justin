"""A wait that, under a debugger, tells what it failed to wait for."""
from typing import Any, Callable

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.explorers.page_explorer import PageExplorer
from justin.shared.run_mode import is_debug


class Wait(WebDriverWait):
    """A bare timeout says nothing about what was on the page.

    The dump is taken under a debugger only: in a normal run it lands in the middle of
    someone's work and helps with nothing. It is substituted in one place — new_wait() —
    so every helper from elements.py gets this behaviour without wrappers.
    """

    def until(self, method: Callable, message: str = "") -> Any:
        try:
            return super().until(method, message)
        except TimeoutException:
            if is_debug():
                PageExplorer(self._driver).explore()

            raise
