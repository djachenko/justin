from typing import List

from v3_0.archive.archive import Archive
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.models.photoset import Photoset


class ArchiveAdder:
    def __get_biggest_tree(self, trees: List[FolderTree]) -> FolderTree:
        trees = [i for i in trees if i is not None]

        trees.sort(key=lambda d: len(d.flatten), reverse=True)

        biggest_tree = trees[0]

        return biggest_tree

    def __get_destination_name(self, photoset: Photoset):
        possible_destinations = [
            photoset.justin,
            photoset.photoclub,
            photoset.closed,
        ]

        possible_destinations = [i for i in possible_destinations if i is not None]

        possible_destinations.sort(key=lambda d: len(d.flatten), reverse=True)

        primary_destination_tree = possible_destinations[0]

        primary_destination_name = primary_destination_tree.name

        return primary_destination_name


    def __get_category_name(self, photoset: Photoset):
        possible_categories =


    def add(self, photoset: Photoset, archive: Archive):
        primary_destination_tree = self.__get_biggest_tree([
                photoset.justin,
                photoset.photoclub,
                photoset.closed
            ])

        primary_destination_name = primary_destination_tree.name

        primary_destination = archive.get_destination(primary_destination_name)

        assert primary_destination is not None

        final_place = primary_destination

        if primary_destination.has_categories:
            primary_category_tree = self.__get_biggest_tree(primary_destination_tree.subtrees)

            primary_category_name = primary_category_tree.name

            primary_category = primary_destination.get_category(primary_category_name)

            assert primary_category is not None

            final_place = primary_category

        final_path = final_place.path

        photoset.move(path=final_path)


