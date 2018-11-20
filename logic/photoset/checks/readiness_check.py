from v3_0.logic.check import Check
from logic.photoset.selectors.unnecessary_folders_selector import UnnecessaryFoldersSelector


class ReadinessCheck(Check):
    @property
    def name(self):
        return "check of destinations"

    def __init__(self) -> None:
        selector = UnnecessaryFoldersSelector(depth=1)
        messages = [
            "Checking structure of depth 1",
            "Have unnecessary folders"
        ]

        super().__init__(messages, selector, None)
