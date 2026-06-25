from functools import cache

from justin.actions.stage.logic.base import Extractor
from justin.actions.stage.logic.candidates import CandidatesExtractor
from justin.actions.stage.logic.metadata import MetadataCheck
from justin.actions.stage.logic.progress import ProgressResultsCheck, ProgressExtractor
from justin.actions.stage.logic.structure import StructureExtractor
from justin.di.selectors import SelectorFactory


class ExtractorFactory:
    __EDITED_FOLDER = "edited"
    __ODD_SELECTION_FOLDER = "odd_selection"
    __TO_SELECT_FOLDER = "to_select"
    __UNEXPECTED_STRUCTURES = "unexpected_structures"

    def __init__(self, selector_factory: SelectorFactory) -> None:
        super().__init__()

        self.__selector_factory = selector_factory
        self.__metadata_check = MetadataCheck(selector_factory.metadata())

    @cache
    def edited(self) -> Extractor:
        return Extractor(
            selector=self.__selector_factory.edited(),
            filter_folder=ExtractorFactory.__EDITED_FOLDER,
            prechecks=[
                self.__metadata_check,
            ]
        )

    @cache
    def candidates(self) -> Extractor:
        return CandidatesExtractor([
            self.__metadata_check,
        ])

    @cache
    def unselected(self) -> Extractor:
        return Extractor(
            selector=self.__selector_factory.unselected(),
            filter_folder=ExtractorFactory.__TO_SELECT_FOLDER,
            prechecks=[
                self.__metadata_check,
            ]
        )

    @cache
    def odd_selection(self) -> Extractor:
        return Extractor(
            selector=self.__selector_factory.odd_selection(),
            filter_folder=ExtractorFactory.__ODD_SELECTION_FOLDER,
            prechecks=[
                self.__metadata_check,
            ]
        )

    @cache
    def structure(self) -> Extractor:
        return StructureExtractor(
            selector=self.__selector_factory.structure(),
            filter_folder=ExtractorFactory.__UNEXPECTED_STRUCTURES,
            prechecks=[
                self.__metadata_check,
            ]
        )

    @cache
    def progress(self) -> Extractor:
        return ProgressExtractor(prechecks=[
            self.__metadata_check,
            # todo: wtf?
            # ProgressResultsCheck(self.__selector_factory.progress_has_results())
        ])
