from argparse import Namespace

from justin.actions.pattern_action import Extra
from justin.actions.pattern_action import PatternAction
from justin.shared.context import Context
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import MetaFolder
from justin.shared.models.photoset import Photoset


class DestinationsAwareAction(PatternAction):
    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        destinations = [
            (part.closed, self.handle_closed),
            (part.drive, self.handle_drive),
            (part.justin, self.handle_justin),
            (part.kot_i_kit, self.handle_kot_i_kit),
            (part.meeting, self.handle_meeting),
            (part.my_people, self.handle_my_people),
            (part.timelapse, self.handle_timelapse),
        ]

        for destination, handler in destinations:
            if destination is None:
                continue

            handler(destination, context, extra)

    def handle_closed(self, closed_folder: MetaFolder, context: Context, extra: Extra) -> None:
        self.handle_common(closed_folder, context, extra)

    def handle_drive(self, drive_folder: MetaFolder, context: Context, extra: Extra) -> None:
        self.handle_common(drive_folder, context, extra)

    def handle_justin(self, justin_folder: MetaFolder, context: Context, extra: Extra) -> None:
        self.handle_common(justin_folder, context, extra)

    def handle_kot_i_kit(self, kot_i_kit_folder: MetaFolder, context: Context, extra: Extra) -> None:
        self.handle_common(kot_i_kit_folder, context, extra)

    def handle_meeting(self, meeting_folder: MetaFolder, context: Context, extra: Extra) -> None:
        self.handle_common(meeting_folder, context, extra)

    def handle_my_people(self, my_people_folder: MetaFolder, context: Context, extra: Extra) -> None:
        self.handle_common(my_people_folder, context, extra)

    def handle_timelapse(self, timelapse_folder: MetaFolder, context: Context, extra: Extra) -> None:
        self.handle_common(timelapse_folder, context, extra)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def handle_common(self, folder: MetaFolder, context: Context, extra: Extra) -> None:
        assert False

    def handle_tagged_folder(self, tagged_folder: MetaFolder, context: Context, extra: Extra) -> None:
        for tag_folder in tagged_folder.subfolders:
            for tag_part_folder in folder_tree_parts(tag_folder):
                self.handle_tag_part(tag_part_folder, context, extra)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def handle_tag_part(self, tag_part_folder: MetaFolder, context: Context, extra: Extra) -> None:
        assert False
