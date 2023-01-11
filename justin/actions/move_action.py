from argparse import Namespace
from pathlib import Path
from typing import List

from justin.actions.pattern_action import Extra
from justin.actions.pattern_action import PatternAction
from justin.actions.stage.logic.base import Check
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.helpers.checks_runner import ChecksRunner
from justin.shared.models.photoset import Photoset
from justin_utils import util


class MoveAction(PatternAction):
    __SELECTED_LOCATION = "selected_location"

    def __init__(self, prechecks: List[Check], runner: ChecksRunner) -> None:
        super().__init__()

        self.__prechecks = prechecks
        self.__runner = runner

    def perform_for_pattern(self, paths: List[Path], args: Namespace, context: Context, extra: Extra) -> None:
        path = paths[0]
        world = context.world

        path_location = world.location_of_path(path)
        all_locations = world.get_locations()

        new_locations = [loc for loc in all_locations if loc != path_location]

        if len(new_locations) == 0:
            print("Current location is the only available.")

            # number of locations is global, photoset may have only one location -> other's can't be moved too
            return
        elif len(new_locations) == 1:
            selected_location = new_locations[0]
        else:
            selected_location = util.ask_for_choice(f"Where would you like to move {path.name}?", new_locations)

        extra[MoveAction.__SELECTED_LOCATION] = selected_location

        super().perform_for_pattern(paths, args, context, extra)

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        world = context.world

        path_location = world.location_of_path(path)
        selected_location = extra[MoveAction.__SELECTED_LOCATION]

        if selected_location == path_location:
            print(f"{path} is already there.")

            return

        photoset = Photoset.from_path(path)

        if photoset is not None:
            issues = self.__runner.run(photoset, self.__prechecks)

            if issues:
                print(f"Unable to move {photoset.name}:")

                for issue in issues:
                    print(issue)

                return

        new_path = selected_location / path.parent.relative_to(path_location.path)

        Folder(path).move(new_path)
