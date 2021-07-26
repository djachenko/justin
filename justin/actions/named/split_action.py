from argparse import Namespace
from typing import List, Optional, Dict

from justin_utils import util

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.shared.filesystem import FolderTree
from justin.shared.filesystem import RelativeFileset, File
from justin.shared.helpers import photoset_utils
from justin.shared.helpers.photoset_utils import JpegType
from justin.shared.models.photoset import Photoset


class SplitAction(NamedAction):
    __PHOTOSET_ROOT_KEY = "photoset_root"
    __PHOTOSET_NAME_KEY = "photoset_name"

    @staticmethod
    def flat_or_empty(tree: Optional[FolderTree]) -> List[File]:
        if tree is None:
            return []

        return tree.flatten()

    # todo: looks like shit, needs refactoring
    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        print("hello this is split")

        extra[SplitAction.__PHOTOSET_ROOT_KEY] = photoset.path
        extra[SplitAction.__PHOTOSET_NAME_KEY] = photoset.name

        super().perform_for_photoset(photoset, args, context, extra)

        photoset.tree.refresh()

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        assert SplitAction.__PHOTOSET_NAME_KEY in extra
        assert SplitAction.__PHOTOSET_ROOT_KEY in extra

        print(f"Splitting {part.name}")

        justin_full = SplitAction.flat_or_empty(part.justin)

        if part.justin is not None:
            justin_report = SplitAction.flat_or_empty(part.justin["report"])
            justin_unpublished = part.justin.files
        else:
            justin_report = []
            justin_unpublished = []

        justin_nonreport = list(set(justin_full).difference(justin_report))

        bases = {
            "All in justin": justin_full,
            "Justin except report": justin_nonreport,
            "Justin unpublished": justin_unpublished,
        }

        files_in_bases = set()
        files_in_bases.update(*bases.values())

        jpegs_not_in_bases = [jpeg for jpeg in part.results if jpeg not in files_in_bases]

        bases["Other"] = jpegs_not_in_bases

        bases: Dict[str, List[File]] = {k: v for k, v in bases.items() if v}

        choice_options = list(bases.keys())

        nothing_option = "Nothing"

        choice_options.append(nothing_option)

        chosen_key = util.ask_for_choice("Which base should be extracted?", choice_options)

        if chosen_key == nothing_option:
            return 

        chosen_base = bases[chosen_key]
        not_chosen_files = [result for result in part.results if result not in chosen_base]

        chosen_stems = util.distinct([file.stem() for file in chosen_base])
        not_chosen_stems = util.distinct(file.stem() for file in not_chosen_files)

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
        photoset_name = extra[SplitAction.__PHOTOSET_NAME_KEY]

        fileset_to_move = RelativeFileset(photoset_root, files_to_move)
        fileset_to_copy = RelativeFileset(photoset_root, files_to_copy)

        outtakes_path = photoset_root.parent / (photoset_name + "_outtakes")

        fileset_to_move.move(outtakes_path)
        fileset_to_copy.copy(outtakes_path)
