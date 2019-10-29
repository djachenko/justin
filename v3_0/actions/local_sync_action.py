from argparse import Namespace
from pathlib import Path
from typing import Iterable

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.shared.metafiles.post_metafile import PostStatus
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class LocalSyncAction(Action):
    def __init__(self, all_published_action: Action) -> None:
        super().__init__()

        self.__all_published_action = all_published_action

    # noinspection PyMethodMayBeStatic
    def __tree_with_sets(self) -> FolderTree:
        # todo: won't work on Mac, need to move to generic location
        ready_path = Path("D:/photos/stages/stage3.schedule")
        # todo: stages_region[stage3.schedule]

        stage_tree = SingleFolderTree(ready_path)

        return stage_tree

    def __check_for_publishing(self, photosets: Iterable[Photoset], world: World, group: Group):
        paths_of_published_sets = []

        for photoset in photosets:
            metafile = photoset.get_metafile()

            post_metafiles = metafile.posts[group.url]

            if not all(post_metafile.status == PostStatus.PUBLISHED for post_metafile in post_metafiles):
                continue

            paths_of_published_sets.append(photoset.path)

        str_paths = [str(path.absolute()) for path in paths_of_published_sets]

        internal_args = Namespace(
            command="publish",
            name=str_paths
        )

        self.__all_published_action.perform(internal_args, world, group)

    def perform(self, args: Namespace, world: World, group: Group) -> None:
        stage_tree = self.__tree_with_sets()

        photosets = [Photoset(subtree) for subtree in stage_tree.subtrees]

        self.__check_for_publishing(photosets, world, group)
