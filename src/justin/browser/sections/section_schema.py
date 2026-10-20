from dataclasses import dataclass, fields
from enum import Enum

from justin_utils.util import first
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException, TimeoutException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.sections.section_settings import (
    AddAllowed, PostsPublishing, SectionSettings,
)
from justin.browser.shared.elements import by_css, by_testid, by_xpath, found, present
from justin.browser.shared.field import Field
from justin.browser.shared.pacing import AFTER_ACTION, BETWEEN_FIELDS, pause
from justin.browser.shared.waiting import Wait

_SWITCH = by_css("[role='switch']")
_STATE_TIMEOUT = 5


def _find(driver: WebDriver, test_id: str) -> WebElement:
    return driver.find_element(*by_testid(test_id))


def _switch_state(element: WebElement) -> bool:
    """Some testids sit on the switch itself, others on the cell that wraps it.

    An element with no state at all is not a switch we know how to read: reporting it as
    enabled would turn "enable this" into a silent no-op, so it raises instead.
    """
    state = element.get_attribute("aria-checked")

    if state is None:
        switches = element.find_elements(*_SWITCH)

        if switches:
            state = switches[0].get_attribute("aria-checked")

    if state not in ("true", "false"):
        raise NoSuchElementException(
            f"No switch state on {element.get_attribute('data-testid')!r}, got {state!r}")

    return (state == "true")


def _wait_for_state(driver: WebDriver, test_id: str, expected: bool) -> None:
    """A JS click that never landed looks exactly like one that did — check the switch moved.

    The element is looked up again on every poll: the list re-renders around a switch,
    so any reference held across the click goes stale.
    """
    def applied(_: WebDriver) -> bool:
        try:
            return _switch_state(_find(driver, test_id)) == expected
        except StaleElementReferenceException:
            return False

    try:
        Wait(driver, _STATE_TIMEOUT).until(applied)
    except TimeoutException:
        raise ValueError(f"Switch {test_id!r} stayed {not expected}, expected {expected}")


@dataclass(frozen=True)
class Toggle(Field[bool]):
    test_id: str

    def set_value(self, value: bool, driver: WebDriver, wait: WebDriverWait) -> None:
        el = _find(driver, self.test_id)
        currently_enabled = _switch_state(el)

        if currently_enabled == value:
            return

        driver.execute_script("arguments[0].click()", el)

        _wait_for_state(driver, self.test_id, value)

        pause(AFTER_ACTION)


@dataclass(frozen=True)
class Radio[E: Enum](Field[E]):
    def set_value(self, value: E, driver: WebDriver, wait: WebDriverWait) -> None:
        """The enum value is the testid of the radio button."""
        el = _find(driver, value.value)

        driver.execute_script("arguments[0].click()", el)

        pause(BETWEEN_FIELDS)


@dataclass(frozen=True)
class Dropdown[E: Enum](Field[E]):
    ITEM = by_testid("dropdownactionsheet-item")

    test_id: str

    def set_value(self, value: E, driver: WebDriver, wait: WebDriverWait) -> None:
        trigger = _find(driver, self.test_id)

        driver.execute_script("arguments[0].click()", trigger)

        pause(AFTER_ACTION)

        option_text = value.value
        option = found(
            wait,
            lambda d: first(d.find_elements(*self.ITEM),
                            key=lambda el: el.is_displayed() and option_text in el.text)
        )

        driver.execute_script("arguments[0].click()", option)

        pause(BETWEEN_FIELDS)


@dataclass(frozen=True)
class SectionSchema:
    class Modal:
        """A section opens its own modal: switches inside, an explicit Save at the bottom."""
        SETTLE = 1.5  # the modal closes with an animation, the list below repaints
        SAVE = by_testid("form_modal_save")
        TITLE = by_xpath(".//span[normalize-space()]")

    test_id: str
    enabled: Toggle

    def __call__(self, settings: SectionSettings, driver: WebDriver, wait: WebDriverWait) -> None:
        self._open(driver, wait)

        self.enabled.set_value(settings.enabled, driver, wait)

        if settings.enabled:
            for f in fields(settings):
                if f.name == "enabled":
                    continue

                element = getattr(self, f.name)
                value = getattr(settings, f.name)

                element.set_value(value, driver, wait)

        self._save(driver, wait)

        pause(self.Modal.SETTLE)

    def _open(self, driver: WebDriver, wait: WebDriverWait) -> None:
        """The modal opens from the section title.

        On Content tabs the cell is a <label> around the switch: a click on the cell itself
        flips the switch instead.
        """
        item = present(wait, by_testid(self.test_id))

        driver.execute_script("arguments[0].click()", item.find_element(*self.Modal.TITLE))

        present(wait, by_testid(self.enabled.test_id))

        pause(AFTER_ACTION)

    def _save(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = present(wait, self.Modal.SAVE)

        driver.execute_script("arguments[0].click()", btn)

        pause(AFTER_ACTION)


@dataclass(frozen=True)
class PostsSchema(SectionSchema):
    enabled: Toggle = Toggle("form_wall_enabled")
    publishing: Dropdown[PostsPublishing] = Dropdown("form_wall_publishing_allowed")
    sharing_disabled: Toggle = Toggle("form_wall_sharing_disabled")


@dataclass(frozen=True)
class PhotosSchema(SectionSchema):
    enabled: Toggle = Toggle("form_photos_toggle")
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class VideosSchema(SectionSchema):
    enabled: Toggle = Toggle("form_videos_toggle")
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class TopicsSchema(SectionSchema):
    enabled: Toggle = Toggle("form_discussions_toggle")
    add_allowed: Radio[AddAllowed] = Radio()


@dataclass(frozen=True)
class MusicSchema(SectionSchema):
    enabled: Toggle = Toggle("form_audios_toggle")
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
    """Products and clips on Content tabs; chats, articles and moments on Sections.

    They switch right in the list — no modal, no save.
    """
    test_id: str

    def __call__(self, settings: SectionSettings, driver: WebDriver, wait: WebDriverWait) -> None:
        item = present(wait, by_testid(self.test_id))

        if _switch_state(item) == settings.enabled:
            return

        driver.execute_script("arguments[0].click()", item)

        _wait_for_state(driver, self.test_id, settings.enabled)

        pause(SectionSchema.Modal.SETTLE)
