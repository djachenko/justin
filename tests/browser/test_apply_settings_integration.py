"""
Integration tests for apply_settings / EventSettingsSchema.
Требуют живой браузер с активной сессией VK.
Запуск: pytest -m integration tests/browser/test_apply_settings_integration.py
"""
import pytest

from justin.browser.event_settings.event_settings_settings import (
    AddressesSettings,
    CtaSettings,
    EventSettingsSettings,
    ExtrasSettings,
    MessagesSettings,
)
from justin.browser.sections.section_settings import PhotosSettings, PostsSettings, SectionsConfig
from justin.browser.vk_browser import VKBrowser


@pytest.mark.integration
def test_apply_settings_messages_only(browser: VKBrowser, event_id: int) -> None:
    browser.apply_settings(event_id, EventSettingsSettings(
        messages=MessagesSettings(enabled=True),
    ))


@pytest.mark.integration
def test_apply_settings_messages_disabled(browser: VKBrowser, event_id: int) -> None:
    browser.apply_settings(event_id, EventSettingsSettings(
        messages=MessagesSettings(enabled=False),
    ))


@pytest.mark.integration
def test_apply_settings_sections_only(browser: VKBrowser, event_id: int) -> None:
    browser.apply_settings(event_id, EventSettingsSettings(
        sections=SectionsConfig(
            posts=PostsSettings(),
            photos=PhotosSettings(),
        ),
    ))


@pytest.mark.integration
def test_apply_settings_cta(browser: VKBrowser, event_id: int) -> None:
    browser.apply_settings(event_id, EventSettingsSettings(
        cta=CtaSettings(enabled=True),
    ))


@pytest.mark.integration
def test_apply_settings_addresses(browser: VKBrowser, event_id: int) -> None:
    browser.apply_settings(event_id, EventSettingsSettings(
        addresses=AddressesSettings(enabled=True),
    ))


@pytest.mark.integration
def test_apply_settings_extras_noop(browser: VKBrowser, event_id: int) -> None:
    """Все поля None — должно пройти без изменений."""
    browser.apply_settings(event_id, EventSettingsSettings(
        extras=ExtrasSettings(),
    ))


@pytest.mark.integration
def test_apply_settings_full(browser: VKBrowser, event_id: int) -> None:
    """Smoke-тест полного набора настроек как в setup_event_command."""
    browser.apply_settings(event_id, EventSettingsSettings(
        messages=MessagesSettings(enabled=True),
        sections=SectionsConfig(
            posts=PostsSettings(),
            photos=PhotosSettings(),
        ),
    ))
