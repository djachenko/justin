from functools import lru_cache

from justin.actions.stage.logic.base import Check, MetaCheck
from justin.actions.stage.logic.gif_sources import GifSourcesCheck
from justin.actions.stage.logic.metadata import MetadataCheck
from justin.actions.stage.logic.metafile_state import MetafilesPublishedCheck, MetafilesExistCheck

from justin.di.extractors import ExtractorFactory
from justin.di.selectors import SelectorFactory


class ChecksFactory:
    def __init__(self, selector_factory: SelectorFactory, extractor_factory: ExtractorFactory) -> None:
        super().__init__()

        self.__selector_factory = selector_factory
        self.__extractor_factory = extractor_factory

    @lru_cache()
    def unselected(self) -> Check:
        return Check(
            name="selection check",
            selector=self.__selector_factory.unselected(),
            hook=self.__extractor_factory.unselected(),
            message="You have results without selection. Extract?"
        )

    @lru_cache()
    def odd_selection(self) -> Check:
        return Check(
            name="odd selection check",
            selector=self.__selector_factory.odd_selection(),
            hook=self.__extractor_factory.odd_selection(),
            message="You have selections without results. Extract?"
        )

    @lru_cache()
    def metadata(self) -> Check:
        return MetadataCheck(self.__selector_factory.metadata())

    @lru_cache()
    def missing_gifs(self) -> Check:
        return Check(
            name="missing gifs check",
            selector=self.__selector_factory.missing_gifs(),
            hook=self.__extractor_factory.missing_gifs(),
            message="You have missing gif. Generate?"
        )

    @lru_cache()
    def gif_sources(self) -> Check:
        return GifSourcesCheck(
            name="gif sources check",
            selector=self.__selector_factory.gif_sources(),
            message="Not all your sources have gif pair. This ok?"
        )

    @lru_cache()
    def structure(self) -> Check:
        return Check(
            name="structure check",
            selector=self.__selector_factory.structure(),
            hook=self.__extractor_factory.structure(),
            message="You have some unexpected structures. Extract?"
        )

    @lru_cache()
    def metafile(self) -> Check:
        return MetaCheck("metafile_check", [
            MetafilesExistCheck("metafiles exist"),
            MetafilesPublishedCheck("metafiles published"),
        ])

    @lru_cache()
    def everything_is_published(self) -> Check:
        return Check(
            name="everything is published check",
            selector=self.__selector_factory.everything_is_published()
        )

    @lru_cache()
    def progress_has_results(self) -> Check:
        return Check(
            name="progress has results",
            selector=self.__selector_factory.progress_has_results()
        )
