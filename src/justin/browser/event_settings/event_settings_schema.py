"""Top-level schema for configuring a VK event after creation."""
from dataclasses import dataclass

from justin_utils.util import first
from selenium.common.exceptions import NoSuchElementException
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
from justin.browser.shared.elements import by_css, by_testid, present
from justin.browser.shared.pacing import AFTER_ACTION, PAGE_SETTLE, pause, varied
from justin.browser.shared.page import wait_for_content
from justin.browser.shared.save_button import click_save, click_save_if_present

_MESSAGES_SELECT = "settings_messages_enabled"
_MESSAGES_ON = "1"
_MESSAGES_OFF = "0"

_CONTENT_TABS_URL = "https://vk.com/event{event_id}/settings/content_tabs"
_SECTIONS_URL = "https://vk.com/event{event_id}/settings/sections"

_SECTIONS_LIST = by_testid("list_sections")
_REORDER_TOGGLE = by_testid("sections_toggle_reorder")
_REORDER_LIST = by_css("[role='main'] [role='list']")  # появляется только в режиме перестановки
_TAB_CELLS = by_css("[data-testid^='content_tabs_'][data-testid$='_cell']")
_MODAL_SAVE = by_testid("form_modal_save")
_DRAG_HANDLE = by_css(".vkuiCellDragger__host")
_DIALOG = by_css("[role='dialog']")

_REORDER_SETTLE = 1.5  # режим перетаскивания включается и выключается с анимацией

# Перетаскивание VKUI: хватка должна быть заметной, а шаг — мелким, иначе оно
# считает движение рывком и бросает элемент.
_GRAB = 0.4
_DRAG_STEP = 0.08
_DRAG_STEPS = 10
_NUDGE = 3  # первый сдвиг на пиксели, без него перетаскивание не начинается

# Атрибут SectionsConfig → схема, по страницам. Порядок — порядок применения.
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


def _set_checkbox_label(driver: WebDriver, testid: str, enabled: bool) -> None:
    """Toggle React checkbox-label (CTA, Extras). State from inner input.checked."""
    el = driver.find_element(*by_testid(testid))
    inp = el.find_element(*by_css("input[type='checkbox']"))

    currently = (inp.get_attribute("checked") == "true")

    if currently == enabled:
        return

    driver.execute_script("arguments[0].click()", el)

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
    """Toggle legacy idd_wrap element (Messages, Addresses). State from text content."""
    el = present(wait, by_testid(testid))

    currently = (el.text.strip().lower() == "enabled")

    if currently == enabled:
        return

    driver.execute_script("arguments[0].click()", el)

    pause(AFTER_ACTION)


def _label_of(cell: WebElement) -> str:
    return cell.text.strip().splitlines()[0]


def _reorder_cells(driver: WebDriver) -> list[WebElement]:
    section_list = driver.find_element(*_REORDER_LIST)
    children = driver.execute_script("return Array.from(arguments[0].children)", section_list)

    return [cell for cell in children if cell.text.strip()]


def _drag_to_top(driver: WebDriver, cell: WebElement, position: int) -> None:
    """VKUI starts dragging only after a hover and a small initial move."""
    handle = cell.find_element(*_DRAG_HANDLE)
    distance = cell.rect["height"] * position + 10

    chain = ActionChains(driver)

    chain \
        .move_to_element(handle) \
        .pause(varied(_GRAB)) \
        .click_and_hold() \
        .pause(varied(_GRAB)) \
        .move_by_offset(0, -_NUDGE) \
        .pause(varied(_DRAG_STEP))

    # Шаги разной длины и с разными паузами — рука не двигается равномерно.
    for _ in range(_DRAG_STEPS):
        chain \
            .move_by_offset(0, -round(varied(distance / _DRAG_STEPS))) \
            .pause(varied(_DRAG_STEP))

    chain \
        .move_by_offset(0, -_NUDGE) \
        .pause(varied(_GRAB)) \
        .release() \
        .perform()

    pause(_REORDER_SETTLE)


def _confirm_reorder(driver: WebDriver) -> None:
    """Saving the order raises a warning dialog — the order is kept only after confirming it."""
    dialogs = [el for el in driver.find_elements(*_DIALOG) if el.is_displayed()]

    if not dialogs:
        return

    dialogs[0].find_element(*_MODAL_SAVE).click()

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
    url = _CONTENT_TABS_URL.format(event_id=event_id)

    driver.get(url)

    label = _label_of(present(wait, by_testid(f"content_tabs_{section.value}_cell")))

    toggle = present(wait, _REORDER_TOGGLE)

    # VK выключает перестановку, когда двигать нечего — в списке меньше двух вкладок.
    if not toggle.is_enabled():
        print(f"    [main] nothing to reorder, {label!r} stays where it is")

        return

    toggle.click()

    pause(_REORDER_SETTLE)

    cells = _reorder_cells(driver)
    movable = [_label_of(cell) for cell in cells]
    found = first(enumerate(cells), key=lambda pair: _label_of(pair[1]) == label)

    if found is None:
        raise NoSuchElementException(f"Tab {label!r} is not in the reorder list {movable}, "
                                     f"cannot make it main")

    position, cell = found

    if position > 0:
        _drag_to_top(driver, cell, position)

        # Перетаскивание могло сорваться молча — проверяем до того, как сохранять порядок.
        _check_first([_label_of(cell) for cell in _reorder_cells(driver)], label, "after drag")

    driver.find_element(*_REORDER_TOGGLE).click()

    pause(_REORDER_SETTLE)

    _confirm_reorder(driver)

    driver.get(url)

    present(wait, _REORDER_TOGGLE)

    pause(PAGE_SETTLE)

    # Вне режима перестановки списка нет — порядок читается по ячейкам вкладок.
    shown = [_label_of(cell) for cell in driver.find_elements(*_TAB_CELLS)]

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
            (_CONTENT_TABS_URL, _REORDER_TOGGLE, _CONTENT_TABS),
            (_SECTIONS_URL, _SECTIONS_LIST, _SECTIONS),
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
        """CTA — call to action: кнопка действия в шапке сообщества («Написать», «Перейти»).

        React-страница, сохраняется сама при переключении — кнопки Save нет.
        """
        driver.get(f"https://vk.com/event{event_id}/settings/cta")

        wait_for_content(wait)

        _set_checkbox_label(driver, "groups_edit_header_switch_label_cta", s.enabled)

    # ── messages ────────────────────────────────────────────────

    @staticmethod
    def _apply_messages(event_id: int, s: MessagesSettings,
                        driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"https://vk.com/event{event_id}/settings/messages")

        wait_for_content(wait)

        if s.enabled:
            value = _MESSAGES_ON
        else:
            value = _MESSAGES_OFF

        _set_custom_select(driver, wait, _MESSAGES_SELECT, value)

        if s.first_message is not None:
            ta = driver.find_element(*by_testid("settings_messages_first_message"))

            driver.execute_script("arguments[0].value = ''", ta)
            ta.send_keys(s.first_message)

            pause(AFTER_ACTION)

        click_save(driver, wait)

    # ── addresses ───────────────────────────────────────────────

    @staticmethod
    def _apply_addresses(event_id: int, s: AddressesSettings,
                         driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"https://vk.com/event{event_id}?act=addresses")

        wait_for_content(wait)

        _set_idd_toggle(driver, wait, "groups_edit_g_addresses", s.enabled)

        click_save_if_present(driver)

    # ── extras ──────────────────────────────────────────────────

    @staticmethod
    def _apply_extras(event_id: int, s: ExtrasSettings,
                      driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"https://vk.com/event{event_id}/settings/extras")

        wait_for_content(wait)

        if s.hide_tag_suggestions is not None:
            _set_checkbox_label(driver, "photo_recognize_enabled", s.hide_tag_suggestions)

        if s.co_creatorship is not None:
            _set_checkbox_label(driver, "clips_co_ownership_enabled", s.co_creatorship)

        if s.story_replies is not None:
            _set_checkbox_label(driver, "stories_replies_enabled", s.story_replies)

        if s.show_in_left_menu is not None:
            _set_checkbox_label(driver, "show_in_left_menu", s.show_in_left_menu)

        click_save_if_present(driver)
