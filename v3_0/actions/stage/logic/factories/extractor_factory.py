from functools import lru_cache

from v3_0.actions.stage.logic.base.extractor import Extractor
from v3_0.actions.stage.logic.factories.selector_factory import SelectorFactory
from v3_0.actions.stage.logic.metadata.metadata_check import MetadataCheck
from v3_0.actions.stage.logic.missing_gifs.missing_gifs_handler import MissingGifsHandler
from v3_0.actions.stage.logic.structure.structure_extractor import StructureExtractor


class ExtractorFactory:
    __EDITED_FOLDER = "edited"
    __ODD_SELECTION_FOLDER = "odd_selection"
    __TO_SELECT_FOLDER = "to_select"
    __UNEXPECTED_STRUCTURES = "unexpected_structures"

    def __init__(self, selector_factory: SelectorFactory) -> None:
        super().__init__()
        self.__selector_factory = selector_factory
        self.__metadata_check = MetadataCheck(selector_factory.metadata())

    @lru_cache()
    def edited(self) -> Extractor:
        return Extractor(
            name="edited",
            selector=self.__selector_factory.edited(),
            filter_folder=ExtractorFactory.__EDITED_FOLDER,
            prechecks=[
                self.__metadata_check
            ]
        )

    @lru_cache()
    def unselected(self) -> Extractor:
        return Extractor(
            name="unselected",
            selector=self.__selector_factory.unselected(),
            filter_folder=ExtractorFactory.__TO_SELECT_FOLDER,
            prechecks=[
                self.__metadata_check
            ]
        )

    @lru_cache()
    def odd_selection(self) -> Extractor:
        return Extractor(
            name="odd selection",
            selector=self.__selector_factory.odd_selection(),
            filter_folder=ExtractorFactory.__ODD_SELECTION_FOLDER,
            prechecks=[
                self.__metadata_check
            ]
        )

    @lru_cache()
    def missing_gifs(self) -> Extractor:
        return MissingGifsHandler(
            name="missing gifs",
            selector=self.__selector_factory.missing_gifs(),
            filter_folder="",
            prechecks=[]
        )

    @lru_cache()
    def structure(self) -> Extractor:
        return StructureExtractor(
            name="structure",
            selector=self.__selector_factory.structure(),
            filter_folder=ExtractorFactory.__UNEXPECTED_STRUCTURES,
            prechecks=[
                self.__metadata_check
            ]
        )
