from typing import List

from v3_0.actions.archive.archive import Archive
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.helpers.singleton import Singleton
from v3_0.shared.models.photoset import Photoset


class ArchiveAdder(Singleton):
    @staticmethod
    def __get_biggest_tree(trees: List[FolderTree]) -> FolderTree:
        trees = [i for i in trees if i is not None]

        trees.sort(key=lambda d: len(d.flatten()), reverse=True)

        biggest_tree = trees[0]

        return biggest_tree

    def add(self, photoset: Photoset, archive: Archive):
        primary_destination_tree = self.__get_biggest_tree([
            photoset.justin,
            photoset.photoclub,
            photoset.closed
        ])

        primary_destination_name = primary_destination_tree.name

        primary_destination = archive.get_destination(primary_destination_name)

        final_path = archive.path / primary_destination_name

        assert primary_destination is not None

        if primary_destination.has_categories:
            primary_category_name = self.__get_biggest_tree(primary_destination_tree.subtrees).name

            final_path /= primary_category_name

        photoset.move(path=final_path)
