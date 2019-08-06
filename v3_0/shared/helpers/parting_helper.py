from typing import List, Optional, Tuple

from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree


class PartingHelper:
    @staticmethod
    def __split_name(name) -> List[str]:
        return name.split(".", maxsplit=1)

    @staticmethod
    def number_and_name(part: FolderTree) -> Tuple[int, Optional[str]]:
        folder_name = part.name

        assert PartingHelper.is_part_name(folder_name)

        name_parts = PartingHelper.__split_name(folder_name)

        number = int(name_parts[0])

        if len(name_parts) > 1:
            name = name_parts[1]
        else:
            name = None

        return number, name

    @staticmethod
    def is_part_name(name: str) -> bool:
        return PartingHelper.__split_name(name)[0].isdecimal()

    @staticmethod
    def is_part(tree: FolderTree) -> bool:
        return PartingHelper.is_part_name(tree.name)

    @staticmethod
    def is_parted(tree: FolderTree) -> bool:
        return all([PartingHelper.is_part(tree) for tree in tree.subtrees]) and len(tree.files) == 0

    @staticmethod
    def folder_tree_parts(tree: FolderTree) -> List[FolderTree]:
        if tree is None:
            return []

        if PartingHelper.is_parted(tree):
            return tree.subtrees
        else:
            return [tree]
