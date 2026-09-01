import time
from dataclasses import dataclass, fields
from enum import Enum

from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException, TimeoutException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.sections.settings import (
    AddAllowed, ContentType, PostsPublishing, SectionSettings,
)


_STATE_TIMEOUT = 5


def _switch_state(element) -> bool:
    """Some testids sit on the switch itself, others on the cell that wraps it.

    An element with no state at all is not a switch we know how to read: reporting it as
    enabled would turn "enable this" into a silent no-op, so it raises instead.
    """
    state = element.get_attribute("aria-checked")

    if state is None:
        switches = element.find_elements(By.CSS_SELECTOR, "[role='switch']")
        state = switches[0].get_attribute("aria-checked") if switches else None

    if state not in ("true", "false"):
        raise NoSuchElementException(
            f"No switch state on {element.get_attribute('data-testid')!r}, got {state!r}")

    return state == "true"


def _wait_for_state(driver: WebDriver, test_id: str, expected: bool) -> None:
    """A JS click that never landed looks exactly like one that did — check the switch moved.

    The element is looked up again on every poll: the list re-renders around a switch,
    so any reference held across the click goes stale.
    """
    def applied(_) -> bool:
        try:
            return _switch_state(_find(driver, test_id)) == expected
        except StaleElementReferenceException:
            return False

    try:
        WebDriverWait(driver, _STATE_TIMEOUT).until(applied)
    except TimeoutException:
        raise ValueError(f"Switch {test_id!r} stayed {not expected}, expected {expected}")


def _find(driver: WebDriver, test_id: str):
    return driver.find_element(By.CSS_SELECTOR, f'[data-testid="{test_id}"]')


@dataclass(frozen=True)
class Toggle:
    test_id: str

    def set_value(self, value: bool, driver: WebDriver, wait: WebDriverWait) -> None:
        el = _find(driver, self.test_id)
        currently_enabled = _switch_state(el)

        if currently_enabled != value:
            driver.execute_script("arguments[0].click()", el)
            _wait_for_state(driver, self.test_id, value)
            time.sleep(0.5)


@dataclass(frozen=True)
class Radio[E: Enum]:
    def set_value(self, value: E, driver: WebDriver, wait: WebDriverWait) -> None:
        """Значение енума — это и есть testid радиокнопки."""
        el = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{value.value}"]')
        driver.execute_script("arguments[0].click()", el)
        time.sleep(0.3)


@dataclass(frozen=True)
class Dropdown[E: Enum]:
    test_id: str

    def set_value(self, value: E, driver: WebDriver, wait: WebDriverWait) -> None:
        trigger = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{self.test_id}"]')
        driver.execute_script("arguments[0].click()", trigger)
        time.sleep(0.5)
        option_text = value.value
        option = wait.until(lambda d: next(
            (el for el in d.find_elements(By.CSS_SELECTOR, "[data-testid='dropdownactionsheet-item']")
             if el.is_displayed() and option_text in el.text),
            None,
        ))
        driver.execute_script("arguments[0].click()", option)
        time.sleep(0.3)


@dataclass(frozen=True)
class SectionSchema:
    test_id: str
    enabled: Toggle
    _SECTION_PAUSE: float = 1.5

    def __call__(self, settings: SectionSettings, driver: WebDriver, wait: WebDriverWait) -> None:
        self._open(driver, wait)
        self.enabled.set_value(settings.enabled, driver, wait)
        if settings.enabled:
            for f in fields(settings):
                if f.name == "enabled":
                    continue
                getattr(self, f.name).set_value(getattr(settings, f.name), driver, wait)
        self._save(driver, wait)
        time.sleep(self._SECTION_PAUSE)

    def _open(self, driver: WebDriver, wait: WebDriverWait) -> None:
        item = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="{self.test_id}"]')))
        driver.execute_script("arguments[0].click()", item)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-testid="{self.enabled.test_id}"]')))
        time.sleep(0.5)

    def _save(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="form_modal_save"]')))
        driver.execute_script("arguments[0].click()", btn)
        time.sleep(0.5)


@dataclass(frozen=True)
class PostsSchema(SectionSchema):
    enabled: Toggle = Toggle("form_wall_enabled")
    publishing: Dropdown[PostsPublishing] = Dropdown("form_wall_publishing_allowed")
    sharing_disabled: Toggle = Toggle("form_wall_sharing_disabled")


@dataclass(frozen=True)
class PhotosSchema(SectionSchema):
    enabled: Toggle = Toggle("form_photos_toggle")
    content_type: Radio[ContentType] = Radio()
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class VideosSchema(SectionSchema):
    enabled: Toggle = Toggle("form_videos_toggle")
    content_type: Radio[ContentType] = Radio()
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class TopicsSchema(SectionSchema):
    enabled: Toggle = Toggle("form_discussions_toggle")
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class MusicSchema(SectionSchema):
    enabled: Toggle = Toggle("form_audios_toggle")
    content_type: Radio[ContentType] = Radio()
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class FilesSchema(SectionSchema):
    enabled: Toggle = Toggle("form_files_toggle")
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class MaterialsSchema(SectionSchema):
    enabled: Toggle = Toggle("form_wiki_toggle")
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class ServicesSchema(SectionSchema):
    enabled: Toggle = Toggle("form_services_enabled")


@dataclass(frozen=True)
class ListSwitchSchema:
    """Chats, clips, articles, moments and products switch in the list — no modal, no save."""
    test_id: str

    def __call__(self, settings: SectionSettings, driver: WebDriver, wait: WebDriverWait) -> None:
        item = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, f'[data-testid="{self.test_id}"]')))

        if _switch_state(item) != settings.enabled:
            driver.execute_script("arguments[0].click()", item)
            _wait_for_state(driver, self.test_id, settings.enabled)
            time.sleep(1.0)
