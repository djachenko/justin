from legacy.logic.photoset.selectors.unnecessary_folders_selector import UnnecessaryFoldersSelector
from v3_0.stage.logic.base.check import Check


class ReadinessCheck(Check):
    def __init__(self) -> None:
        selector = UnnecessaryFoldersSelector(depth=1)

        super().__init__("check of destinations", selector, None)
