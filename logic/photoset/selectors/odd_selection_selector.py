from typing import List

from v3_0.helpers import util
from v3_0.logic.selector import Selector
from v3_0.filesystem.movable import Movable
from v3_0.models.photoset import Photoset


class OddSelectionSelector(Selector):
    def source_folder(self, photoset: Photoset) -> str:
        return photoset.selection_folder_name

    def select(self, photoset: Photoset) -> List[Movable]:
        selection = photoset.selection
        results = photoset.results

        join = util.left_join(selection, results, lambda x: x.name_without_extension())

        return [i[0] for i in join if i[1] is None]
