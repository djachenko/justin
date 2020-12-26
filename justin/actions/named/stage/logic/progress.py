from typing import List

from justin.actions.named.stage.logic.base import Extractor, AbstractCheck
from justin.shared.filesystem.path_based import PathBased
from justin.shared.models.photoset import Photoset


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
