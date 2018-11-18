from typing import List

from v3_0.helpers import util
from v3_0.logic.selector import Selector
from v3_0.filesystem.movable import Movable
from v3_0.models.photoset import Photoset


class EditedSelector(Selector):

    def source_folder(self, photoset: Photoset) -> str:
        return photoset.sources_folder_name

    def select(self, photoset: Photoset) -> List[Movable]:
        results = photoset.results
        sources = photoset.sources

        join = util.left_join(
            results,
            sources,
            lambda result: result.name_without_extension(),
            lambda source: source.name
        )

        results = [i[1] for i in join]

        unique_results = list(set(results))

        return unique_results
