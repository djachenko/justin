"""apply_settings / EventSettingsSchema against live VK."""
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
class TestApplySettings:
    """No asserts on purpose: every setter re-reads the state after writing and raises
    if the write did not land — see test_settings_toggles and test_switch_state."""

    def test_messages_only(self, browser: VKBrowser, event_id: int) -> None:
        browser.apply_settings(event_id, EventSettingsSettings(
            messages=MessagesSettings(enabled=True),
        ))

    def test_messages_disabled(self, browser: VKBrowser, event_id: int) -> None:
        browser.apply_settings(event_id, EventSettingsSettings(
            messages=MessagesSettings(enabled=False),
        ))

    def test_sections_only(self, browser: VKBrowser, event_id: int) -> None:
        browser.apply_settings(event_id, EventSettingsSettings(
            sections=SectionsConfig(
                posts=PostsSettings(),
                photos=PhotosSettings(),
            ),
        ))

    def test_cta(self, browser: VKBrowser, event_id: int) -> None:
        browser.apply_settings(event_id, EventSettingsSettings(
            cta=CtaSettings(enabled=True),
        ))

    def test_addresses(self, browser: VKBrowser, event_id: int) -> None:
        browser.apply_settings(event_id, EventSettingsSettings(
            addresses=AddressesSettings(enabled=True),
        ))

    def test_extras_noop(self, browser: VKBrowser, event_id: int) -> None:
        browser.apply_settings(event_id, EventSettingsSettings(
            extras=ExtrasSettings(),
        ))

    def test_full(self, browser: VKBrowser, event_id: int) -> None:
        browser.apply_settings(event_id, EventSettingsSettings(
            messages=MessagesSettings(enabled=True),
            sections=SectionsConfig(
                posts=PostsSettings(),
                photos=PhotosSettings(),
            ),
        ))
