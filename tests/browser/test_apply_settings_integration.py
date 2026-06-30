"""
Integration tests for apply_settings / EventSettingsSchema.
Требуют живой браузер с активной сессией VK.
Запуск: VK_TEST_EVENT_ID=<id> pytest -m integration tests/browser/test_apply_settings_integration.py
"""
import os

import pytest

from justin.browser.event_settings_settings import (
    AddressesSettings,
    CtaSettings,
    EventSettingsSettings,
    ExtrasSettings,
    MessagesSettings,
)
from justin.browser.section_settings import PhotosSettings, PostsSettings, SectionsConfig
from justin.browser.vk_browser import VKBrowser

TEST_EVENT_ID = int(os.environ["VK_TEST_EVENT_ID"])


@pytest.fixture(scope="module")
def browser():
    with VKBrowser() as b:
        yield b


@pytest.mark.integration
def test_apply_settings_messages_only(browser: VKBrowser) -> None:
    browser.apply_settings(TEST_EVENT_ID, EventSettingsSettings(
        messages=MessagesSettings(enabled=True),
    ))


@pytest.mark.integration
def test_apply_settings_messages_disabled(browser: VKBrowser) -> None:
    browser.apply_settings(TEST_EVENT_ID, EventSettingsSettings(
        messages=MessagesSettings(enabled=False),
    ))


@pytest.mark.integration
def test_apply_settings_sections_only(browser: VKBrowser) -> None:
    browser.apply_settings(TEST_EVENT_ID, EventSettingsSettings(
        sections=SectionsConfig(
            posts=PostsSettings(),
            photos=PhotosSettings(),
        ),
    ))


@pytest.mark.integration
def test_apply_settings_cta(browser: VKBrowser) -> None:
    browser.apply_settings(TEST_EVENT_ID, EventSettingsSettings(
        cta=CtaSettings(enabled=True),
    ))


@pytest.mark.integration
def test_apply_settings_addresses(browser: VKBrowser) -> None:
    browser.apply_settings(TEST_EVENT_ID, EventSettingsSettings(
        addresses=AddressesSettings(enabled=True),
    ))


@pytest.mark.integration
def test_apply_settings_extras_noop(browser: VKBrowser) -> None:
    """Все поля None — должно пройти без изменений."""
    browser.apply_settings(TEST_EVENT_ID, EventSettingsSettings(
        extras=ExtrasSettings(),
    ))


@pytest.mark.integration
def test_apply_settings_full(browser: VKBrowser) -> None:
    """Smoke-тест полного набора настроек как в setup_event_command."""
    browser.apply_settings(TEST_EVENT_ID, EventSettingsSettings(
        messages=MessagesSettings(enabled=True),
        sections=SectionsConfig(
            posts=PostsSettings(),
            photos=PhotosSettings(),
        ),
    ))
