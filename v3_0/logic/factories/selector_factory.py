from functools import lru_cache

from v3_0.logic.base.selector import Selector
from v3_0.logic.edited.edited_selector import EditedSelector
from v3_0.logic.gif_sources.gif_sources_selector import GifSourcesSelector
from v3_0.logic.missing_gifs.missing_gifs_selector import MissingGifsSelector
from v3_0.logic.metadata.metadata_selector import MetadataSelector
from v3_0.logic.odd_selection.odd_selection_selector import OddSelectionSelector
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

    @lru_cache()
    def missing_gifs(self) -> Selector:
        return MissingGifsSelector()

    @lru_cache()
    def gif_sources(self) -> Selector:
        return GifSourcesSelector()
