"""Schema for editing an existing VK event via ?act=edit."""
import re
from dataclasses import dataclass
from datetime import datetime

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_creation.event_creation_settings import Category
from justin.browser.event_setup.event_setup_settings import EventSetupSettings
from justin.browser.shared.elements import by_css, by_testid, by_xpath, found, present
from justin.browser.shared.pacing import AFTER_ACTION, AFTER_SCROLL, pause
from justin.browser.shared.page import content_rendered
from justin.browser.shared.save_button import click_save


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

    pause(AFTER_ACTION)


_MAX_YEAR_STEPS = 20

_LAZY_BLOCKS = 1.0  # ленивые блоки страницы догружаются после прокрутки донизу

_SUBJECT = 0
_CITY = 6
_EVENT_HOST = by_css("input[name='event_host'], input[id='event_host']")
_ACCESS = "#groups_edit_g_access"
_ACCESS_ITEMS = by_css(f"{_ACCESS} .idd_item")
_ACCESS_VALUE = by_css("input[name='groups_edit_g_access']")
_OPEN = 0
_CLOSED = 1

_NAME = by_css("[id='group_edit_name']")
_RIGHT_MENU = by_testid("rightmenu")
_DAY = by_css("td.day")
_MONTH = by_css("td.month")
_MONTH_MODE = by_css("a.cal_month_sel")
_SELECTOR_INPUT = by_css(".selector_input")
_RESULT_ITEM = by_css(".result_list li")
_DROPDOWN_ITEM = by_css("[class*='dropdown'] li")
_CALENDAR = by_xpath("ancestor::*[contains(@class, 'datepicker_container')][1]")


def _visible_cells(calendar) -> list:
    """Months and days share the td.day class — only one set is visible at a time."""
    return [el for el in calendar.find_elements(*_DAY) if el.is_displayed()]


def _click_arrow(calendar, direction: str) -> None:
    """Day and month modes each carry their own arrows — the hidden ones have no click area."""
    arrows = [el for el in calendar.find_elements(*by_css(f"a.arr.{direction}"))
              if el.is_displayed()]

    if not arrows:
        raise NoSuchElementException(f"No {direction} arrow in datepicker")

    arrows[0].click()


def _pick_year_and_month(driver: WebDriver, wait: WebDriverWait, calendar, dt: datetime) -> None:
    """Month names are localised — the year is read as a number, the month picked by position."""
    calendar.find_element(*_MONTH_MODE).click()
    wait.until(lambda _: len(_visible_cells(calendar)) == 12)

    for _ in range(_MAX_YEAR_STEPS):
        years = [re.search(r"\d{4}", el.text) for el in
                 calendar.find_elements(*_MONTH) if el.is_displayed()]
        shown = next((match for match in years if match), None)

        if shown is None:
            raise NoSuchElementException("Datepicker header has no year")

        shown_year = int(shown.group())

        if shown_year == dt.year:
            break

        if dt.year < shown_year:
            _click_arrow(calendar, "left")
        else:
            _click_arrow(calendar, "right")

        pause(AFTER_ACTION)
    else:
        raise NoSuchElementException(f"Year {dt.year} not reachable in datepicker")

    _visible_cells(calendar)[dt.month - 1].click()
    wait.until(lambda _: len(_visible_cells(calendar)) > 12)


def _pick_date(driver: WebDriver, wait: WebDriverWait, date_el, dt: datetime) -> None:
    """The date field is readonly — the value can only be set through the datepicker."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", date_el)

    pause(AFTER_SCROLL)

    date_el.click()

    calendar = date_el.find_element(*_CALENDAR)

    wait.until(lambda _: calendar.find_elements(*_DAY))

    _pick_year_and_month(driver, wait, calendar, dt)

    days = [el for el in _visible_cells(calendar)
            if "prev_month_day" not in el.get_attribute("class")
            and "next_month_day" not in el.get_attribute("class")
            and el.text.strip() == str(dt.day)]

    if not days:
        raise NoSuchElementException(f"Day {dt.day} not found in datepicker")

    days[0].click()

    pause(AFTER_ACTION)


def _pick_from_selector(driver: WebDriver, wait: WebDriverWait, selector_input, value: int) -> None:
    """Hours and minutes are readonly VK selectors — the value is picked from a dropdown."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", selector_input)

    pause(AFTER_SCROLL)

    selector_input.click()

    def option(_) -> WebElement | None:
        items = [el for el in driver.find_elements(*_DROPDOWN_ITEM)
                 if el.is_displayed() and el.text.strip().isdigit()
                 and int(el.text.strip()) == value]

        if not items:
            return None

        return items[0]

    found(wait, option).click()

    pause(AFTER_ACTION)


def _fill_date_field(driver: WebDriver, wait: WebDriverWait, date_input_id: str,
                     dt: datetime) -> None:
    """Fill VK date picker + the hour/minute selectors that follow it.

    date_input_id: 'group_start_date_date_input' or 'group_finish_date_date_input'
    """
    date_el = driver.find_element(*by_css(f"[id='{date_input_id}']"))

    _pick_date(driver, wait, date_el, dt)

    shown = _value_of(date_el)

    if str(dt.day) not in shown or str(dt.year) not in shown:
        raise ValueError(f"Date not applied: field shows {shown!r}, expected {dt.date()}")

    hour, minute = (
        date_el.find_element(*by_xpath(f"following::input[contains(@class, 'selector_input')][{i}]"))
        for i in (1, 2)
    )

    _pick_from_selector(driver, wait, hour, dt.hour)
    _pick_from_selector(driver, wait, minute, dt.minute)

    got = (int(_value_of(hour)), int(_value_of(minute)))

    if got != (dt.hour, dt.minute):
        raise ValueError(f"Time not applied: fields show {got}, expected {dt:%H:%M}")


def _visible_selectors(driver: WebDriver) -> list:
    """Subject, organiser, hours, minutes and city all render as the same selector widget."""
    return [el for el in driver.find_elements(*_SELECTOR_INPUT) if el.is_displayed()]


def _pick_from_result_list(driver: WebDriver, wait: WebDriverWait, field, label: str) -> None:
    """The selector opens a result_list — options carry no ids, only their labels."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", field)

    pause(AFTER_SCROLL)

    field.click()

    def option(_) -> WebElement | None:
        items = [el for el in driver.find_elements(*_RESULT_ITEM)
                 if el.is_displayed() and el.text.strip() == label]

        if not items:
            return None

        return items[0]

    found(wait, option).click()

    pause(AFTER_ACTION)

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
    if is_closed:
        expected = _CLOSED
    else:
        expected = _OPEN

    wrap = driver.find_element(*by_css(_ACCESS))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", wrap)

    pause(AFTER_SCROLL)

    wrap.click()

    def items(_) -> list[WebElement] | None:
        visible = [el for el in driver.find_elements(*_ACCESS_ITEMS) if el.is_displayed()]

        if len(visible) <= expected:
            return None

        return visible

    found(wait, items)[expected].click()

    pause(AFTER_ACTION)

    shown = _value_of(driver.find_element(*_ACCESS_VALUE))

    if int(shown) != expected:
        raise ValueError(f"Access not applied: widget holds {shown!r}, expected {expected}")


def _set_hidden(driver: WebDriver, locator: tuple[str, str], value: str) -> None:
    field = driver.find_element(*locator)
    driver.execute_script("arguments[0].value = arguments[1]", field, value)

    shown = _value_of(field)

    if shown != value:
        raise ValueError(f"Field {locator[1]!r} holds {shown!r}, expected {value!r}")


def _set_organiser(driver: WebDriver, organiser_id: int) -> None:
    """The option list carries names only — the id lives in the hidden event_host field."""
    _set_hidden(driver, _EVENT_HOST, str(organiser_id))


def _form_ready(driver: WebDriver) -> bool:
    """Форма legacy-страницы либо уже без скелетонов, либо хотя бы с правым меню."""
    if content_rendered(driver):
        return True

    try:
        menu = driver.find_elements(*_RIGHT_MENU)

        return bool(menu and menu[0].is_displayed())
    except StaleElementReferenceException:
        return False


def _wait_for_form(driver: WebDriver, wait: WebDriverWait) -> None:
    wait.until(_form_ready)

    # Прокрутка донизу и обратно будит ленивые блоки — без неё часть полей не отрисована.
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

    pause(_LAZY_BLOCKS)

    driver.execute_script("window.scrollTo(0, 0)")

    pause(AFTER_SCROLL)

    present(wait, _NAME)


def _set_city(driver: WebDriver, wait: WebDriverWait, city: str) -> None:
    """The city is a selector like the category, not a text field: typing into it leaves
    the hidden id untouched, so the value has to be picked from the result list."""
    selectors = _visible_selectors(driver)

    if len(selectors) <= _CITY:
        raise NoSuchElementException(
            f"City selector not found: page has {len(selectors)} selectors")

    _pick_from_result_list(driver, wait, selectors[_CITY], city)


@dataclass(frozen=True)
class EventSetupSchema:
    _SETTINGS_URL_TMPL: str = "https://vk.com/event{event_id}?act=edit"

    def __call__(self, event_id: int, settings: EventSetupSettings,
                 driver: WebDriver, wait: WebDriverWait) -> None:
        driver.get(self._SETTINGS_URL_TMPL.format(event_id=event_id))

        _wait_for_form(driver, wait)

        for field_id, value in [
            ("group_edit_name", settings.title),
            ("group_edit_desc", settings.description),
            ("group_website", settings.website),
            ("group_edit_phone", settings.phone),
            ("event_mail", settings.email),
        ]:
            if value is None:
                continue

            _clear_and_type(driver, driver.find_element(*by_css(f"[id='{field_id}']")), value)

        if settings.category is not None:
            _set_category(driver, wait, settings.category)

        if settings.organiser_id is not None:
            _set_organiser(driver, settings.organiser_id)

        if settings.is_closed is not None:
            _set_access(driver, wait, settings.is_closed)

        if settings.city is not None:
            _set_city(driver, wait, settings.city)

        if settings.start_dt is not None:
            _fill_date_field(driver, wait, "group_start_date_date_input", settings.start_dt)

        if settings.end_dt is not None:
            _fill_date_field(driver, wait, "group_finish_date_date_input", settings.end_dt)

        click_save(driver, wait)
