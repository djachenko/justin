from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EventSetupSettings:
    """Settings for editing an existing VK event via ?act=edit."""
    title: str | None = None
    description: str | None = None
    start_dt: datetime | None = None
    end_dt: datetime | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
