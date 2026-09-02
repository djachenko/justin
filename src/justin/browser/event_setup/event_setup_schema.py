"""Schema for editing an existing VK event via ?act=edit."""
import re
import time
from dataclasses import dataclass
from datetime import datetime

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_creation.event_creation_settings import Category
from justin.browser.event_setup.event_setup_settings import EventSetupSettings
from justin.browser.shared.save_button import find_save_buttons


def _value_of(element) -> str:
    """Selenium отдаёт None, когда атрибута нет.

    Для нас это такая же непринятая настройка, как и неверное значение, — иначе
    вместо «дата не применилась» получим TypeError из середины сравнения.
    """
    value = element.get_attribute("value")

    if value is None:
        raise ValueError(f"Field {element.get_attribute('id')!r} has no value attribute")

    return value


def _clear_and_type(driver: WebDriver, el, value: str) -> None:
    driver.execute_script("arguments[0].value = ''", el)
    el.send_keys(value)
    time.sleep(0.3)


_MAX_YEAR_STEPS = 20

_SUBJECT = 0
_CITY = 6
_EVENT_HOST = "input[name='event_host'], input[id='event_host']"
_ACCESS = "#groups_edit_g_access"
_ACCESS_VALUE = "input[name='groups_edit_g_access']"
_OPEN = 0
_CLOSED = 1


def _pick_date(driver: WebDriver, wait: WebDriverWait, date_el, dt: datetime) -> None:
    """The date field is readonly — the value can only be set through the datepicker."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", date_el)
    time.sleep(0.3)
    date_el.click()

    calendar = date_el.find_element(
        By.XPATH, "ancestor::*[contains(@class, 'datepicker_container')][1]")
    wait.until(lambda _: calendar.find_elements(By.CSS_SELECTOR, "td.day"))

    _pick_year_and_month(driver, wait, calendar, dt)

    days = [el for el in _visible_cells(calendar)
            if "prev_month_day" not in el.get_attribute("class")
            and "next_month_day" not in el.get_attribute("class")
            and el.text.strip() == str(dt.day)]

    if not days:
        raise NoSuchElementException(f"Day {dt.day} not found in datepicker")

    days[0].click()
    time.sleep(0.5)


def _pick_year_and_month(driver: WebDriver, wait: WebDriverWait, calendar, dt: datetime) -> None:
    """Month names are localised — the year is read as a number, the month picked by position."""
    calendar.find_element(By.CSS_SELECTOR, "a.cal_month_sel").click()
    wait.until(lambda _: len(_visible_cells(calendar)) == 12)

    for _ in range(_MAX_YEAR_STEPS):
        years = [re.search(r"\d{4}", el.text) for el in
                 calendar.find_elements(By.CSS_SELECTOR, "td.month") if el.is_displayed()]
        shown = next((match for match in years if match), None)

        if shown is None:
            raise NoSuchElementException("Datepicker header has no year")

        shown_year = int(shown.group())

        if shown_year == dt.year:
            break

        _click_arrow(calendar, "left" if dt.year < shown_year else "right")
        time.sleep(0.4)
    else:
        raise NoSuchElementException(f"Year {dt.year} not reachable in datepicker")

    _visible_cells(calendar)[dt.month - 1].click()
    wait.until(lambda _: len(_visible_cells(calendar)) > 12)


def _click_arrow(calendar, direction: str) -> None:
    """Day and month modes each carry their own arrows — the hidden ones have no click area."""
    arrows = [el for el in calendar.find_elements(By.CSS_SELECTOR, f"a.arr.{direction}")
              if el.is_displayed()]

    if not arrows:
        raise NoSuchElementException(f"No {direction} arrow in datepicker")

    arrows[0].click()


def _visible_cells(calendar) -> list:
    """Months and days share the td.day class — only one set is visible at a time."""
    return [el for el in calendar.find_elements(By.CSS_SELECTOR, "td.day") if el.is_displayed()]


def _pick_from_selector(driver: WebDriver, wait: WebDriverWait, selector_input, value: int) -> None:
    """Hours and minutes are readonly VK selectors — the value is picked from a dropdown."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", selector_input)
    time.sleep(0.3)
    selector_input.click()

    def option(_):
        items = [el for el in driver.find_elements(By.CSS_SELECTOR, "[class*='dropdown'] li")
                 if el.is_displayed() and el.text.strip().isdigit()
                 and int(el.text.strip()) == value]

        return items[0] if items else None

    wait.until(option).click()
    time.sleep(0.3)


def _fill_date_field(driver: WebDriver, wait: WebDriverWait, date_input_id: str,
                     dt: datetime) -> None:
    """Fill VK date picker + the hour/minute selectors that follow it.

    date_input_id: 'group_start_date_date_input' or 'group_finish_date_date_input'
    """
    date_el = driver.find_element(By.CSS_SELECTOR, f"[id='{date_input_id}']")

    _pick_date(driver, wait, date_el, dt)

    shown = _value_of(date_el)

    if str(dt.day) not in shown or str(dt.year) not in shown:
        raise ValueError(f"Date not applied: field shows {shown!r}, expected {dt.date()}")

    hour, minute = (
        date_el.find_element(By.XPATH, f"following::input[contains(@class, 'selector_input')][{i}]")
        for i in (1, 2)
    )

    _pick_from_selector(driver, wait, hour, dt.hour)
    _pick_from_selector(driver, wait, minute, dt.minute)

    got = (int(_value_of(hour)), int(_value_of(minute)))

    if got != (dt.hour, dt.minute):
        raise ValueError(f"Time not applied: fields show {got}, expected {dt:%H:%M}")


def _visible_selectors(driver: WebDriver) -> list:
    """Subject, organiser, hours, minutes and city all render as the same selector widget."""
    return [el for el in driver.find_elements(By.CSS_SELECTOR, ".selector_input") if el.is_displayed()]


def _pick_from_result_list(driver: WebDriver, wait: WebDriverWait, field, label: str) -> None:
    """The selector opens a result_list — options carry no ids, only their labels."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", field)
    time.sleep(0.3)
    field.click()

    def option(_):
        items = [el for el in driver.find_elements(By.CSS_SELECTOR, ".result_list li")
                 if el.is_displayed() and el.text.strip() == label]

        return items[0] if items else None

    wait.until(option).click()
    time.sleep(0.5)

    shown = _value_of(field)

    if shown != label:
        raise ValueError(f"Selector not applied: field shows {shown!r}, expected {label!r}")


def _set_category(driver: WebDriver, wait: WebDriverWait, category: Category) -> None:
    _pick_from_result_list(driver, wait, _visible_selectors(driver)[_SUBJECT], category.value)


def _set_access(driver: WebDriver, wait: WebDriverWait, is_closed: bool) -> None:
    """Access comes from the dropdown widget, not from the hidden field it keeps in sync.

    Writing the hidden input alone is silently dropped on save. Options are localised,
    so the one to pick is chosen by position: 0 open, 1 closed.
    """
    expected = _CLOSED if is_closed else _OPEN

    wrap = driver.find_element(By.CSS_SELECTOR, _ACCESS)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", wrap)
    time.sleep(0.3)
    wrap.click()

    def items(_):
        found = [el for el in driver.find_elements(By.CSS_SELECTOR, f"{_ACCESS} .idd_item")
                 if el.is_displayed()]

        return found if len(found) > expected else None

    wait.until(items)[expected].click()
    time.sleep(0.5)

    shown = _value_of(driver.find_element(By.CSS_SELECTOR, _ACCESS_VALUE))

    if int(shown) != expected:
        raise ValueError(f"Access not applied: widget holds {shown!r}, expected {expected}")


def _set_hidden(driver: WebDriver, selector: str, value: str) -> None:
    field = driver.find_element(By.CSS_SELECTOR, selector)
    driver.execute_script("arguments[0].value = arguments[1]", field, value)

    shown = _value_of(field)

    if shown != value:
        raise ValueError(f"Field {selector!r} holds {shown!r}, expected {value!r}")


def _set_organiser(driver: WebDriver, organiser_id: int) -> None:
    """The option list carries names only — the id lives in the hidden event_host field."""
    _set_hidden(driver, _EVENT_HOST, str(organiser_id))


@dataclass(frozen=True)
class EventSetupSchema:
    _SETTINGS_URL_TMPL: str = "https://vk.com/event{event_id}?act=edit"

    def __call__(self, event_id: int, settings: EventSetupSettings,
                 driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(self._SETTINGS_URL_TMPL.format(event_id=event_id))
        self._wait_for_form(driver, wait)

        if settings.title is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='group_edit_name']")
            _clear_and_type(driver, el, settings.title)

        if settings.description is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='group_edit_desc']")
            _clear_and_type(driver, el, settings.description)

        if settings.category is not None:
            _set_category(driver, wait, settings.category)

        if settings.organiser_id is not None:
            _set_organiser(driver, settings.organiser_id)

        if settings.is_closed is not None:
            _set_access(driver, wait, settings.is_closed)

        if settings.website is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='group_website']")
            _clear_and_type(driver, el, settings.website)

        if settings.phone is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='group_edit_phone']")
            _clear_and_type(driver, el, settings.phone)

        if settings.email is not None:
            el = driver.find_element(By.CSS_SELECTOR, "[id='event_mail']")
            _clear_and_type(driver, el, settings.email)

        if settings.city is not None:
            self._set_city(driver, wait, settings.city)

        if settings.start_dt is not None:
            _fill_date_field(driver, wait, "group_start_date_date_input", settings.start_dt)

        if settings.end_dt is not None:
            _fill_date_field(driver, wait, "group_finish_date_date_input", settings.end_dt)

        self._save(driver, wait)

    @staticmethod
    def _wait_for_form(driver: WebDriver, wait: WebDriverWait) -> None:
        from selenium.common.exceptions import StaleElementReferenceException

        def content_ready(d) -> bool:
            try:
                skeletons = d.find_elements(By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
                if not any(el.is_displayed() for el in skeletons):
                    return True
                rm = d.find_elements(By.CSS_SELECTOR, "[data-testid='rightmenu']")
                return bool(rm and rm[0].is_displayed())
            except StaleElementReferenceException:
                return False

        wait.until(content_ready)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.0)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(0.3)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[id='group_edit_name']")))

    @staticmethod
    def _set_city(driver: WebDriver, wait: WebDriverWait, city: str) -> None:
        """The city is a selector like the category, not a text field: typing into it leaves
        the hidden id untouched, so the value has to be picked from the result list."""
        selectors = _visible_selectors(driver)

        if len(selectors) <= _CITY:
            raise NoSuchElementException(
                f"City selector not found: page has {len(selectors)} selectors")

        _pick_from_result_list(driver, wait, selectors[_CITY], city)

    @staticmethod
    def _save(driver: WebDriver, wait: WebDriverWait) -> None:
        save_btn = wait.until(lambda d: next(iter(find_save_buttons(d)), None))
        driver.execute_script("arguments[0].click()", save_btn)
        time.sleep(1.0)
