from functools import lru_cache

from v3_0.logic.base.check import Check
from v3_0.logic.factories.extractor_factory import ExtractorFactory
from v3_0.logic.factories.selector_factory import SelectorFactory
from v3_0.logic.metadata.metadata_check import MetadataCheck


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

        self.selector_factory = selector_factory
        self.extractor_factory = extractor_factory

    @lru_cache()
    def unselected(self) -> Check:
        return Check(
            "selection check",
            self.selector_factory.unselected(),
            self.extractor_factory.unselected()
        )

    @lru_cache()
    def odd_selection(self) -> Check:
        return Check(
            name="odd selection check",
            selector=self.selector_factory.odd_selection(),
            hook=self.extractor_factory.odd_selection()
        )

    @lru_cache()
    def metadata(self) -> Check:
        return MetadataCheck.instance()
