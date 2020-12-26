from typing import List

from justin.shared.helpers.parting_helper import PartingHelper
from justin.actions.named.stage.logic.base.selector import Selector
from justin.shared.models.photoset import Photoset


class MissingGifsSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        parts = PartingHelper.folder_tree_parts(photoset.gif)

        result = []

        for part in parts:
            part_files = set([file.extension.lower().strip(" .") for file in part.files])

            if "gif" not in part_files:
                result.append(part.name)

        return result
