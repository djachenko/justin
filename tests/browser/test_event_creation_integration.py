"""
Integration tests — требуют живой браузер с активной сессией VK.

Маркеры:
  integration  — любой тест с живым браузером
  destructive  — создаёт реальные ивенты на VK, запускать отдельно/редко

Запуск smoke (без последствий): pytest -m "integration and not destructive"
Запуск всего:                    pytest -m integration
"""
from datetime import datetime, timedelta

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_creation_schema import EventCreationSchema
from justin.browser.event_creation_settings import (
    Category,
    EventCreationSettings,
    EventStep1Settings,
    EventStep2Settings,
)
from justin.browser.vk_browser import VKBrowser


# --- fixtures ---

@pytest.fixture(scope="module")
def browser():
    with VKBrowser() as b:
        yield b


@pytest.fixture(scope="module")
def driver(browser: VKBrowser):
    return browser.driver


@pytest.fixture
def wait(browser: VKBrowser):
    return browser.new_wait()


# --- helpers ---

def _step1() -> EventStep1Settings:
    start = datetime(2026, 1, 1, 12, 0)
    return EventStep1Settings(
        title="Integration test",
        start_dt=start,
        end_dt=start + timedelta(hours=4),
        is_closed=True,
    )


def _open_wizard(driver, wait) -> EventCreationSchema:
    schema = EventCreationSchema()
    driver.get(schema._URL)
    iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, schema._IFRAME_CSS)))
    driver.switch_to.frame(iframe)
    return schema


def _close(driver) -> None:
    driver.switch_to.default_content()
    driver.get("about:blank")


# --- step 1 smoke tests ---

@pytest.mark.integration
def test_step1_title(driver, wait) -> None:
    schema = _open_wizard(driver, wait)
    schema.step1.title.set_value("Smoke test title", driver, wait)
    _close(driver)


@pytest.mark.integration
def test_step1_is_closed(driver, wait) -> None:
    schema = _open_wizard(driver, wait)
    schema.step1.is_closed.set_value(True, driver, wait)
    _close(driver)


@pytest.mark.integration
def test_step1_start_date(driver, wait) -> None:
    schema = _open_wizard(driver, wait)
    schema.step1.start_dt.set_value(datetime(2026, 6, 15, 18, 0), driver, wait)
    _close(driver)


@pytest.mark.integration
def test_step1_end_date(driver, wait) -> None:
    schema = _open_wizard(driver, wait)
    schema.step1.end_dt.set_value(datetime(2026, 6, 15, 22, 0), driver, wait)
    _close(driver)


@pytest.mark.integration
def test_step1_organizer(driver, wait) -> None:
    schema = _open_wizard(driver, wait)
    schema.step1.organiser_id.set_value(None, driver, wait)  # None = skip, проверяем что не падает
    _close(driver)


@pytest.mark.integration
def test_step1_full_fill(driver, wait) -> None:
    schema = _open_wizard(driver, wait)
    schema.step1.fill(_step1(), driver, wait)
    _close(driver)


# --- step 2 smoke tests ---

def _navigate_to_step2(driver, wait) -> EventCreationSchema:
    schema = _open_wizard(driver, wait)
    schema.step1.fill(_step1(), driver, wait)
    schema.step1.submit(driver, wait)
    return schema


@pytest.mark.integration
@pytest.mark.parametrize("category", list(Category))
def test_step2_category_selectable(driver, wait, category: Category) -> None:
    schema = _navigate_to_step2(driver, wait)
    schema.step2.fill(EventStep2Settings(category=category), driver, wait)
    _close(driver)


# --- destructive ---

@pytest.mark.integration
@pytest.mark.destructive
def test_create_event_returns_id(browser: VKBrowser) -> None:
    settings = EventCreationSettings(step1=_step1())
    event_id = browser.create_event(
        title=settings.step1.title,
        start_dt=settings.step1.start_dt,
        end_dt=settings.step1.end_dt,
        is_closed=settings.step1.is_closed,
    )
    assert isinstance(event_id, int)
    assert event_id > 0
