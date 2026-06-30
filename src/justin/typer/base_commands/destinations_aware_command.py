from justin.actions.pattern_action import Extra
from justin.shared.filesystem import Folder
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.models.photoset import Photoset
from justin.typer.base_commands.pattern_command import PatternCommand


class DestinationsAwareCommand(PatternCommand):
    def run_for_part(self, part: Photoset, extra: Extra) -> None:
        destinations = [
            (part.closed, self.handle_closed),
            (part.cullen, self.handle_cullen),
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

            handler(destination, extra)

    def handle_closed(self, closed_folder: Folder, extra: Extra) -> None:
        self.handle_common(closed_folder, extra)

    def handle_drive(self, drive_folder: Folder, extra: Extra) -> None:
        self.handle_common(drive_folder, extra)

    def handle_justin(self, justin_folder: Folder, extra: Extra) -> None:
        self.handle_common(justin_folder, extra)

    def handle_kot_i_kit(self, kot_i_kit_folder: Folder, extra: Extra) -> None:
        self.handle_common(kot_i_kit_folder, extra)

    def handle_meeting(self, meeting_folder: Folder, extra: Extra) -> None:
        self.handle_common(meeting_folder, extra)

    def handle_my_people(self, my_people_folder: Folder, extra: Extra) -> None:
        self.handle_common(my_people_folder, extra)

    def handle_timelapse(self, timelapse_folder: Folder, extra: Extra) -> None:
        self.handle_common(timelapse_folder, extra)

    def handle_cullen(self, cullen_folder: Folder, extra: Extra) -> None:
        self.handle_common(cullen_folder, extra)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def handle_common(self, folder: Folder, extra: Extra) -> None:
        raise NotImplementedError(f"{type(self).__name__} must implement handle_common")

    def handle_tagged_folder(self, tagged_folder: Folder, extra: Extra) -> None:
        for tag_folder in tagged_folder.subfolders:
            for tag_part_folder in folder_tree_parts(tag_folder):
                self.handle_tag_part(tag_part_folder, extra)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def handle_tag_part(self, tag_part_folder: Folder, extra: Extra) -> None:
        raise NotImplementedError(f"{type(self).__name__} must implement handle_tag_part")
