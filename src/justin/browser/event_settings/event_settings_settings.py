from dataclasses import dataclass

from justin.browser.event_setup.event_setup_settings import EventSetupSettings
from justin.browser.sections.section_settings import SectionsConfig


@dataclass(frozen=True)
class CtaSettings:
    """Action button toggle (/settings/cta)."""
    enabled: bool


@dataclass(frozen=True)
class MessagesSettings:
    """Messages page (?act=messages)."""
    enabled: bool = True
    first_message: str | None = None  # None — leave alone


@dataclass(frozen=True)
class AddressesSettings:
    """Addresses toggle (?act=addresses)."""
    enabled: bool


@dataclass(frozen=True)
class ExtrasSettings:
    """Additional settings (/settings/extras). None — leave alone."""
    co_creatorship: bool | None = None
    story_replies: bool | None = None
    show_in_left_menu: bool | None = None


@dataclass(frozen=True)
class EventSettingsSettings:
    """Top-level settings for a VK event after creation.

    None — leave the matching block alone.
    """
    setup: EventSetupSettings | None = None
    sections: SectionsConfig | None = None
    cta: CtaSettings | None = None
    messages: MessagesSettings | None = None
    addresses: AddressesSettings | None = None
    extras: ExtrasSettings | None = None
