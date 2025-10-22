from typing import List

from justin.actions.stage.logic.base import Extractor, Selector, AbstractCheck
from justin.shared.filesystem import PathBased
from justin.shared.models.photoset import Photoset
from justin_utils.util import flat_map


class CandidatesExtractor(Extractor):
    def __init__(self, prechecks: List[AbstractCheck] = None) -> None:
        # noinspection PyTypeChecker
        super().__init__(
            None,
            "candidates",
            prechecks
        )

    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        return flat_map(source.files() for source in photoset.sources)
