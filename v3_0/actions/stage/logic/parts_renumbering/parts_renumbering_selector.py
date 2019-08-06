from typing import List

from v3_0.actions.stage.logic.base.selector import Selector
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.shared.models.photoset import Photoset


class PartsRenumberingSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        if not PartingHelper.is_parted(photoset.tree):
            return []

        parts = PartingHelper.folder_tree_parts(photoset.tree)

        parts_number_strings = [part.name.split(".", maxsplit=1)[0] for part in parts]
        numbers_lengths = [len(number) for number in parts_number_strings]

        if len(set(numbers_lengths)) == 1:
            return []

        return [str(part.path) for part in parts]
