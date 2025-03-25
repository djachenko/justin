from argparse import Namespace
from typing import List, Optional

from justin.actions.pattern_action import Context, Extra
from justin.actions.pattern_action import PatternAction
from justin.shared.filesystem import Folder
from justin.shared.filesystem import RelativeFileset, File
from justin.shared.helpers import photoset_utils
from justin.shared.helpers.utils import JpegType
from justin.shared.models.photoset import Photoset
from justin_utils import util
from justin_utils.cli import Parameter


class SplitAction(PatternAction):
    __PHOTOSET_ROOT_KEY = "photoset_root"

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("split_pattern", nargs="+"),
        ]

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        super().perform_for_photoset(photoset, args, context, extra | {
            SplitAction.__PHOTOSET_ROOT_KEY: photoset.path,
        })

        photoset.folder.refresh()

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        assert SplitAction.SET_NAME in extra
        assert SplitAction.__PHOTOSET_ROOT_KEY in extra

        print(f"Splitting {part.name}")

        split_patterns = args.split_pattern
        split_paths = list(util.resolve_patterns(split_patterns))
        split_files = [File(path) for path in split_paths]

        chosen_base = split_files
        not_chosen_files = [result for result in part.results if result not in chosen_base]

        chosen_stems = util.distinct([file.stem for file in chosen_base])
        not_chosen_stems = util.distinct(file.stem for file in not_chosen_files)

        stems_to_copy = []
        stems_to_move = []

        # выбранную базу двигаем
        # остальные не трогаем
        # selection and sources copy

        for stem in chosen_stems:
            if stem in not_chosen_stems:
                stems_to_copy.append(stem)
            else:
                stems_to_move.append(stem)

        files_to_move = photoset_utils.files_by_stems(stems_to_move, part, JpegType.SELECTION)
        files_to_move += chosen_base

        files_to_copy = photoset_utils.files_by_stems(stems_to_copy, part, JpegType.SELECTION)

        photoset_root = extra[SplitAction.__PHOTOSET_ROOT_KEY]
        photoset_name = extra[SplitAction.SET_NAME]

        fileset_to_move = RelativeFileset(photoset_root, files_to_move)
        fileset_to_copy = RelativeFileset(photoset_root, files_to_copy)

        outtakes_path = photoset_root.parent / (photoset_name + "_outtakes")

        fileset_to_move.move(outtakes_path)
        fileset_to_copy.copy(outtakes_path)
