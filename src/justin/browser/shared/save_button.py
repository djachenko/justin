"""Кнопка Save: VK убрал с неё класс group_save, осталась только подпись."""
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.shared.pacing import pause

SAVE_LABELS = {"save", "сохранить"}

_AFTER_SAVE = 1.0  # страница перезагружается сама, дать ей уйти


def find_save_buttons(driver: WebDriver) -> list[WebElement]:
    return [
        el for el in driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
        if el.is_displayed() and el.text.strip().lower() in SAVE_LABELS
    ]


def click_save(driver: WebDriver, wait: WebDriverWait) -> None:
    """Страницы, где без Save ничего не применится: кнопка обязана быть."""
    button = wait.until(lambda d: next(iter(find_save_buttons(d)), None))

    if button is None:
        raise NoSuchElementException("Save button not found")

    _click(driver, button)


def click_save_if_present(driver: WebDriver) -> None:
    """React-страницы сохраняются сами — кнопки может и не быть."""
    buttons = find_save_buttons(driver)

    if not buttons:
        return

    _click(driver, buttons[0])


def _click(driver: WebDriver, button: WebElement) -> None:
    # JS-клик намеренно: на legacy-страницах кнопку перекрывает подпись поиска в шапке,
    # и настоящий клик падает с ElementClickInterceptedException.
    driver.execute_script("arguments[0].click()", button)

    pause(_AFTER_SAVE)
