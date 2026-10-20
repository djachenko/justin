"""Readiness of a VK page: the React markup arrives after the skeletons."""
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.shared.elements import by_testid
from justin.browser.shared.pacing import AFTER_ACTION, pause

_SKELETON = by_testid("loading-skeleton")


def content_rendered(driver: WebDriver) -> bool:
    """Skeletons gone means the content is there. While they are being repainted,
    references to them go stale — that is "not ready yet", not an error."""
    try:
        skeletons = driver.find_elements(*_SKELETON)

        return not any(el.is_displayed() for el in skeletons)
    except StaleElementReferenceException:
        return False


def wait_for_content(wait: WebDriverWait) -> None:
    wait.until(content_rendered)

    pause(AFTER_ACTION)
