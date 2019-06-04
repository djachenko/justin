from typing import List

from v3_0.helpers import joins
from v3_0.logic.base.selector import Selector
from v3_0.models.photoset import Photoset


class EditedSelector(Selector):

    def source_folder(self, photoset: Photoset) -> str:
        return photoset.sources_folder_name

    def select(self, photoset: Photoset) -> List[str]:
        results = photoset.results
        sources = photoset.sources

        join = joins.left(
            results,
            sources,
            lambda result, source: result.stem() == source.name
        )

        results = [i[1].stem() for i in join]

        unique_results = list(set(results))

        return unique_results
