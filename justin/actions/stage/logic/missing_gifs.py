from typing import List, Iterable

from justin.actions.stage.logic.base import Extractor, Problem
from justin.shared.helpers.gif_maker import GifMaker
from justin.shared.helpers.parts import folder_tree_parts
from justin.actions.stage.logic.base import Selector
from justin.shared.models.photoset import Photoset


class MissingGifsSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        parts = folder_tree_parts(photoset.gif)

        result = []

        for part in parts:
            part_files = set([file.extension.lower().strip(" .") for file in part.files])

            if "gif" not in part_files:
                result.append(part.name)

        return result


class MissingGifsHandler(Extractor):
    def forward(self, photoset: Photoset) -> Iterable[Problem]:
        parts = folder_tree_parts(photoset.gif)

        parts_to_generate = self.selector.select(photoset)

        maker = GifMaker()

        for part_number, part in enumerate(parts, start=1):
            if part.name not in parts_to_generate:
                continue

            print(f"Generating gif for {part.path.relative_to(photoset.path.parent)}")

            if len(parts) == 1:
                name = f"{photoset.name}.gif"
            else:
                name = f"{photoset.name}_{part_number}.gif"

            maker.make_gif(part.path, name)

        return []

    def backwards(self, photoset: Photoset) -> Iterable[Problem]:
        return []
