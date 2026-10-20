"""The event creation wizard against live VK.

Opening and filling the wizard is integration; actually creating an event is destructive —
it leaves a real event behind.
"""
from datetime import datetime, timedelta

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from justin.browser.event_creation.event_creation_schema import EventCreationSchema
from justin.browser.event_creation.event_creation_settings import (
    Category,
    EventCreationSettings,
    EventStep1Settings,
    EventStep2Settings,
)
from justin.browser.shared.elements import by_css, present
from justin.browser.vk_browser import VKBrowser


@pytest.fixture(scope="module")
def driver(browser: VKBrowser) -> WebDriver:
    return browser.driver


@pytest.fixture
def wait(browser: VKBrowser) -> WebDriverWait:
    return browser.new_wait()


def _step1() -> EventStep1Settings:
    start = datetime(2026, 1, 1, 12, 0)

    return EventStep1Settings(
        title="Integration test",
        start_dt=start,
        end_dt=start + timedelta(hours=4),
        is_closed=True,
    )


def _open_wizard(driver: WebDriver, wait: WebDriverWait) -> EventCreationSchema:
    schema = EventCreationSchema()

    driver.get(schema._URL)

    iframe = present(wait, by_css(schema._IFRAME_CSS))

    driver.switch_to.frame(iframe)

    return schema


def _navigate_to_step2(driver: WebDriver, wait: WebDriverWait) -> EventCreationSchema:
    schema = _open_wizard(driver, wait)

    schema.step1.fill(_step1(), driver, wait)
    schema.step1.submit(driver, wait)

    return schema


def _close(driver: WebDriver) -> None:
    driver.switch_to.default_content()
    driver.get("about:blank")


@pytest.mark.integration
class TestStep1:
    def test_title(self, driver: WebDriver, wait: WebDriverWait) -> None:
        schema = _open_wizard(driver, wait)

        schema.step1.title.set_value("Smoke test title", driver, wait)

        _close(driver)

    def test_is_closed(self, driver: WebDriver, wait: WebDriverWait) -> None:
        schema = _open_wizard(driver, wait)

        schema.step1.is_closed.set_value(True, driver, wait)

        _close(driver)

    def test_start_date(self, driver: WebDriver, wait: WebDriverWait) -> None:
        schema = _open_wizard(driver, wait)

        schema.step1.start_dt.set_value(datetime(2026, 6, 15, 18, 0), driver, wait)

        _close(driver)

    def test_end_date(self, driver: WebDriver, wait: WebDriverWait) -> None:
        schema = _open_wizard(driver, wait)

        schema.step1.end_dt.set_value(datetime(2026, 6, 15, 22, 0), driver, wait)

        _close(driver)

    def test_organiser_skipped_when_none(self, driver: WebDriver, wait: WebDriverWait) -> None:
        schema = _open_wizard(driver, wait)

        schema.step1.organiser_id.set_value(None, driver, wait)

        _close(driver)

    def test_full_fill(self, driver: WebDriver, wait: WebDriverWait) -> None:
        schema = _open_wizard(driver, wait)

        schema.step1.fill(_step1(), driver, wait)

        _close(driver)


@pytest.mark.integration
class TestStep2:
    @pytest.mark.parametrize("category", list(Category))
    def test_category_selectable(self, driver: WebDriver, wait: WebDriverWait,
                                 category: Category) -> None:
        schema = _navigate_to_step2(driver, wait)

        schema.step2.fill(EventStep2Settings(category=category), driver, wait)

        _close(driver)


@pytest.mark.integration
@pytest.mark.destructive
class TestCreateEvent:
    def test_event_id_is_returned(self, browser: VKBrowser) -> None:
        settings = EventCreationSettings(step1=_step1())

        event_id = browser.create_event(
            title=settings.step1.title,
            start_dt=settings.step1.start_dt,
            end_dt=settings.step1.end_dt,
            is_closed=settings.step1.is_closed,
        )

        assert isinstance(event_id, int)
        assert event_id > 0
