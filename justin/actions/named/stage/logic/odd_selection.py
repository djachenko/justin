from typing import List

from justin_utils import joins

from justin.actions.named.stage.logic.base import Selector
from justin.shared.models.photoset import Photoset


class OddSelectionSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        selection = photoset.selection

        if selection is None:
            return []

        results = photoset.results

        join = joins.left(
            selection,
            results,
            lambda x, y: x.stem() == y.stem()
        )

        return [i[0].stem() for i in join if i[1] is None]