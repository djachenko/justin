from argparse import Namespace

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.actions.archive.archive_adder import ArchiveAdder
from v3_0.shared.filesystem.folder_tree import FolderTree
from v3_0.shared.helpers import util
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class ArchiveAction(Action):
    def perform(self, args: Namespace, world: World, group: Group) -> None:
        adder = ArchiveAdder.instance()
        archive = world.archive

        for path in util.resolve_patterns(args.name):
            photoset = Photoset(FolderTree(path))

            adder.add(photoset, archive)
