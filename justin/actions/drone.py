from argparse import Namespace
from collections import defaultdict
from functools import lru_cache

from justin.actions.pattern_action import Extra
from justin.actions.pattern_action import PatternAction
from justin.shared.filesystem import Folder
from justin_utils.cli import Context


class PanoExtractAction(PatternAction):
    mapping = {
        0: [3, 19, ],
        1: [2, 10, 11, 18, 20, 27, 28, 35],  # 20 is sidelink
        2: [1, 9, 12, 17, 21, 26, 29, 34],  # 21 is sidelink
        3: [4, 8, 13, 16, 22, 25, 30, 33],  # 22 is sidelink
        4: [5, 7, 14, 15, 23, 24, 31, 32],
        5: [6, ]
    }

    @property
    @lru_cache
    def reverse_mapping(self) -> dict:
        reverse_mapping = {}

        for row, row_members in PanoExtractAction.mapping.items():
            for member in row_members:
                reverse_mapping[member] = row

        return reverse_mapping

    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        if len(folder.files) != 35:
            return

        for index, file in enumerate(folder.files, start=1):
            file_row = PanoExtractAction.reverse_mapping[index]

            subfolder = folder / f"row_{file_row}"

            subfolder.mkdir()

            file.move(subfolder.path)


class JpgDngDuplicatesAction(PatternAction):
    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        buckets = defaultdict(lambda: [])

        for item in folder.files:
            buckets[item.stem].append(item.suffix.lower())

        for stem, bucket in buckets.items():
            if ".dng" in bucket and ".jpg" in bucket:
                jpg_path = (folder.path / stem).with_suffix(".jpg")

                jpg_path.unlink()


class HandleDroneAction(PatternAction):
    def __init__(self, pano_action: PanoExtractAction, duplicate_action: JpgDngDuplicatesAction) -> None:
        super().__init__()

        self.__pano_action = pano_action
        self.__duplicate_action = duplicate_action

    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        self.__duplicate_action.perform_for_folder(folder / "100MEDIA", args, context, extra)

        for pano_folder in (folder / "PANORAMA").subfolders:
            self.__pano_action.perform_for_folder(pano_folder, args, context, extra)
