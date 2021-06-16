from typing import List

from justin.shared.filesystem import FolderTree


def is_part_name(name: str) -> bool:
    return name.split(".", maxsplit=1)[0].isdecimal()


def is_part(tree: FolderTree) -> bool:
    return is_part_name(tree.name)


def is_parted(tree: FolderTree) -> bool:
    return all([is_part(tree) for tree in tree.subtrees]) and len(tree.files) == 0


def folder_tree_parts(tree: FolderTree) -> List[FolderTree]:
    if tree is None:
        return []

    if is_parted(tree):
        return tree.subtrees
    else:
        return [tree]
