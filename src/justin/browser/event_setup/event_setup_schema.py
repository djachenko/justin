"""Schema for editing an existing VK event via ?act=edit."""
import re
from dataclasses import dataclass
from datetime import date, datetime

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from justin_utils.util import first

from justin.browser.event_creation.event_creation_settings import Category
from justin.browser.event_setup.event_setup_settings import EventSetupSettings
from justin.browser.shared.elements import by_css, by_testid, by_xpath, found, present, type_into
from justin.browser.shared.pacing import AFTER_ACTION, AFTER_SCROLL, pause
from justin.browser.shared.page import content_rendered
from justin.browser.shared.save_button import click_save
from justin.shared.vk import VK_URL


def _value_of(element: WebElement) -> str:
    """Selenium returns None when the attribute is absent.

    That is a setting that did not apply, same as a wrong value: without the check a
    missing date surfaces as a TypeError from the middle of a comparison.
    """
    value = element.get_attribute("value")

    if value is None:
        raise ValueError(f"Field {element.get_attribute('id')!r} has no value attribute")

    return value


def _clear_and_type(el: WebElement, value: str) -> None:
    el.clear()

    type_into(el, value)

    pause(AFTER_ACTION)


_MAX_YEAR_STEPS = 20

_LAZY_BLOCKS = 1.0  # lazy blocks of the page load after scrolling to the bottom


class Access:
    """Access is not a VK selector but a legacy dropdown: items are picked by position."""
    WIDGET = "#groups_edit_g_access"
    ITEMS = by_css(f"{WIDGET} .idd_item")
    VALUE = by_css("input[name='groups_edit_g_access']")
    OPEN = 0
    CLOSED = 1


class Selectors:
    """Subject, organiser, hours, minutes and city are the same widget — only position differs."""
    SUBJECT = 0
    CITY = 6
    INPUT = by_css(".selector_input")
    FOLLOWING = by_xpath("following::input[contains(@class, 'selector_input')]")
    RESULT_ITEM = by_css(".result_list li")
    DROPDOWN_ITEM = by_css("[class*='dropdown'] li")


class Calendar:
    """Datepicker: months and days live in the very same td.day cells."""
    CONTAINER = by_xpath("ancestor::*[contains(@class, 'datepicker_container')][1]")
    DAY = by_css("td.day")
    MONTH = by_css("td.month")
    MONTH_MODE = by_css("a.cal_month_sel")


_EVENT_HOST = by_css("input[name='event_host'], input[id='event_host']")
_NAME = by_css("[id='group_edit_name']")
_RIGHT_MENU = by_testid("rightmenu")


def _classes_of(element: WebElement) -> str:
    return element.get_attribute("class") or ""


def _is_day(cell: WebElement, day: int) -> bool:
    """Neighbouring months sit in the same calendar — their cells carry a class."""
    classes = _classes_of(cell)

    if "prev_month_day" in classes or "next_month_day" in classes:
        return False

    return cell.text.strip() == str(day)


def _has_label(item: WebElement, label: str) -> bool:
    return item.is_displayed() and item.text.strip() == label


def _is_number(item: WebElement, value: int) -> bool:
    text = item.text.strip()

    if not item.is_displayed() or not text.isdigit():
        return False

    return int(text) == value


def _visible_cells(calendar: WebElement) -> list[WebElement]:
    """Months and days share the td.day class — only one set is visible at a time."""
    return [el for el in calendar.find_elements(*Calendar.DAY) if el.is_displayed()]


def _click_arrow(calendar: WebElement, direction: str) -> None:
    """Day and month modes each carry their own arrows — the hidden ones have no click area."""
    arrows = [el for el in calendar.find_elements(*by_css(f"a.arr.{direction}"))
              if el.is_displayed()]

    if not arrows:
        raise NoSuchElementException(f"No {direction} arrow in datepicker")

    arrows[0].click()


def _pick_year_and_month(driver: WebDriver, wait: WebDriverWait, calendar: WebElement, dt: datetime) -> None:
    """Month names are localised — the year is read as a number, the month picked by position."""
    calendar.find_element(*Calendar.MONTH_MODE).click()
    wait.until(lambda _: len(_visible_cells(calendar)) == 12)

    for _ in range(_MAX_YEAR_STEPS):
        years = [re.search(r"\d{4}", el.text) for el in
                 calendar.find_elements(*Calendar.MONTH) if el.is_displayed()]
        shown = first(years)

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


def _pick_date(driver: WebDriver, wait: WebDriverWait, date_el: WebElement, dt: datetime) -> None:
    """The date field is readonly — the value can only be set through the datepicker."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", date_el)

    pause(AFTER_SCROLL)

    date_el.click()

    calendar = date_el.find_element(*Calendar.CONTAINER)

    wait.until(lambda _: calendar.find_elements(*Calendar.DAY))

    _pick_year_and_month(driver, wait, calendar, dt)

    day = first(_visible_cells(calendar), key=lambda cell: _is_day(cell, dt.day))

    if day is None:
        raise NoSuchElementException(f"Day {dt.day} not found in datepicker")

    day.click()

    pause(AFTER_ACTION)


def _pick_from_selector(driver: WebDriver, wait: WebDriverWait, selector_input: WebElement, value: int) -> None:
    """Hours and minutes are readonly VK selectors — the value is picked from a dropdown."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", selector_input)

    pause(AFTER_SCROLL)

    selector_input.click()

    def option(_: WebDriver) -> WebElement | None:
        items = driver.find_elements(*Selectors.DROPDOWN_ITEM)

        return first(items, key=lambda item: _is_number(item, value))

    found(wait, option).click()

    pause(AFTER_ACTION)


_SHOWN_DATE_FORMATS = ("%d %B %Y", "%d %b %Y", "%d.%m.%Y")


def _shown_date(shown: str) -> date:
    """The interface is English, so the field shows the month by name, e.g. '5 March 2026'.

    %B and %b follow the process locale: nothing here calls setlocale, so English names parse.
    """
    text = " ".join(shown.split())

    for fmt in _SHOWN_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Date field shows {shown!r}, which is not a date")


def _fill_date_field(driver: WebDriver, wait: WebDriverWait, date_input_id: str,
                     dt: datetime) -> None:
    """Fill VK date picker + the hour/minute selectors that follow it.

    date_input_id: 'group_start_date_date_input' or 'group_finish_date_date_input'
    """
    date_el = driver.find_element(*by_css(f"[id='{date_input_id}']"))

    _pick_date(driver, wait, date_el, dt)

    shown = _value_of(date_el)

    if _shown_date(shown) != dt.date():
        raise ValueError(f"Date not applied: field shows {shown!r}, expected {dt.date()}")

    try:
        hour, minute, *_ = date_el.find_elements(*Selectors.FOLLOWING)
    except ValueError as e:
        raise ValueError("Could not find a matching hour/minute selector") from e

    _pick_from_selector(driver, wait, hour, dt.hour)
    _pick_from_selector(driver, wait, minute, dt.minute)

    got = (int(_value_of(hour)), int(_value_of(minute)))

    if got != (dt.hour, dt.minute):
        raise ValueError(f"Time not applied: fields show {got}, expected {dt:%H:%M}")


def _visible_selectors(driver: WebDriver) -> list[WebElement]:
    """Subject, organiser, hours, minutes and city all render as the same selector widget."""
    return [el for el in driver.find_elements(*Selectors.INPUT) if el.is_displayed()]


def _pick_from_result_list(driver: WebDriver, wait: WebDriverWait, field: WebElement, label: str) -> None:
    """The selector opens a result_list — options carry no ids, only their labels."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", field)

    pause(AFTER_SCROLL)

    field.click()

    def option(_: WebDriver) -> WebElement | None:
        items = driver.find_elements(*Selectors.RESULT_ITEM)

        return first(items, key=lambda item: _has_label(item, label))

    found(wait, option).click()

    pause(AFTER_ACTION)

    shown = _value_of(field)

    if shown != label:
        raise ValueError(f"Selector not applied: field shows {shown!r}, expected {label!r}")


def _set_category(driver: WebDriver, wait: WebDriverWait, category: Category) -> None:
    _pick_from_result_list(driver, wait, _visible_selectors(driver)[Selectors.SUBJECT], category.value)


def _set_access(driver: WebDriver, wait: WebDriverWait, is_closed: bool) -> None:
    """Access comes from the dropdown widget, not from the hidden field it keeps in sync.

    Writing the hidden input alone is silently dropped on save. Options are localised,
    so the one to pick is chosen by position: 0 open, 1 closed.
    """
    if is_closed:
        expected = Access.CLOSED
    else:
        expected = Access.OPEN

    wrap = driver.find_element(*by_css(Access.WIDGET))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", wrap)

    pause(AFTER_SCROLL)

    wrap.click()

    def items(_: WebDriver) -> list[WebElement] | None:
        visible = [el for el in driver.find_elements(*Access.ITEMS) if el.is_displayed()]

        if len(visible) <= expected:
            return None

        return visible

    found(wait, items)[expected].click()

    pause(AFTER_ACTION)

    try:
        wait.until(lambda _: _value_of(driver.find_element(*Access.VALUE)) == str(expected))
    except TimeoutException:
        shown = _value_of(driver.find_element(*Access.VALUE))

        raise ValueError(f"Access not applied: widget holds {shown!r}, expected {expected}")


def _set_hidden(driver: WebDriver, locator: tuple[str, str], value: str) -> None:
    field = driver.find_element(*locator)
    driver.execute_script("arguments[0].value = arguments[1]", field, value)


def _set_organiser(driver: WebDriver, organiser_id: int) -> None:
    """The option list carries names only — the id lives in the hidden event_host field.

    Reading the field back only returns what was just written; whether it held shows
    after save and reload alone. That round trip was checked live — event_host is the
    source the form submits, unlike the access mirror.
    """
    _set_hidden(driver, _EVENT_HOST, str(organiser_id))


def _form_ready(driver: WebDriver) -> bool:
    """The legacy page form is either past its skeletons or at least has the right menu."""
    if content_rendered(driver):
        return True

    try:
        menu = driver.find_elements(*_RIGHT_MENU)

        return bool(menu and menu[0].is_displayed())
    except StaleElementReferenceException:
        return False


def _wait_for_form(driver: WebDriver, wait: WebDriverWait) -> None:
    wait.until(_form_ready)

    # Scrolling down and back wakes the lazy blocks — without it some fields are not drawn.
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

    pause(_LAZY_BLOCKS)

    driver.execute_script("window.scrollTo(0, 0)")

    pause(AFTER_SCROLL)

    present(wait, _NAME)


def _set_city(driver: WebDriver, wait: WebDriverWait, city: str) -> None:
    """The city is a selector like the category, not a text field: typing into it leaves
    the hidden id untouched, so the value has to be picked from the result list."""
    selectors = _visible_selectors(driver)

    if len(selectors) <= Selectors.CITY:
        raise NoSuchElementException(
            f"City selector not found: page has {len(selectors)} selectors")

    _pick_from_result_list(driver, wait, selectors[Selectors.CITY], city)


@dataclass(frozen=True)
class EventSetupSchema:
    _SETTINGS_URL_TMPL: str = VK_URL + "/event{event_id}?act=edit"

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

            _clear_and_type(driver.find_element(*by_css(f"[id='{field_id}']")), value)

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
