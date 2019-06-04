from v3_0.logic.base.check import Check
from logic.photoset.selectors.unnecessary_folders_selector import UnnecessaryFoldersSelector


class ReadinessCheck(Check):
    def __init__(self) -> None:
        selector = UnnecessaryFoldersSelector(depth=1)

        super().__init__("check of destinations", selector, None)
