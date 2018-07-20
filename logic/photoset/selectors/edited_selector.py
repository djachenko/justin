from typing import List

import util
from logic.photoset.selectors.base_selector import BaseSelector
from models.movable import Movable
from models.photoset import Photoset


class EditedSelector(BaseSelector):

    def source_folder(self, photoset: Photoset) -> str:
        return photoset.sources_folder_name

    def select(self, photoset: Photoset) -> List[Movable]:
        results = photoset.results
        sources = photoset.sources

        join = util.left_join(
            results,
            sources,
            lambda result: result.name_without_extension(),
            lambda source: source.name
        )

        results = [i[1] for i in join]

        unique_results = list(set(results))

        return unique_results
