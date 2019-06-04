from functools import lru_cache

from logic.photoset.selectors.odd_selection_selector import OddSelectionSelector
from v3_0.logic.base.selector import Selector
from v3_0.logic.edited.edited_selector import EditedSelector
from v3_0.logic.metadata.metadata_selector import MetadataSelector
from v3_0.logic.unselected.unselected_selector import UnselectedSelector


class SelectorFactory:
    @staticmethod
    @lru_cache()
    def instance() -> 'SelectorFactory':
        return SelectorFactory()

    @lru_cache()
    def edited(self) -> Selector:
        return EditedSelector()

    @lru_cache()
    def unselected(self) -> Selector:
        return UnselectedSelector()

    @lru_cache()
    def odd_selection(self) -> Selector:
        return OddSelectionSelector()

    @lru_cache()
    def metadata(self) -> Selector:
        return MetadataSelector()
