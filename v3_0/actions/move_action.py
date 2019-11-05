from argparse import Namespace
from pathlib import Path
from typing import List

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.actions.checks_runner import ChecksRunner
from v3_0.actions.stage.exceptions.check_failed_error import CheckFailedError
from v3_0.actions.stage.logic.base.check import Check
from v3_0.shared.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.shared.helpers import util
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class MoveAction(Action):

    def __init__(self, prechecks: List[Check]) -> None:
        super().__init__()

        self.__prechecks = prechecks

    def perform(self, args: Namespace, world: World, group: Group) -> None:
        all_locations = world.all_locations

        for path in util.resolve_patterns(args.name):
            photoset = Photoset(SingleFolderTree(path))

            try:
                ChecksRunner.instance().run(photoset, self.__prechecks)

                photoset_location = world.location_of_path(photoset.path)

                new_locations = [loc for loc in all_locations if loc != photoset_location]

                if len(new_locations) == 0:
                    print("Current location is the only available.")

                    continue

                chosen_location = ask_for_choice("Where would you like to move photoset?", new_locations)

                print(chosen_location)
                print(photoset.path.parent)
                print(photoset.path.parent.relative_to(photoset_location))

                new_path = chosen_location / photoset.path.parent.relative_to(photoset_location)

                photoset.move(new_path)

            except CheckFailedError as error:
                print(f"Unable to move {photoset.name}: {error}")
