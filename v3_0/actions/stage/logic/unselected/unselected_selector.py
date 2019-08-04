from typing import List

from v3_0.shared.helpers import joins
from v3_0.actions.stage.logic.base.selector import Selector
from v3_0.shared.models.photoset import Photoset


class UnselectedSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        selection = photoset.selection
        results = photoset.results

        join = joins.left(
            results,
            selection,
            lambda x, y: x.stem() == y.stem()
        )

        names_of_unselected_jpegs = [i[0].stem() for i in join if i[1] is None]

        return names_of_unselected_jpegs
