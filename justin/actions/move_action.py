from argparse import Namespace
from pathlib import Path
from typing import List

from justin.actions.named.named_action import Extra
from justin.actions.named.stage.exceptions.check_failed_error import CheckFailedError
from justin.actions.named.stage.logic.base import Check
from justin.actions.pattern_action import PatternAction
from justin.shared.context import Context
from justin.shared.helpers.checks_runner import ChecksRunner
from justin.shared.models.photoset import Photoset
from justin_utils import util


class MoveAction(PatternAction):
    __SELECTED_LOCATION = "selected_location"

    def __init__(self, prechecks: List[Check]) -> None:
        super().__init__()

        self.__prechecks = prechecks

    def perform_for_pattern(self, paths: List[Path], args: Namespace, context: Context, extra: Extra) -> None:
        path = paths[0]
        world = context.world

        path_location = world.location_of_path(path)
        all_locations = world.all_locations

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

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        world = context.world

        from_location = world.location_of_path(photoset.path)
        selected_location = extra[MoveAction.__SELECTED_LOCATION]

        if selected_location == from_location:
            print(f"{photoset.name} is already there.")

            return

        try:
            ChecksRunner.instance().run(photoset, self.__prechecks)

            new_path = selected_location / photoset.path.parent.relative_to(from_location)

            photoset.move(new_path)

        except CheckFailedError as error:
            print(f"Unable to move {photoset.name}: {error}")
