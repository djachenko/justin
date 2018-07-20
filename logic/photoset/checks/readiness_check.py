from logic.photoset.checks.base_check import BaseCheck
from logic.photoset.selectors.unnecessary_folders_selector import UnnecessaryFoldersSelector


class ReadinessCheck(BaseCheck):
    @property
    def check_name(self):
        return "check of destinations"

    @property
    def failed_files_characteristic(self):
        return "which aren't designed in structure"

    @property
    def file_type(self):
        return "Folders"

    def __init__(self) -> None:
        selector = UnnecessaryFoldersSelector(depth=1)
        messages = [
            "Checking structure of depth 1",
            "Have unnecessary folders"
        ]

        super().__init__(messages, selector, None)
