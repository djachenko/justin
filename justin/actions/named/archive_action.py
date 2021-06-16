from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from py_linq import Enumerable

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

        roots = [
            "justin",
            "photoclub",
            "closed",
        ]

        root_paths = [Path(root) for root in roots]

        def downstride_tree(tree: FolderTree, path: Path) -> Optional[FolderTree]:
            root = tree

            for component in path.parts:
                root = root[component]

                if root is None:
                    return None

            return root

        def get_count(path: Path) -> int:
            int_sum = Enumerable(photoset.parts) \
                .select(lambda part: downstride_tree(part.tree, path)) \
                .where(lambda e: e is not None) \
                .select(lambda tree: tree.file_count()) \
                .sum()

            return int_sum

        def get_biggest_tree(paths: List[Path]) -> Path:
            return sorted(paths, key=get_count, reverse=True)[0]

        primary_path = get_biggest_tree(root_paths)

        primary_destination_name = primary_path.name

        primary_destination = archive.get_destination(primary_destination_name)

        final_path = archive.path / primary_destination_name

        assert primary_destination is not None

        if primary_destination.has_categories:
            primary_category_name = Enumerable(photoset.parts) \
                .select(lambda part: downstride_tree(part.tree, primary_path)) \
                .where(lambda e: e is not None) \
                .select_many(lambda t: t.subtrees) \
                .group_by(key_names=["name"], key=lambda x: x.name) \
                .select(lambda g: (g.key.name, g.sum(lambda e: e.file_count()))) \
                .order_by_descending(lambda e: e[1]) \
                .first()[0]

            final_path /= primary_category_name

        print(f"Moving {photoset.name} to {final_path.relative_to(archive.path)}")

        photoset.move(path=final_path)

        archive.refresh()
