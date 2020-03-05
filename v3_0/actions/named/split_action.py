from argparse import Namespace
from typing import List, Optional, Dict

from pyvko.models.group import Group

from v3_0.actions.named.named_action import NamedAction
from v3_0.shared.filesystem.file import File
from v3_0.shared.filesystem.folder_tree import FolderTree
from v3_0.shared.filesystem.relative_fileset import RelativeFileset
from v3_0.shared.helpers import util, photoset_utils
from v3_0.shared.helpers.photoset_utils import JpegType
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class SplitAction(NamedAction):

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, world: World, group: Group) -> None:
        def flat_or_empty(tree: Optional[FolderTree]) -> List[File]:
            if tree is None:
                return []

            return tree.flatten()

        justin_full = flat_or_empty(photoset.justin)

        if photoset.justin is not None:
            justin_report = flat_or_empty(photoset.justin["report"])
            justin_unpublished = photoset.justin.files
        else:
            justin_report = []
            justin_unpublished = []

        justin_nonreport = list(set(justin_full).difference(justin_report))

        bases = {
            "All in justin": justin_full,
            "Justin except report": justin_nonreport,
            "Justin unpublished": justin_unpublished,
            "Closed": flat_or_empty(photoset.closed),
            "Our people": flat_or_empty(photoset.our_people),
        }

        files_in_bases = set()
        files_in_bases.update(*bases.values())

        jpegs_not_in_bases = [jpeg for jpeg in photoset.results if jpeg not in files_in_bases]

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

        files_to_move = photoset_utils.files_by_stems(stems_to_move, photoset)
        files_to_move += chosen_base

        fileset_to_move = RelativeFileset(photoset.path, files_to_move)

        files_to_copy = photoset_utils.files_by_stems(stems_to_copy, photoset, JpegType.SELECTION)
        fileset_to_copy = RelativeFileset(photoset.path, files_to_copy)

        outtakes_path = photoset.path / ".." / (photoset.name + "_outtakes")

        fileset_to_move.move(outtakes_path)
        fileset_to_copy.copy(outtakes_path)

        photoset.tree.refresh()
