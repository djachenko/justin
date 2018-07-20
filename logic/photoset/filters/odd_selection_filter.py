from logic.photoset.checks.metadata_check import MetadataCheck
from logic.photoset.filters.base_filter import BaseFilter
from logic.photoset.selectors.odd_selection_selector import OddSelectionSelector


class OddSelectionFilter(BaseFilter):
    __ODD_SELECTION_FOLDER = "odd_selection"

    def __init__(self, selector=None) -> None:
        if selector is None:
            selector = OddSelectionSelector()

        super().__init__(
            selector=selector,
            filter_folder=OddSelectionFilter.__ODD_SELECTION_FOLDER,
            prechecks=[
                MetadataCheck()
            ]
        )
