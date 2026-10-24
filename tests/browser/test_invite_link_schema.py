"""Invite link creation on fakes: the new link is told apart from the ones already there."""
from typing import cast

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver

from justin.browser.invite_link import invite_link_schema
from justin.browser.invite_link.invite_link_schema import InviteLinkSchema
from justin.browser.invite_link.invite_link_settings import InviteLinkSettings, LinkLifetime, LinkUses
from tests.browser.fakes import fast_wait


class FakeInput:
    def __init__(self, value: str | None) -> None:
        self.value = value

    def get_attribute(self, name: str) -> str | None:
        assert name == "value"
        return self.value


class FakeButton:
    def __init__(self, on_click=lambda: None) -> None:
        self.on_click = on_click

    def is_displayed(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True

    def click(self) -> None:
        self.on_click()


class FakeModal(FakeButton):
    def __init__(self, create: FakeButton) -> None:
        super().__init__()
        self.create = create

    def find_element(self, by: str, selector: str) -> FakeButton:
        assert selector == "[data-testid='settings-invite-link-modal-create-button']"
        return self.create


class FakeDriver:
    """The Invites page: link inputs already there, and the ones Create adds."""

    def __init__(self, existing: list[str | None], created: list[str]) -> None:
        self.inputs = [FakeInput(value) for value in existing]
        self.opened: list[str] = []
        self.modal = FakeModal(FakeButton(lambda: self.inputs.extend(FakeInput(v) for v in created)))
        self.buttons = {
            "[data-testid='settings-invitations-create-link-button']": FakeButton(),
            "[data-testid='link_invite_modal']": self.modal,
        }

    def get(self, url: str) -> None:
        self.opened.append(url)

    def find_element(self, by: str, selector: str) -> FakeButton:
        return self.buttons[selector]

    def find_elements(self, by: str, selector: str) -> list[FakeInput]:
        assert selector == "input[value^='https://vk.']"
        return self.inputs


@pytest.fixture
def selects(monkeypatch) -> list[tuple]:
    selects: list[tuple] = []
    monkeypatch.setattr(invite_link_schema, "set_custom_select_at",
                        lambda driver, wait, container, position, value: selects.append((position, value)))
    return selects


def _create(driver: FakeDriver, settings: InviteLinkSettings | None = None) -> str:
    return InviteLinkSchema()(7, settings or InviteLinkSettings(), cast(WebDriver, driver), fast_wait(driver))


@pytest.mark.usefixtures("selects")
class TestInviteLinkSchema:
    def test_returns_the_new_link_only(self) -> None:
        """Every link on the page is an input — the new one is what Create added."""
        driver = FakeDriver(
            existing=["https://vk.ru/invite/old", "https://vk.ru/some_page", None],
            created=["https://vk.ru/invite/new"],
        )

        assert _create(driver) == "https://vk.ru/invite/new"
        assert driver.opened == ["https://vk.ru/event7/settings/requests"]

    def test_lifetime_and_uses_go_to_their_selects(self, selects: list[tuple]) -> None:
        driver = FakeDriver(existing=[], created=["https://vk.ru/invite/new"])

        _create(driver, InviteLinkSettings(lifetime=LinkLifetime.HOUR, uses=LinkUses.ONCE))

        assert selects == [(0, "3600"), (1, "1")]

    def test_more_than_one_new_link_raises(self) -> None:
        driver = FakeDriver(existing=[], created=["https://vk.ru/invite/a", "https://vk.ru/invite/b"])

        with pytest.raises(NoSuchElementException):
            _create(driver)

    def test_no_new_link_times_out(self) -> None:
        driver = FakeDriver(existing=["https://vk.ru/invite/old"], created=["https://vk.ru/invite/old"])

        with pytest.raises(TimeoutException):
            _create(driver)
