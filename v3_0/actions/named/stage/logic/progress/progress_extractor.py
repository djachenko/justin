from typing import List

from v3_0.actions.named.stage.logic.base.abstract_check import AbstractCheck
from v3_0.actions.named.stage.logic.base.extractor import Extractor
from v3_0.shared.filesystem.path_based import PathBased
from v3_0.shared.models.photoset import Photoset


class ProgressExtractor(Extractor):

    def __init__(self, prechecks: List[AbstractCheck]) -> None:
        # noinspection PyTypeChecker
        super().__init__(
            name="progress",
            selector=None,
            filter_folder="progress",
            prechecks=prechecks)

    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        return []
