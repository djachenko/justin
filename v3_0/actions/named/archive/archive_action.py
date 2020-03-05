from argparse import Namespace
from typing import List

from pyvko.models.group import Group

from v3_0.actions.named.named_action import NamedAction
from v3_0.shared.filesystem.folder_tree import FolderTree
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class ArchiveAction(NamedAction):
    @staticmethod
    def __get_biggest_tree(trees: List[FolderTree]) -> FolderTree:
        trees = [i for i in trees if i is not None]

        trees.sort(key=lambda d: len(d.flatten()), reverse=True)

        biggest_tree = trees[0]

        return biggest_tree

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, world: World, group: Group) -> None:
        archive = world.archive

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

        print(f"Moving {photoset.name} to {final_path.relative_to(archive.path)}")

        photoset.move(path=final_path)

        archive.refresh()
