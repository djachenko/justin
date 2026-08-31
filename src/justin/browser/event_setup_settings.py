from dataclasses import dataclass, field
from datetime import datetime

from justin.browser.event_creation_settings import Category


@dataclass
class EventSetupSettings:
    """Settings for editing an existing VK event via ?act=edit."""
    title: str | None = None
    description: str | None = None
    category: Category | None = None
    organiser_id: int | None = None
    is_closed: bool | None = None
    start_dt: datetime | None = None
    end_dt: datetime | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
