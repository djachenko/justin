from v3_0.actions.stage.logic.base.extractor import Extractor
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.shared.models.photoset import Photoset


class PartsRenumberingHandler(Extractor):
    def forward(self, photoset: Photoset) -> bool:
        if not PartingHelper.is_parted(photoset.tree):
            return True

        parts = PartingHelper.folder_tree_parts(photoset.tree)

        number_strings = []

        for part in parts:
            name_parts = part.name.split(".", maxsplit=1)

            number_part = name_parts[0]

            number_strings.append(number_part)

        longest_number = max(len(string) for string in number_strings)

        for part in parts:
            name_parts = part.name.split(".", maxsplit=1)

            number_part = name_parts[0]

            while len(number_part) < longest_number:
                number_part = "0" + number_part

            name_parts[0] = number_part

            new_name = ".".join(name_parts)

            new_part_path = part.path.with_name(new_name)

            part.path.rename(new_part_path)

        return True
