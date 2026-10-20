from dataclasses import dataclass
from enum import Enum


_HOUR = 60 * 60


class LinkLifetime(str, Enum):
    """How long the link stays valid, in seconds — zero never expires."""
    HALF_HOUR = str(_HOUR // 2)
    HOUR = str(_HOUR)
    SIX_HOURS = str(6 * _HOUR)
    TWELVE_HOURS = str(12 * _HOUR)
    DAY = str(24 * _HOUR)
    INDEFINITE = "0"


class LinkUses(str, Enum):
    """How many times the link can be used — zero is unlimited."""
    ONCE = "1"
    FIVE = "5"
    TEN = "10"
    TWENTY_FIVE = "25"
    HUNDRED = "100"
    UNLIMITED = "0"


@dataclass(frozen=True)
class InviteLinkSettings:
    """Settings of the new-link modal on the invites page."""
    lifetime: LinkLifetime = LinkLifetime.INDEFINITE
    uses: LinkUses = LinkUses.TWENTY_FIVE
