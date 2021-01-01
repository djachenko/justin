from functools import lru_cache

from justin.actions.named.stage.logic.base import Selector
from justin.actions.named.stage.logic.edited import EditedSelector
from justin.actions.named.stage.logic.everything_is_published_selector import EverythingIsPublishedSelector
from justin.actions.named.stage.logic.gif_sources import GifSourcesSelector
from justin.actions.named.stage.logic.metadata import MetadataSelector
from justin.actions.named.stage.logic.missing_gifs import MissingGifsSelector
from justin.actions.named.stage.logic.odd_selection import OddSelectionSelector
from justin.actions.named.stage.logic.structure import StructureSelector
from justin.actions.named.stage.logic.unselected import UnselectedSelector
from justin.shared.structure import Structure


class SelectorFactory:

    def __init__(self, photoset_structure: Structure) -> None:
        super().__init__()

        self.__photoset_structure = photoset_structure

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

    @lru_cache()
    def structure(self) -> Selector:
        return StructureSelector(self.__photoset_structure)

    @lru_cache()
    def everything_is_published(self) -> Selector:
        return EverythingIsPublishedSelector()
