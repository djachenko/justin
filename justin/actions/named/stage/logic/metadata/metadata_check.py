from justin.actions.named.stage.logic.base.check import Check
from justin.actions.named.stage.logic.base.selector import Selector


class MetadataCheck(Check):
    def __init__(self, selector: Selector) -> None:
        super().__init__(
            name="metadata check",
            selector=selector,
        )
