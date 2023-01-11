from typing import List

from justin.actions.stage.logic.base import Selector
from justin.shared.models.photoset import Photoset


class EditedSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        results = photoset.results
        results_stems = [result.stem for result in results]

        unique_results = list(set(results_stems))

        return unique_results
