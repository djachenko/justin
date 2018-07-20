from logic.photoset.checks.metadata_check import MetadataCheck
from logic.photoset.filters.base_filter import BaseFilter
from logic.photoset.selectors.unselected_selector import UnselectedSelector


class UnselectedFilter(BaseFilter):
    __TO_SELECT_FOLDER = "to_select"

    def __init__(self, selector=None) -> None:
        if selector is None:
            selector = UnselectedSelector()

        super().__init__(
            selector=selector,
            filter_folder=UnselectedFilter.__TO_SELECT_FOLDER,
            prechecks=[
                MetadataCheck()
            ]
        )
