"""Schema for creating an invite link on the Invites settings page."""
from dataclasses import dataclass

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.invite_link.invite_link_settings import InviteLinkSettings
from justin.browser.shared.custom_select import set_custom_select_at
from justin.browser.shared.elements import by_css, by_testid, clickable, found, visible
from justin.shared.vk import VK_URL


class Link:
    INPUT = by_css("input[value^='https://vk.']")
    PREFIX = "/invite/"


def _links(driver: WebDriver) -> set[str]:
    """Every link item keeps its url in a plain input — that is what the copy button reads."""
    return {
        value for value in (
            el.get_attribute("value") for el in driver.find_elements(*Link.INPUT)
        ) if value and Link.PREFIX in value
    }


@dataclass(frozen=True)
class InviteLinkSchema:
    """Create an invite link and return its url."""

    class Modal:
        """The new-link modal: its two selects carry no testids, only their order."""
        OPEN_BUTTON = by_testid("settings-invitations-create-link-button")
        SELF = by_testid("link_invite_modal")
        CREATE = by_testid("settings-invite-link-modal-create-button")
        LIFETIME = 0
        USES = 1

    _INVITES_URL_TMPL: str = VK_URL + "/event{event_id}/settings/requests"

    def __call__(self, event_id: int, settings: InviteLinkSettings,
                 driver: WebDriver, wait: WebDriverWait) -> str:
        driver.get(self._INVITES_URL_TMPL.format(event_id=event_id))

        clickable(wait, self.Modal.OPEN_BUTTON)
        existing = _links(driver)

        driver.find_element(*self.Modal.OPEN_BUTTON).click()

        modal = visible(wait, self.Modal.SELF)

        set_custom_select_at(driver, wait, modal, self.Modal.LIFETIME, settings.lifetime.value)
        set_custom_select_at(driver, wait, modal, self.Modal.USES, settings.uses.value)

        modal.find_element(*self.Modal.CREATE).click()

        created = found(wait, lambda d: _links(d) - existing)

        if len(created) != 1:
            raise NoSuchElementException(f"Expected one new invite link, got {sorted(created)}")

        return created.pop()
