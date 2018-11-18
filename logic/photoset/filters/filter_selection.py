from v3_0.logic.filter import Filter
from logic.photoset.filters.odd_selection_filter import OddSelectionFilter
from v3_0.logic.unselected.unselected_filter import UnselectedFilter
from v3_0.models.photoset import Photoset


class SelectionFilter(Filter):
    def __init__(self) -> None:
        super().__init__()

        self.__inner_filters = [
            OddSelectionFilter(),
            UnselectedFilter(),
        ]

    def forward(self, photoset: Photoset) -> None:
        for inner_filter in self.__inner_filters:
            inner_filter.forward(photoset)

    def backwards(self, photoset: Photoset) -> None:
        for inner_filter in self.__inner_filters:
            inner_filter.backwards(photoset)
