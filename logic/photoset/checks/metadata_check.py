from logic.photoset.checks.base_check import BaseCheck
from logic.photoset.selectors.outdated_selector import OutdatedSelector


class MetadataCheck(BaseCheck):
    @property
    def failed_files_characteristic(self) -> str:
        return "with outdated metadata"

    @property
    def check_name(self) -> str:
        return "metadata check"

    def __init__(self) -> None:
        selector = OutdatedSelector()

        super().__init__(["Checking timings", "Have outdated metadata"], selector, None)
