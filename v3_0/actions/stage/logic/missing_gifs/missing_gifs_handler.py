from v3_0.actions.stage.helpers.gif_maker import GifMaker
from v3_0.shared.filesystem.file import File
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.actions.stage.logic.base.extractor import Extractor
from v3_0.shared.models.photoset import Photoset


class MissingGifsHandler(Extractor):
    def forward(self, photoset: Photoset) -> bool:
        parts_to_generate = self.selector.select(photoset)

        maker = GifMaker()

        for part_number, part_name in enumerate(parts_to_generate, start=1):
            part = photoset.tree[part_name]

            print(f"Generating gif for {part.path.relative_to(photoset.path.parent)}")

            if len(parts_to_generate) == 1:
                name = f"{photoset.name}.gif"
            else:
                name = f"{photoset.name}_{part_number}.gif"

            maker.make_gif(part.path, name)

        return True

    def backwards(self, photoset: Photoset) -> bool:
        parts = PartingHelper.folder_tree_parts(photoset.gif)

        for part in parts:
            for file in part.files:
                if file.extension == ".gifs":
                    File.remove(file.path)

        return True
