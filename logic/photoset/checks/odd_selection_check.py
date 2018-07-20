from logic.photoset.checks.base_check import BaseCheck
from logic.photoset.filters.odd_selection_filter import OddSelectionFilter
from logic.photoset.selectors.odd_selection_selector import OddSelectionSelector


class OddSelectionCheck(BaseCheck):
    @property
    def check_name(self):
        return "odd selection check"

    @property
    def failed_files_characteristic(self):
        return "without signed pair"

    def __init__(self) -> None:
        selector = OddSelectionSelector()

        super().__init__(["Checking selection", "odd selected"], selector, OddSelectionFilter(selector))
