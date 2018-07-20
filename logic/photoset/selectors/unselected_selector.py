from typing import List

import util
from logic.photoset.selectors.base_selector import BaseSelector
from models.movable import Movable
from models.photoset import Photoset


class UnselectedSelector(BaseSelector):
    def source_folder(self, photoset: Photoset) -> str:
        return photoset.sources_folder_name

    def select(self, photoset: Photoset) -> List[Movable]:
        selection = photoset.selection
        results = photoset.results

        join = util.left_join(results, selection, lambda x: x.name_without_extension())

        unselected = [i[0] for i in join if i[1] is None]

        sources = photoset.sources

        join2 = util.left_join(
            unselected,
            sources,
            lambda jpeg: jpeg.name_without_extension(),
            lambda source: source.name
        )

        unselected_sources = [i[1] for i in join2]

        return unselected_sources
