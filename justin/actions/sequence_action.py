from argparse import Namespace
from typing import List

from justin.actions.check_ratios_action import PatternAction
from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.models.exif import exif_sorted
from justin_utils.cli import Parameter


class SequenceAction(PatternAction):
    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(name="prefix", default=""),
            Parameter(name="start", default=0, type=int),
        ]

    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        prefix = args.prefix
        start = args.start

        files = exif_sorted(folder.files)
        files = [file.path for file in files]

        for index, file in enumerate(files, start=start):
            new_stem = f"{index:04}"

            if prefix:
                new_stem = f"{prefix}_{new_stem}"

            new_path = file.with_stem(new_stem)

            file.rename(new_path)
