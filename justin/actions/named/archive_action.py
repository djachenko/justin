from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from justin_utils.pylinq import Sequence

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
            "meeting",
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
            int_sum = Sequence(photoset.parts) \
                .map(lambda part: downstride_tree(part.tree, path)) \
                .filter(lambda e: e is not None) \
                .map(lambda tree: tree.file_count()) \
                .sum()

            return int_sum

        def get_biggest_tree(paths: List[Path]) -> Path:
            return sorted(paths, key=get_count, reverse=True)[0]

        primary_path = get_biggest_tree(root_paths)

        primary_destination_name = primary_path.name

        primary_destination = archive.get_destination(primary_destination_name)

        final_path = archive.path / primary_destination_name

        assert primary_destination is not None

        print(f"Moving {photoset.name} to {final_path.relative_to(archive.path)}")

        if primary_destination.has_categories:
            primary_category_name = Sequence(photoset.parts)\
                .map(lambda part: downstride_tree(part.tree, primary_path)) \
                .cache() \
                .filter(lambda e: e is not None) \
                .flat_map(lambda t: t.subtrees) \
                .group_by(lambda x: x.name) \
                .map(lambda t: (t[0], t[1].map(lambda e: e.file_count()).sum())) \
                .max(lambda e: e[1])[0]

            final_path /= primary_category_name

            print(f"Moving {photoset.name} to {final_path.relative_to(archive.path)}")

        photoset.move(path=final_path)

        archive.refresh()
