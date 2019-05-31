from typing import List

from v3_0.filesystem.movable import Movable
from v3_0.helpers import joins
from v3_0.logic.selector import Selector
from v3_0.models.photoset import Photoset


class UnselectedSelector(Selector):
    def source_folder(self, photoset: Photoset) -> str:
        return photoset.sources_folder_name

    def select(self, photoset: Photoset) -> List[Movable]:
        selection = photoset.selection
        results = photoset.results

        join = joins.left(
            results,
            selection,
            lambda x, y: x.stem() == y.stem()
        )

        unselected = [i[0] for i in join if i[1] is None]

        sources = photoset.sources

        join2 = joins.left(
            unselected,
            sources,
            lambda jpeg, source: jpeg.stem() == source.name
        )

        unselected_sources = [i[1] for i in join2]

        return unselected_sources
