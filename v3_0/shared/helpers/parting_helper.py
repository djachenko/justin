from typing import List

from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree


class PartingHelper:
    @staticmethod
    def is_part_name(name: str) -> bool:
        return name.split(".", maxsplit=1)[0].isdecimal()

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
