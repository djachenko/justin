"""Selector contract: the elements the schemas rely on are still on the live VK pages.
Changes nothing — only reads.

A failure means VK rewrote the page: see the test name and the selector.
"""
from datetime import datetime

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

from justin.browser.event_creation.event_creation_schema import EventCreationSchema
from justin.browser.event_settings.event_settings_schema import Messages
from justin.browser.event_setup.event_setup_schema import (
    Access, Selectors, _fill_date_field, _visible_selectors,
)
from justin.browser.shared.custom_select import SELECT_HOLDER, option_by_value
from justin.browser.shared.elements import by_css, by_testid, by_xpath, clickable, found, present, visible
from justin.browser.invite_link.invite_link_schema import InviteLinkSchema
from justin.browser.invite_link.invite_link_settings import LinkLifetime, LinkUses
from justin.browser.shared.save_button import find_save_buttons
from justin.browser.sections.section_schema import (
    FilesSchema, MaterialsSchema, MusicSchema, SectionSchema,
    PhotosSchema, PostsSchema, TopicsSchema, VideosSchema,
)
from justin.browser.vk_browser import VKBrowser
from justin.shared.vk import VK_URL
from tests.browser.vk_page import editing, modal, reading

PAGES = {
    "setup": (
        VK_URL + "/event{event_id}?act=edit",
        [
            "[id='group_edit_name']",
            "[id='group_edit_desc']",
            "[id='group_website']",
            "[id='group_edit_phone']",
            "[id='event_mail']",
        ],
    ),
    "content_tabs": (
        VK_URL + "/event{event_id}/settings/content_tabs",
        ["[data-testid='sections_toggle_reorder']"],
    ),
    "sections": (
        VK_URL + "/event{event_id}/settings/sections",
        ["[data-testid='list_sections']"],
    ),
    "cta": (
        VK_URL + "/event{event_id}/settings/cta",
        ["[data-testid='groups_edit_header_switch_label_cta'] input[type='checkbox']"],
    ),
    "messages": (
        VK_URL + "/event{event_id}/settings/messages",
        [
            "input[data-testid='settings_messages_enabled']",
            "select[data-testid='settings_messages_enabled']",
            "textarea[data-testid='settings_messages_first_message']",
        ],
    ),
    "addresses": (
        VK_URL + "/event{event_id}?act=addresses",
        ["[data-testid='groups_edit_g_addresses']"],
    ),
    "invites": (
        VK_URL + "/event{event_id}/settings/requests",
        [
            "[data-testid='settings-invitations-create-link-button']",
            "[data-testid='settings-invitations-by-link']",
        ],
    ),
    "extras": (
        VK_URL + "/event{event_id}/settings/extras",
        [
            "[data-testid='clips_co_ownership_enabled']",
            "[data-testid='stories_replies_enabled']",
            "[data-testid='show_in_left_menu']",
        ],
    ),
}

_NAME_FIELD = by_css("[id='group_edit_name']")

SECTIONS = [
    ("content_tabs", PostsSchema("content_tabs_wall_cell")),
    ("content_tabs", PhotosSchema("content_tabs_photos_cell")),
    ("content_tabs", VideosSchema("content_tabs_videos_cell")),
    ("content_tabs", TopicsSchema("content_tabs_discussions_cell")),
    ("content_tabs", MusicSchema("content_tabs_audios_cell")),
    ("sections", FilesSchema("files")),
    ("sections", MaterialsSchema("wiki")),
]


@pytest.mark.integration
class TestSelectorContract:
    @pytest.mark.parametrize("page", PAGES)
    def test_page_selectors_present(self, browser: VKBrowser, event_id: int, page: str) -> None:
        url_tmpl, selectors = PAGES[page]

        def missing_in(driver: WebDriver) -> list[str]:
            return [selector for selector in selectors
                    if not driver.find_elements(*by_css(selector))]

        with reading(browser, url_tmpl.format(event_id=event_id)) as wait:
            try:
                wait.until(lambda driver: not missing_in(driver))
            except TimeoutException:
                pass

            missing = missing_in(browser.driver)

        assert not missing, f"[{page}] selectors gone: {missing}"

    def test_messages_select_values(self, browser: VKBrowser, event_id: int) -> None:
        """The schema picks by value, not by label."""
        with reading(browser, f"{VK_URL}/event{event_id}/settings/messages"):
            native = browser.driver.find_element(*by_css(f"select[data-testid='{Messages.SELECT}']"))
            values = [option.get_attribute("value")
                      for option in native.find_elements(*by_css("option"))]

        assert sorted(values) == ["0", "1"], f"select values: {values}"
        assert native.get_attribute("value") in values

    @pytest.mark.parametrize("position,hidden", [
        (Selectors.SUBJECT, "group_category_0"),
        (Selectors.CITY, "sel_groups_edit_city"),
    ], ids=["category", "city"])
    def test_selector_positions(self, browser: VKBrowser, event_id: int, position: int, hidden: str) -> None:
        """Category and city are picked by index among identical widgets — the index must
        point to the widget bound to the hidden input."""
        with reading(browser, PAGES["setup"][0].format(event_id=event_id)) as wait:
            present(wait, _NAME_FIELD)

            widget = browser.driver.find_element(*by_css(f"input[name='{hidden}']")).find_element(
                *by_xpath("ancestor::*[contains(@class, 'selector')][1]"))

            at_position = _visible_selectors(browser.driver)[position]

        assert at_position in widget.find_elements(*by_css(".selector_input")), \
            f"position {position} does not hold the widget of {hidden!r}"

    @pytest.mark.parametrize("page", ["setup", "messages", "addresses"])
    def test_save_button_present(self, browser: VKBrowser, event_id: int, page: str) -> None:
        url_tmpl, _ = PAGES[page]

        with reading(browser, url_tmpl.format(event_id=event_id)) as wait:
            wait.until(lambda d: find_save_buttons(d))

    @pytest.mark.parametrize("page,section", SECTIONS, ids=[s.test_id for _, s in SECTIONS])
    def test_section_modal_selectors(self, browser: VKBrowser, event_id: int, page: str, section: SectionSchema) -> None:
        toggle = by_testid(section.enabled.test_id)
        url = PAGES[page][0].format(event_id=event_id)

        with modal(browser, url, inside_modal=toggle) as wait:
            section._open(browser.driver, wait)

            present(wait, by_testid("form_modal_save"))

    @pytest.mark.parametrize("dt", [
        datetime(2027, 2, 3, 9, 5),      # another year ahead
        datetime(2025, 12, 28, 20, 0),   # a year back
    ])
    def test_date_field_is_filled(self, browser: VKBrowser, event_id: int, dt: datetime) -> None:
        with editing(browser, PAGES["setup"][0].format(event_id=event_id)) as wait:
            present(wait, _NAME_FIELD)

            _fill_date_field(browser.driver, wait, "group_start_date_date_input", dt)

            shown = browser.driver.find_element(
                *by_css("[id='group_start_date_date_input']")).get_attribute("value")

        assert str(dt.day) in shown and str(dt.year) in shown, f"the field shows {shown!r}"

    def test_access_dropdown_has_both_options(self, browser: VKBrowser, event_id: int) -> None:
        with editing(browser, PAGES["setup"][0].format(event_id=event_id)) as wait:
            present(wait, _NAME_FIELD)

            browser.driver.find_element(*by_css(Access.WIDGET)).click()

            items = found(wait, lambda d: [el for el in d.find_elements(
                *Access.ITEMS) if el.is_displayed()] or None)

        assert len(items) == 2, f"the access dropdown has {len(items)} items: {[i.text for i in items]}"

    @pytest.mark.parametrize("position,options", [
        (InviteLinkSchema.Modal.LIFETIME, list(LinkLifetime)),
        (InviteLinkSchema.Modal.USES, list(LinkUses)),
    ], ids=["lifetime", "uses"])
    def test_invite_modal_options(self, browser: VKBrowser, event_id: int, position: int, options: list) -> None:
        url = PAGES["invites"][0].format(event_id=event_id)

        with modal(browser, url, inside_modal=InviteLinkSchema.Modal.SELF) as wait:
            clickable(wait, InviteLinkSchema.Modal.OPEN_BUTTON).click()

            dialog = visible(wait, InviteLinkSchema.Modal.SELF)
            dialog.find_element(*InviteLinkSchema.Modal.CREATE)

            holder = dialog.find_elements(*SELECT_HOLDER)[position]

            browser.driver.execute_script("arguments[0].click()", holder)

            found(wait, lambda d: d.find_elements(*by_css("[role='option']")))

            missing = [option.name for option in options
                       if not [el for el in browser.driver.find_elements(
                           *by_css(option_by_value(option.value))) if el.is_displayed()]]

        assert not missing, f"options gone: {missing}"

    def test_event_creation_wizard_opens(self, browser: VKBrowser) -> None:
        with editing(browser, EventCreationSchema._URL) as wait:
            present(wait, by_css(EventCreationSchema._IFRAME_CSS))
