from v3_0.logic.check import Check
from logic.photoset.selectors.outdated_selector import OutdatedSelector


class MetadataCheck(Check):

    @property
    def name(self) -> str:
        return "metadata check"

    def __init__(self) -> None:
        selector = OutdatedSelector()

        super().__init__(["Checking timings", "Have outdated metadata"], selector, None)
