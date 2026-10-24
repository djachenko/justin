"""Top-level schema for configuring a VK event after creation."""
from dataclasses import dataclass
from typing import Callable

from justin_utils.util import first
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException, TimeoutException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_settings.event_settings_settings import (
    AddressesSettings, CtaSettings, EventSettingsSettings,
    ExtrasSettings, MessagesSettings,
)
from justin.browser.event_setup.event_setup_schema import EventSetupSchema
from justin.browser.sections.section_schema import (
    FilesSchema, ListSwitchSchema, MaterialsSchema, MusicSchema, PhotosSchema,
    PostsSchema, SectionSchema, ServicesSchema, TopicsSchema, VideosSchema,
)
from justin.browser.sections.section_settings import MainSection, SectionsConfig
from justin.browser.shared.custom_select import set_custom_select
from justin.browser.shared.elements import by_css, by_testid, found, present, type_into
from justin.browser.shared.pacing import AFTER_ACTION, PAGE_SETTLE, pause, varied
from justin.browser.shared.page import wait_for_content
from justin.browser.shared.save_button import click_save, click_save_if_present
from justin.browser.shared.waiting import Wait
from justin.shared.vk import VK_URL


class Messages:
    """The messages page keeps its state in a hidden native select — values, not labels."""
    SELECT = "settings_messages_enabled"


class Pages:
    CONTENT_TABS = VK_URL + "/event{event_id}/settings/content_tabs"
    SECTIONS = VK_URL + "/event{event_id}/settings/sections"


class Reorder:
    """The main block is set by dragging a tab to the top of the content tabs list."""
    TOGGLE = by_testid("sections_toggle_reorder")
    LIST = by_css("[role='main'] [role='list']")  # only exists in reorder mode
    TAB_CELLS = by_css("[data-testid^='content_tabs_'][data-testid$='_cell']")
    DRAG_HANDLE = by_css(".vkuiCellDragger__host")
    SETTLE = 1.5  # reorder mode turns on and off with an animation


_STATE_TIMEOUT = 5

_SECTIONS_LIST = by_testid("list_sections")
_DIALOG = by_css("[role='dialog']")

# VKUI drag and drop: the grab has to be noticeable and the step small, or it reads the
# movement as a jerk and drops the element.
_GRAB = 0.4
_DRAG_STEP = 0.08
_DRAG_STEPS = 10
_NUDGE = 3  # the first few pixels; without them the drag never starts

# SectionsConfig attribute → schema, by page. The order is the order of application.
_CONTENT_TABS: list[tuple[str, SectionSchema | ListSwitchSchema]] = [
    ("posts", PostsSchema("content_tabs_wall_cell")),
    ("photos", PhotosSchema("content_tabs_photos_cell")),
    ("videos", VideosSchema("content_tabs_videos_cell")),
    ("topics", TopicsSchema("content_tabs_discussions_cell")),
    ("music", MusicSchema("content_tabs_audios_cell")),
    ("services", ServicesSchema("content_tabs_services_cell")),
    ("products", ListSwitchSchema("content_tabs_market_switch")),
    ("clips", ListSwitchSchema("content_tabs_short_videos_switch")),
]

_SECTIONS: list[tuple[str, SectionSchema | ListSwitchSchema]] = [
    ("files", FilesSchema("files")),
    ("materials", MaterialsSchema("wiki")),
    ("chats", ListSwitchSchema("chats_switch")),
    ("articles", ListSwitchSchema("articles_switch")),
    ("moments", ListSwitchSchema("narratives_switch")),
]


def _checkbox(driver: WebDriver, testid: str) -> WebElement:
    """React checkbox-label (CTA, Extras): the state and the click both belong to the inner input."""
    return driver.find_element(*by_testid(testid)).find_element(*by_css("input[type='checkbox']"))


def _checkbox_label_state(driver: WebDriver, testid: str) -> bool:
    return _checkbox(driver, testid).is_selected()


def _idd_toggle_state(driver: WebDriver, testid: str) -> bool:
    """Legacy idd_wrap (Addresses): the state is in the hidden input next to the label."""
    return driver.find_element(*by_css(f"#{testid}_input")).get_attribute("value") == "1"


def _wait_for_state(driver: WebDriver, read: Callable[[WebDriver, str], bool],
                    testid: str, expected: bool) -> None:
    """A JS click that never landed looks exactly like one that did — check the state moved."""
    def applied(_: WebDriver) -> bool:
        try:
            return read(driver, testid) == expected
        except StaleElementReferenceException:
            return False

    try:
        Wait(driver, _STATE_TIMEOUT).until(applied)
    except TimeoutException:
        raise ValueError(f"{testid!r} stayed {not expected}, expected {expected}")


def _set_checkbox_label(driver: WebDriver, testid: str, enabled: bool) -> None:
    checkbox = _checkbox(driver, testid)

    if checkbox.is_selected() == enabled:
        return

    driver.execute_script("arguments[0].click()", checkbox)

    _wait_for_state(driver, _checkbox_label_state, testid, enabled)

    pause(AFTER_ACTION)


def _set_custom_select(driver: WebDriver, wait: WebDriverWait, testid: str, value: str) -> None:
    """Set a VKUI CustomSelect by value — both the state and the check come from the
    hidden native select, so nothing here depends on the interface language."""
    native = present(wait, by_css(f"select[data-testid='{testid}']"))

    if native.get_attribute("value") == value:
        return

    holder = driver.find_element(*by_css(f"input[data-testid='{testid}']"))

    set_custom_select(driver, wait, holder, value)

    shown = native.get_attribute("value")

    if shown != value:
        raise ValueError(f"Select {testid!r} holds {shown!r}, expected {value!r}")


def _set_idd_toggle(driver: WebDriver, wait: WebDriverWait, testid: str, enabled: bool) -> None:
    el = present(wait, by_testid(testid))

    if _idd_toggle_state(driver, testid) == enabled:
        return

    driver.execute_script("arguments[0].click()", el)

    item = found(wait, lambda d: el.find_element(*by_testid(f"idd_item_{int(enabled)}")))

    driver.execute_script("arguments[0].click()", item)

    _wait_for_state(driver, _idd_toggle_state, testid, enabled)

    pause(AFTER_ACTION)


def _label_of(cell: WebElement) -> str:
    return cell.text.strip().splitlines()[0]


def _reorder_cells(driver: WebDriver) -> list[WebElement]:
    section_list = driver.find_element(*Reorder.LIST)
    children = driver.execute_script("return Array.from(arguments[0].children)", section_list)

    return [cell for cell in children if cell.text.strip()]


def _drag_to_top(driver: WebDriver, cell: WebElement, position: int) -> None:
    """VKUI starts dragging only after a hover and a small initial move."""
    handle = cell.find_element(*Reorder.DRAG_HANDLE)
    distance = cell.rect["height"] * position + 10

    chain = ActionChains(driver)

    chain \
        .move_to_element(handle) \
        .pause(varied(_GRAB)) \
        .click_and_hold() \
        .pause(varied(_GRAB)) \
        .move_by_offset(0, -_NUDGE) \
        .pause(varied(_DRAG_STEP))

    # Uneven steps with uneven pauses — a hand does not move at a constant rate.
    for _ in range(_DRAG_STEPS):
        chain \
            .move_by_offset(0, -round(varied(distance / _DRAG_STEPS))) \
            .pause(varied(_DRAG_STEP))

    chain \
        .move_by_offset(0, -_NUDGE) \
        .pause(varied(_GRAB)) \
        .release() \
        .perform()

    pause(Reorder.SETTLE)


def _confirm_reorder(driver: WebDriver) -> None:
    """Saving the order raises a warning dialog — the order is kept only after confirming it."""
    dialogs = [el for el in driver.find_elements(*_DIALOG) if el.is_displayed()]

    if not dialogs:
        return

    dialogs[0].find_element(*SectionSchema.Modal.SAVE).click()

    pause(PAGE_SETTLE)


def _check_first(labels: list[str], label: str, stage: str) -> None:
    if labels[0] != label:
        raise ValueError(f"Main section not applied {stage}: list starts with {labels[0]!r}, "
                         f"expected {label!r}")


def _set_main_section(driver: WebDriver, wait: WebDriverWait, event_id: int,
                      section: MainSection) -> None:
    """The main block is whatever tab sits first, so the tab is dragged to the top of the list.

    Not every enabled tab can be moved — only those the reorder list offers.
    """
    url = Pages.CONTENT_TABS.format(event_id=event_id)

    driver.get(url)

    label = _label_of(present(wait, by_testid(f"content_tabs_{section.value}_cell")))

    toggle = present(wait, Reorder.TOGGLE)

    # VK hides reordering when there is nothing to move — fewer than two tabs in the list.
    if not toggle.is_enabled():
        print(f"    [main] nothing to reorder, {label!r} stays where it is")

        return

    toggle.click()

    pause(Reorder.SETTLE)

    cells = _reorder_cells(driver)
    movable = [_label_of(cell) for cell in cells]
    found = first(enumerate(cells), key=lambda pair: _label_of(pair[1]) == label)

    if found is None:
        raise NoSuchElementException(f"Tab {label!r} is not in the reorder list {movable}, "
                                     f"cannot make it main")

    position, cell = found

    if position > 0:
        _drag_to_top(driver, cell, position)

        # The drag may have failed silently — check before saving the order.
        _check_first([_label_of(cell) for cell in _reorder_cells(driver)], label, "after drag")

    driver.find_element(*Reorder.TOGGLE).click()

    pause(Reorder.SETTLE)

    _confirm_reorder(driver)

    driver.get(url)

    present(wait, Reorder.TOGGLE)

    pause(PAGE_SETTLE)

    # Outside reorder mode there is no list — the order is read from the tab cells.
    shown = [_label_of(cell) for cell in driver.find_elements(*Reorder.TAB_CELLS)]

    _check_first([shown_label for shown_label in shown if shown_label in movable], label, "after save")


@dataclass(frozen=True)
class EventSettingsSchema:
    setup: EventSetupSchema = EventSetupSchema()

    def __call__(self, event_id: int, settings: EventSettingsSettings,
                 driver: WebDriver, wait: WebDriverWait) -> None:
        if settings.setup is not None:
            print("  [setup] applying edit-page settings")
            self.setup(event_id, settings.setup, driver, wait)

        if settings.sections is not None:
            print("  [sections] applying sections config")
            self._apply_sections(event_id, settings.sections, driver, wait)

        if settings.cta is not None:
            print(f"  [cta] enabled={settings.cta.enabled}")
            self._apply_cta(event_id, settings.cta, driver, wait)

        if settings.messages is not None:
            print(f"  [messages] enabled={settings.messages.enabled}")
            self._apply_messages(event_id, settings.messages, driver, wait)

        if settings.addresses is not None:
            print(f"  [addresses] enabled={settings.addresses.enabled}")
            self._apply_addresses(event_id, settings.addresses, driver, wait)

        if settings.extras is not None:
            print(f"  [extras] {settings.extras}")
            self._apply_extras(event_id, settings.extras, driver, wait)

    # ── sections ────────────────────────────────────────────────

    @staticmethod
    def _apply_sections(event_id: int, config: SectionsConfig,
                        driver: WebDriver, wait: WebDriverWait) -> None:
        for url, ready, schemas in [
            (Pages.CONTENT_TABS, Reorder.TOGGLE, _CONTENT_TABS),
            (Pages.SECTIONS, _SECTIONS_LIST, _SECTIONS),
        ]:
            pending = [(name, schema, getattr(config, name)) for name, schema in schemas
                       if getattr(config, name) is not None]

            if not pending:
                continue

            driver.get(url.format(event_id=event_id))

            present(wait, ready)

            pause(AFTER_ACTION)

            for name, schema, settings in pending:
                print(f"    [{name}] {settings}")

                schema(settings, driver, wait)

        if config.main_section is not None:
            print(f"    [main] {config.main_section.name}")

            _set_main_section(driver, wait, event_id, config.main_section)

    # ── cta ─────────────────────────────────────────────────────

    @staticmethod
    def _apply_cta(event_id: int, s: CtaSettings, driver: WebDriver, wait: WebDriverWait) -> None:
        """CTA — call to action: the action button in the community header ("Write", "Go to").

        A React page: it saves itself on toggle, there is no Save button.
        """
        driver.get(f"{VK_URL}/event{event_id}/settings/cta")

        wait_for_content(wait)

        _set_checkbox_label(driver, "groups_edit_header_switch_label_cta", s.enabled)

    # ── messages ────────────────────────────────────────────────

    @staticmethod
    def _apply_messages(event_id: int, s: MessagesSettings,
                        driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"{VK_URL}/event{event_id}/settings/messages")

        wait_for_content(wait)

        _set_custom_select(driver, wait, Messages.SELECT, str(int(s.enabled)))

        if s.first_message is not None:
            ta = driver.find_element(*by_testid("settings_messages_first_message"))

            ta.clear()

            type_into(ta, s.first_message)

            pause(AFTER_ACTION)

        click_save(driver, wait)

    # ── addresses ───────────────────────────────────────────────

    @staticmethod
    def _apply_addresses(event_id: int, s: AddressesSettings,
                         driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"{VK_URL}/event{event_id}?act=addresses")

        wait_for_content(wait)

        _set_idd_toggle(driver, wait, "groups_edit_g_addresses", s.enabled)

        click_save_if_present(driver)

    # ── extras ──────────────────────────────────────────────────

    @staticmethod
    def _apply_extras(event_id: int, s: ExtrasSettings,
                      driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"{VK_URL}/event{event_id}/settings/extras")

        wait_for_content(wait)

        if s.co_creatorship is not None:
            _set_checkbox_label(driver, "clips_co_ownership_enabled", s.co_creatorship)

        if s.story_replies is not None:
            _set_checkbox_label(driver, "stories_replies_enabled", s.story_replies)

        if s.show_in_left_menu is not None:
            _set_checkbox_label(driver, "show_in_left_menu", s.show_in_left_menu)

        click_save_if_present(driver)
