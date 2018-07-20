from typing import List

import util
from logic.photoset.selectors.base_selector import BaseSelector
from models.movable import Movable
from models.photoset import Photoset


class OddSelectionSelector(BaseSelector):
    def source_folder(self, photoset: Photoset) -> str:
        return photoset.selection_folder_name

    def select(self, photoset: Photoset) -> List[Movable]:
        selection = photoset.selection
        results = photoset.results

        join = util.left_join(selection, results, lambda x: x.name_without_extension())

        return [i[0] for i in join if i[1] is None]
