"""Top-level schema for configuring a VK event after creation."""
import time
from dataclasses import dataclass

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException

from justin.browser.event_settings_settings import (
    AddressesSettings, CtaSettings, EventSettingsSettings,
    ExtrasSettings, MessagesSettings,
)
from justin.browser.event_setup_schema import EventSetupSchema
from justin.browser.section_schema import (
    FilesSchema, MaterialsSchema, MusicSchema,
    PhotosSchema, PostsSchema, TopicsSchema, VideosSchema,
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
    """Click group_save if present (legacy pages). React pages auto-save."""
    btns = driver.find_elements(By.CSS_SELECTOR, "button.group_save")
    visible = [b for b in btns if b.is_displayed()]
    if visible:
        driver.execute_script("arguments[0].click()", visible[0])
        time.sleep(1.0)


def _set_checkbox_label(driver: WebDriver, testid: str, enabled: bool) -> None:
    """Toggle React checkbox-label (CTA, Extras). State from inner input.checked."""
    el = driver.find_element(By.CSS_SELECTOR, f"[data-testid='{testid}']")
    inp = el.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
    currently = inp.get_attribute("checked") == "true"
    if currently != enabled:
        driver.execute_script("arguments[0].click()", el)
        time.sleep(0.4)


def _set_idd_toggle(driver: WebDriver, wait: WebDriverWait, testid: str, enabled: bool) -> None:
    """Toggle legacy idd_wrap element (Messages, Addresses). State from text content."""
    el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{testid}']")))
    currently = el.text.strip().lower() == "enabled"
    if currently != enabled:
        driver.execute_script("arguments[0].click()", el)
        time.sleep(0.4)


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
        driver.get(f"https://vk.com/event{event_id}?act=messages")
        _wait_for_content(driver, wait)
        _set_idd_toggle(driver, wait, "groups_edit_g_messages", s.enabled)
        if s.first_message is not None:
            ta = driver.find_element(By.CSS_SELECTOR, "[id='group_edit_first_message']")
            driver.execute_script("arguments[0].value = ''", ta)
            ta.send_keys(s.first_message)
            time.sleep(0.3)
        _save(driver, wait)

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
