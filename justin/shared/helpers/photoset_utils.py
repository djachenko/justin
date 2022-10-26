from typing import Iterable, List

from justin.shared.filesystem import PathBased, File
from justin.shared.helpers.utils import __validate_join, JpegType
from justin.shared.metafile import MetaFolder
from justin.shared.models.photoset import Photoset
from justin_utils import joins, util


def files_by_stems(stems: Iterable[str], photoset: Photoset, jpeg_types: JpegType = None) -> List[PathBased]:
    if jpeg_types is None:
        jpeg_types = JpegType.ALL

    jpeg_trees = []

    mapping = {
        JpegType.JUSTIN: photoset.justin,
        JpegType.MY_PEOPLE: photoset.my_people,
        JpegType.CLOSED: photoset.closed,
        JpegType.PHOTOCLUB: photoset.photoclub,
        JpegType.MEETING: photoset.meeting,
        JpegType.KOT_I_KIT: photoset.kot_i_kit,
    }

    for t, tree in mapping.items():
        if t in jpeg_types and tree is not None:
            jpeg_trees.append(tree)

    jpegs_lists = [tree.flatten() for tree in jpeg_trees]

    if JpegType.SELECTION in jpeg_types and photoset.not_signed is not None:
        jpegs_lists.append(photoset.not_signed)

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

    jpegs_set = set(jpegs_to_move)

    def collect_metafiles(tree_: MetaFolder):
        result = []

        if jpegs_set.issuperset(tree_.flatten()):
            result.append(tree_.metafile_path)

        for subtree in tree_.subfolders:
            result += collect_metafiles(subtree)

        return result

    metafile_paths = util.flatten(collect_metafiles(tree) for tree in jpeg_trees)
    metafiles = [File(path) for path in metafile_paths if path.exists()]

    files_to_move = jpegs_to_move + sources_contents_to_move + metafiles

    return files_to_move
