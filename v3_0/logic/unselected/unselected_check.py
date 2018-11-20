from v3_0.logic.check import Check
from v3_0.logic.unselected.unselected_filter import UnselectedFilter
from v3_0.logic.unselected.unselected_selector import UnselectedSelector


class UnselectedCheck(Check):
    @property
    def name(self):
        return "selection check"

    def __init__(self) -> None:
        selector = UnselectedSelector()

        super().__init__(["Checking selection", "odd selected"], selector, UnselectedFilter(selector))
