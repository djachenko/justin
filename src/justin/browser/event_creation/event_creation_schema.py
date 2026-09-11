from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, ClassVar
from urllib.parse import urlparse

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_creation.event_creation_settings import Category, EventCreationSettings, \
    EventStep1Settings, EventStep2Settings
from justin.browser.shared.captcha import wait_for_captcha_if_needed
from justin.browser.shared.elements import by_css, by_testid, by_xpath
from justin.browser.shared.pacing import AFTER_ACTION, BETWEEN_FIELDS, pause
from justin.browser.shared.react_select import set_react_select
from justin.browser.shared.waiting import wait_for


@dataclass(frozen=True)
class TitleInput:
    test_id: str

    def set_value(self, value: str, driver: WebDriver, wait: WebDriverWait) -> None:
        el = wait_for(driver, wait, EC.element_to_be_clickable(by_testid(self.test_id)))

        ActionChains(driver) \
            .click(el) \
            .send_keys(value) \
            .perform()

        pause(AFTER_ACTION)


@dataclass(frozen=True)
class AccessSelect:
    def set_value(self, value: bool, driver: WebDriver, wait: WebDriverWait) -> None:
        if not value:
            return

        select_el = driver.find_element(*by_css('[name="access"]'))
        driver.execute_script("arguments[0].click()", select_el)

        pause(AFTER_ACTION)

        closed_option = driver.find_element(*by_css('[role="option"][value="1"]'))
        driver.execute_script("arguments[0].click()", closed_option)

        pause(AFTER_ACTION)


@dataclass(frozen=True)
class DateSpinGroup:
    n: int = 0

    def set_value(self, value: datetime, driver: WebDriver, wait: WebDriverWait) -> None:
        parts = [
            ("День", str(value.day).zfill(2)),
            ("Месяц", str(value.month).zfill(2)),
            ("Год", str(value.year)),
            ("Час", str(value.hour).zfill(2)),
            ("Минута", str(value.minute).zfill(2)),
        ]

        for aria_label, val in parts:
            spinbuttons = driver.find_elements(*by_css(f'[aria-label="{aria_label}"]'))

            spinbutton = spinbuttons[self.n]
            driver.execute_script("arguments[0].focus()", spinbutton)
            spinbutton.send_keys(val)


@dataclass(frozen=True)
class OptionalDateSpinGroup:
    def set_value(self, value: datetime | None, driver: WebDriver, wait: WebDriverWait) -> None:
        if value is None:
            return

        end_date_btn = wait_for(
            driver,
            wait,
            EC.presence_of_element_located(by_xpath("//*[contains(text(), 'Enter end date')]"))
        )

        driver.execute_script("arguments[0].click()", end_date_btn)

        pause(AFTER_ACTION)

        DateSpinGroup(n=1).set_value(value, driver, wait)


@dataclass(frozen=True)
class OrganizerSelect:
    name: str = "eventGroupId"

    def set_value(self, value: int | None, driver: WebDriver, wait: WebDriverWait) -> None:
        if value is None:
            return

        set_react_select(driver, self.name, str(abs(value)))


@dataclass(frozen=True)
class CategorySelect:
    def set_value(self, value: Category, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait_for(
            driver,
            wait,
            EC.element_to_be_clickable(
                by_css(f'[data-testid="wizard_theme_subcathegory"][data-name="{value.value}"]')
            )
        )

        driver.execute_script("arguments[0].click()", btn)

        pause(AFTER_ACTION)


@dataclass(frozen=True)
class WizardStep[S](ABC):
    """Шаг визарда: поля-контролы заполняются из одноимённых полей настроек, потом «дальше»."""

    def fill(self, settings: S, driver: WebDriver, wait: WebDriverWait) -> None:
        for f in fields(self):
            element = getattr(self, f.name)
            value = getattr(settings, f.name)

            element.set_value(value, driver, wait)

            pause(BETWEEN_FIELDS)

    @abstractmethod
    def submit(self, driver: WebDriver, wait: WebDriverWait) -> None: ...


@dataclass(frozen=True)
class EventStep1Schema(WizardStep[EventStep1Settings]):
    title: TitleInput = TitleInput("title_input")
    is_closed: AccessSelect = AccessSelect()
    start_dt: DateSpinGroup = DateSpinGroup(n=0)
    end_dt: OptionalDateSpinGroup = OptionalDateSpinGroup()
    organiser_id: OrganizerSelect = OrganizerSelect()

    def submit(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait_for(driver, wait, EC.element_to_be_clickable(by_testid("done_button")))

        btn.click()

        pause(AFTER_ACTION)


@dataclass(frozen=True)
class EventStep2Schema(WizardStep[EventStep2Settings]):
    category: CategorySelect = CategorySelect()

    def submit(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait_for(
            driver,
            wait,
            EC.element_to_be_clickable(
                by_xpath("//button[normalize-space()='Create event' and not(@disabled)]")
            )
        )

        driver.execute_script("arguments[0].click()", btn)

        pause(AFTER_ACTION)


_CREATION_URL_TAIL = "/groups_create"
_EVENT_PREFIXES = ("event", "club")


def _event_id_in(url: str) -> int | None:
    """Адрес созданного события кончается на event<id> либо club<id>."""
    tail = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]

    for prefix in _EVENT_PREFIXES:
        digits = tail.removeprefix(prefix)

        if digits != tail and digits.isdigit():
            return int(digits)

    return None


@dataclass(frozen=True)
class EventStep3Schema:
    def submit(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait_for(driver, wait, EC.element_to_be_clickable(by_testid("go_to_community")))

        driver.execute_script("arguments[0].click()", btn)
        driver.switch_to.default_content()

        wait_for_captcha_if_needed(driver, _CREATION_URL_TAIL)

    def event_id(self, driver: WebDriver, wait: WebDriverWait) -> int:
        wait_for(driver, wait, lambda d: _event_id_in(d.current_url) is not None)

        return self._parse_event_id(driver.current_url)

    @staticmethod
    def _parse_event_id(url: str) -> int:
        event_id = _event_id_in(url)

        if event_id is None:
            raise ValueError(f"Could not parse event ID from URL: {url}")

        return event_id


@dataclass(frozen=True)
class EventCreationSchema:
    _URL: ClassVar[str] = "https://vk.com/groups/my_events?w=groups_create_new_event"
    _IFRAME_CSS: ClassVar[str] = "#react_rootcommunity_create iframe"

    step1: EventStep1Schema = EventStep1Schema()
    step2: EventStep2Schema = EventStep2Schema()
    step3: EventStep3Schema = EventStep3Schema()

    def __call__(self, settings: EventCreationSettings, driver: WebDriver, wait: WebDriverWait) -> int:
        driver.get(self._URL)

        iframe = wait_for(driver, wait, EC.presence_of_element_located(by_css(self._IFRAME_CSS)))

        driver.switch_to.frame(iframe)

        steps: tuple[WizardStep[Any], ...] = (self.step1, self.step2)
        step_settings: tuple[Any, ...] = (settings.step1, settings.step2)

        for step, its_settings in zip(steps, step_settings, strict=True):
            step.fill(its_settings, driver, wait)
            step.submit(driver, wait)

        self.step3.submit(driver, wait)

        return self.step3.event_id(driver, wait)
