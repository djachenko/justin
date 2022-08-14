from argparse import Namespace

from justin.actions.named.named_action import Extra
from justin.actions.pattern_action import PatternAction
from justin.shared.context import Context
from justin.shared.filesystem import FolderTree
from justin.shared.models.photoset import Photoset


class DestinationsAwareAction(PatternAction):
    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        destinations = [
            (part.justin, self.handle_justin),
            (part.closed, self.handle_closed),
            (part.meeting, self.handle_meeting),
            (part.kot_i_kit, self.handle_kot_i_kit),
            (part.my_people, self.handle_my_people),
        ]

        for destination, handler in destinations:
            if destination is None:
                continue

            handler(destination, context, extra)

    def handle_justin(self, justin_folder: FolderTree, context: Context, extra: Extra) -> None:
        self.handle_common(justin_folder, context, extra)

    def handle_closed(self, closed_folder: FolderTree, context: Context, extra: Extra) -> None:
        self.handle_common(closed_folder, context, extra)

    def handle_meeting(self, meeting_folder: FolderTree, context: Context, extra: Extra) -> None:
        self.handle_common(meeting_folder, context, extra)

    def handle_kot_i_kit(self, kot_i_kit_folder: FolderTree, context: Context, extra: Extra) -> None:
        self.handle_common(kot_i_kit_folder, context, extra)

    def handle_my_people(self, my_people_folder: FolderTree, context: Context, extra: Extra) -> None:
        self.handle_common(my_people_folder, context, extra)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def handle_common(self, folder: FolderTree, context: Context, extra: Extra) -> None:
        assert False
