from typing import List

from v3_0.helpers import joins
from v3_0.logic.base.selector import Selector
from v3_0.models.photoset import Photoset


class MetadataSelector(Selector):
    def source_folder(self, photoset: Photoset) -> str:
        return ""

    def select(self, photoset: Photoset) -> List[str]:
        results = photoset.big_jpegs
        sources = photoset.sources

        join = joins.inner(
            results,
            sources,
            lambda jpeg, source: jpeg.stem() == source.stem()
        )

        time_diffs = [(jpeg, jpeg.mtime - source.mtime) for jpeg, source in join]

        outdated = [time_diff for time_diff in time_diffs if time_diff[1] > 0]

        outdated_jpegs_names = [jpeg.stem() for jpeg, time in outdated]

        return outdated_jpegs_names
