from abc import ABC, abstractmethod

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait


class Field[V](ABC):
    """A control on a page that takes one settings value. Schemas fill them by field name."""

    @abstractmethod
    def set_value(self, value: V, driver: WebDriver, wait: WebDriverWait) -> None: ...
