from logic.photoset.checks.base_check import BaseCheck
from logic.photoset.filters.unselected_filter import UnselectedFilter
from logic.photoset.selectors.unselected_selector import UnselectedSelector


class UnselectedCheck(BaseCheck):
    @property
    def check_name(self):
        return "selection check"

    @property
    def failed_files_characteristic(self):
        return "without unsigned copies"

    def __init__(self) -> None:
        selector = UnselectedSelector()

        super().__init__(["Checking selection", "odd selected"], selector, UnselectedFilter(selector))
