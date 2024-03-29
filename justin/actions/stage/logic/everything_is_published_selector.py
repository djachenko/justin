from typing import List

from justin.actions.stage.logic.base import Selector
from justin.shared.models.photoset import Photoset


class EverythingIsPublishedSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        if photoset.justin is None:
            return []

        return [file.stem for file in photoset.justin.files]
