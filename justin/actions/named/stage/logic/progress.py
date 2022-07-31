from typing import List

from justin_utils import joins

from justin.actions.named.stage.logic.base import Extractor, AbstractCheck, Check, Selector
from justin.shared.filesystem import PathBased
from justin.shared.models.photoset import Photoset


class ProgressExtractor(Extractor):

    def __init__(self, prechecks: List[AbstractCheck]) -> None:
        # noinspection PyTypeChecker
        super().__init__(
            name="progress",
            selector=None,
            filter_folder="progress",
            prechecks=prechecks
        )

    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        return []

    def forward(self, photoset: Photoset):
        pass


class ProgressResultsSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        if photoset.name != "progress":
            return []

        results = photoset.results
        sources = photoset.sources

        join = joins.left(sources, results, lambda s, r: s.stem() == r.stem())

        sources_without_results = [s.name for s, r in join if r is None]

        return sources_without_results


class ProgressResultsCheck(Check):
    def __init__(self, selector: Selector) -> None:
        super().__init__(
            name="progress check",
            selector=selector
        )
