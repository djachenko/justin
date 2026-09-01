from dataclasses import dataclass
from enum import Enum


class LinkLifetime(str, Enum):
    """How long the link stays valid, in seconds — zero never expires."""
    HALF_HOUR = "1800"
    HOUR = "3600"
    SIX_HOURS = "21600"
    TWELVE_HOURS = "43200"
    DAY = "86400"
    INDEFINITE = "0"


class LinkUses(str, Enum):
    """How many times the link can be used — zero is unlimited."""
    ONCE = "1"
    FIVE = "5"
    TEN = "10"
    TWENTY_FIVE = "25"
    HUNDRED = "100"
    UNLIMITED = "0"


@dataclass
class InviteLinkSettings:
    """Settings of the new-link modal on the invites page."""
    lifetime: LinkLifetime = LinkLifetime.INDEFINITE
    uses: LinkUses = LinkUses.TWENTY_FIVE
