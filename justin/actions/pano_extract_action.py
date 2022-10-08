from argparse import Namespace
from pathlib import Path

from justin.actions.pattern_action import Extra
from justin.actions.pattern_action import PatternAction
from justin_utils.cli import Context


class PanoExtractAction(PatternAction):
    mapping = {
        0: [3, 19, ],
        1: [2, 10, 11, 18, 20, 27, 28, 35],
        2: [1, 9, 12, 17, 21, 26, 29, 34],
        3: [4, 8, 13, 16, 22, 25, 30, 33],
        4: [5, 7, 14, 15, 23, 24, 31, 32],
        5: [6, ]
    }

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        reverse_mapping = {}

        for row, row_members in PanoExtractAction.mapping.items():
            for member in row_members:
                reverse_mapping[member] = row

        for index, file in enumerate(filter(lambda x: x.is_file(), sorted(path.iterdir())), start=1):
            file_row = reverse_mapping[index]

            subfolder = path / f"row_{file_row}"

            subfolder.mkdir(exist_ok=True)

            file.rename(subfolder / file.name)
