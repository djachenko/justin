from argparse import Namespace
from typing import List

from justin.actions.pattern_action import PatternAction, Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.metafiles.metafile import LocationMetafile
from justin_utils.cli import Parameter


def is_location(folder: Folder):
    return LocationMetafile.has(folder)


class LocationAction(PatternAction):

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("--touch", action=Parameter.Action.STORE_TRUE),
        ]

    @staticmethod
    def __touch_location(folder: Folder) -> None:
        if is_location(folder):
            print("Already location.")

            return

        if folder.name != "photos":
            print("Location must be names photos.")

            return

        for parent in folder.path.parents:
            meta_parent = Folder.from_path(parent)

            print(meta_parent.path)

            if is_location(meta_parent):
                print(f"Unable to touch location at {folder.path} inside location {parent}")

                return

        queue = [(folder, 0)]

        while queue:
            candidate, depth = queue.pop(0)

            print(candidate.path)

            if is_location(candidate):
                print(f"Unable to touch location at {folder.path} with inner location {candidate.path}")

                return

            if depth <= 10:
                queue += [(subfolder, depth + 1) for subfolder in candidate.subfolders]

        location_name = ""

        while not location_name:
            location_name = input("Enter location name: ")

        if location_name == "-":
            return

        location_description = input("Enter location description: ")

        metafile = LocationMetafile(
            location_name=location_name,
            location_description=location_description,
            location_order=0
        )

        metafile.save(folder)

    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        if args.touch:
            self.__touch_location(folder)
        else:
            print("And what?")
