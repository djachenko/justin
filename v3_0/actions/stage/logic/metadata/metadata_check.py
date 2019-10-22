from functools import lru_cache
from typing import Optional

from v3_0.actions.stage.logic.base.check import Check
from v3_0.actions.stage.logic.base.extractor import Extractor
from v3_0.actions.stage.logic.base.selector import Selector
from v3_0.actions.stage.logic.factories.selector_factory import SelectorFactory


class MetadataCheck(Check):
    def __init__(self, selector_factory: SelectorFactory) -> None:
        super().__init__(
            name="metadata check",
            selector=selector_factory.metadata(),
        )
