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
    # todo: looks like shit, needs refactoring
    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Optional[Extra])\
            -> None:
        def flat_or_empty(tree: Optional[FolderTree]) -> List[File]:
            if tree is None:
                return []

            return tree.flatten()

        for part in photoset.parts:
            justin_full = flat_or_empty(part.justin)

            if part.justin is not None:
                justin_report = flat_or_empty(part.justin["report"])
                justin_unpublished = part.justin.files
            else:
                justin_report = []
                justin_unpublished = []

            justin_nonreport = list(set(justin_full).difference(justin_report))

            bases = {
                "All in justin": justin_full,
                "Justin except report": justin_nonreport,
                "Justin unpublished": justin_unpublished,
                "Closed": flat_or_empty(part.closed),
                "Our people": flat_or_empty(part.our_people),
            }

            files_in_bases = set()
            files_in_bases.update(*bases.values())

            jpegs_not_in_bases = [jpeg for jpeg in part.results if jpeg not in files_in_bases]

            bases["Other"] = jpegs_not_in_bases

            bases: Dict[str, List[File]] = {k: v for k, v in bases.items() if v}

            chosen_key = util.ask_for_choice("Which base should be extracted?", list(bases.keys()))

            chosen_base = bases[chosen_key]
            not_chosen_bases = [bases[key] for key in bases if key != chosen_key]
            not_chosen_files = util.flatten(not_chosen_bases)
            not_chosen_files = list(set(not_chosen_files).difference(chosen_base))

            chosen_stems = [file.stem() for file in chosen_base]
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

            files_to_move = photoset_utils.files_by_stems(stems_to_move, part)
            files_to_move += chosen_base

            fileset_to_move = RelativeFileset(photoset.path, files_to_move)

            files_to_copy = photoset_utils.files_by_stems(stems_to_copy, part, JpegType.SELECTION)
            fileset_to_copy = RelativeFileset(photoset.path, files_to_copy)

            outtakes_path = photoset.path / ".." / (photoset.name + "_outtakes")

            fileset_to_move.move(outtakes_path)
            fileset_to_copy.copy(outtakes_path)

        photoset.tree.refresh()
