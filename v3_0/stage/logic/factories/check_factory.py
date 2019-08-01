from functools import lru_cache

from v3_0.stage.logic.base.check import Check
from v3_0.stage.logic.factories.extractor_factory import ExtractorFactory
from v3_0.stage.logic.factories.selector_factory import SelectorFactory
from v3_0.stage.logic.gif_sources.gif_sources_check import GifSourcesCheck
from v3_0.stage.logic.metadata.metadata_check import MetadataCheck


class CheckFactory:
    @staticmethod
    @lru_cache()
    def instance() -> 'CheckFactory':
        return CheckFactory(
            selector_factory=SelectorFactory.instance(),
            extractor_factory=ExtractorFactory.instance()
        )

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
        return MetadataCheck.instance()

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

    def structure(self) -> Check:
        return Check(
            name="structure check",
            selector=self.__selector_factory.structure(),
            hook=self.__extractor_factory.structure(),
            message="You have some unexpected structures. Extract?"
        )