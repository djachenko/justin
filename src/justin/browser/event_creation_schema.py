import re
from dataclasses import dataclass, fields
from datetime import datetime
from typing import ClassVar

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_creation_settings import Category, EventCreationSettings, EventStep1Settings, EventStep2Settings
from justin.browser.pacing import pause
from justin.browser.waiting import wait_or_explore


@dataclass(frozen=True)
class TitleInput:
    test_id: str

    def set_value(self, value: str, driver: WebDriver, wait: WebDriverWait) -> None:
        el = wait_or_explore(driver, wait, EC.element_to_be_clickable(
            (By.CSS_SELECTOR, f'[data-testid="{self.test_id}"]')))
        ActionChains(driver).click(el).send_keys(value).perform()
        pause(0.5)


@dataclass(frozen=True)
class AccessSelect:
    def set_value(self, value: bool, driver: WebDriver, wait: WebDriverWait) -> None:
        if not value:
            return
        select_el = driver.find_element(By.CSS_SELECTOR, '[name="access"]')
        driver.execute_script("arguments[0].click()", select_el)
        pause(0.5)
        closed_option = driver.find_element(By.CSS_SELECTOR, '[role="option"][value="1"]')
        driver.execute_script("arguments[0].click()", closed_option)
        pause(0.5)


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
            spinbuttons = driver.find_elements(By.CSS_SELECTOR, f'[aria-label="{aria_label}"]')
            spinbutton = spinbuttons[self.n]
            driver.execute_script("arguments[0].focus()", spinbutton)
            spinbutton.send_keys(val)


@dataclass(frozen=True)
class OptionalDateSpinGroup:
    def set_value(self, value: datetime | None, driver: WebDriver, wait: WebDriverWait) -> None:
        if value is None:
            return
        end_date_btn = wait_or_explore(driver, wait, EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Enter end date')]")
        ))
        driver.execute_script("arguments[0].click()", end_date_btn)
        pause(0.5)
        DateSpinGroup(n=1).set_value(value, driver, wait)


@dataclass(frozen=True)
class OrganizerSelect:
    name: str = "eventGroupId"

    def set_value(self, value: int | None, driver: WebDriver, wait: WebDriverWait) -> None:
        if value is None:
            return
        driver.execute_script("""
            var select = document.querySelector('[name="' + arguments[0] + '"]');
            var setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
            setter.call(select, arguments[1]);
            select.dispatchEvent(new Event('change', {bubbles: true}));
        """, self.name, str(abs(value)))


@dataclass(frozen=True)
class CategorySelect:
    def set_value(self, value: Category, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait_or_explore(driver, wait, EC.element_to_be_clickable(
            (By.CSS_SELECTOR, f'[data-testid="wizard_theme_subcathegory"][data-name="{value.value}"]')
        ))
        driver.execute_script("arguments[0].click()", btn)
        pause(0.5)


@dataclass(frozen=True)
class EventStep1Schema:
    title: TitleInput = TitleInput("title_input")
    is_closed: AccessSelect = AccessSelect()
    start_dt: DateSpinGroup = DateSpinGroup(n=0)
    end_dt: OptionalDateSpinGroup = OptionalDateSpinGroup()
    organiser_id: OrganizerSelect = OrganizerSelect()

    def fill(self, settings: EventStep1Settings, driver: WebDriver, wait: WebDriverWait) -> None:
        for f in fields(self):
            getattr(self, f.name).set_value(getattr(settings, f.name), driver, wait)

            pause(0.3)

    def submit(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait_or_explore(driver, wait, EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="done_button"]')))
        btn.click()

        pause(0.5)


@dataclass(frozen=True)
class EventStep2Schema:
    category: CategorySelect = CategorySelect()

    def fill(self, settings: EventStep2Settings, driver: WebDriver, wait: WebDriverWait) -> None:
        for f in fields(self):
            getattr(self, f.name).set_value(getattr(settings, f.name), driver, wait)
            pause(0.3)

    def submit(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait_or_explore(driver, wait, EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Create event' and not(@disabled)]")
        ))
        driver.execute_script("arguments[0].click()", btn)
        pause(0.5)


_EVENT_URL = r'(?:event|club)(\d+)'
_CREATION_URL_TAIL = "/groups_create"


def _wait_for_captcha_if_needed(driver: WebDriver) -> None:
    """VK answers event creation with a captcha now and then — only a human gets past it."""
    pause(2.0, jitter=0)

    if driver.current_url.rstrip("/").endswith(_CREATION_URL_TAIL):
        input("Капча! Реши её в браузере и нажми Enter здесь, когда готово: ")


@dataclass(frozen=True)
class EventStep3Schema:
    def submit(self, driver: WebDriver, wait: WebDriverWait) -> None:
        btn = wait_or_explore(driver, wait, EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="go_to_community"]')))
        driver.execute_script("arguments[0].click()", btn)
        driver.switch_to.default_content()

        _wait_for_captcha_if_needed(driver)

    def event_id(self, driver: WebDriver, wait: WebDriverWait) -> int:
        wait_or_explore(driver, wait, lambda d: re.search(_EVENT_URL, d.current_url))

        return self._parse_event_id(driver.current_url)

    @staticmethod
    def _parse_event_id(url: str) -> int:
        match = re.search(_EVENT_URL, url)

        if not match:
            raise ValueError(f"Could not parse event ID from URL: {url}")

        return int(match.group(1))


@dataclass(frozen=True)
class EventCreationSchema:
    _URL: ClassVar[str] = "https://vk.com/groups/my_events?w=groups_create_new_event"
    _IFRAME_CSS: ClassVar[str] = "#react_rootcommunity_create iframe"

    step1: EventStep1Schema = EventStep1Schema()
    step2: EventStep2Schema = EventStep2Schema()
    step3: EventStep3Schema = EventStep3Schema()

    def __call__(self, settings: EventCreationSettings, driver: WebDriver, wait: WebDriverWait) -> int:
        driver.get(self._URL)

        iframe = wait_or_explore(driver, wait, EC.presence_of_element_located(
            (By.CSS_SELECTOR, self._IFRAME_CSS)))
        driver.switch_to.frame(iframe)

        self.step1.fill(settings.step1, driver, wait)
        self.step1.submit(driver, wait)

        self.step2.fill(settings.step2, driver, wait)
        self.step2.submit(driver, wait)

        self.step3.submit(driver, wait)

        return self.step3.event_id(driver, wait)
