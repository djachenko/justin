from abc import abstractmethod
from typing import List

from justin.shared.filesystem import Folder


def is_part_name(name: str) -> bool:
    return name.split(".", maxsplit=1)[0].isdecimal()


def is_part(tree: Folder) -> bool:
    return is_part_name(tree.name)


def is_parted(tree: Folder) -> bool:
    if tree is None:
        return False

    return all([is_part(tree) for tree in tree.subfolders]) and len(tree.files) == 0


def folder_tree_parts(tree: Folder) -> List[Folder]:
    if tree is None:
        return []

    if is_parted(tree):
        return tree.subfolders
    else:
        return [tree]


class PartsMixin:
    # noinspection PyTypeChecker
    @property
    @abstractmethod
    def tree(self) -> Folder:
        assert False

    @property
    def is_parted(self) -> bool:
        return is_parted(self.tree)

    @property
    def parts(self) -> List[Folder]:
        if self.tree is None:
            return []

        if is_parted(self.tree):
            return self.tree.subfolders
        else:
            return [self.tree]
