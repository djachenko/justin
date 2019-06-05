from typing import List

from v3_0.filesystem.folder_tree.folder_tree import FolderTree


class PartingHelper:
    @staticmethod
    def folder_tree_parts(tree: FolderTree) -> List[FolderTree]:
        if tree is None:
            return []

        subtrees_names = tree.subtree_names

        def is_part(name: str) -> bool:
            return name.split(".", maxsplit=1)[0].isdecimal()

        is_parted = all([is_part(name) for name in subtrees_names])

        if is_parted:
            return tree.subtrees
        else:
            return [tree]
