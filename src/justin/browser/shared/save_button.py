"""The Save button: VK dropped its group_save class, only the label is left."""
from justkitten.util import first
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.shared.elements import by_css, found
from justin.browser.shared.pacing import pause

SAVE_LABELS = {"save", "сохранить"}  # the label is localised — both interface languages

_AFTER_SAVE = 1.0  # the page reloads on its own, let it go


def find_save_buttons(driver: WebDriver) -> list[WebElement]:
    return [
        el for el in driver.find_elements(*by_css("button, [role='button']"))
        if el.is_displayed() and el.text.strip().lower() in SAVE_LABELS
    ]


def click_save(driver: WebDriver, wait: WebDriverWait) -> None:
    """Pages where nothing applies without Save: the button has to be there."""
    button = found(wait, lambda d: first(find_save_buttons(d)))

    _click(driver, button)


def click_save_if_present(driver: WebDriver) -> None:
    """React pages save themselves — there may be no button at all."""
    buttons = find_save_buttons(driver)

    if not buttons:
        return

    _click(driver, buttons[0])


def _click(driver: WebDriver, button: WebElement) -> None:
    # The JS click is deliberate: on legacy pages the search label in the header overlaps
    # the button, and a real click fails with ElementClickInterceptedException.
    driver.execute_script("arguments[0].click()", button)

    pause(_AFTER_SAVE)
