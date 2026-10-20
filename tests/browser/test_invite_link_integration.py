"""Tests that really change the test event: an invite link stays in the list,
access is switched and put back.
"""
import pytest
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_setup.event_setup_schema import Access, EventSetupSchema, _set_access
from justin.browser.invite_link.invite_link_schema import Link
from justin.browser.shared.elements import by_css, present
from justin.browser.shared.pacing import PAGE_SETTLE, pause
from justin.browser.shared.save_button import click_save
from justin.browser.vk_browser import VKBrowser
from tests.browser.vk_page import editing

_NAME_FIELD = by_css("[id='group_edit_name']")


def _open_edit(browser: VKBrowser, event_id: int) -> WebDriverWait:
    with editing(browser, EventSetupSchema._SETTINGS_URL_TMPL.format(event_id=event_id)) as wait:
        present(wait, _NAME_FIELD)

        return wait


def _saved_access(browser: VKBrowser) -> int:
    value = browser.driver.find_element(*Access.VALUE).get_attribute("value")

    return int(value)


def _save_and_reopen(browser: VKBrowser, event_id: int, wait: WebDriverWait) -> WebDriverWait:
    click_save(browser.driver, wait)

    pause(PAGE_SETTLE)

    return _open_edit(browser, event_id)


@pytest.mark.integration
class TestInviteLink:
    @pytest.mark.destructive
    def test_link_is_created(self, browser: VKBrowser, event_id: int) -> None:
        link = browser.create_invite_link(event_id)

        assert Link.PREFIX in link, f"not an invite link: {link!r}"


@pytest.mark.integration
class TestAccess:
    def test_access_survives_save(self, browser: VKBrowser, event_id: int) -> None:
        """Both values, not the target one: it may have been there already — that is how
        a silently ignored write hid."""
        wait = _open_edit(browser, event_id)
        original = _saved_access(browser)

        try:
            for expected in (Access.OPEN, Access.CLOSED):
                _set_access(browser.driver, wait, is_closed=expected == Access.CLOSED)

                wait = _save_and_reopen(browser, event_id, wait)

                assert _saved_access(browser) == expected, \
                    f"access did not survive the save: expected {expected}"
        finally:
            _set_access(browser.driver, wait, is_closed=original == Access.CLOSED)

            _save_and_reopen(browser, event_id, wait)
