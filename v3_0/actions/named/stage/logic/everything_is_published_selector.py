from typing import List

from v3_0.actions.named.stage.logic.base.selector import Selector
from v3_0.shared.models.photoset import Photoset


class EverythingIsPublishedSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        if photoset.justin is None:
            return []

        return [file.stem() for file in photoset.justin.files]
