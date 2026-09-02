"""Schema for creating an invite link on the Invites settings page."""
from dataclasses import dataclass

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.shared.custom_select import set_custom_select
from justin.browser.invite_link.invite_link_settings import InviteLinkSettings

_CREATE_LINK_BUTTON = "[data-testid='settings-invitations-create-link-button']"
_MODAL = "[data-testid='link_invite_modal']"
_MODAL_CREATE = "[data-testid='settings-invite-link-modal-create-button']"
_SELECT_HOLDER = "input.vkuiCustomSelectInput__el"
_LIFETIME = 0
_USES = 1
_LINK_INPUT = "input[value^='https://vk.']"
_LINK_PREFIX = "/invite/"


def _links(driver: WebDriver) -> set[str]:
    """Every link item keeps its url in a plain input — that is what the copy button reads."""
    return {
        value for value in (
            el.get_attribute("value") for el in driver.find_elements(By.CSS_SELECTOR, _LINK_INPUT)
        ) if value and _LINK_PREFIX in value
    }


def _set_select(driver: WebDriver, wait: WebDriverWait, modal, position: int, value: str) -> None:
    """The modal selects carry no testid — they are told apart by their order."""
    holder = modal.find_elements(By.CSS_SELECTOR, _SELECT_HOLDER)[position]
    set_custom_select(driver, wait, holder, value)


@dataclass(frozen=True)
class InviteLinkSchema:
    """Create an invite link and return its url."""

    _INVITES_URL_TMPL: str = "https://vk.com/event{event_id}/settings/requests"

    def __call__(self, event_id: int, settings: InviteLinkSettings,
                 driver: WebDriver, wait: WebDriverWait) -> str:
        driver.get(self._INVITES_URL_TMPL.format(event_id=event_id))

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, _CREATE_LINK_BUTTON)))
        existing = _links(driver)

        driver.find_element(By.CSS_SELECTOR, _CREATE_LINK_BUTTON).click()

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, _MODAL)))

        _set_select(driver, wait, modal, _LIFETIME, settings.lifetime.value)
        _set_select(driver, wait, modal, _USES, settings.uses.value)

        modal.find_element(By.CSS_SELECTOR, _MODAL_CREATE).click()

        created = wait.until(lambda d: _links(d) - existing)

        if len(created) != 1:
            raise NoSuchElementException(f"Expected one new invite link, got {sorted(created)}")

        return created.pop()
