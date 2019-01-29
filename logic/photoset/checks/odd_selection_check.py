from v3_0.logic.check import Check
from logic.photoset.filters.odd_selection_filter import OddSelectionFilter
from logic.photoset.selectors.odd_selection_selector import OddSelectionSelector


class OddSelectionCheck(Check):
    @property
    def name(self):
        return "odd selection check"

    def __init__(self) -> None:
        selector = OddSelectionSelector()

        super().__init__(["Checking selection", "odd selected"], selector, OddSelectionFilter(selector))
