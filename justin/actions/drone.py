from argparse import Namespace
from collections import defaultdict
from pathlib import Path

from justin.actions.pattern_action import Extra
from justin.actions.pattern_action import PatternAction
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

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        if len([item for item in path.iterdir() if item.is_file()]) != 35:
            return

        reverse_mapping = {}

        for row, row_members in PanoExtractAction.mapping.items():
            for member in row_members:
                reverse_mapping[member] = row

        for index, file in enumerate(filter(lambda x: x.is_file(), sorted(path.iterdir())), start=1):
            file_row = reverse_mapping[index]

            subfolder = path / f"row_{file_row}"

            subfolder.mkdir(exist_ok=True)

            file.rename(subfolder / file.name)


class JpgDngDuplicatesAction(PatternAction):
    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        buckets = defaultdict(lambda: [])

        for item in path.iterdir():
            assert not item.is_dir()

            buckets[item.stem].append(item.suffix.lower())

        for stem, bucket in buckets.items():
            if ".dng" in bucket and ".jpg" in bucket:
                jpg_path = (path / stem).with_suffix(".jpg")

                jpg_path.unlink()


class HandleDroneAction(PatternAction):
    def __init__(self, pano_action: PanoExtractAction, duplicate_action: JpgDngDuplicatesAction) -> None:
        super().__init__()

        self.__pano_action = pano_action
        self.__duplicate_action = duplicate_action

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        self.__duplicate_action.perform_for_path(path / "100MEDIA", args, context, extra)

        for pano_folder in (path / "PANORAMA").iterdir():
            if not pano_folder.is_dir():
                continue

            self.__pano_action.perform_for_path(pano_folder, args, context, extra)
