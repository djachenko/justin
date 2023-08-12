from functools import lru_cache

from justin.actions.stage.logic.base import Selector
from justin.actions.stage.logic.edited import EditedSelector
from justin.actions.stage.logic.everything_is_published_selector import EverythingIsPublishedSelector
from justin.actions.stage.logic.gif_sources import GifSourcesSelector
from justin.actions.stage.logic.metadata import MetadataSelector
from justin.actions.stage.logic.odd_selection import OddSelectionSelector
from justin.actions.stage.logic.progress import AllSourcesHaveResultsSelector
from justin.actions.stage.logic.structure import ValidateStructureVisitor

from justin.actions.stage.logic.unselected import UnselectedSelector
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
    def gif_sources(self) -> Selector:
        return GifSourcesSelector()

    @lru_cache()
    def structure(self) -> Selector:
        return ValidateStructureVisitor(self.__photoset_structure)

    @lru_cache()
    def everything_is_published(self) -> Selector:
        return EverythingIsPublishedSelector()

    @lru_cache()
    def progress_has_results(self) -> Selector:
        return AllSourcesHaveResultsSelector()
