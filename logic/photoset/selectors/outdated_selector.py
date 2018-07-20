from typing import List

import util
from logic.photoset.selectors.base_selector import BaseSelector
from models.movable import Movable
from models.photoset import Photoset


class OutdatedSelector(BaseSelector):
    def source_folder(self, photoset: Photoset) -> str:
        return ""

    def select(self, photoset: Photoset) -> List[Movable]:
        results = photoset.results + photoset.selection
        sources = photoset.sources

        join = util.inner_join(
            results,
            sources,
            lambda jpeg: jpeg.name_without_extension(),
            lambda source: source.name
        )

        time_diffs = [(jpeg, jpeg.mtime - source.mtime) for jpeg, source in join]

        outdated = [time_diff for time_diff in time_diffs if time_diff[1] > 0]

        outdated_jpegs = [jpeg for jpeg, time in outdated]

        return outdated_jpegs
