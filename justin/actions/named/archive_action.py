from argparse import Namespace
from typing import List

from justin_utils.multiplexer import Multiplexer

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.shared.filesystem import FolderTree
from justin.shared.models.photoset import Photoset


# todo: may be reduced to stage
class ArchiveAction(NamedAction):
    @staticmethod
    def __get_biggest_tree(trees: List[FolderTree]) -> FolderTree:
        trees = [i for i in trees if i is not None]

        trees.sort(key=lambda d: d.file_count(), reverse=True)

        biggest_tree = trees[0]

        return biggest_tree

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        world = context.world
        archive = world.archive

        multiplexer = Multiplexer(photoset.parts)

        primary_destination_tree = self.__get_biggest_tree([
            multiplexer.justin,
            multiplexer.photoclub,
            multiplexer.closed
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
