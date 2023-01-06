from typing import List

from justin_utils import joins

from justin.actions.stage.logic.base import Selector
from justin.shared.models.photoset import Photoset


class UnselectedSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        selection = photoset.not_signed
        results = photoset.results

        join = joins.left(
            results,
            selection,
            lambda x, y: x.stem() == y.stem()
        )

        names_of_unselected_jpegs = [i[0].stem() for i in join if i[1] is None]

        return names_of_unselected_jpegs
