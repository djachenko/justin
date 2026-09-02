from dataclasses import dataclass

from justin.browser.event_setup.event_setup_settings import EventSetupSettings
from justin.browser.sections.section_settings import SectionsConfig


@dataclass
class CtaSettings:
    """Action button toggle (/settings/cta)."""
    enabled: bool


@dataclass
class MessagesSettings:
    """Messages page (?act=messages)."""
    enabled: bool = True
    first_message: str | None = None  # None = не трогать


@dataclass
class AddressesSettings:
    """Addresses toggle (?act=addresses)."""
    enabled: bool


@dataclass
class ExtrasSettings:
    """Additional settings (/settings/extras). None = не трогать."""
    hide_tag_suggestions: bool | None = None
    co_creatorship: bool | None = None
    story_replies: bool | None = None
    show_in_left_menu: bool | None = None


@dataclass
class EventSettingsSettings:
    """Top-level settings for a VK event after creation.

    None = не трогать соответствующий блок.
    """
    setup: EventSetupSettings | None = None
    sections: SectionsConfig | None = None
    cta: CtaSettings | None = None
    messages: MessagesSettings | None = None
    addresses: AddressesSettings | None = None
    extras: ExtrasSettings | None = None
