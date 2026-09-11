"""Schema for creating an invite link on the Invites settings page."""
from dataclasses import dataclass

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.invite_link.invite_link_settings import InviteLinkSettings
from justin.browser.shared.custom_select import set_custom_select
from justin.browser.shared.elements import by_css, by_testid, clickable, found, visible

_CREATE_LINK_BUTTON = by_testid("settings-invitations-create-link-button")
_MODAL = by_testid("link_invite_modal")
_MODAL_CREATE = by_testid("settings-invite-link-modal-create-button")
_SELECT_HOLDER = by_css("input.vkuiCustomSelectInput__el")
_LIFETIME = 0
_USES = 1
_LINK_INPUT = by_css("input[value^='https://vk.']")
_LINK_PREFIX = "/invite/"


def _links(driver: WebDriver) -> set[str]:
    """Every link item keeps its url in a plain input — that is what the copy button reads."""
    return {
        value for value in (
            el.get_attribute("value") for el in driver.find_elements(*_LINK_INPUT)
        ) if value and _LINK_PREFIX in value
    }


def _set_select(driver: WebDriver, wait: WebDriverWait, modal, position: int, value: str) -> None:
    """The modal selects carry no testid — they are told apart by their order."""
    holder = modal.find_elements(*_SELECT_HOLDER)[position]
    set_custom_select(driver, wait, holder, value)


@dataclass(frozen=True)
class InviteLinkSchema:
    """Create an invite link and return its url."""

    _INVITES_URL_TMPL: str = "https://vk.com/event{event_id}/settings/requests"

    def __call__(self, event_id: int, settings: InviteLinkSettings,
                 driver: WebDriver, wait: WebDriverWait) -> str:
        driver.get(self._INVITES_URL_TMPL.format(event_id=event_id))

        clickable(wait, _CREATE_LINK_BUTTON)
        existing = _links(driver)

        driver.find_element(*_CREATE_LINK_BUTTON).click()

        modal = visible(wait, _MODAL)

        _set_select(driver, wait, modal, _LIFETIME, settings.lifetime.value)
        _set_select(driver, wait, modal, _USES, settings.uses.value)

        modal.find_element(*_MODAL_CREATE).click()

        created = found(wait, lambda d: _links(d) - existing)

        if len(created) != 1:
            raise NoSuchElementException(f"Expected one new invite link, got {sorted(created)}")

        return created.pop()
