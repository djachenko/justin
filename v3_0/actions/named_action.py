from abc import abstractmethod
from argparse import Namespace

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.shared.filesystem.folder_tree import FolderTree
from v3_0.shared.helpers import util
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class NamedAction(Action):
    def perform(self, args: Namespace, world: World, group: Group) -> None:
        if not any(util.resolve_patterns(args.name)):
            print("No items found for that pattern.")

        for path in util.resolve_patterns(args.name):
            photoset = Photoset(FolderTree(path))

            self.perform_for_photoset(photoset, args, world, group)

    @abstractmethod
    def perform_for_photoset(self, photoset: Photoset, args: Namespace, world: World, group: Group) -> None:
        pass
