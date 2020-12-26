from typing import List

from justin_utils import joins

from justin.actions.named.stage.logic.base.selector import Selector
from justin.shared.models.photoset import Photoset


class EditedSelector(Selector):
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
