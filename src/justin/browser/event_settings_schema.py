"""Top-level schema for configuring a VK event after creation."""
import time
from dataclasses import dataclass

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from justin.browser.event_settings_settings import (
    AddressesSettings, CtaSettings, EventSettingsSettings,
    ExtrasSettings, MessagesSettings,
)
from justin.browser.custom_select import set_custom_select
from justin.browser.event_setup_schema import EventSetupSchema
from justin.browser.save_button import find_save_buttons
from justin.browser.section_settings import MainSection
from justin.browser.section_schema import (
    FilesSchema, ListSwitchSchema, MaterialsSchema, MusicSchema,
    PhotosSchema, PostsSchema, ServicesSchema, TopicsSchema, VideosSchema,
)


def _wait_for_content(driver: WebDriver, wait: WebDriverWait) -> None:
    def ready(d) -> bool:
        try:
            skeletons = d.find_elements(By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
            return not any(el.is_displayed() for el in skeletons)
        except StaleElementReferenceException:
            return False
    wait.until(ready)
    time.sleep(0.5)


def _save(driver: WebDriver, wait: WebDriverWait) -> None:
    """Click the save button if the page has one. React pages auto-save."""
    buttons = find_save_buttons(driver)
    if buttons:
        driver.execute_script("arguments[0].click()", buttons[0])
        time.sleep(1.0)


def _set_checkbox_label(driver: WebDriver, testid: str, enabled: bool) -> None:
    """Toggle React checkbox-label (CTA, Extras). State from inner input.checked."""
    el = driver.find_element(By.CSS_SELECTOR, f"[data-testid='{testid}']")
    inp = el.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
    currently = inp.get_attribute("checked") == "true"
    if currently != enabled:
        driver.execute_script("arguments[0].click()", el)
        time.sleep(0.4)


_MESSAGES_SELECT = "settings_messages_enabled"
_MESSAGES_ON = "1"
_MESSAGES_OFF = "0"


def _set_custom_select(driver: WebDriver, wait: WebDriverWait, testid: str, value: str) -> None:
    """Set a VKUI CustomSelect by value — both the state and the check come from the
    hidden native select, so nothing here depends on the interface language."""
    native = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, f"select[data-testid='{testid}']")))

    if native.get_attribute("value") == value:
        return

    holder = driver.find_element(By.CSS_SELECTOR, f"input[data-testid='{testid}']")
    set_custom_select(driver, wait, holder, value)

    shown = native.get_attribute("value")

    if shown != value:
        raise ValueError(f"Select {testid!r} holds {shown!r}, expected {value!r}")


def _click_submit(driver: WebDriver) -> None:
    """Click the React settings Save button (no testid, matched by label)."""
    buttons = find_save_buttons(driver)

    if not buttons:
        raise NoSuchElementException("Save button not found")

    driver.execute_script("arguments[0].click()", buttons[0])
    time.sleep(1.0)


def _set_idd_toggle(driver: WebDriver, wait: WebDriverWait, testid: str, enabled: bool) -> None:
    """Toggle legacy idd_wrap element (Messages, Addresses). State from text content."""
    el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{testid}']")))
    currently = el.text.strip().lower() == "enabled"
    if currently != enabled:
        driver.execute_script("arguments[0].click()", el)
        time.sleep(0.4)


_REORDER_TOGGLE = "[data-testid='sections_toggle_reorder']"


def _enabled_cells(driver: WebDriver) -> list:
    section_list = driver.find_element(By.CSS_SELECTOR, "[data-testid='list_enabled']")
    children = driver.execute_script("return Array.from(arguments[0].children)", section_list)

    return [cell for cell in children if cell.text.strip()]


def _set_main_section(driver: WebDriver, wait: WebDriverWait, event_id: int,
                      section: MainSection) -> None:
    """The main block is whatever sits first, so the section is dragged to the top of the list."""
    label = driver.find_element(
        By.CSS_SELECTOR, f"[data-testid='{section.value}']").text.strip().splitlines()[0]

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, _REORDER_TOGGLE))).click()
    time.sleep(1.5)

    cells = _enabled_cells(driver)
    position = next((i for i, cell in enumerate(cells)
                     if cell.text.strip().splitlines()[0] == label), None)

    if position is None:
        raise NoSuchElementException(f"Section {label!r} is not enabled, cannot make it main")

    if position > 0:
        _drag_to_top(driver, cells[position], position)

    driver.find_element(By.CSS_SELECTOR, _REORDER_TOGGLE).click()
    time.sleep(1.5)
    _confirm_reorder(driver)

    driver.get(f"https://vk.com/event{event_id}/settings/sections")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='list_enabled']")))
    time.sleep(1.0)

    first = _enabled_cells(driver)[0].text.strip().splitlines()[0]

    if first != label:
        raise ValueError(f"Main section not applied: list starts with {first!r}, expected {label!r}")


def _confirm_reorder(driver: WebDriver) -> None:
    """Saving the order raises a warning dialog — the order is kept only after confirming it."""
    dialogs = [el for el in driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
               if el.is_displayed()]

    if not dialogs:
        return

    dialogs[0].find_element(By.CSS_SELECTOR, "[data-testid='form_modal_save']").click()
    time.sleep(2.0)


def _drag_to_top(driver: WebDriver, cell, position: int) -> None:
    """VKUI starts dragging only after a hover and a small initial move."""
    handle = cell.find_element(By.CSS_SELECTOR, ".vkuiCellDragger__host")
    distance = cell.rect["height"] * position + 10
    steps = 10

    chain = ActionChains(driver)
    chain.move_to_element(handle).pause(0.4).click_and_hold().pause(0.4)
    chain.move_by_offset(0, -3).pause(0.2)

    for _ in range(steps):
        chain.move_by_offset(0, -distance / steps).pause(0.08)

    chain.pause(0.4).release().perform()
    time.sleep(1.5)


@dataclass(frozen=True)
class EventSettingsSchema:
    setup: EventSetupSchema = EventSetupSchema()

    def __call__(self, event_id: int, settings: EventSettingsSettings,
                 driver: WebDriver, wait: WebDriverWait) -> None:
        if settings.setup is not None:
            print(f"  [setup] applying edit-page settings")
            self.setup(event_id, settings.setup, driver, wait)

        if settings.sections is not None:
            print(f"  [sections] applying sections config")
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
    def _apply_sections(event_id: int, config, driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"https://vk.com/event{event_id}/settings/sections")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='list_enabled']")))
        time.sleep(0.5)

        if config.posts is not None:
            print(f"    [posts] {config.posts}")
            PostsSchema("wall")(config.posts, driver, wait)
        if config.photos is not None:
            print(f"    [photos] {config.photos}")
            PhotosSchema("photos")(config.photos, driver, wait)
        if config.videos is not None:
            print(f"    [videos] {config.videos}")
            VideosSchema("videos")(config.videos, driver, wait)
        if config.topics is not None:
            print(f"    [topics] {config.topics}")
            TopicsSchema("discussions")(config.topics, driver, wait)
        if config.music is not None:
            print(f"    [music] {config.music}")
            MusicSchema("audios")(config.music, driver, wait)
        if config.files is not None:
            print(f"    [files] {config.files}")
            FilesSchema("files")(config.files, driver, wait)
        if config.materials is not None:
            print(f"    [materials] {config.materials}")
            MaterialsSchema("wiki")(config.materials, driver, wait)
        if config.services is not None:
            print(f"    [services] {config.services}")
            ServicesSchema("services")(config.services, driver, wait)

        for name, test_id in [("chats", "chats"), ("clips", "short_videos"),
                              ("articles", "articles"), ("moments", "narratives"),
                              ("products", "market")]:
            settings = getattr(config, name)

            if settings is not None:
                print(f"    [{name}] {settings}")
                ListSwitchSchema(test_id)(settings, driver, wait)

        if config.main_section is not None:
            print(f"    [main] {config.main_section.name}")
            _set_main_section(driver, wait, event_id, config.main_section)

    # ── cta ─────────────────────────────────────────────────────

    @staticmethod
    def _apply_cta(event_id: int, s: CtaSettings, driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"https://vk.com/event{event_id}/settings/cta")
        _wait_for_content(driver, wait)
        _set_checkbox_label(driver, "groups_edit_header_switch_label_cta", s.enabled)
        # React page — auto-saves on toggle, no group_save button

    # ── messages ────────────────────────────────────────────────

    @staticmethod
    def _apply_messages(event_id: int, s: MessagesSettings,
                        driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"https://vk.com/event{event_id}/settings/messages")
        _wait_for_content(driver, wait)
        _set_custom_select(driver, wait, _MESSAGES_SELECT,
                           _MESSAGES_ON if s.enabled else _MESSAGES_OFF)
        if s.first_message is not None:
            ta = driver.find_element(By.CSS_SELECTOR, "[data-testid='settings_messages_first_message']")
            driver.execute_script("arguments[0].value = ''", ta)
            ta.send_keys(s.first_message)
            time.sleep(0.3)
        _click_submit(driver)

    # ── addresses ───────────────────────────────────────────────

    @staticmethod
    def _apply_addresses(event_id: int, s: AddressesSettings,
                         driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"https://vk.com/event{event_id}?act=addresses")
        _wait_for_content(driver, wait)
        _set_idd_toggle(driver, wait, "groups_edit_g_addresses", s.enabled)
        _save(driver, wait)

    # ── extras ──────────────────────────────────────────────────

    @staticmethod
    def _apply_extras(event_id: int, s: ExtrasSettings,
                      driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(f"https://vk.com/event{event_id}/settings/extras")
        _wait_for_content(driver, wait)

        if s.hide_tag_suggestions is not None:
            _set_checkbox_label(driver, "photo_recognize_enabled", s.hide_tag_suggestions)
        if s.co_creatorship is not None:
            _set_checkbox_label(driver, "clips_co_ownership_enabled", s.co_creatorship)
        if s.story_replies is not None:
            _set_checkbox_label(driver, "stories_replies_enabled", s.story_replies)
        if s.show_in_left_menu is not None:
            _set_checkbox_label(driver, "show_in_left_menu", s.show_in_left_menu)

        _save(driver, wait)
