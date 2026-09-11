"""Готовность страницы VK: React-разметка приходит после скелетонов."""
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.shared.elements import by_testid
from justin.browser.shared.pacing import AFTER_ACTION, pause

_SKELETON = by_testid("loading-skeleton")


def content_rendered(driver: WebDriver) -> bool:
    """Скелетоны исчезли — значит, контент на месте. Пока они перерисовываются,
    ссылки на них протухают, и это не ошибка, а «ещё не готово»."""
    try:
        skeletons = driver.find_elements(*_SKELETON)

        return not any(el.is_displayed() for el in skeletons)
    except StaleElementReferenceException:
        return False


def wait_for_content(wait: WebDriverWait) -> None:
    wait.until(content_rendered)

    pause(AFTER_ACTION)
