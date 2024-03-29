from typing import List

from justin_utils import joins

from justin.actions.stage.logic.base import Check
from justin.actions.stage.logic.base import Selector
from justin.shared.models.photoset import Photoset


class MetadataSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        results = photoset.big_jpegs
        sources = photoset.sources

        join = joins.inner(
            results,
            sources,
            lambda jpeg, source: jpeg.stem == source.stem
        )

        time_diffs = [(jpeg.name, jpeg.mtime - source.mtime) for jpeg, source in join]

        outdated = [time_diff for time_diff in time_diffs if time_diff[1] > 0]

        outdated_jpegs_names = [jpeg_name for jpeg_name, _ in outdated]

        return outdated_jpegs_names


class MetadataCheck(Check):
    def __init__(self, selector: Selector) -> None:
        super().__init__(
            name="metadata check",
            selector=selector,
        )
