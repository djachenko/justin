from typing import List

from justin_utils import util

from justin.actions.named.stage.logic.base import Check
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, PhotosetMetafile, PostStatus
from justin.shared.models.photoset import Photoset


class MetafileStateCheck(Check):
    def __init__(self) -> None:
        super().__init__("metafile check")

    @staticmethod
    def __metafile_required(photoset: Photoset) -> bool:
        return photoset.justin is not None

    @staticmethod
    def __metafile_has_no_group_entries(photoset_metafile: PhotosetMetafile) -> bool:
        return len(photoset_metafile.posts) == 0

    @staticmethod
    def __group_entry_has_no_post_entries(post_metafiles: List[PostMetafile]) -> bool:
        return len(post_metafiles) == 0

    @staticmethod
    def __metafile_has_not_published_entries(post_metafiles: List[PostMetafile]) -> bool:
        return any(post_metafile.status != PostStatus.PUBLISHED for post_metafile in post_metafiles)

    @staticmethod
    def __photoset_has_folders_not_in_metafile(photoset: Photoset, post_metafiles: List[PostMetafile]) -> bool:
        posted_paths = {post_metafile.path for post_metafile in post_metafiles}

        subtrees_parts = util.flatten([
            util.flatten([folder_tree_parts(tag_subtree) for tag_subtree in photoset.justin.subtrees]),
            util.flatten([folder_tree_parts(name_subtree) for name_subtree in photoset.closed.subtrees]),
            # todo: meeting
        ])

        relative_paths = [part.path.relative_to(photoset.path) for part in subtrees_parts]

        return any(path not in posted_paths for path in relative_paths)

    def is_good(self, photoset: Photoset) -> bool:
        if not MetafileStateCheck.__metafile_required(photoset):
            return True

        if not photoset.has_metafile():
            return False

        photoset_metafile = photoset.get_metafile()

        if MetafileStateCheck.__metafile_has_no_group_entries(photoset_metafile):
            return False

        all_metafiles = util.flatten(photoset_metafile.posts.values())

        return not any([
            MetafileStateCheck.__group_entry_has_no_post_entries(all_metafiles),
            MetafileStateCheck.__metafile_has_not_published_entries(all_metafiles),
            MetafileStateCheck.__photoset_has_folders_not_in_metafile(photoset, all_metafiles),
        ])
