from typing import List

from v3_0.helpers.parting_helper import PartingHelper
from v3_0.logic.base.selector import Selector
from v3_0.models.photoset import Photoset


class MissingGifsSelector(Selector):
    def source_folder(self, photoset: Photoset) -> str:
        pass

    def select(self, photoset: Photoset) -> List[str]:
        parts = PartingHelper.folder_tree_parts(photoset.gif)

        result = []

        for part in parts:
            part_files = set([file.extension.lower().strip(" .") for file in part.files])

            if "gif" not in part_files:
                result.append(part.name)

        return result
