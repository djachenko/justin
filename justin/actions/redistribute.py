from argparse import Namespace
from typing import List, Tuple

from justin.actions.move_action import MoveAction
from justin.shared.context import Context
from justin.shared.locations.locations_new import Location
from justin.shared.models.photoset import Photoset
from justin_utils.cli import Action


class RedistributeAction(Action):

    def __init__(self, move_action: MoveAction) -> None:
        super().__init__()

        self.__move_action = move_action

    def perform(self, args: Namespace, context: Context) -> None:
        world = context.world
        locations = world.find_locations()

        mapping: List[Tuple[Photoset, Location]] = []

        for location in locations:
            for set_ in location.sets():
                mapping.append((set_, location))

        mapping.sort(key=lambda x: x[0].date)
        locations.sort()

        locations_iter = iter(locations)

        active_location = next(locations_iter)
        sentinel = -42

        for set_, set_location in mapping:
            if set_location == active_location:
                continue

            if active_location.empty_space() < set_.total_size:
                active_location = next(locations_iter, __default=sentinel)

                if active_location == sentinel:
                    return

                if set_location == active_location:
                    continue

            self.__move_action.perform_for_photoset(set_, args, context, {
                MoveAction.SELECTED_LOCATION: active_location
            })
