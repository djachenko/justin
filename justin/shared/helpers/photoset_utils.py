from enum import Flag, auto
from typing import Iterable, Tuple, Any, List

from justin_utils import util, joins

from justin.actions.named.stage.exceptions.no_files_for_name_error import NoFilesForNameError
from justin.shared.filesystem import PathBased
from justin.shared.models.photoset import Photoset


def __validate_join(join: Iterable[Tuple[str, Any]], name: str):
    names_of_unjoined_files = []

    for source_name, source in join:
        if source is None:
            names_of_unjoined_files.append(source_name)

    if names_of_unjoined_files:
        unjoined_files_names_string = ", ".join(names_of_unjoined_files)

        raise NoFilesForNameError(f"Failed join for {name}: {unjoined_files_names_string}")


class JpegType(Flag):
    SELECTION = auto()
    JUSTIN = auto()
    MEETING = auto()
    KOT_I_KIT = auto()
    OUR_PEOPLE = auto()
    CLOSED = auto()
    PHOTOCLUB = auto()
    SIGNED = JUSTIN | OUR_PEOPLE | CLOSED | PHOTOCLUB | MEETING | KOT_I_KIT
    ALL = SELECTION | SIGNED


def files_by_stems(stems: Iterable[str], photoset: Photoset, jpeg_types: JpegType = None) -> List[PathBased]:
    if jpeg_types is None:
        jpeg_types = JpegType.ALL

    jpeg_trees = []

    mapping = {
        JpegType.JUSTIN: photoset.justin,
        JpegType.OUR_PEOPLE: photoset.our_people,
        JpegType.CLOSED: photoset.closed,
        JpegType.PHOTOCLUB: photoset.photoclub,
        JpegType.MEETING: photoset.meeting,
        JpegType.KOT_I_KIT: photoset.kot_i_kit,
    }

    for t, tree in mapping.items():
        if t in jpeg_types and tree is not None:
            jpeg_trees.append(tree)

    jpegs_lists = [tree.flatten() for tree in jpeg_trees]

    if JpegType.SELECTION in jpeg_types and photoset.selection is not None:
        jpegs_lists.append(photoset.selection)

    jpegs_join = joins.left(
        stems,
        util.flatten(jpegs_lists),
        lambda s, f: s == f.stem()
    )

    __validate_join(jpegs_join, "jpegs")

    sources_join = list(joins.left(
        stems,
        photoset.sources,
        lambda s, f: s == f.stem()
    ))

    __validate_join(sources_join, "sources")

    jpegs_to_move = [jpeg for _, jpeg in jpegs_join]
    sources_contents_to_move = util.flatten(source.files() for _, source in sources_join)

    files_to_move = jpegs_to_move + sources_contents_to_move

    return files_to_move
