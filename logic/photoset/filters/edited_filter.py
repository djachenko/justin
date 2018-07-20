from logic.photoset.checks.metadata_check import MetadataCheck
from logic.photoset.filters.base_filter import BaseFilter
from logic.photoset.selectors.edited_selector import EditedSelector


class EditedFilter(BaseFilter):
    __edited_folder = "edited_sources"

    def __init__(self) -> None:
        super().__init__(
            selector=EditedSelector(),
            filter_folder=EditedFilter.__edited_folder,
            prechecks=[
                MetadataCheck()
            ]
        )
